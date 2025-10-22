from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import (
    QuestionnaireVersion,Questionnaire)
from typing import List,Optional
from pydantic import BaseModel

router = APIRouter(prefix="/questionnaire")

# Response schema
class QuestionnaireResponse(BaseModel):
    id: int
    code: str
    label: str


@router.post("/add",response_model=QuestionnaireResponse)
def create_questionnaire(code: str, label: str, db: Session = Depends(get_db)):
    db_questionnaire = db.query(Questionnaire).filter(Questionnaire.code == code).first()
   
    if db_questionnaire:
        raise HTTPException(status_code=400, detail="Questionnaire code already exist")
    
    new_questionnaire = Questionnaire(code=code, label=label)
    db.add(new_questionnaire)
    db.commit()
    db.refresh(new_questionnaire)
    return new_questionnaire


@router.get("/getAll", response_model=List[QuestionnaireResponse])
def get_questionnaires(db: Session = Depends(get_db)):
    db_questionnaires = db.query(Questionnaire).all()

    if not db_questionnaires:
        raise HTTPException(status_code=404, detail="No questionnaires found")

    return db_questionnaires

# Get one questionnaire by ID
@router.get("/{questionnaire_id}", response_model=QuestionnaireResponse)
def get_questionnaire(questionnaire_id: int, db: Session = Depends(get_db)):
    questionnaire = db.query(Questionnaire).filter_by(id=questionnaire_id).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return questionnaire

# Update an existing questionnaire
@router.put("/{questionnaire_id}", response_model=QuestionnaireResponse)
def update_questionnaire(questionnaire_id: int, label: Optional[str] = None, db: Session = Depends(get_db)):
    questionnaire = db.query(Questionnaire).filter_by(id=questionnaire_id).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    if label:
        questionnaire.label = label
    db.commit()
    db.refresh(questionnaire)
    return questionnaire

# Delete a questionnaire
@router.delete("/{questionnaire_id}")
def delete_questionnaire(questionnaire_id: int, db: Session = Depends(get_db)):
    questionnaire = db.query(Questionnaire).filter_by(id=questionnaire_id).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    db.delete(questionnaire)
    db.commit()
    return {"message": "Questionnaire deleted successfully"}




