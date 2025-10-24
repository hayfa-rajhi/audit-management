from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.services import role_service
from app.schemas.schema import RoleCreate, RoleUpdate, RoleResponse, RoleAssignmentRequest

router = APIRouter(prefix="/role", tags=["Roles"])


@router.post("/add")
def create_role(data: RoleCreate, db: Session = Depends(get_db)):
    return role_service.create_role(data, db)


@router.get("/all", response_model=List[RoleResponse])
def get_all_roles(db: Session = Depends(get_db)):
    return role_service.get_all_roles(db)


@router.get("/{code}", response_model=RoleResponse)
def get_role(code: str, db: Session = Depends(get_db)):
    return role_service.get_role(code, db)


@router.put("/{code}", response_model=RoleResponse)
def update_role(code: str, data: RoleUpdate, db: Session = Depends(get_db)):
    return role_service.update_role(code, data, db)


@router.delete("/{code}")
def delete_role(code: str, db: Session = Depends(get_db)):
    return role_service.delete_role(code, db)


@router.post("/assign-role")
def assign_role(request: RoleAssignmentRequest, db: Session = Depends(get_db)):
    return role_service.assign_role_to_user(request, db)
