from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.services import questionnaire_service
from app.schemas.schema import QuestionnaireCreate, QuestionnaireUpdate, QuestionnaireResponse

router = APIRouter(prefix="/questionnaire", tags=["Questionnaires"])


@router.post("/add", response_model=QuestionnaireResponse)
def create_questionnaire(data: QuestionnaireCreate, db: Session = Depends(get_db)):
    return questionnaire_service.create_questionnaire(data, db)


@router.get("/getAll", response_model=List[QuestionnaireResponse])
def get_questionnaires(db: Session = Depends(get_db)):
    return questionnaire_service.get_all_questionnaires(db)


@router.get("/{questionnaire_id}", response_model=QuestionnaireResponse)
def get_questionnaire(questionnaire_id: int, db: Session = Depends(get_db)):
    return questionnaire_service.get_questionnaire(questionnaire_id, db)


@router.put("/{questionnaire_id}", response_model=QuestionnaireResponse)
def update_questionnaire(questionnaire_id: int, data: QuestionnaireUpdate, db: Session = Depends(get_db)):
    return questionnaire_service.update_questionnaire(questionnaire_id, data, db)


@router.delete("/{questionnaire_id}")
def delete_questionnaire(questionnaire_id: int, db: Session = Depends(get_db)):
    return questionnaire_service.delete_questionnaire(questionnaire_id, db)
