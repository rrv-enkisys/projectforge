from __future__ import annotations

"""Chat service for conversation management"""
import logging
from datetime import datetime
from uuid import UUID

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..copilot.project_data import ProjectDataRepository
from ..database import get_db
from ..documents.repository import DocumentRepository
from ..embeddings.service import EmbeddingService
from ..embeddings.vertex_client import VertexAIClient, get_vertex_client
from .models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)

# Max messages to include in prompt context window
MAX_HISTORY_MESSAGES = 20
# Approximate max chars of context to send to LLM
MAX_CONTEXT_CHARS = 4000


class ChatService:
    """Service for chat conversation management with RAG integration"""

    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        vertex_client: VertexAIClient = Depends(get_vertex_client),
    ) -> None:
        self.db = db
        self.vertex_client = vertex_client
        self.embedding_service = EmbeddingService(vertex_client)
        self.project_data_repo = ProjectDataRepository(db)

    async def create_session(
        self,
        project_id: UUID | None,
        organization_id: UUID,
        user_id: str,
        title: str | None = None,
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            project_id=project_id,
            organization_id=organization_id,
            user_id=user_id,
            title=title,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(
        self,
        session_id: UUID,
        organization_id: UUID,
        with_messages: bool = False,
    ) -> ChatSession | None:
        """Get chat session by ID"""
        query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.organization_id == organization_id,
        )

        if with_messages:
            query = query.options(selectinload(ChatSession.messages))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_sessions(
        self,
        project_id: UUID,
        organization_id: UUID,
        user_id: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[ChatSession]:
        """List chat sessions for a project"""
        query = select(ChatSession).where(
            ChatSession.project_id == project_id,
            ChatSession.organization_id == organization_id,
        )

        if user_id:
            query = query.where(ChatSession.user_id == user_id)

        query = query.order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_user_sessions(
        self,
        organization_id: UUID,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[ChatSession]:
        """List all chat sessions for a user across all projects"""
        query = (
            select(ChatSession)
            .where(
                ChatSession.organization_id == organization_id,
                ChatSession.user_id == user_id,
            )
            .order_by(ChatSession.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
    ) -> ChatMessage:
        """Add a message to a chat session"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_conversation_history(
        self,
        session_id: UUID,
        limit: int = MAX_HISTORY_MESSAGES,
    ) -> list[ChatMessage]:
        """Get recent messages from a session in chronological order"""
        query = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        return list(reversed(messages))  # Return in chronological order

    async def get_rag_context(
        self,
        question: str,
        project_id: UUID,
        organization_id: UUID,
        max_chunks: int = 3,
    ) -> str:
        """
        Retrieve relevant document context via RAG for the question.
        Returns formatted context string, or empty string if no docs found.
        """
        try:
            query_embedding = await self.embedding_service.embed_query(question)
            doc_repo = DocumentRepository(self.db)
            chunks_with_scores = await doc_repo.vector_search(
                query_embedding=query_embedding,
                project_id=project_id,
                organization_id=organization_id,
                limit=max_chunks,
            )

            if not chunks_with_scores:
                return ""

            # Only use high-relevance chunks (similarity > 0.5)
            relevant = [(c, s) for c, s in chunks_with_scores if s > 0.5]
            if not relevant:
                return ""

            context_parts = []
            for chunk, score in relevant:
                context_parts.append(f"[Relevance: {score:.2f}]\n{chunk.content}")

            return "\n\n---\n\n".join(context_parts)

        except Exception as e:
            logger.debug(f"RAG context retrieval failed (non-critical): {e}")
            return ""

    async def generate_response(
        self,
        session_id: UUID,
        user_message: str,
        project_id: UUID | None = None,
        organization_id: UUID | None = None,
    ) -> str:
        """
        Generate AI response to user message with conversation history
        and optional RAG context from project documents.
        """
        # Get conversation history
        history = await self.get_conversation_history(session_id)

        # Build project context from live DB data
        project_context = ""
        if project_id and organization_id:
            try:
                project_data = await self.project_data_repo.get_project_data(
                    project_id=project_id,
                    organization_id=organization_id,
                )

                tasks = project_data.get("tasks", [])
                milestones = project_data.get("milestones", [])
                today = datetime.now().date()

                overdue_tasks = [
                    t for t in tasks
                    if t.get("due_date") and t["due_date"] < str(today)
                    and t.get("status") not in ("done", "completed")
                ]
                in_progress = [t for t in tasks if t.get("status") == "in_progress"]
                completed = [t for t in tasks if t.get("status") in ("done", "completed")]

                project_context = f"""
PROJECT CONTEXT (use this to answer questions about this project):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project: {project_data.get('name', 'Unknown')}
Status: {project_data.get('status', 'Unknown')}
Timeline: {project_data.get('start_date', '?')} → {project_data.get('end_date', '?')}

TASKS SUMMARY:
- Total: {len(tasks)}
- Completed: {len(completed)}
- In Progress: {len(in_progress)}
- Overdue: {len(overdue_tasks)}

OVERDUE TASKS:
{chr(10).join([f"  • {t['title']} (due: {t['due_date']})" for t in overdue_tasks[:5]]) or '  None'}

IN PROGRESS:
{chr(10).join([f"  • {t['title']}" for t in in_progress[:5]]) or '  None'}

MILESTONES:
{chr(10).join([f"  • {m['title']} - {m['status']} (target: {m['target_date']})" for m in milestones]) or '  None'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            except Exception as e:
                logger.warning(f"Failed to load project context: {e}")
                project_context = ""

        # Retrieve RAG context if project context is available
        rag_context = ""
        if project_id and organization_id:
            rag_context = await self.get_rag_context(
                user_message, project_id, organization_id
            )

        # Build prompt parts
        system_prompt = f"""You are an AI assistant for ProjectForge, a project management platform.
{project_context}
Be concise, practical, and helpful. When asked about tasks, milestones, or project status, \
use the PROJECT CONTEXT above to give accurate answers.
"""
        parts: list[str] = [system_prompt]

        # Include RAG context if available
        if rag_context:
            parts.append(
                f"RELEVANT DOCUMENT CONTEXT:\n{rag_context[:MAX_CONTEXT_CHARS]}"
            )

        # Include conversation history
        if history:
            conversation_lines = [
                f"{msg.role.upper()}: {msg.content}" for msg in history
            ]
            parts.append("CONVERSATION HISTORY:\n" + "\n\n".join(conversation_lines))

        parts.append(f"USER: {user_message}")
        parts.append("ASSISTANT:")

        prompt = "\n\n".join(parts)

        # Generate response (graceful fallback if Vertex AI unavailable)
        try:
            response = await self.vertex_client.generate_text(
                prompt=prompt,
                temperature=0.7,
                max_output_tokens=1024,
            )
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Vertex AI unavailable, using fallback response: {e}")
            if "429" in err_str or "Resource exhausted" in err_str or "quota" in err_str.lower():
                response = (
                    "⏳ El servicio de IA está temporalmente saturado (límite de cuota de Gemini alcanzado). "
                    "Por favor espera unos segundos y vuelve a intentarlo."
                )
            else:
                response = (
                    "⚠️ El servicio de IA no está disponible en este momento. "
                    "Por favor intenta de nuevo en unos momentos.\n\n"
                    f"Tu mensaje fue: *{user_message}*"
                )

        # Store user message and assistant response
        await self.add_message(session_id, "user", user_message)
        await self.add_message(session_id, "assistant", response)

        # Auto-title session from first message if no title set
        if not history:
            await self._auto_title_session(session_id, user_message)

        logger.info(f"Generated response for session {session_id}, rag_context={'yes' if rag_context else 'no'}")

        return response

    async def stream_response(
        self,
        session_id: UUID,
        user_message: str,
        project_id: UUID | None = None,
        organization_id: UUID | None = None,
    ):
        """
        Stream AI response for better UX.
        Saves full response to DB after streaming completes.
        """
        history = await self.get_conversation_history(session_id)

        project_context = ""
        if project_id and organization_id:
            try:
                project_data = await self.project_data_repo.get_project_data(
                    project_id=project_id,
                    organization_id=organization_id,
                )
                tasks = project_data.get("tasks", [])
                milestones = project_data.get("milestones", [])
                today = datetime.now().date()
                overdue_tasks = [
                    t for t in tasks
                    if t.get("due_date") and t["due_date"] < str(today)
                    and t.get("status") not in ("done", "completed")
                ]
                in_progress = [t for t in tasks if t.get("status") == "in_progress"]
                completed = [t for t in tasks if t.get("status") in ("done", "completed")]
                project_context = f"""
PROJECT CONTEXT (use this to answer questions about this project):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project: {project_data.get('name', 'Unknown')}
Status: {project_data.get('status', 'Unknown')}
Timeline: {project_data.get('start_date', '?')} → {project_data.get('end_date', '?')}

TASKS SUMMARY:
- Total: {len(tasks)}
- Completed: {len(completed)}
- In Progress: {len(in_progress)}
- Overdue: {len(overdue_tasks)}

OVERDUE TASKS:
{chr(10).join([f"  • {t['title']} (due: {t['due_date']})" for t in overdue_tasks[:5]]) or '  None'}

IN PROGRESS:
{chr(10).join([f"  • {t['title']}" for t in in_progress[:5]]) or '  None'}

MILESTONES:
{chr(10).join([f"  • {m['title']} - {m['status']} (target: {m['target_date']})" for m in milestones]) or '  None'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            except Exception as e:
                logger.warning(f"Failed to load project context for stream: {e}")
                project_context = ""

        rag_context = ""
        if project_id and organization_id:
            rag_context = await self.get_rag_context(
                user_message, project_id, organization_id
            )

        system_prompt = f"""You are an AI assistant for ProjectForge, a project management platform.
{project_context}
Be concise, practical, and helpful. When asked about tasks, milestones, or project status, \
use the PROJECT CONTEXT above to give accurate answers.
"""
        parts: list[str] = [system_prompt]

        if rag_context:
            parts.append(
                f"RELEVANT DOCUMENT CONTEXT:\n{rag_context[:MAX_CONTEXT_CHARS]}"
            )

        if history:
            conversation_lines = [
                f"{msg.role.upper()}: {msg.content}" for msg in history
            ]
            parts.append("CONVERSATION HISTORY:\n" + "\n\n".join(conversation_lines))

        parts.append(f"USER: {user_message}")
        parts.append("ASSISTANT:")

        prompt = "\n\n".join(parts)

        # Store user message first
        await self.add_message(session_id, "user", user_message)

        # Stream response and accumulate for storage
        full_response_parts: list[str] = []
        try:
            response_stream = await self.vertex_client.generate_text_stream(
                prompt=prompt,
                temperature=0.7,
                max_output_tokens=1024,
            )
            for chunk in response_stream:
                text = chunk.text if hasattr(chunk, "text") else str(chunk)
                full_response_parts.append(text)
                yield text
        finally:
            # Always save complete response to DB
            if full_response_parts:
                full_response = "".join(full_response_parts)
                await self.add_message(session_id, "assistant", full_response)

                if not history:
                    await self._auto_title_session(session_id, user_message)

    async def _auto_title_session(self, session_id: UUID, first_message: str) -> None:
        """Generate and set a title for the session based on the first message."""
        try:
            session_result = await self.db.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
            session = session_result.scalar_one_or_none()

            if session and not session.title:
                # Generate a short title from the first message
                title = first_message[:60].strip()
                if len(first_message) > 60:
                    title += "..."
                session.title = title
                await self.db.commit()
        except Exception as e:
            logger.debug(f"Could not auto-title session {session_id}: {e}")

    async def delete_session(
        self,
        session_id: UUID,
        organization_id: UUID,
    ) -> bool:
        """Delete a chat session and all its messages"""
        session = await self.get_session(session_id, organization_id)
        if not session:
            return False

        await self.db.delete(session)
        await self.db.commit()
        return True
