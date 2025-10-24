from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services import user_service  
from typing import List
import uuid
from app.schemas.schema import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])




@router.post("/add", response_model=UserResponse)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(data, db)


@router.get("/all", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    return user_service.get_all_users(db)


@router.get("/{user_email}", response_model=UserResponse)
def get_user_by_email(user_email: str, db: Session = Depends(get_db)):
    return user_service.get_user_by_email(user_email, db)



@router.put("/{user_email}", response_model=UserResponse)
def update_user(user_email: str, data: UserUpdate, db: Session = Depends(get_db)):
    return user_service.update_user(user_email, data, db)


@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    return user_service.delete_user(user_id, db)
