from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import (
    Entity,QuestionnaireVersion,Questionnaire,AuditSession,User,UserRole,Audit,AuditParticipant,
    AuditQuestion,AuditResponse,Finding,CorrectiveAction,Attachment,AuditQuestion,Question)

from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta
import logging
from datetime import timezone, timedelta
from sqlalchemy.orm import Session
from app.utility import validate_final_score
import os
from fastapi import UploadFile, File

router = APIRouter(prefix="/audit")

# Setup logging
logging.basicConfig(
    filename="audit_reschedule.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Request schema for rescheduling
class RescheduleRequest(BaseModel):
    # audit_code: str  # e.g., "A-2025-01"
    audit_id:int
    new_start_time: Optional[datetime] = None
    new_end_time: Optional[datetime] = None
    # new_auditee_email: Optional[str] = None
    reason: str

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

@router.put("/reschedule")
def reschedule(request: RescheduleRequest, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter_by(id=request.audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    sessions = db.query(AuditSession).filter_by(audit_id=audit.id).order_by(AuditSession.start_time).all()
    if not sessions:
        raise HTTPException(status_code=404, detail="Audit session not found")

    if request.new_start_time or request.new_end_time:
        # Normalize to UTC
        start_time = (request.new_start_time or sessions[0].start_time).astimezone(timezone.utc)
        end_time = (request.new_end_time or sessions[-1].end_time).astimezone(timezone.utc)

        duration = end_time - start_time
        if duration.total_seconds() <= 0:
            raise HTTPException(status_code=400, detail="Invalid session duration: end_time must be after start_time")

        max_duration = timedelta(hours=2)
        current_start = start_time
        session_plan = []

        # Build the new session plan
        while current_start < end_time:
            current_end = min(current_start + max_duration, end_time)
            session_plan.append((current_start, current_end))
            current_start = current_end

        # Update existing sessions or create new ones
        for i, (new_start, new_end) in enumerate(session_plan):
            if i < len(sessions):
                sessions[i].start_time = new_start
                sessions[i].end_time = new_end
                logging.info(f"Audit {audit.id} session {i+1} updated to {new_start}–{new_end}")
            else:
                new_session = AuditSession(
                    audit_id=audit.id,
                    start_time=new_start,
                    end_time=new_end
                )
                db.add(new_session)
                logging.info(f"Audit {audit.id} new session created: {new_start}–{new_end}")

        # Delete leftover sessions
        for leftover in sessions[len(session_plan):]:
            db.delete(leftover)
            logging.info(f"Audit {audit.id} leftover session {leftover.id} deleted")

    # Update audit status
    audit.status = 'postponed'
    logging.info(f"Audit {audit.id} status updated to 'postponed' due to: {request.reason}")

    db.commit()
    return {"message": "Audit rescheduled successfully", "audit_id": audit.id}


#QUESTION here does we need to delete related records like sessions and participants
#FOR now we will not delete them because we need to see analytics about who cancel an audit always etc..
@router.put("/cancel/{audit_id}")
def cancel_audit(audit_id: int, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter_by(id=audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    audit.status = "cancled"  
    logging.info(f"Audit {audit.id} status updated to 'cancelled' due to supplier not ready")

    db.commit()
    return {"message": "Audit cancelled successfully", "audit_id": audit.id}

#NOT CLEAR but implemented related to specification
@router.put("/start/{audit_id}")
def start_audit(audit_id:int,db:Session=Depends(get_db)):
    audit = db.query(Audit).filter_by(id=audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    audit.status = "started"  
    logging.info(f"Audit {audit.id} status updated to 'started'")

    db.commit()
    return {"message": "Audit started successfully", "audit_id": audit.id}

@router.post("/record_answer")
def record_answer(
    audit_id: int,
    question_id: int,
    file: UploadFile = File(...),
    
    db: Session = Depends(get_db)
):
    # Validate audit
    audit = db.query(Audit).filter_by(id=audit_id).first()
    
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    question = db.query(Question).filter_by(id=question_id).first()
    if not question :
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Validate audit question
    auditQ = db.query(AuditQuestion).filter_by(audit_id=audit.id,question_id=question.id).first()
    if not auditQ:
        raise HTTPException(status_code=404, detail="AuditQuestion not found")
    

    auditee=db.query(AuditParticipant).filter_by(audit_id=audit.id,local_role="auditee").first()
    # Read file content
    file_bytes = file.file.read()

    # Create response
    new_audit_response = AuditResponse(
        audit_question_id=auditQ.id,
        author_id=auditee.user_id,  #
        value=file_bytes
    )
    db.add(new_audit_response)
    db.commit()
    db.refresh(new_audit_response)

    return {
        "message": "Response recorded successfully",
        "response_id": new_audit_response.id,
        "filename": file.filename
    }


@router.post("/finding")
def add_finding(
    audit_id: int,
    audit_question_id: int,
    type: str,
    description: str,
    db: Session = Depends(get_db)
):
    # 1. Validate audit
    audit = db.query(Audit).filter_by(id=audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # 2. Validate audit question
    audit_question = db.query(AuditQuestion).filter_by(id=audit_question_id, audit_id=audit_id).first()
    if not audit_question:
        raise HTTPException(status_code=404, detail="Audit question not found or doesn't belong to this audit")

    # 3. Create finding
    new_finding = Finding(
        audit_id=audit_id,
        audit_question_id=audit_question_id,
        type=type
    )
    db.add(new_finding)
    db.commit()
    db.refresh(new_finding)

    # 4. Create corrective action
    new_corrective_action = CorrectiveAction(
        finding_id=new_finding.id,
        title=description,
        status="in_progress"  # for now it is in progress_but we must replace it to opened
    )
    db.add(new_corrective_action)
    db.commit()
    db.refresh(new_corrective_action)

    # 5. Return result
    return {
        "message": "Finding and corrective action created successfully",
        "finding_id": new_finding.id,
        "corrective_action_id": new_corrective_action.id
    }


@router.get("/get/{audit_id}")
def get_audit(audit_id: int, db: Session = Depends(get_db)):
    audit = db.query(Audit).filter_by(id=audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    # Entity info
    entity = db.query(Entity).filter_by(id=audit.entity_id).first()

    # Questionnaire info
    qv = db.query(QuestionnaireVersion).filter_by(id=audit.questionnaire_version_id).first()
    questionnaire = db.query(Questionnaire).filter_by(id=qv.questionnaire_id).first() if qv else None

    # Sessions
    sessions = db.query(AuditSession).filter_by(audit_id=audit.id).order_by(AuditSession.start_time).all()
    session_data = [
        {"start_time": s.start_time, "end_time": s.end_time}
        for s in sessions
    ]

    # Participants
    participants = db.query(AuditParticipant).filter_by(audit_id=audit.id).all()
    participant_data = []
    for p in participants:
        user = db.query(User).filter_by(id=p.user_id).first()
        participant_data.append({
            "email": user.email if user else None,
            "role": p.local_role
        })

    return {
        "audit_id": audit.id,
        "status": audit.status,
        "entity": {
            "type": entity.type if entity else None,
            "code": entity.code if entity else None,
            "label": entity.label if entity else None
        },
        "questionnaire": {
            "code": questionnaire.code if questionnaire else None,
            "version": qv.version_no if qv else None
        },
        "sessions": session_data,
        "participants": participant_data
    }


#TO Be reviewed if we dont need to create a file using the api and only updating here status, or we just instruct
#the gpt via instructions when auditor close it it generates a report with finding and ca from the extchanged conversation
#NOTE we have to update the status of audit to add opened/closed status
@router.post("/close/")
def close_audit(audit_id: int, final_score: str,score_type, db: Session = Depends(get_db)):
    # 1. Retrieve audit
    audit = db.query(Audit).filter_by(id=audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # 2. Update audit status and final score
    validate_final_score(final_score, score_type)
    # Update audit
    # audit.status = "closed"
    audit.final_score_type = score_type
    audit.final_score = final_score
    logging.info(f"Audit {audit.id} closed with score {final_score} ({score_type})")
    audit.final_score = final_score
    logging.info(f"Audit {audit.id} status updated to 'closed' with score {final_score}")

    # 3. Gather related data
    questions = db.query(AuditQuestion).filter_by(audit_id=audit.id).all()
    responses = db.query(AuditResponse).filter(AuditResponse.audit_question_id.in_([q.id for q in questions])).all()
    findings = db.query(Finding).filter_by(audit_id=audit.id).all()
    corrective_actions = db.query(CorrectiveAction).filter(CorrectiveAction.finding_id.in_([f.id for f in findings])).all()
    participants = db.query(AuditParticipant).filter_by(audit_id=audit.id).all()

    # 4. Build report content (as text or binary)
    report_lines = [
        f"Audit ID: {audit.id}",
        f"Status: {audit.status}",
        f"Final Score: {audit.final_score}",
    ]
    
    report_lines.append("Questions and Responses:")
    for q in questions:
        q_responses = [r for r in responses if r.audit_question_id == q.id]
        for r in q_responses:
            report_lines.append(f"  - Q{q.id}: {r.value}")

    report_lines.append("Findings and Corrective Actions:")
    for f in findings:
        report_lines.append(f"  - Finding {f.id} ({f.type})")
        related_actions = [ca for ca in corrective_actions if ca.finding_id == f.id]
        for ca in related_actions:
            report_lines.append(f"    - Action: {ca.title} [{ca.status}]")

    report_lines.append("Participants:")
    for p in participants:
        user = db.query(User).filter_by(id=p.user_id).first()
        report_lines.append(f"  - {user.email} as {p.local_role}")

    report_text = "\n".join(report_lines)
    report_bytes = report_text.encode("utf-8")
    folder_path = "reports"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    # Create a dynamic file name based on the current date/time
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_filename = f"report_{current_datetime}-{audit.id}.txt"
    report_file_path = os.path.join(folder_path, report_filename)

    # Save the encoded bytes to a file under the 'reports' folder
    with open(report_file_path, "wb") as file:
        file.write(report_bytes)

    print(f"Report saved as '{report_file_path}'")
    # 5. Create attachment record
    attachment = Attachment(
    filename=report_filename,                     
    path=report_file_path,                         
    object=report_bytes                            
        )
    db.add(attachment)

    # 6. Final commit
    db.commit()

    return {
        "message": "Audit closed and report generated",
        "audit_id": audit.id,
        "final_score": final_score,
        "attachment_id": attachment.id
    }



@router.post("/question")
def add_audit_question(audit_id:int,question_id,db:Session=Depends(get_db)):
    
    audit = db.query(Audit).filter_by(id=audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    question = db.query(Question).filter_by(id=question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    audit_question=AuditQuestion(audit_id=audit_id,
                                 question_id=question_id)
    db.add(audit_question)
    db.commit()
    db.refresh(audit_question)
    return {
        "message": f"audit question  added successfully to {audit.id}",
        "audit_question": question.title,
    }
