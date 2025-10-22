from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Role,UserRole,User
from pydantic import BaseModel
from typing import List
router = APIRouter(prefix="/role")

# Pydantic schemas
class RoleCreate(BaseModel):
    code:str
    label:str



class RoleResponse(BaseModel):
    code:str
    label:str
    class Config:
        orm_mode = True


# Create a role
@router.post("/add")
def create_role(data: RoleCreate, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.code == data.code).first()
    if role:
        raise HTTPException(status_code=400, detail="Code Role already registered")

    new_role = Role(
        code=data.code,
        label=data.label
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role

#  Get all roles
@router.get("/all", response_model=List[RoleResponse])
def get_all_roles(db: Session = Depends(get_db)):
    roles = db.query(Role).all()
    return roles

#Get a role by code
@router.get("/{code}", response_model=RoleResponse)
def get_role(code: str, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.code == code).first()
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


# Update a role
@router.put("/{code}", response_model=RoleResponse)
def update_role(code:str, label: str, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.code == code).first()
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    if label:
        role.label = label
    db.commit()
    db.refresh(role)
    return role


# Delete a role
@router.delete("/{code}", response_model=dict)
def delete_role(code: str, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.code == code).first()
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    db.delete(role)
    db.commit()
    return {"message": f"Role {role.code} deleted successfully"}


class RoleAssignmentRequest(BaseModel):
    user_email: str
    role_code: str

@router.post("/assign-role", response_model=dict)
def assign_role_to_user(request: RoleAssignmentRequest, db: Session = Depends(get_db)):
    # Check user exists
    user = db.query(User).filter_by(email=request.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check role exists
    role = db.query(Role).filter_by(code=request.role_code).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if role already assigned
    existing = db.query(UserRole).filter_by(user_id=user.id, role_code=role.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role already assigned to user")

    # Assign role
    assignment = UserRole(user_id=user.id, role_code=role.code)
    db.add(assignment)
    db.commit()

    return {"message": f"Role '{role.code}' assigned to user '{user.email}'"}