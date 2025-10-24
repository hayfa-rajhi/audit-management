from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import Finding, CorrectiveAction, Audit, AuditQuestion
from app.schemas.schema import FindingUpdate


def add_finding(audit_id: int, audit_question_id: int, type: str, description: str, db: Session):
    # Validate audit
    audit = db.query(Audit).filter_by(id=audit_id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Validate question
    audit_question = db.query(AuditQuestion).filter_by(question_id=audit_question_id, audit_id=audit_id).first()
    if not audit_question:
        raise HTTPException(status_code=404, detail="Audit question not found or doesn't belong to this audit")

    # Create finding
    new_finding = Finding(audit_id=audit_id, audit_question_id=audit_question.id, type=type)
    db.add(new_finding)
    db.commit()
    db.refresh(new_finding)

    # Create corrective action
    new_corrective_action = CorrectiveAction(
        finding_id=new_finding.id,
        title=description,
        status="in_progress"  # keeping same as before
    )
    db.add(new_corrective_action)
    db.commit()
    db.refresh(new_corrective_action)

    return {
        "message": "Finding and corrective action created successfully",
        "finding_id": new_finding.id,
        "corrective_action_id": new_corrective_action.id
    }


def get_findings_by_question(audit_question_id: int, db: Session):
    findings = db.query(Finding).filter_by(audit_question_id=audit_question_id).all()
    if not findings:
        raise HTTPException(status_code=404, detail=f"No findings for question ID {audit_question_id}")
    return findings


def get_findings_by_audit(audit_id: int, db: Session):
    findings = db.query(Finding).filter_by(audit_id=audit_id).all()
    if not findings:
        raise HTTPException(status_code=404, detail=f"No findings for audit ID {audit_id}")
    return findings


def list_all_findings(db: Session):
    return db.query(Finding).all()


def update_finding(finding_id: int, update: FindingUpdate, db: Session):
    finding = db.query(Finding).filter_by(id=finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(finding, key, value)
    db.commit()
    db.refresh(finding)
    return finding


def delete_finding(finding_id: int, db: Session):
    finding = db.query(Finding).filter_by(id=finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    db.delete(finding)
    db.commit()
    return {"message": f"Finding {finding_id} deleted successfully"}
