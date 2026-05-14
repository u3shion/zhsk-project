from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI

from models import *
from core.database import Base, engine
from notifications.router import router as notifications_router
from scheduler import check_meter_verifications


Base.metadata.create_all(bind=engine)

scheduler = BackgroundScheduler(timezone="Europe/Moscow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(check_meter_verifications, "cron", hour=8, minute=0, id="meter_check")
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Notifications Service", lifespan=lifespan)

app.include_router(notifications_router)


@app.get("/")
def root():
    return {"status": "ok"}
