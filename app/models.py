from sqlalchemy import (
    Column, Integer, String, Boolean, Text, ForeignKey, Sequence, Enum, CheckConstraint, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import UUID, BYTEA, TSRANGE
from sqlalchemy.orm import relationship, backref
import uuid
from app.db import Base 

# ENUM definitions
entity_type_enum = Enum('site', 'process', 'suplier', name='entity_type')
questionnaire_label_enum = Enum('ISO', 'IATF', 'VDA', 'INTERNAL', 'CLIENT', name='questionnaire_label')
responsetype_enum = Enum('yes/no', 'scale', 'color', 'text', 'file', name='responsetype')
criticality_enum = Enum('critical', 'not_ctrical', name='criticality_level')
audit_status_enum = Enum('planned', 'confirmed', 'postponed', 'cancled', name='audit_status')
score_type_enum = Enum('color', 'scale', 'yes_no', name='score_type')
corrective_action_status_enum = Enum('in_progress', 'completed', 'post_ponned', name='corrective_action_status')
kpi_type_enum = Enum('performance', 'management', name='kpi_type')
period_type_enum = Enum('monthy', 'quarterly', 'annuaely', name='period_type')

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
    type = Column(entity_type_enum, nullable=False)
    code = Column(Text, unique=True)
    label = Column(String(250))
    parent_id = Column(Integer, ForeignKey('entity.id', ondelete='SET NULL'))
    parent = relationship('Entity', remote_side=[id], backref=backref('children', lazy='dynamic'))

class Questionnaire(Base):
    __tablename__ = "questionnaire"
    id = Column(Integer, Sequence('questionnaire_id_seq'), primary_key=True)
    code = Column(Text, unique=True)
    label = Column(String(250))

class QuestionnaireVersion(Base):
    __tablename__ = "questionnaire_version"
    id = Column(Integer, Sequence('questionnaire_version_id_seq'), primary_key=True)
    questionnaire_id = Column(Integer, ForeignKey('questionnaire.id', ondelete='CASCADE'))
    version_no = Column(Integer)
    status = Column(Text)

class Question(Base):
    __tablename__ = "question"
    id = Column(Integer, Sequence('question_id_seq'), primary_key=True)
    title = Column(Text)
    response_type = Column(responsetype_enum)
    criticality = Column(criticality_enum, nullable=False)

class QuestionnaireVersionQuestion(Base):
    __tablename__ = "questionnaire_version_question"
    questionnaire_version_id = Column(Integer, ForeignKey('questionnaire_version.id', ondelete='CASCADE'), primary_key=True)
    question_id = Column(Integer, ForeignKey('question.id'), primary_key=True)

class Audit(Base):
    __tablename__ = "audit"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey('entity.id', ondelete='SET NULL'))
    questionnaire_version_id = Column(Integer, ForeignKey('questionnaire_version.id', ondelete='SET NULL'))
    status = Column(audit_status_enum)
    final_score_type = Column(score_type_enum)
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

class CorrectiveAction(Base):
    __tablename__ = "corrective_action"
    id = Column(Integer, primary_key=True)
    finding_id = Column(Integer, ForeignKey('finding.id'), unique=True)
    title = Column(Text)
    status = Column(corrective_action_status_enum)

# KPI: Definitions, Targets, Values, Process Actions
class KPIDefinition(Base):
    __tablename__ = "kpi_definition"
    id = Column(Integer, primary_key=True)
    code = Column(Text, unique=True)
    label = Column(Text)
    type = Column(kpi_type_enum)

class KPIValue(Base):
    __tablename__ = "kpi_value"
    id = Column(Integer, primary_key=True)
    kpi_id = Column(Integer, ForeignKey('kpi_definition.id'))
    periodtype = Column(period_type_enum)
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
