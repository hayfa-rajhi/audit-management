from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Question,QuestionnaireVersionQuestion,QuestionnaireVersion
from app.db import get_db

router = APIRouter(prefix="/question")

from pydantic import BaseModel
from typing import Optional
from enum import Enum

class ResponseType(str, Enum):
    yes_no = "yes_no"
    scale = "scale"
    color = "color"
    text="text"
    file="file"

class CriticalityLevel(str, Enum):
    critical = "critical"
    not_ctrical = "not_ctrical"

class QuestionCreate(BaseModel):
    title: str
    response_type: ResponseType
    criticality: CriticalityLevel

class QuestionUpdate(BaseModel):
    title: Optional[str]
    response_type: Optional[ResponseType]
    criticality: Optional[CriticalityLevel]

class QuestionOut(BaseModel):
    id: int
    title: str
    response_type: ResponseType
    criticality: CriticalityLevel

    class Config:
        orm_mode = True


@router.post("/", response_model=QuestionOut)
def create_question(
    question: QuestionCreate,
    questionnaire_version_id: int,
    db: Session = Depends(get_db)
):
    # 1. Verify questionnaire version exists
    qv = db.query(QuestionnaireVersion).filter_by(id=questionnaire_version_id).first()
    if not qv:
        raise HTTPException(status_code=404, detail="Questionnaire version not found")

    # 2. Check for duplicate question title
    existing_q = db.query(Question).filter_by(title=question.title).first()
    if existing_q:
        raise HTTPException(status_code=400, detail="Question already exists")


    # 3. Create new Question
    new_q = Question(**question.model_dump())
    db.add(new_q)
    db.flush()   

    # 4. Link Question to Questionnaire Version
    link = QuestionnaireVersionQuestion(
        questionnaire_version_id=questionnaire_version_id,
        question_id=new_q.id
    )
    db.add(link)

    # 5. Commit once (atomic transaction)
    db.commit()
    db.refresh(new_q)

    return new_q


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q

@router.get("/", response_model=list[QuestionOut])
def list_questions(db: Session = Depends(get_db)):
    return db.query(Question).all()

@router.put("/{question_id}", response_model=QuestionOut)
def update_question(question_id: int, update: QuestionUpdate, db: Session = Depends(get_db)):
    q = db.query(Question).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(q, key, value)
    db.commit()
    db.refresh(q)
    return q

@router.delete("/{question_id}")
def delete_question(question_id: int, db: Session = Depends(get_db)):
    q = db.query(Question).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(q)
    db.commit()
    return {"message": f"Question {question_id} deleted"}


@router.get("/by_version/{version_id}", response_model=list[QuestionOut])
def get_questions_by_version(version_id: int, db: Session = Depends(get_db)):
    version = db.query(QuestionnaireVersion).filter_by(id=version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Questionnaire version not found")
    return version.questions
