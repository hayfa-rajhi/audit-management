from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import (
    Entity,QuestionnaireVersion,Questionnaire,AuditSession,User,UserRole,Audit,AuditParticipant)

from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta
import logging
from datetime import timezone

router = APIRouter(prefix="/audit")

# Setup logging
logging.basicConfig(
    filename="audit_reschedule.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
class auditRequest(BaseModel):
    entity_code: str
    auditor_email: str
    auditee_email: str
    start_time: datetime
    end_time: datetime
    questionnaire_code:str

@router.post("/plan")
def plan_audit(auditR: auditRequest, db: Session = Depends(get_db)):
    # 1. Retrieve the entity
    entity = db.query(Entity).filter_by(code=auditR.entity_code).first()
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity '{auditR.entity_code}' not found")

    # 2. Retrieve the questionnaire and latest version
    questionnaire = db.query(Questionnaire).filter_by(code=auditR.questionnaire_code).first()
    if not questionnaire:
        raise HTTPException(status_code=404, detail=f"Questionnaire '{auditR.questionnaire_code}' not found")

    questionnaire_version = db.query(QuestionnaireVersion)\
        .filter_by(questionnaire_id=questionnaire.id)\
        .order_by(QuestionnaireVersion.version_no.desc())\
        .first()
    if not questionnaire_version:
        raise HTTPException(status_code=404, detail=f"No version found for questionnaire '{auditR.questionnaire_code}'")

    # 3. Retrieve users
    auditor = db.query(User).filter_by(email=auditR.auditor_email).first()
    auditee = db.query(User).filter_by(email=auditR.auditee_email).first()
    if not auditor or not auditee:
        raise HTTPException(status_code=404, detail="Auditor or Auditee not found")

    # 4. Validate roles
    auditor_role = db.query(UserRole).filter_by(user_id=auditor.id, role_code='auditor').first()
    auditee_role = db.query(UserRole).filter_by(user_id=auditee.id, role_code='auditee').first()
    if not auditor_role:
        raise HTTPException(status_code=403, detail=f"User '{auditR.auditor_email}' does not have 'auditor' role")
    if not auditee_role:
        raise HTTPException(status_code=403, detail=f"User '{auditR.auditee_email}' does not have 'auditee' role")

    # 5. Create the Audit
    audit = Audit(
        entity_id=entity.id,
        questionnaire_version_id=questionnaire_version.id,
        status='planned',
        final_score_type='scale',
        final_score=None
    )
    db.add(audit)
    db.flush()

    # 6. Create AuditSession(s)
    duration = auditR.end_time - auditR.start_time
    max_duration = timedelta(hours=2)

    if duration <= max_duration:
        db.add(AuditSession(audit_id=audit.id, start_time=auditR.start_time, end_time=auditR.end_time))
    else:
        current_start = auditR.start_time
        while current_start < auditR.end_time:
            current_end = min(current_start + max_duration, auditR.end_time)
            db.add(AuditSession(audit_id=audit.id, start_time=current_start, end_time=current_end))
            current_start = current_end

    # 7. Assign participants
    db.add(AuditParticipant(audit_id=audit.id, user_id=auditor.id, local_role='auditor'))
    db.add(AuditParticipant(audit_id=audit.id, user_id=auditee.id, local_role='auditee'))

    # 8. Create AuditLog entry (optional)
    # db.add(AuditLog(audit_id=audit.id, action='planned', timestamp=datetime.utcnow()))

    db.commit()
    return {"message": "Audit planned successfully", "audit_id": audit.id}


# Request schema
class RescheduleRequest(BaseModel):
    # audit_code: str  # e.g., "A-2025-01"
    audit_id:int
    new_start_time: Optional[datetime] = None
    new_end_time: Optional[datetime] = None
    # new_auditee_email: Optional[str] = None
    reason: str
@router.put("/reschedule")
def reschedule(request: RescheduleRequest, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter_by(id=request.audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    sessions = db.query(AuditSession).filter_by(audit_id=audit.id).all()
    if not sessions:
        raise HTTPException(status_code=404, detail="Audit session not found")

    if request.new_start_time or request.new_end_time:
        session = sessions[0]

        # Normalize to UTC
        start_time = (request.new_start_time or session.start_time).astimezone(timezone.utc)
        end_time = (request.new_end_time or session.end_time).astimezone(timezone.utc)

        duration = end_time - start_time
        max_duration = timedelta(hours=2)

        if duration.total_seconds() <= 0:
            raise HTTPException(status_code=400, detail="Invalid session duration: end_time must be after start_time")

        if duration <= max_duration:
            # Update first session
            session.start_time = start_time
            session.end_time = end_time
            logging.info(f"Audit {audit.id} session updated to {start_time}–{end_time}")

            # Delete extra sessions
            for extra_session in sessions[1:]:
                db.delete(extra_session)
                logging.info(f"Audit {audit.id} extra session {extra_session.id} deleted")
        else:
            # Update existing sessions sequentially
            current_start = start_time
            for i, session in enumerate(sessions):
                current_end = min(current_start + max_duration, end_time)
                session.start_time = current_start
                session.end_time = current_end
                logging.info(f"Audit {audit.id} session updated to {current_start}–{current_end}")
                current_start = current_end
                if current_start >= end_time:
                    # Delete any remaining unused sessions
                    for leftover in sessions[i+1:]:
                        db.delete(leftover)
                        logging.info(f"Audit {audit.id} leftover session {leftover.id} deleted")
                    break


    # # Update auditee if provided
    # if request.new_auditee_email:
    #     new_auditee = db.query(User).filter_by(email=request.new_auditee_email).first()
    #     if not new_auditee:
    #         raise HTTPException(status_code=404, detail="New auditee not found")

    #     auditee_participant = db.query(AuditParticipant)\
    #         .filter_by(audit_id=audit.id, local_role='auditee')\
    #         .first()
    #     if auditee_participant:
    #         auditee_participant.user_id = new_auditee.id
    #         logging.info(f"Audit {audit.id} auditee changed to {new_auditee.email}")

    # Update audit status
    audit.status = 'postponed'
    logging.info(f"Audit {audit.id} status updated to 'postponed' due to: {request.reason}")

    db.commit()
    return {"message": "Audit rescheduled successfully", "audit_id": audit.id}

