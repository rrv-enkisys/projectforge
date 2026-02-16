"""Chat API endpoints"""
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

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
    x_user_id: str = Header(..., alias="X-User-ID")
) -> SessionResponse:
    """Create a new chat session for a project"""
    session = await service.create_session(
        project_id=data.project_id,
        organization_id=x_organization_id,
        user_id=x_user_id,
        title=data.title
    )
    return SessionResponse.model_validate(session)


@router.get("/sessions/{session_id}", response_model=SessionWithMessages)
async def get_chat_session(
    session_id: UUID,
    service: ChatService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> SessionWithMessages:
    """Get chat session with message history"""
    session = await service.get_session(session_id, x_organization_id, with_messages=True)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    return SessionWithMessages.model_validate(session)


@router.get("/projects/{project_id}/sessions", response_model=list[SessionResponse])
async def list_project_sessions(
    project_id: UUID,
    service: ChatService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
    x_user_id: str = Header(..., alias="X-User-ID")
) -> list[SessionResponse]:
    """List all chat sessions for a project (for current user)"""
    sessions = await service.list_sessions(
        project_id=project_id,
        organization_id=x_organization_id,
        user_id=x_user_id
    )
    return [SessionResponse.model_validate(s) for s in sessions]


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    data: MessageCreate,
    service: ChatService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> dict:
    """
    Send a message and get AI response.
    Returns both the user message and AI response.
    """
    # Verify session exists and belongs to organization
    session = await service.get_session(data.session_id, x_organization_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    # Generate AI response
    response = await service.generate_response(data.session_id, data.content)

    return {
        "user_message": data.content,
        "assistant_response": response
    }


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: UUID,
    service: ChatService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> None:
    """Delete a chat session and all its messages"""
    deleted = await service.delete_session(session_id, x_organization_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
