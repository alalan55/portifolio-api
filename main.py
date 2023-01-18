from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from database import engine, SessionLocal
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import timedelta, datetime
import models


SECRET_KEY = "KlgH6AzYDeZeGwD288to79I3vTHT8wp7"
ALGOTIGHTM = 'HS256'

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")


class CreateUser(BaseModel):
    name: str
    email: str
    password: str
    about: Optional[str]
    profile_pic: Optional[str]


class UserLogin(BaseModel):
    email: str
    password: str


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


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


def get_user_exception():
    credential_exprction = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Não foi possível validar as credenciais", headers={"WWW-Authenticate": "Bearer"})
    return credential_exprction


def token_exception():
    token_exception_resp = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Usuário ou senha icorretos", headers={"WWW-Authenticate": "Bearer"})
    return token_exception_resp
