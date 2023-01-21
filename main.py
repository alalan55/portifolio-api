from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from routes import auth, projects, experiences, courses
import models

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(experiences.router)
app.include_router(courses.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
