from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import Optional, Union
from database import engine, SessionLocal
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import timedelta, datetime
# import datetime
import models


SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGOTIGHTM = 'HS256'

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")


def get_current_year():
    today = datetime.now()
    return today.year


class CreateUser(BaseModel):
    name: str
    email: str
    password: str
    about: Optional[str]
    profile_pic: Optional[str]


class UserLogin(BaseModel):
    email: str
    password: str


class Project(BaseModel):
    name: str
    pre_description: Optional[str]
    description: Optional[str]
    year: Union[int, None] = get_current_year()
    image: Optional[str]
    state: Optional[int] = Field(
        gt=-1, lt=2, description="O estado do projeto deve estar entre 0 e 1")


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


# AÇÕES DO USUÁRIO ------------------------------------------------


def create_access_token(email: str, id: int, expires_delta: Optional[timedelta] = None):
    encode = {"sub": email, "id": id}

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGOTIGHTM)


def password_hash(password):
    return bcrypt_context.hash(password)


def verify_password(passrowd, hash_password):
    return bcrypt_context.verify(passrowd, hash_password)


def authenticate_user(email: str, password: str, db):
    user = db.query(models.Users).filter(models.Users.email == email).first()

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGOTIGHTM])
        email: str = payload.get("sub")
        id: int = payload.get("id")
        if email is None or id is None:
            raise HTTPException(
                status_code=404, detail="Usuário não encontrado")
        return {"email": email, "id": id}
    except JWTError:
        raise HTTPException(
            status_code=404, detail="Não foi possível validar as credenciais")


@app.get("/")
async def health():
    return {"message": "Is ok"}


@app.post("/user/create")
async def create_user(user: CreateUser, db: Session = Depends(get_db)):
    user_model = models.Users()
    user_model.name = user.name
    user_model.email = user.email
    user_model.about = user.about
    user_model.profile_pic = user.profile_pic
    hash_pass = password_hash(user.password)
    user_model.hashed_password = hash_pass

    db.add(user_model)
    db.commit()


@app.post("/user/token")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(user.email, user.password, db)
    print(user.email)

    if not user:
        raise token_exception()

    token_expires = timedelta(minutes=60)
    token = create_access_token(
        user.email, user.id, expires_delta=token_expires)

    return {"token": token}


# AÇÕES DAS EXPERIÊNCIAS ------------------------------------------------

@app.get("/experiences")
async def get_experices(db: Session = Depends(get_db)):
    projects = db.query(models.Experiences).all()
    return successful_response(200, projects)


@app.post("/experience")
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

@app.put("/experience/{id}")
async def update_experience(id: int, experience: Experience, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    exp = db.query(models.Experiences).filter(models.Experiences.id == id).filter(models.Experiences.owner_id == user.get("id")).first()

    if exp is None:
        raise HTTPException(status_code=404, detail="Experiência não encontrada")

    exp.name_company = experience.name_company
    exp.start_at = experience.start_at
    exp.end_at = experience.end_at
    exp.description = experience.description
    exp.role = experience.role
    exp.is_my_current_work = experience.is_my_current_work

    db.add(exp)
    db.commit()

    return successful_response(200, experience)




# AÇÕES DOS PROJETOS ------------------------------------------------


@app.get("/projects")
async def get_projects(db: Session = Depends(get_db)):
    projects = db.query(models.Projects).all()
    return successful_response(200, projects)


@app.post("/project")
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


@app.put("/project/{id}")
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


@app.delete("/project/{id}")
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


# EXCEPTIONS ------------------------------------------------


def get_user_exception():
    credential_exprction = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Não foi possível validar as credenciais", headers={"WWW-Authenticate": "Bearer"})
    return credential_exprction


def token_exception():
    token_exception_resp = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Usuário ou senha icorretos", headers={"WWW-Authenticate": "Bearer"})
    return token_exception_resp


def successful_response(status_code: int, content: Optional[dict or list] = None):
    return {
        "status": status_code,
        "message": "Sucesso!",
        "content": content
    }
