from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from api.schemas import ConversationOut, MessageOut
from models import User, Conversation, Message
from api.auth import get_current_user
from logger import logger

router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.get("/", response_model=list[ConversationOut])
def get_conversations(
    guest_session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetches all conversations for the sidebar. 
    Prioritizes the authenticated user, falls back to the guest session.
    """
    if current_user:
        # Fetch logged-in user's history
        query = select(Conversation).where(
            Conversation.user_id == current_user.id
        ).order_by(Conversation.created_at.desc())
    
    elif guest_session_id:
        # Fetch anonymous guest's history
        query = select(Conversation).where(
            Conversation.guest_session_id == guest_session_id
        ).order_by(Conversation.created_at.desc())
        
    else:
        # No user and no guest ID provided
        return []

    conversations = db.execute(query).scalars().all()
    return conversations

@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    guest_session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Delete request for conversation {conversation_id}")

    conv = db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    ).scalar_one_or_none()

    if not conv:
        logger.warning(f"Delete failed: Conversation {conversation_id} not found")
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if current_user:
        if conv.user_id != current_user.id:
            logger.error(f"Unauthorized delete attempt by user {current_user.id} on {conversation_id}")
            raise HTTPException(status_code=403, detail="Not authorised")
    else:
        if conv.guest_session_id != guest_session_id:
            logger.error(f"Unauthorized delete attempt by guest {guest_session_id} on {conversation_id}")
            raise HTTPException(status_code=403, detail="Not authorised")

    try:    
        db.delete(conv)
        db.commit()
        logger.info(f"Successfully deleted conversation {conversation_id}")
        return {"status": "success", "message": "Conversation deleted"}
    except Exception as e:
        logger.error(f"Database error during deletion: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(
    conversation_id: str, 
    db: Session = Depends(get_db)
):
    """
    Fetches the chronological message history for a specific chat.
    Includes the cited_chunks JSON so the UI Drawer can rehydrate.
    """
    logger.info(f"Loading history for conversation: {conversation_id}")

    # Fetch all messages in chronological order
    messages = db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    ).scalars().all()

    return messages


