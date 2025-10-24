from pydantic import BaseModel, EmailStr
from typing import  Optional
import uuid
from enum import Enum
 
   
from app.routers.corrective_action_api import CorrectiveActionStatus

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    active: Optional[bool]


class UserResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    active: bool

    model_config = {
        "from_attributes": True
    }



class ResponseType(str, Enum):
    yes_no = "yes_no"
    scale = "scale"
    color = "color"
    text = "text"
    file = "file"


class CriticalityLevel(str, Enum):
    critical = "critical"
    not_critical = "not_critical"


class QuestionCreate(BaseModel):
    title: str
    response_type: ResponseType
    criticality: CriticalityLevel


class QuestionUpdate(BaseModel):
    title: Optional[str]
    response_type: Optional[ResponseType]
    criticality: Optional[CriticalityLevel]


class QuestionOut(BaseModel):
    id: int
    title: str
    response_type: ResponseType
    criticality: CriticalityLevel

    model_config = {"from_attributes": True}


class QuestionnaireCreate(BaseModel):
    code: str
    label: str


class QuestionnaireUpdate(BaseModel):
    label: Optional[str]


class QuestionnaireResponse(BaseModel):
    id: int
    code: str
    label: str

    model_config = {"from_attributes": True}



class RoleCreate(BaseModel):
    code: str
    label: str


class RoleUpdate(BaseModel):
    label: str


class RoleResponse(BaseModel):
    code: str
    label: str

    model_config = {"from_attributes": True}


class RoleAssignmentRequest(BaseModel):
    user_email: str
    role_code: str



class CorrectiveActionOut(BaseModel):
    id: int
    title: str
    status: CorrectiveActionStatus

    model_config = {"from_attributes": True}


class CorrectiveActionUpdate(BaseModel):
    title: Optional[str]
    status: Optional[CorrectiveActionStatus]


class FindingOut(BaseModel):
    id: int
    audit_question_id: int
    type: str
    corrective_action: Optional[CorrectiveActionOut]

    model_config = {"from_attributes": True}


class FindingUpdate(BaseModel):
    type: Optional[str] = None
    audit_question_id: Optional[int] = None

 

class EntityCreate(BaseModel):
    type: str
    code: str
    label: str
    parent_id: Optional[int] = None


class EntityUpdate(BaseModel):
    type: Optional[str] = None
    code: Optional[str] = None
    label: Optional[str] = None
    parent_id: Optional[int] = None


class EntityResponse(BaseModel):
    type: str
    code: str
    label: str

    model_config = {"from_attributes": True}


from datetime import datetime
 

class AuditRequest(BaseModel):
    entity_code: str
    questionnaire_code: str
    auditor_email: str
    auditee_email: str
    start_time: datetime
    end_time: datetime


class RescheduleRequest(BaseModel):
    audit_id: int
    new_start_time: Optional[datetime] = None
    new_end_time: Optional[datetime] = None
    reason: Optional[str] = None


class AuditResponse(BaseModel):
    id: int
    status: str
    final_score: Optional[str] = None
    final_score_type: Optional[str] = None

    model_config = {"from_attributes": True}


class AuditDetailResponse(BaseModel):
    audit_id: int
    status: str
    entity: dict
    questionnaire: dict
    sessions: list
    participants: list


 
 
from app.models.models import KPIType
class KPIDefinitionBase(BaseModel):
    code: str
    label: str
    type: KPIType

class KPIDefinitionCreate(KPIDefinitionBase):
    pass

class KPIDefinitionUpdate(BaseModel):
    label: Optional[str] = None
    type: Optional[KPIType] = None

class KPIDefinitionOut(KPIDefinitionBase):
    id: int

    model_config = {"from_attributes": True}
