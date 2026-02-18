"""Cloud Storage service for document management."""

import logging
import mimetypes
import os
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing document storage (Cloud Storage or local filesystem)."""

    def __init__(
        self,
        bucket_name: str | None = None,
        use_local_storage: bool = True,
        local_storage_path: str = "/tmp/projectforge-documents",
    ):
        """
        Initialize storage service.

        Args:
            bucket_name: GCS bucket name (for production)
            use_local_storage: If True, use local filesystem (for development)
            local_storage_path: Path for local storage
        """
        self.bucket_name = bucket_name
        self.use_local_storage = use_local_storage
        self.local_storage_path = local_storage_path

        if use_local_storage:
            os.makedirs(local_storage_path, exist_ok=True)
            logger.info(f"Using local storage at: {local_storage_path}")
        else:
            try:
                from google.cloud import storage

                self.client = storage.Client()
                self.bucket = self.client.bucket(bucket_name)
                logger.info(f"Using Cloud Storage bucket: {bucket_name}")
            except ImportError:
                logger.warning(
                    "google-cloud-storage not installed, falling back to local storage"
                )
                self.use_local_storage = True
                os.makedirs(local_storage_path, exist_ok=True)

    def _get_local_path(self, file_path: str) -> str:
        """Get full local file path."""
        return os.path.join(self.local_storage_path, file_path)

    async def upload_file(
        self,
        file: BinaryIO,
        file_name: str,
        organization_id: UUID,
        project_id: UUID,
        content_type: str | None = None,
    ) -> str:
        """
        Upload file to storage.

        Args:
            file: File object to upload
            file_name: Original file name
            organization_id: Organization ID
            project_id: Project ID
            content_type: MIME type of file

        Returns:
            Storage path (GCS path or local path)
        """
        # Generate storage path
        storage_path = f"{organization_id}/{project_id}/{file_name}"

        if self.use_local_storage:
            # Save to local filesystem
            local_path = self._get_local_path(storage_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            with open(local_path, "wb") as f:
                content = file.read()
                f.write(content)

            logger.info(f"Uploaded file to local storage: {local_path}")
            return storage_path

        else:
            # Upload to Cloud Storage
            if content_type is None:
                content_type, _ = mimetypes.guess_type(file_name)

            blob = self.bucket.blob(storage_path)
            blob.upload_from_file(file, content_type=content_type)

            logger.info(f"Uploaded file to GCS: gs://{self.bucket_name}/{storage_path}")
            return f"gs://{self.bucket_name}/{storage_path}"

    async def download_file(self, file_path: str) -> bytes:
        """
        Download file from storage.

        Args:
            file_path: Storage path

        Returns:
            File content as bytes
        """
        if self.use_local_storage:
            local_path = self._get_local_path(file_path)
            with open(local_path, "rb") as f:
                return f.read()
        else:
            # Remove gs:// prefix if present
            if file_path.startswith("gs://"):
                file_path = file_path.replace(f"gs://{self.bucket_name}/", "")

            blob = self.bucket.blob(file_path)
            return blob.download_as_bytes()

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            file_path: Storage path

        Returns:
            True if deleted successfully
        """
        try:
            if self.use_local_storage:
                local_path = self._get_local_path(file_path)
                if os.path.exists(local_path):
                    os.remove(local_path)
                    logger.info(f"Deleted file from local storage: {local_path}")
                    return True
                return False
            else:
                if file_path.startswith("gs://"):
                    file_path = file_path.replace(f"gs://{self.bucket_name}/", "")

                blob = self.bucket.blob(file_path)
                blob.delete()
                logger.info(f"Deleted file from GCS: {file_path}")
                return True

        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists in storage."""
        if self.use_local_storage:
            return os.path.exists(self._get_local_path(file_path))
        else:
            if file_path.startswith("gs://"):
                file_path = file_path.replace(f"gs://{self.bucket_name}/", "")
            blob = self.bucket.blob(file_path)
            return blob.exists()


# Global storage instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Get or create storage service singleton."""
    global _storage_service
    if _storage_service is None:
        # Use local storage by default in development
        _storage_service = StorageService(use_local_storage=True)
    return _storage_service
