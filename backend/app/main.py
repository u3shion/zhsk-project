from fastapi import FastAPI
from app.core.database import Base, engine
from app.models.test import Test 

app = FastAPI()

# создаём таблицы в базе
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"status": "ok"}