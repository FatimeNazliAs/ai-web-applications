from typing import Annotated
from fastapi import APIRouter, Depends, Path, HTTPException,Request
from google.auth.aws import RequestSigner
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse

from models import Base, ToDo
from database import engine, SessionLocal
from routers.auth import get_current_user
from fastapi.templating import Jinja2Templates

from dotenv import load_dotenv
import google.generativeai as genai
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage,AIMessage

import markdown
from bs4 import BeautifulSoup


router=APIRouter(
    prefix="/to_do",
    tags=["ToDo"]
)

templates=Jinja2Templates(directory="templates")



class ToDoRequest(BaseModel):
    title:str=Field(min_length=3)
    description:str=Field(min_length=3,max_length=1000)
    priority:int=Field(gt=0,lt=6)
    complete:bool



def get_db():
    # bu methodun amacı database'i çağırmak, her endpointe dependency olarak verilecek.
    db=SessionLocal()
    try:
        # yield'ın return'den farkı generator fonksiyon olması, return 1 değer döndürürken
        #yield birkaç değer döndürebilir
        yield db
    finally:
        # session iş bittikten sonra kapatılıyor
        db.close()


#normalde, her fonksiyona parametre olarak uzun bir şekilde vermektense, değişken yaratıp
#sadece değişken ismini çağırabilirsin
db_dependency=Annotated[Session,Depends(get_db)]
#get_current_user returns dictionary
user_dependency=Annotated[dict,Depends(get_current_user)]


def redirect_to_login():
    redirect_response=RedirectResponse(url="/auth/login-page",status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response



@router.get("/todo-page")
async def render_todo_page(request:Request,db:db_dependency):
    try:
        #base.js dosyasında token 'access_token' olarak kaydedilmiş!
        user=await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        todos=db.query(ToDo).filter(ToDo.owner_id==user.get('id')).all()

        return templates.TemplateResponse("todo.html",{"request":request,"todos":todos,"user":user})

    except:
        return redirect_to_login()




@router.get("/edit-todo-page/{to_do_id}")
async def render_edit_todo_page(request:Request,to_do_id:int,db:db_dependency):
    try:
        #base.js dosyasında token 'access_token' olarak kaydedilmiş!
        user=await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        todo=db.query(ToDo).filter(ToDo.id==to_do_id).first()

        return templates.TemplateResponse("edit-todo.html",{"request":request,"todo":todo,"user":user})

    except:
        return redirect_to_login()



@router.get("/add-todo-page")
async def render_add_todo_page(request:Request):
    try:
        user=await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("add-todo.html",{"request":request,"user":user})

    except:
        return redirect_to_login()








@router.get("/read_all")
async def read_all(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(ToDo).filter(ToDo.owner_id==user.get('id')).all()


@router.get("/to_do/{to_do_id}",status_code=status.HTTP_200_OK)
async  def read_by_id(user:user_dependency,db:db_dependency,to_do_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    #ilk olarak todo'yu id üzerinden bul
    #sonra da o todo ilgili kullanıcıya mı ait filtrele

    todo=db.query(ToDo).filter(ToDo.id==to_do_id).filter(ToDo.owner_id==user.get('id')).first()
    if todo is not None:
        return todo
    raise  HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo id not found")



@router.post("/to_do",status_code=status.HTTP_201_CREATED)
async def create_to_do(user:user_dependency,db:db_dependency,to_do_request:ToDoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    todo=ToDo(**to_do_request.dict(),owner_id=user.get("id"))
    todo.description=create_to_do_with_gemini(todo.description)
    db.add(todo)
    db.commit()


@router.put("/to_do/{to_do_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_to_do(user:user_dependency,db:db_dependency,to_do_request:ToDoRequest,to_do_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(ToDo).filter(ToDo.id == to_do_id).filter(ToDo.owner_id==user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo id not found")

    todo.title=to_do_request.title
    todo.description=to_do_request.description
    todo.priority=to_do_request.priority
    todo.complete=to_do_request.complete

    db.add(todo)
    db.commit()

@router.delete("/to_do/{to_do_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_to_do(user:user_dependency,db:db_dependency,to_do_id:int=Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    todo = db.query(ToDo).filter(ToDo.id == to_do_id).filter(ToDo.owner_id==user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo id not found")
   # db.query(ToDo).filter(ToDo.id == to_do_id).delete()
    db.delete(todo)
    db.commit()



def create_to_do_with_gemini(to_do_string:str):
    load_dotenv()
    genai.configure(api_key=os.environ.get('GOOGLE_API_KEY'))
    llm=ChatGoogleGenerativeAI(model="gemini-1.5-pro")
    response=llm.invoke(
        [
            HumanMessage(content="I will provide you a todo item to add my to do list. "
                                 "What I want you to do is to create a longer and more comprehensive description of that todo item, "
                                 "my next message will be my todo: "),
            HumanMessage(content=to_do_string),
        ]
    )
    return markdown_to_text(response.content)

def markdown_to_text(markdown_string):
    html=markdown.markdown(markdown_string)
    soup=BeautifulSoup(html,"html.parser")
    text=soup.get_text()
    return text



