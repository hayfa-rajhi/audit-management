from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import CorrectiveAction

def get_corrective_action(action_id: int, db: Session):
    action = db.query(CorrectiveAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found")
    return action

def list_corrective_actions(db: Session):
    return db.query(CorrectiveAction).all()

def get_actions_by_status(status: str, db: Session):
    return db.query(CorrectiveAction).filter_by(status=status).all()

def update_corrective_action(action_id: int, update_data: dict, db: Session):
    action = db.query(CorrectiveAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found")
    for key, value in update_data.items():
        setattr(action, key, value)
    db.commit()
    db.refresh(action)
    return action

def delete_corrective_action(action_id: int, db: Session):
    action = db.query(CorrectiveAction).filter_by(id=action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Corrective action not found")
    db.delete(action)
    db.commit()
    return {"message": f"Corrective action {action_id} deleted"}
