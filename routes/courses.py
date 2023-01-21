from fastapi import APIRouter
from sqlalchemy.orm import Session
from pydantic import BaseModel
from routes.auth import get_current_user, get_user_exception
from database import engine, SessionLocal
import models
import sys
sys.path.append("..")


models.Base.metadata.create_all(bind=engine)

router = APIRouter(
    prefix="/couses",
    tags=["Courses"],
    responses={404: {"description": "Não encontrado"}}
)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
