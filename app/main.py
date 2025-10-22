from fastapi import FastAPI
from app.db import Base, engine
from app.questionnaire_api import router as questionnaire_router
from app.audit_api import router as audit_router
from app.user_api import router as user_router
from app.role_api import router as role_router

# Create all the tables in the database
Base.metadata.create_all(bind=engine)

app=FastAPI()

app.include_router(audit_router)
app.include_router(questionnaire_router)
app.include_router(user_router)
app.include_router(role_router)



