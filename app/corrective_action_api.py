from pydantic import BaseModel
from enum import Enum
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import CorrectiveAction
from app.db import get_db

class CorrectiveActionStatus(str, Enum):
    opened = "opened"
    in_progress = "in_progress"
    closed = "closed"
    completed='completed'
    postponed='postponed'

class CorrectiveActionUpdate(BaseModel):
    title: Optional[str]
    status: Optional[CorrectiveActionStatus]

class CorrectiveActionOut(BaseModel):
    id: int
    finding_id: int
    title: str
    status: CorrectiveActionStatus

    class Config:
        orm_mode = True


router = APIRouter(prefix="/corrective_action")

# Get by ID
@router.get("/{action_id}", response_model=CorrectiveActionOut)
def get_corrective_action(action_id: int, db: Session = Depends(get_db)):
    action = db.query(CorrectiveAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found")
    return action

# List all
@router.get("/", response_model=list[CorrectiveActionOut])
def list_corrective_actions(db: Session = Depends(get_db)):
    return db.query(CorrectiveAction).all()

# Filter by status
@router.get("/status/{status}", response_model=list[CorrectiveActionOut])
def get_by_status(status: str, db: Session = Depends(get_db)):
    actions = db.query(CorrectiveAction).filter_by(status=status).all()
    return actions

# Update
@router.put("/{action_id}", response_model=CorrectiveActionOut)
def update_corrective_action(action_id: int, update: CorrectiveActionUpdate, db: Session = Depends(get_db)):
    action = db.query(CorrectiveAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found")
    for key, value in update.dict(exclude_unset=True).items():
        setattr(action, key, value)
    db.commit()
    db.refresh(action)
    return action

# Delete
@router.delete("/{action_id}")
def delete_corrective_action(action_id: int, db: Session = Depends(get_db)):
    action = db.query(CorrectiveAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found")
    db.delete(action)
    db.commit()
    return {"message": f"Corrective action {action_id} deleted"}
