from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import engine, SessionLocal
from routes.auth import get_current_user, get_user_exception
import models
import sys
sys.path.append("..")


models.Base.metadata.create_all(bind=engine)


router = APIRouter(
    prefix="/experiences",
    tags=["Experiences"],
    responses={404: {"description": "Não encontrado"}}
)


class Experience(BaseModel):
    name_company: str
    start_at: str
    end_at: str
    description: str
    role: str
    is_my_current_work: bool


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/")
async def get_experices(db: Session = Depends(get_db)):
    projects = db.query(models.Experiences).all()
    return successful_response(200, projects)


@router.post("/")
async def create_experience(experience: Experience, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    exp_model = models.Experiences()

    exp_model.name_company = experience.name_company
    exp_model.start_at = experience.start_at
    exp_model.end_at = experience.end_at
    exp_model.description = experience.description
    exp_model.role = experience.role
    exp_model.is_my_current_work = experience.is_my_current_work
    exp_model.owner_id = user.get("id")

    db.add(exp_model)
    db.commit()

    return successful_response(201, experience)


@router.put("/{id}")
async def update_experience(id: int, experience: Experience, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    exp = db.query(models.Experiences).filter(models.Experiences.id == id).filter(
        models.Experiences.owner_id == user.get("id")).first()

    if exp is None:
        raise HTTPException(
            status_code=404, detail="Experiência não encontrada")

    exp.name_company = experience.name_company
    exp.start_at = experience.start_at
    exp.end_at = experience.end_at
    exp.description = experience.description
    exp.role = experience.role
    exp.is_my_current_work = experience.is_my_current_work

    db.add(exp)
    db.commit()

    return successful_response(200, experience)


@router.delete("/{id}")
async def delete_experience(id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    exp = db.query(models.Experiences).filter(models.Experiences.id == id).filter(
        models.Experiences.owner_id == user.get("id")).first()

    if exp is None:
        raise HTTPException(
            status_code=404, detail="Experiência não encontrada")

    db.query(models.Experiences).filter(models.Experiences.id == id).delete()
    db.commit()
    return successful_response(200)


def successful_response(status_code: int, content: Optional[dict or list] = None):
    return {
        "status": status_code,
        "message": "Sucesso!",
        "content": content
    }
