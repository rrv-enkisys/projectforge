from __future__ import annotations

"""Chat API endpoints"""
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse

from .schemas import (
    CreateSession,
    MessageCreate,
    MessageResponse,
    SessionResponse,
    SessionWithMessages,
)
from .service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    data: CreateSession,
    service: ChatService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> SessionResponse:
    """Create a new chat session for a project"""
    session = await service.create_session(
        project_id=data.project_id,
        organization_id=x_organization_id,
        user_id=x_user_id,
        title=data.title,
    )
    return SessionResponse.model_validate(session)


@router.get("/sessions/{session_id}", response_model=SessionWithMessages)
async def get_chat_session(
    session_id: UUID,
    service: ChatService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
) -> SessionWithMessages:
    """Get chat session with message history"""
    session = await service.get_session(session_id, x_organization_id, with_messages=True)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return SessionWithMessages.model_validate(session)


@router.get("/projects/{project_id}/sessions", response_model=list[SessionResponse])
async def list_project_sessions(
    project_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: ChatService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
    x_user_id: str = Header(..., alias="X-User-ID"),
) -> list[SessionResponse]:
    """List all chat sessions for a project (for current user)"""
    sessions = await service.list_sessions(
        project_id=project_id,
        organization_id=x_organization_id,
        user_id=x_user_id,
        skip=skip,
        limit=limit,
    )
    return [SessionResponse.model_validate(s) for s in sessions]


@router.post("/messages", response_model=dict)
async def send_message(
    data: MessageCreate,
    service: ChatService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
) -> dict:
    """
    Send a message and get AI response with optional RAG context.
    Returns both the user message and AI response.
    """
    session = await service.get_session(data.session_id, x_organization_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    # Use project_id from session if not provided in message
    project_id = data.project_id or session.project_id

    response = await service.generate_response(
        session_id=data.session_id,
        user_message=data.content,
        project_id=project_id,
        organization_id=x_organization_id,
    )

    return {
        "user_message": data.content,
        "assistant_response": response,
        "session_id": str(data.session_id),
    }


@router.post("/messages/stream")
async def stream_message(
    data: MessageCreate,
    service: ChatService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
) -> StreamingResponse:
    """
    Send a message and stream the AI response token by token.
    Uses Server-Sent Events format for real-time streaming.
    """
    session = await service.get_session(data.session_id, x_organization_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )

    project_id = data.project_id or session.project_id

    async def generate():
        async for chunk in service.stream_response(
            session_id=data.session_id,
            user_message=data.content,
            project_id=project_id,
            organization_id=x_organization_id,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: UUID,
    service: ChatService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
) -> Response:
    """Delete a chat session and all its messages"""
    deleted = await service.delete_session(session_id, x_organization_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
