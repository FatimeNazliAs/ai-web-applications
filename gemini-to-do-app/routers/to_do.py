from typing import Annotated

from fastapi import APIRouter, Depends, Path, HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from starlette import status

from models import Base, ToDo
from database import engine, SessionLocal

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

@router.get("/read_all")
async def read_all(db:db_dependency):
    return db.query(ToDo).all()


@router.get("/get_by_id/{to_do_id}",status_code=status.HTTP_200_OK)
async  def read_by_id(db:db_dependency,to_do_id:int=Path(gt=0)):
    todo=db.query(ToDo).filter(ToDo.id==to_do_id).first()
    if todo is not None:
        return todo
    raise  HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Todo id not found")



@router.post("/create_to_do",status_code=status.HTTP_201_CREATED)
async def create_to_do(db:db_dependency,to_do_request:ToDoRequest):
    todo=ToDo(**to_do_request.dict())
    db.add(todo)
    db.commit()


@router.put("/update_to_do/{to_do_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_to_do(db:db_dependency,to_do_request:ToDoRequest,to_do_id:int=Path(gt=0)):
    todo = db.query(ToDo).filter(ToDo.id == to_do_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo id not found")

    todo.title=to_do_request.title
    todo.description=to_do_request.description
    todo.priority=to_do_request.priority
    todo.complete=to_do_request.complete

    db.add(todo)
    db.commit()

@router.delete("/delete_to_do/{to_do_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_to_do(db:db_dependency,to_do_id:int=Path(gt=0)):
    todo = db.query(ToDo).filter(ToDo.id == to_do_id).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo id not found")
   # db.query(ToDo).filter(ToDo.id == to_do_id).delete()
    db.delete(todo)
    db.commit()
