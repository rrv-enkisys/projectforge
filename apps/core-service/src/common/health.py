"""Health check utilities for the core service."""

import time
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session_maker


class HealthCheck:
    """Health check utilities."""

    _start_time: float = time.time()

    @classmethod
    def get_uptime_seconds(cls) -> int:
        """Get service uptime in seconds."""
        return int(time.time() - cls._start_time)

    @staticmethod
    async def check_database() -> dict[str, Any]:
        """
        Check database connection health.

        Returns:
            dict: Health status with details
        """
        try:
            async with async_session_maker() as session:
                # Execute simple query
                result = await session.execute(text("SELECT 1"))
                result.scalar()

            return {
                "status": "healthy",
                "message": "Database connection OK",
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(exc)}",
            }

    @staticmethod
    async def check_database_pool() -> dict[str, Any]:
        """
        Check database connection pool status.

        Returns:
            dict: Pool statistics
        """
        try:
            from ..database import engine

            pool = engine.pool
            return {
                "status": "healthy",
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }
        except Exception as exc:
            return {
                "status": "unknown",
                "message": f"Could not get pool stats: {str(exc)}",
            }

    @classmethod
    async def get_health_status(cls, detailed: bool = False) -> dict[str, Any]:
        """
        Get comprehensive health status.

        Args:
            detailed: Include detailed checks (database, etc.)

        Returns:
            dict: Health status
        """
        health_status: dict[str, Any] = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": cls.get_uptime_seconds(),
        }

        if detailed:
            # Database check
            db_health = await cls.check_database()
            health_status["database"] = db_health

            # Pool check
            pool_health = await cls.check_database_pool()
            health_status["database_pool"] = pool_health

            # Overall status
            if db_health["status"] != "healthy":
                health_status["status"] = "degraded"

        return health_status
