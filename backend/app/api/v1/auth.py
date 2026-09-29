"""Registration and login. SRS 2.2, REQ-23."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas import LoginRequest, Token, UserCreate, UserOut
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])


def normalise_email(email: str) -> str:
    """One canonical form for an address, used on the way in and on lookup.

    Email domains are case-insensitive by specification, and no mail provider
    in practice treats the local part as case-sensitive either. Comparing them
    literally means a capitalised first letter -- which phone keyboards and
    Windows autocomplete add without being asked -- reads as a wrong password.
    """
    return email.strip().lower()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Public registration always creates a Victim. Elevated roles are granted
    by an administrator (REQ-23), never self-selected -- otherwise anyone could
    sign up as an investigator and read every case."""
    # Addresses are stored lower-cased. Nobody thinks of Asha@ and asha@ as two
    # accounts, and phone keyboards capitalise the first letter by default, so
    # storing them as typed produces accounts their owners cannot sign in to.
    email = normalise_email(payload.email)

    existing = db.scalars(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    user = User(
        full_name=payload.full_name,
        email=email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=Role.VICTIM,
    )
    db.add(user)
    db.flush()
    audit.record(db, actor_id=user.id, action="user.register", target=f"user:{user.id}")
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.scalars(
        select(User).where(User.email == normalise_email(payload.email))
    ).first()

    # Same message and code for "no such user" and "wrong password" so the
    # endpoint cannot be used to enumerate which emails are registered.
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated"
        )

    audit.record(db, actor_id=user.id, action="user.login", target=f"user:{user.id}")
    db.commit()

    return Token(access_token=create_access_token(str(user.id), user.role), role=user.role)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
