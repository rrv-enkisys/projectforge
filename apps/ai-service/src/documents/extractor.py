"""Text extraction from various document formats."""

import logging
from typing import BinaryIO

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract text from various document formats."""

    @staticmethod
    async def extract_text(file_content: bytes, file_type: str) -> str:
        """
        Extract text from file content.

        Args:
            file_content: File content as bytes
            file_type: MIME type or file extension

        Returns:
            Extracted text
        """
        file_type = file_type.lower()

        try:
            # Plain text
            if file_type in ("text/plain", ".txt"):
                return file_content.decode("utf-8")

            # PDF files
            elif file_type in ("application/pdf", ".pdf"):
                return await TextExtractor._extract_from_pdf(file_content)

            # Word documents
            elif file_type in (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".docx",
            ):
                return await TextExtractor._extract_from_docx(file_content)

            # Markdown
            elif file_type in ("text/markdown", ".md"):
                return file_content.decode("utf-8")

            # HTML
            elif file_type in ("text/html", ".html"):
                return await TextExtractor._extract_from_html(file_content)

            # Default: try to decode as text
            else:
                try:
                    return file_content.decode("utf-8")
                except UnicodeDecodeError:
                    logger.warning(f"Could not decode file type: {file_type}")
                    return ""

        except Exception as e:
            logger.error(f"Error extracting text from {file_type}: {e}")
            raise

    @staticmethod
    async def _extract_from_pdf(content: bytes) -> str:
        """Extract text from PDF using PyPDF2 or pdfplumber."""
        try:
            # Try pdfplumber first (better quality)
            import pdfplumber
            import io

            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                return "\n\n".join(text_parts)

        except ImportError:
            # Fallback to PyPDF2
            try:
                import PyPDF2
                import io

                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text_parts = []
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n\n".join(text_parts)

            except ImportError:
                logger.error("Neither pdfplumber nor PyPDF2 installed, cannot extract PDF")
                raise ImportError("PDF extraction requires pdfplumber or PyPDF2")

    @staticmethod
    async def _extract_from_docx(content: bytes) -> str:
        """Extract text from DOCX using python-docx."""
        try:
            import docx
            import io

            doc = docx.Document(io.BytesIO(content))
            text_parts = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)

            return "\n\n".join(text_parts)

        except ImportError:
            logger.error("python-docx not installed, cannot extract DOCX")
            raise ImportError("DOCX extraction requires python-docx")

    @staticmethod
    async def _extract_from_html(content: bytes) -> str:
        """Extract text from HTML using BeautifulSoup."""
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)

            return text

        except ImportError:
            logger.warning("beautifulsoup4 not installed, returning raw HTML")
            return content.decode("utf-8")


# Global extractor instance
_text_extractor: TextExtractor | None = None


def get_text_extractor() -> TextExtractor:
    """Get or create text extractor singleton."""
    global _text_extractor
    if _text_extractor is None:
        _text_extractor = TextExtractor()
    return _text_extractor
