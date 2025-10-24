from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from services import KPIDefinitionService, KPIValueService, KPICorrectiveActionService

router = APIRouter(prefix="/kpis", tags=["KPI Definitions"])

# Get KPI by code
@router.get("/definition/{code}")
def get_kpi_definition(code: str, db: Session = Depends(get_db)):
    return KPIDefinitionService(db).get(code)

# List all KPI Definitions
@router.get("/definition")
def list_kpis(db: Session = Depends(get_db)):
    return KPIDefinitionService(db).list()

# Create KPI Value
@router.post("/value")
def create_kpi_value(kpi_id: int, periodtype: str, period: str, value: int, db: Session = Depends(get_db)):
    return KPIValueService(db).create(kpi_id, periodtype, period, value)

# List corrective actions for a KPI Value
@router.get("/value/{kpi_value_id}/actions")
def list_actions(kpi_value_id: int, db: Session = Depends(get_db)):
    return KPICorrectiveActionService(db).list_by_value(kpi_value_id)
