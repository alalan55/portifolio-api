from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()


class createUser(BaseModel):
    name: str
    email: str
    password: str
    about: Optional[str]
    profile_pic: Optional[str]


@app.get("/")
async def health():
    return {"message": "Is ok"}
