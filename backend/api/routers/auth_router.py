from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from api.schemas import UserCreate
from models import User
from api.auth import get_password_hash, create_access_token, verify_password, get_current_user
from logger import logger

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Registration attempt for email: {user.email}")

    try:
        db_user = db.execute(
            select(User).where(User.email == user.email)
        ).scalar_one_or_none()

        if db_user:
            logger.warning(f"Registration failed: Email {user.email} already exists")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = get_password_hash(user.password)
        new_user = User(name=user.name, email=user.email, hashed_password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info(f"User registered successfully: {new_user.id}")
        # Auto login after registration
        access_token = create_access_token(data={"sub": new_user.id})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "name": new_user.name,
                "email": new_user.email
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Login attempt for: {form_data.username}")

    try: 
        user = db.execute(
            select(User).where(User.email == form_data.username)
        ).scalar_one_or_none()

        if not user or not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Failed login attempt for: {form_data.username}")
            raise HTTPException(status_code=401, detail="Incorrect email or password.")
        
        logger.info(f"Successful login: {user.id}")
        access_token = create_access_token(data={"sub": user.id})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Login system error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Authentication service unavailable")

@router.get("/users/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "name": current_user.name,
        "email": current_user.email
    }