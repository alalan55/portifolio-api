from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
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


class CreateCourse(BaseModel):
    name: str
    description: str
    start_at: str
    end_at: str
    pic: str
    institution: str
    link: str


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


@router.post("/")
async def create_course(course: CreateCourse, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    course_model = models.Courses()

    course_model.name = course.name
    course_model.description = course.description
    course_model.start_at = course.start_at
    course_model.end_at = course.end_at
    course_model.pic = course.pic
    course_model.institution = course.institution
    course_model.link = course.link
    course_model.owner_id = user.get("id")

    db.add(course_model)
    db.commit()

    return successful_response(201, course)


def successful_response(status_code: int, content: Optional[dict or list] = None):
    return {
        "status": status_code,
        "message": "Sucesso!",
        "content": content
    }
