from fastapi import FastAPI
from database import engine
from routes import auth, projects, experiences
import models

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(experiences.router)
