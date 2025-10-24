from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.config.database import get_db
from app.services import entity_service
from app.schemas.schema import EntityCreate, EntityUpdate, EntityResponse

router = APIRouter(prefix="/entity", tags=["Entities"])


@router.post("/add", response_model=EntityResponse)
def create_entity(entity: EntityCreate, db: Session = Depends(get_db)):
    return entity_service.create_entity(entity, db)


@router.get("/getAll", response_model=List[EntityResponse])
def get_entities(db: Session = Depends(get_db)):
    return entity_service.get_all_entities(db)


@router.get("/{entity_code}", response_model=EntityResponse)
def get_entity(entity_code: str, db: Session = Depends(get_db)):
    return entity_service.get_entity_by_code(entity_code, db)


@router.put("/{entity_code}", response_model=EntityResponse)
def update_entity(entity_code: str, entity_data: EntityUpdate, db: Session = Depends(get_db)):
    return entity_service.update_entity(entity_code, entity_data, db)


@router.delete("/{entity_id}")
def delete_entity(entity_id: int, db: Session = Depends(get_db)):
    return entity_service.delete_entity(entity_id, db)
