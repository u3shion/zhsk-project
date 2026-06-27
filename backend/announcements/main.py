from fastapi import FastAPI

from models import *
from core.database import Base, engine
from announcements.router import router as announcements_router


app = FastAPI(title="Announcements Service")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(announcements_router)


@app.get("/")
def root():
    return {"status": "ok"}
