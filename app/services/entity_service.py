from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.models import Entity
from app.schemas.schema import EntityCreate, EntityUpdate


def create_entity(data: EntityCreate, db: Session):
    existing = db.query(Entity).filter_by(code=data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Entity code already exists")

    new_entity = Entity(
        type=data.type,
        code=data.code,
        label=data.label,
        parent_id=data.parent_id
    )
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)
    return new_entity


def get_all_entities(db: Session):
    entities = db.query(Entity).all()
    if not entities:
        raise HTTPException(status_code=404, detail="No entities found")
    return entities


def get_entity_by_code(entity_code: str, db: Session):
    entity = db.query(Entity).filter_by(code=entity_code).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


def update_entity(entity_code: str, data: EntityUpdate, db: Session):
    entity = db.query(Entity).filter_by(code=entity_code).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(entity, key, value)
    db.commit()
    db.refresh(entity)
    return entity


def delete_entity(entity_id: int, db: Session):
    entity = db.query(Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    db.delete(entity)
    db.commit()
    return {"message": f"Entity {entity_id} deleted successfully"}
