from fastapi import FastAPI

from auth.router import router as auth_router
from users.router import router as users_router

from models import *
from core.database import Base, engine


app = FastAPI(title="Users Service")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
def root():
    return {"status": "ok"}
