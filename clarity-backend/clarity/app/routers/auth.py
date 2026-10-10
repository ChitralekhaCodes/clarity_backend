from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import RegisterIn, LoginIn
from ..security import hash_password, verify_password, create_token, current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def user_out(u: User):
    return {"id": u.id, "name": u.name, "email": u.email, "is_admin": u.is_admin}


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(409, "Email already registered")
    user = User(name=body.name.strip(), email=email, password_hash=hash_password(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"token": create_token(user), "user": user_out(user)}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=body.email.lower()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"token": create_token(user), "user": user_out(user)}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return user_out(user)
