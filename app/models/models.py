from sqlalchemy import (
    Column, Integer, String, Boolean, Text, ForeignKey, Sequence, Enum, CheckConstraint, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID, BYTEA, TSRANGE
from sqlalchemy.orm import relationship, backref
import uuid
from app.config.database import Base 

import enum



class EntityType(str, enum.Enum):
    site = "site"
    process = "process"
    supplier = "supplier"


class QuestionnaireLabel(str, enum.Enum):
    ISO = "ISO"
    IATF = "IATF"
    VDA = "VDA"
    INTERNAL = "INTERNAL"
    CLIENT = "CLIENT"


class ResponseType(str, enum.Enum):
    yes_no = "yes_no"
    scale = "scale"
    color = "color"
    text = "text"
    file = "file"


class CriticalityLevel(str, enum.Enum):
    critical = "critical"
    not_critical = "not_critical"


class AuditStatus(str, enum.Enum):
    planned = "planned"
    confirmed = "confirmed"
    postponed = "postponed"
    cancelled = "cancelled"


class ScoreType(str, enum.Enum):
    color = "color"
    scale = "scale"
    yes_no = "yes_no"


class CorrectiveActionStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    postponed = "postponed"


class KPIType(str, enum.Enum):
    performance = "performance"
    management = "management"


class PeriodType(str, enum.Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    annually = "annually"

class User(Base):
    __tablename__ = "user"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(250), nullable=False, unique=True)
    first_name = Column(String(250))
    last_name = Column(String(250))
    active = Column(Boolean)
    roles = relationship('Role', secondary='user_role', backref=backref('users', lazy='dynamic'))

class Role(Base):
    __tablename__ = "role"
    code = Column(Text, primary_key=True)
    label = Column(String(250))

class UserRole(Base):
    __tablename__ = "user_role"
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete='CASCADE'), primary_key=True)
    role_code = Column(Text, ForeignKey("role.code"), primary_key=True)

# Audited Entities
class Entity(Base):
    __tablename__ = "entity"
    id = Column(Integer, Sequence('entity_id_seq'), primary_key=True)
    type = Column(Enum(EntityType), nullable=False)
    code = Column(Text, unique=True)
    label = Column(String(250))
    parent_id = Column(Integer, ForeignKey('entity.id', ondelete='SET NULL'))
    parent = relationship('Entity', remote_side=[id], backref=backref('children', lazy='dynamic'))

class Questionnaire(Base):
    __tablename__ = "questionnaire"
    id = Column(Integer, Sequence('questionnaire_id_seq'), primary_key=True)
    code = Column(Text, unique=True)
    label = Column(String(250))

    versions = relationship("QuestionnaireVersion", back_populates="questionnaire", cascade="all, delete")

class QuestionnaireVersion(Base):
    __tablename__ = "questionnaire_version"
    id = Column(Integer, Sequence('questionnaire_version_id_seq'), primary_key=True)
    questionnaire_id = Column(Integer, ForeignKey('questionnaire.id', ondelete='CASCADE'))
    version_no = Column(Integer)
    status = Column(Text)

    questionnaire = relationship("Questionnaire", back_populates="versions")
    questions = relationship("Question", secondary="questionnaire_version_question", back_populates="versions")

class Question(Base):
     __tablename__ = "question" 
     id = Column(Integer, Sequence('question_id_seq'), primary_key=True) 
     title = Column(Text) 
     response_type = Column(Enum(ResponseType)) 
     criticality = Column(Enum(CriticalityLevel), nullable=False)
     versions = relationship("QuestionnaireVersion", secondary="questionnaire_version_question", back_populates="questions")

class QuestionnaireVersionQuestion(Base):
    __tablename__ = "questionnaire_version_question"
    questionnaire_version_id = Column(Integer, ForeignKey('questionnaire_version.id', ondelete='CASCADE'), primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id', ondelete='CASCADE'), primary_key=True)
class Audit(Base):
    __tablename__ = "audit"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey('entity.id', ondelete='SET NULL'))
    questionnaire_version_id = Column(Integer, ForeignKey('questionnaire_version.id', ondelete='SET NULL'))
    status = Column(Enum(AuditStatus))
    final_score_type = Column(Enum(ScoreType))
    final_score = Column(Text)
    __table_args__ = (
        CheckConstraint(
            "(final_score_type = 'color' AND final_score IN ('green', 'yellow', 'red')) OR "
            "(final_score_type = 'yes_no' AND final_score IN ('yes', 'no')) OR "
            "(final_score_type = 'scale' AND final_score ~ '^[1-9]$|10')",
            name='final_score_check'
        ),
    )

class AuditSession(Base):
    __tablename__ = "audit_session"
    id = Column(Integer, primary_key=True)
    audit_id = Column(Integer, ForeignKey('audit.id'))
    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))

class AuditParticipant(Base):
    __tablename__ = "audit_participant"
    audit_id = Column(Integer, ForeignKey('audit.id', ondelete='CASCADE'), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), primary_key=True)
    local_role = Column(Text, ForeignKey('role.code'), primary_key=True)

class AuditQuestion(Base):
    __tablename__ = "audit_question"
    id = Column(Integer, primary_key=True)
    audit_id = Column(Integer, ForeignKey('audit.id'))
    question_id = Column(Integer, ForeignKey('question.id'))

class AuditResponse(Base):
    __tablename__ = "audit_response"
    id = Column(Integer, primary_key=True)
    audit_question_id = Column(Integer, ForeignKey('audit_question.id', ondelete='CASCADE'))
    author_id = Column(UUID(as_uuid=True), ForeignKey('user.id', ondelete='SET NULL'))
    value = Column(BYTEA)

class Finding(Base):
    __tablename__ = "finding"
    id = Column(Integer, primary_key=True)
    audit_id = Column(Integer, ForeignKey('audit.id', ondelete='CASCADE'))
    audit_question_id = Column(Integer, ForeignKey('audit_question.id', ondelete='SET NULL'))
    type = Column(Text)
    corrective_action = relationship(
        "CorrectiveAction",
        back_populates="finding",
        uselist=False,  # one-to-one relationship
        cascade="all, delete-orphan"
    )

class CorrectiveAction(Base):
    __tablename__ = "corrective_action"
    id = Column(Integer, primary_key=True)
    finding_id = Column(Integer, ForeignKey('finding.id'), unique=True)
    title = Column(Text)
    status = Column(Enum(CorrectiveActionStatus))
    finding = relationship("Finding", back_populates="corrective_action")

# KPI: Definitions, Targets, Values, Process Actions
class KPIDefinition(Base):
    __tablename__ = "kpi_definition"
    id = Column(Integer, primary_key=True)
    code = Column(Text, unique=True)
    label = Column(Text)
    type = Column(Enum(KPIType))

class KPIValue(Base):
    __tablename__ = "kpi_value"
    id = Column(Integer, primary_key=True)
    kpi_id = Column(Integer, ForeignKey('kpi_definition.id'))
    periodtype = Column(Enum(PeriodType))
    period = Column(TSRANGE)
    value = Column(Integer)

class KPICorrectiveAction(Base):
    __tablename__ = "kpi_corrective_action"
    id = Column(Integer, primary_key=True)
    kpi_value_id = Column(Integer, ForeignKey('kpi_value.id'))
    title = Column(Text)

# Attachments
class Attachment(Base):
    __tablename__ = "attachement"
    id = Column(Integer, primary_key=True)
    filename = Column(Text)
    path = Column(Text)
    object = Column(BYTEA)
