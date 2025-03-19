from typing import Annotated

from fastapi import APIRouter, Depends, Path, HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from starlette import status

from models import Base, ToDo
from database import engine, SessionLocal
from routers.auth import get_current_user

router=APIRouter(
    prefix="/to_do",
    tags=["ToDo"]
)


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
