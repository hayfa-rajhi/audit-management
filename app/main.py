from fastapi import FastAPI
from app.config.database import Base, engine
from app.routers.questionnaire_api import router as questionnaire_router
from app.routers.audit_api import router as audit_router
from app.routers.user_api import router as user_router
from app.routers.role_api import router as role_router
from app.routers.question_api import router as question_router
from app.routers.entity_api import router as entity_router
from app.routers.corrective_action_api import router as corrective_action
from app.routers.finding_api import router as finding_router
# Create all the tables in the database
Base.metadata.create_all(bind=engine)

app=FastAPI()

app.include_router(audit_router)
app.include_router(questionnaire_router)
app.include_router(user_router)
app.include_router(role_router)
app.include_router(question_router)
app.include_router(entity_router)
app.include_router(corrective_action)
app.include_router(finding_router)



