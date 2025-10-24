from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import Role, UserRole, User
from app.schemas.schema import RoleCreate, RoleUpdate, RoleAssignmentRequest


def create_role(data: RoleCreate, db: Session):
    existing = db.query(Role).filter_by(code=data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role code already registered")
    r = Role(code=data.code, label=data.label)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get_all_roles(db: Session):
    return db.query(Role).all()


def get_role(code: str, db: Session):
    r = db.query(Role).filter_by(code=code).first()
    if not r:
        raise HTTPException(status_code=404, detail="Role not found")
    return r


def update_role(code: str, data: RoleUpdate, db: Session):
    r = db.query(Role).filter_by(code=code).first()
    if not r:
        raise HTTPException(status_code=404, detail="Role not found")
    r.label = data.label
    db.commit()
    db.refresh(r)
    return r


def delete_role(code: str, db: Session):
    r = db.query(Role).filter_by(code=code).first()
    if not r:
        raise HTTPException(status_code=404, detail="Role not found")
    db.delete(r)
    db.commit()
    return {"message": f"Role {code} deleted successfully"}


def assign_role_to_user(request: RoleAssignmentRequest, db: Session):
    user = db.query(User).filter_by(email=request.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter_by(code=request.role_code).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    existing = db.query(UserRole).filter_by(user_id=user.id, role_code=role.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role already assigned to user")

    assignment = UserRole(user_id=user.id, role_code=role.code)
    db.add(assignment)
    db.commit()
    return {"message": f"Role '{role.code}' assigned to user '{user.email}'"}
