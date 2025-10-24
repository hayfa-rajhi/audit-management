from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.schemas.schema import FindingOut, FindingUpdate
from app.services import finding_service

router = APIRouter(prefix="/finding", tags=["Findings"])


@router.post("/finding")
def add_finding(audit_id: int, audit_question_id: int, type: str, description: str, db: Session = Depends(get_db)):
    return finding_service.add_finding(audit_id, audit_question_id, type, description, db)


@router.get("/", response_model=List[FindingOut])
def get_findings_by_question(audit_question_id: int, db: Session = Depends(get_db)):
    return finding_service.get_findings_by_question(audit_question_id, db)


@router.get("/by_audit", response_model=List[FindingOut])
def get_findings_by_audit(audit_id: int, db: Session = Depends(get_db)):
    return finding_service.get_findings_by_audit(audit_id, db)


@router.get("/all", response_model=List[FindingOut])
def list_all_findings(db: Session = Depends(get_db)):
    return finding_service.list_all_findings(db)


@router.put("/update/{finding_id}", response_model=FindingOut)
def update_finding(finding_id: int, update: FindingUpdate, db: Session = Depends(get_db)):
    return finding_service.update_finding(finding_id, update, db)


@router.delete("/{finding_id}")
def delete_finding(finding_id: int, db: Session = Depends(get_db)):
    return finding_service.delete_finding(finding_id, db)
