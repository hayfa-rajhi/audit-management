from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import User
from app.schemas.schema import UserCreate, UserUpdate
import uuid


def create_user(data: UserCreate, db: Session):
    db_user = db.query(User).filter(User.email == data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_all_users(db: Session):
    return db.query(User).all()


def get_user_by_email(user_email: str, db: Session):
    user = db.query(User).filter(User.email == user_email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_user_by_id(user_id: uuid.UUID, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def update_user(user_email: str, data: UserUpdate, db: Session):
    user = db.query(User).filter(User.email == user_email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user(user_id: uuid.UUID, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return {"message": f"User {user.email} deleted successfully"}
