from fastapi import FastAPI

from models import *
from core.database import Base, engine
from readings.router import router as readings_router
from water_meters.router import router as water_meters_router


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Meters Service")

app.include_router(readings_router)
app.include_router(water_meters_router)


@app.get("/")
def root():
    return {"status": "ok"}
