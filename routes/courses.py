from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from routes.auth import get_current_user, get_user_exception
from database import engine, SessionLocal
import models
import sys
sys.path.append("..")


models.Base.metadata.create_all(bind=engine)

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
    responses={404: {"description": "Não encontrado"}}
)


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/")
async def get_all_courses(db: Session = Depends(get_db)):
    courses = db.query(models.Courses).all()
    return courses
