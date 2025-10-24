from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import Question, QuestionnaireVersion, QuestionnaireVersionQuestion
from app.schemas.schema import QuestionCreate, QuestionUpdate


def create_question(data: QuestionCreate, questionnaire_version_id: int, db: Session):
    # 1. Verify questionnaire version exists
    qv = db.query(QuestionnaireVersion).filter_by(id=questionnaire_version_id).first()
    if not qv:
        raise HTTPException(status_code=404, detail="Questionnaire version not found")

    # 2. Check for duplicate question title
    existing_q = db.query(Question).filter_by(title=data.title).first()
    if existing_q:
        raise HTTPException(status_code=400, detail="Question already exists")

    # 3. Create new Question
    new_q = Question(**data.model_dump())
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


def get_question(question_id: int, db: Session):
    q = db.query(Question).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


def list_questions(db: Session):
    return db.query(Question).all()


def update_question(question_id: int, data: QuestionUpdate, db: Session):
    q = db.query(Question).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(q, key, value)

    db.commit()
    db.refresh(q)
    return q


def delete_question(question_id: int, db: Session):
    q = db.query(Question).filter_by(id=question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    db.delete(q)
    db.commit()
    return {"message": f"Question {question_id} deleted"}


def get_questions_by_version(version_id: int, db: Session):
    version = db.query(QuestionnaireVersion).filter_by(id=version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Questionnaire version not found")
    return version.questions
