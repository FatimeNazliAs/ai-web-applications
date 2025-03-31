from fastapi import FastAPI, Request
from .models import Base, ToDo
from .database import engine, SessionLocal
from .routers.auth import router as auth_router
from .routers.to_do import router as to_do_router
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from starlette import status

import os

script_dir=os.path.dirname(__file__)
st_abs_path=os.path.join(script_dir,"static/")

app=FastAPI()
app.mount("/static",StaticFiles(directory=st_abs_path),name="static")

app.get("/")
def read_root(request:Request):
    #bir request geldiğinde ve kullanıcı zaten giriş yaptıysa todo.xhtml sayfasına gitsin
    return RedirectResponse(url="/to_do/todo-page",status_code=status.HTTP_302_FOUND)


app.include_router(auth_router)
app.include_router(to_do_router)

Base.metadata.create_all(bind=engine)

