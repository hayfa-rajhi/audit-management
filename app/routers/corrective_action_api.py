from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services import *
from pydantic import BaseModel
from enum import Enum
from typing import Optional

router = APIRouter(prefix="/corrective_action")

class CorrectiveActionStatus(str, Enum):
    opened = "opened"
    in_progress = "in_progress"
    closed = "closed"
    completed = "completed"
    postponed = "postponed"

class CorrectiveActionUpdate(BaseModel):
    title: Optional[str]
    status: Optional[CorrectiveActionStatus]

class CorrectiveActionOut(BaseModel):
    id: int
    finding_id: int
    title: str
    status: CorrectiveActionStatus

    model_config = {"from_attributes": True}


@router.get("/{action_id}", response_model=CorrectiveActionOut)
def get_action(action_id: int, db: Session = Depends(get_db)):
    return get_corrective_action(action_id, db)

@router.get("/", response_model=list[CorrectiveActionOut])
def list_actions(db: Session = Depends(get_db)):
    return list_corrective_actions(db)

@router.get("/status/{status}", response_model=list[CorrectiveActionOut])
def list_by_status(status: str, db: Session = Depends(get_db)):
    return get_actions_by_status(status, db)

@router.put("/{action_id}", response_model=CorrectiveActionOut)
def update_action(action_id: int, update: CorrectiveActionUpdate, db: Session = Depends(get_db)):
    return update_corrective_action(action_id, update.model_dump(exclude_unset=True), db)

@router.delete("/{action_id}")
def delete_action(action_id: int, db: Session = Depends(get_db)):
    return delete_corrective_action(action_id, db)
