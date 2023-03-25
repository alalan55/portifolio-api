from fastapi import APIRouter, HTTPException, Depends, status, File
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from database import engine, SessionLocal
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import timedelta, datetime
import base64
import imghdr
import models
import sys
import os
import uuid
sys.path.append("..")


SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGOTIGHTM = 'HS256'

models.Base.metadata.create_all(bind=engine)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={401: {"user": "Não autorizado"}}
)


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")


class CreateUser(BaseModel):
    name: str
    email: str
    password: str
    about: Optional[str]
    profile_pic: Optional[str]


class UpdateUser(BaseModel):
    name: str
    email: str
    about: Optional[str]
    profile_pic: Optional[str]


class UpdatePassword(BaseModel):
    current_password: str
    new_password: str


class UserLogin(BaseModel):
    email: str
    password: str


class ImgTest(BaseModel):
    image: str


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


@router.post("/user/create")
async def create_user(user: CreateUser, db: Session = Depends(get_db)):
    user_model = models.Users()
    user_model.name = user.name
    user_model.email = user.email
    user_model.about = user.about
    img_path = save_image(user.profile_pic)
    user_model.profile_pic = img_path
    hash_pass = password_hash(user.password)
    user_model.hashed_password = hash_pass

    db.add(user_model)
    db.commit()

    return successful_response(201, None, user_model)

@router.post("/user/token")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(user.email, user.password, db)

    if not user:
        raise token_exception()

    token_expires = timedelta(minutes=60)
    token = create_access_token(
        user.email, user.id, expires_delta=token_expires)

    user.hashed_password = None
    # return {"token": token, }
    # VERIFICA O RESPONSE MODEL PARA REMOVER O HASH DE SENHA DA RESPOSTA, RESPONSE MODEL SÓ SERVE SE FOR RETORNADO UM OBJETO INTEIRO
    return successful_response(200, token, user)


@router.put("/user/update/{id}")
async def update_user(id: int, user: UpdateUser, userLogged: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if userLogged is None:
        raise get_user_exception()

    user_model = db.query(models.Users).filter(
        models.Users.id == id and userLogged.get("id")).first()

    if user_model is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user_model.name = user.name
    user_model.email = user.email
    user_model.about = user.about
    user_model.profile_pic = user.profile_pic

    db.add(user_model)
    db.commit()

    return successful_response(200)


@router.put("/user/update-password/{id}")
async def update_password(id: int, datas: UpdatePassword, userLogged: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if userLogged is None:
        raise get_user_exception()

    user_model = db.query(models.Users).filter(
        models.Users.id == id and userLogged.get("id")).first()

    if user_model is None:
        raise user_not_found()

    if not verify_password(datas.current_password, user_model.hashed_password):
        raise password_not_confirmed()

    hash_pass = password_hash(datas.new_password)
    user_model.hashed_password = hash_pass

    db.add(user_model)
    db.commit()

    return successful_response(200)


def get_user_exception():
    credential_exprction = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Não foi possível validar as credenciais", headers={"WWW-Authenticate": "Bearer"})
    return credential_exprction


def user_not_found():
    return {"status": 404, "message": "Usuário não encontrado"}


def token_exception():
    token_exception_resp = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Usuário ou senha icorretos", headers={"WWW-Authenticate": "Bearer"})
    return token_exception_resp


def password_not_confirmed():
    resp = HTTPException(status_code=status.HTTP_409_CONFLICT,
                         detail="Senha atual não confere com a cadastrada no banco de dados")
    # return {"status": 409, "message": "Senha atual não confere com a cadastrada no banco de dados"}
    return resp


def successful_response(status_code: int, token: Optional[str] = None, content: Optional[dict or list] = None):
    return {
        "status": status_code,
        "message": "Sucesso!",
        "content": content,
        "token": token
    }


def save_image(img: str):
    try:
        if not os.path.exists("uploads"):
            os.mkdir("uploads")

        imgabe_bytes = base64.b64decode(img, validate=True)
        image_type = imghdr.what(None, imgabe_bytes)
        file_path = os.path.join(
            "uploads", f"image-{uuid.uuid4()}.{image_type}").replace("\\", "/")

        with open(file_path, "wb") as buffer:
            buffer.write(imgabe_bytes)

        return f"image/{file_path}"

    except:
        return None
