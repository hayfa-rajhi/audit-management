from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import Questionnaire
from app.schemas.schema import QuestionnaireCreate, QuestionnaireUpdate


def create_questionnaire(data: QuestionnaireCreate, db: Session):
    existing = db.query(Questionnaire).filter_by(code=data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Questionnaire code already exists")
    q = Questionnaire(code=data.code, label=data.label)
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


def get_all_questionnaires(db: Session):
    questionnaires = db.query(Questionnaire).all()
    if not questionnaires:
        raise HTTPException(status_code=404, detail="No questionnaires found")
    return questionnaires


def get_questionnaire(questionnaire_id: int, db: Session):
    q = db.query(Questionnaire).filter_by(id=questionnaire_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    return q


def update_questionnaire(questionnaire_id: int, data: QuestionnaireUpdate, db: Session):
    q = db.query(Questionnaire).filter_by(id=questionnaire_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    if data.label:
        q.label = data.label
    db.commit()
    db.refresh(q)
    return q


def delete_questionnaire(questionnaire_id: int, db: Session):
    q = db.query(Questionnaire).filter_by(id=questionnaire_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Questionnaire not found")
    db.delete(q)
    db.commit()
    return {"message": "Questionnaire deleted successfully"}
