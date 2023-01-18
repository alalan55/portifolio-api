from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Union
from database import engine, SessionLocal
from datetime import datetime
from routes import auth
from routes.auth import get_current_user, get_user_exception
import models
import sys
sys.path.append("..")


models.Base.metadata.create_all(bind=engine)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
    responses={404: {"description": "Não encontrado"}}
)


def get_current_year():
    today = datetime.now()
    return today.year


class Project(BaseModel):
    name: str
    pre_description: Optional[str]
    description: Optional[str]
    year: Union[int, None] = get_current_year()
    image: Optional[str]
    state: Optional[int] = Field(
        gt=-1, lt=2, description="O estado do projeto deve estar entre 0 e 1")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# AÇÕES DOS PROJETOS ------------------------------------------------


@router.get("/")
async def get_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Projects).all()
    return successful_response(200, projects)


@router.post("/")
async def create_project(project: Project, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if user is None:
        raise get_user_exception()

    project_model = models.Projects()
    project_model.name = project.name
    project_model.pre_description = project.pre_description
    project_model.description = project.description
    project_model.year = project.year
    project_model.image = project.image
    project_model.state = project.state
    project_model.owner_id = user.get("id")

    db.add(project_model)
    db.commit()

    return successful_response(201)


@router.put("/{id}")
async def update_projet(id: int, project: Project, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):

    if user is None:
        raise get_user_exception()

    project_model = db.query(models.Projects).filter(models.Projects.id == id).filter(
        models.Projects.owner_id == user.get("id")).first()

    if project_model is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    project_model.name = project.name
    project_model.pre_description = project.pre_description
    project_model.description = project.description
    project_model.year = project.year
    project_model.state = project.state

    db.add(project_model)
    db.commit()

    return successful_response(200, project)


@router.delete("/{id}")
async def delete_project(id: int, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if user is None:
        raise get_user_exception()

    project_model = db.query(models.Projects).filter(models.Projects.id == id).filter(
        models.Projects.owner_id == user.get("id")).first()

    if project_model is None:
        raise HTTPException(status_code=404, detail='Projeto não encontrado')

    db.query(models.Projects).filter(models.Projects.id == id).delete()
    db.commit()
    return successful_response(200)


def successful_response(status_code: int, content: Optional[dict or list] = None):
    return {
        "status": status_code,
        "message": "Sucesso!",
        "content": content
    }
