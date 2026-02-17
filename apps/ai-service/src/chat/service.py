from __future__ import annotations

"""Chat service for conversation management"""
import logging
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..embeddings.vertex_client import VertexAIClient, get_vertex_client
from .models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat conversation management"""

    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        vertex_client: VertexAIClient = Depends(get_vertex_client)
    ):
        self.db = db
        self.vertex_client = vertex_client

    async def create_session(
        self,
        project_id: UUID,
        organization_id: UUID,
        user_id: str,
        title: str | None = None
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            project_id=project_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(
        self,
        session_id: UUID,
        organization_id: UUID,
        with_messages: bool = False
    ) -> ChatSession | None:
        """Get chat session by ID"""
        query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.organization_id == organization_id
        )

        if with_messages:
            query = query.options(selectinload(ChatSession.messages))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        project_id: UUID,
        organization_id: UUID,
        user_id: str | None = None
    ) -> list[ChatSession]:
        """List chat sessions for a project"""
        query = select(ChatSession).where(
            ChatSession.project_id == project_id,
            ChatSession.organization_id == organization_id
        )

        if user_id:
            query = query.where(ChatSession.user_id == user_id)

        query = query.order_by(ChatSession.updated_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str
    ) -> ChatMessage:
        """Add a message to a chat session"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_conversation_history(
        self,
        session_id: UUID,
        limit: int = 20
    ) -> list[ChatMessage]:
        """Get recent messages from a session"""
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        return list(reversed(messages))  # Return in chronological order

    async def generate_response(
        self,
        session_id: UUID,
        user_message: str
    ) -> str:
        """
        Generate AI response to user message with conversation history

        Args:
            session_id: Chat session ID
            user_message: User's message

        Returns:
            AI-generated response
        """
        # Get conversation history
        history = await self.get_conversation_history(session_id)

        # Build prompt with history
        conversation = []
        for msg in history:
            conversation.append(f"{msg.role.upper()}: {msg.content}")

        conversation.append(f"USER: {user_message}")

        prompt = "\n\n".join([
            "You are an AI assistant helping with project management.",
            "Based on the conversation history, provide a helpful response.",
            "",
            "CONVERSATION:",
            "\n".join(conversation),
            "",
            "ASSISTANT:"
        ])

        # Generate response
        response = await self.vertex_client.generate_text(
            prompt=prompt,
            temperature=0.7,
            max_output_tokens=1024
        )

        # Store user message and assistant response
        await self.add_message(session_id, "user", user_message)
        await self.add_message(session_id, "assistant", response)

        logger.info(f"Generated response for session {session_id}")

        return response

    async def delete_session(
        self,
        session_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Delete a chat session"""
        session = await self.get_session(session_id, organization_id)
        if not session:
            return False

        await self.db.delete(session)
        await self.db.commit()
        return True
