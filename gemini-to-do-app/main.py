from fastapi import FastAPI
from models import Base, ToDo
from database import engine, SessionLocal
from routers.auth import router as auth_router
from routers.to_do import router as to_do_router


app=FastAPI()
app.include_router(auth_router)
app.include_router(to_do_router)

Base.metadata.create_all(bind=engine)

