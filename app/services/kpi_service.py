from sqlalchemy.orm import Session
from models import KPIDefinition, KPIValue, KPICorrectiveAction

# ----------------------
# KPI Definition Service
# ----------------------
class KPIDefinitionService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, code: str, label: str, type: str):
        kpi = KPIDefinition(code=code, label=label, type=type)
        self.db.add(kpi)
        self.db.commit()
        self.db.refresh(kpi)
        return kpi

    def get(self, kpi_code: str):
        return self.db.query(KPIDefinition).filter_by(code=kpi_code).first()

    def list(self):
        return self.db.query(KPIDefinition).all()

    def update(self, kpi_id: int, **kwargs):
        kpi = self.get(kpi_id)
        if not kpi:
            return None
        for key, value in kwargs.items():
            setattr(kpi, key, value)
        self.db.commit()
        return kpi

    def delete(self, kpi_id: int):
        kpi = self.get(kpi_id)
        if not kpi:
            return None
        self.db.delete(kpi)
        self.db.commit()
        return kpi

# ----------------------
# KPI Value Service
# ----------------------
class KPIValueService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, kpi_id: int, periodtype: str, period, value: int):
        kpi_value = KPIValue(kpi_id=kpi_id, periodtype=periodtype, period=period, value=value)
        self.db.add(kpi_value)
        self.db.commit()
        self.db.refresh(kpi_value)
        return kpi_value

    def get(self, value_id: int):
        return self.db.query(KPIValue).filter_by(id=value_id).first()

    def list_by_kpi(self, kpi_id: int):
        return self.db.query(KPIValue).filter_by(kpi_id=kpi_id).all()

    def update(self, value_id: int, **kwargs):
        kpi_value = self.get(value_id)
        if not kpi_value:
            return None
        for key, value in kwargs.items():
            setattr(kpi_value, key, value)
        self.db.commit()
        return kpi_value

    def delete(self, value_id: int):
        kpi_value = self.get(value_id)
        if not kpi_value:
            return None
        self.db.delete(kpi_value)
        self.db.commit()
        return kpi_value

# ----------------------
# KPI Corrective Action Service
# ----------------------
class KPICorrectiveActionService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, kpi_value_id: int, title: str):
        action = KPICorrectiveAction(kpi_value_id=kpi_value_id, title=title)
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    def get(self, action_id: int):
        return self.db.query(KPICorrectiveAction).filter_by(id=action_id).first()

    def list_by_value(self, kpi_value_id: int):
        return self.db.query(KPICorrectiveAction).filter_by(kpi_value_id=kpi_value_id).all()

    def update(self, action_id: int, **kwargs):
        action = self.get(action_id)
        if not action:
            return None
        for key, value in kwargs.items():
            setattr(action, key, value)
        self.db.commit()
        return action

    def delete(self, action_id: int):
        action = self.get(action_id)
        if not action:
            return None
        self.db.delete(action)
        self.db.commit()
        return action
