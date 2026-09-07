from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.models import User, UserRole, generate_uuid
from app.schemas import UserOut, UserCreate, Token, UserLogin
from app.api.deps import get_current_user
from app.audit.service import audit_service

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login_access_token(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(user.id, expires_delta=access_token_expires)

    audit_service.record_event(
        db=db,
        action="USER_LOGIN",
        entity_type="User",
        entity_id=user.id,
        user_id=user.id,
        metadata_json={"email": user.email, "role": user.role.value}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
def read_user_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        # Fallback for demo
        user = db.query(User).filter(User.role == UserRole.PROCUREMENT_OFFICER).first()
        if user:
            return user
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user
