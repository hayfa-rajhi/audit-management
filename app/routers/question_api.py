from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.services import question_service
from app.schemas.schema import QuestionCreate, QuestionUpdate, QuestionOut

router = APIRouter(prefix="/question", tags=["Questions"])


@router.post("/", response_model=QuestionOut)
def create_question(
    question: QuestionCreate,
    questionnaire_version_id: int,
    db: Session = Depends(get_db)
):
    return question_service.create_question(question, questionnaire_version_id, db)


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db)):
    return question_service.get_question(question_id, db)


@router.get("/", response_model=List[QuestionOut])
def list_questions(db: Session = Depends(get_db)):
    return question_service.list_questions(db)


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(question_id: int, data: QuestionUpdate, db: Session = Depends(get_db)):
    return question_service.update_question(question_id, data, db)


@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    return question_service.delete_question(question_id, db)


@router.get("/by_version/{version_id}", response_model=List[QuestionOut])
def get_questions_by_version(version_id: int, db: Session = Depends(get_db)):
    return question_service.get_questions_by_version(version_id, db)
