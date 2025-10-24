from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import (
    Entity,entity_type_enum)
from typing import List,Optional
from pydantic import BaseModel

router = APIRouter(prefix="/entity")

class EntityCreate(BaseModel):
    type: str
    code: str
    label: str
    parent_id:Optional[int]
# Response schema
class EntityResponse(BaseModel):
    type:str
    code:str
    label:str

class EntityUpdate(BaseModel):
    type: Optional[str] = None
    code: Optional[str] = None
    label: Optional[str] = None
    parent_id: Optional[int] = None


@router.post("/add",response_model=EntityResponse)
def create_entity(entity:EntityCreate, db: Session = Depends(get_db)):
   
    db_entity = db.query(Entity).filter(Entity.code == entity.code).first()
   
    if db_entity:
        raise HTTPException(status_code=400, detail="Entity code already exist")
    
    new_entity = Entity(type=entity.type,code=entity.code, label=entity.label)
    db.add(new_entity)
    db.commit()
    db.refresh(new_entity)
    return new_entity


@router.get("/getAll", response_model=List[EntityResponse])
def get_entities(db: Session = Depends(get_db)):
    db_entities = db.query(Entity).all()

    if not db_entities:
        raise HTTPException(status_code=404, detail="No Entity found")

    return db_entities

#get entity by code
@router.get("/{entity_code}", response_model=EntityResponse)
def get_entity(entity_code: str, db: Session = Depends(get_db)):
    entity = db.query(Entity).filter_by(code=entity_code).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity

# Update an existing entity
@router.put("/{entity_code}", response_model=EntityResponse)
def update_entity(entity_code: str, entity_data:EntityUpdate, db: Session = Depends(get_db)):
    entity = db.query(Entity).filter_by(code=entity_code).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    for key, value in entity_data.model_dump(exclude_unset=True).items():
        setattr(entity, key, value)
    db.commit()
    db.refresh(entity)
    return entity

# Delete an entity
@router.delete("/{entity_id}")
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    entity = db.query(Entity).filter_by(id=entity_id).first()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    db.delete(entity)
    db.commit()
    return {"message": "Entity deleted successfully"}


