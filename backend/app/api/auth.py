from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, get_current_user_id, get_password_hash, verify_password
from app.models import User
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)) -> Token:
    """Register a new user."""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate token
    access_token = create_access_token(subject=new_user.id)
    return Token(access_token=access_token, user=UserResponse.model_validate(new_user))


@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Login user and return access token."""
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def read_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Get current user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.model_validate(user)
