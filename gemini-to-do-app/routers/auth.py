from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel
from sqlalchemy.util import deprecated
from typing import Annotated
from database import engine, SessionLocal
from models import User
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from jose import jwt,JWTError
from datetime import timedelta,datetime,timezone


router=APIRouter(
    prefix="/auth",
    tags=["Authentication"])

SECRET_KEY="np4pu48pawtshh1drsj7lgacpuvt8hxu"
ALGORITHM="HS256"



def get_db():
    db=SessionLocal()
    try:

        yield db
    finally:
        db.close()

db_dependency=Annotated[Session,Depends(get_db)]


bcrypt_context=CryptContext(schemes=["bcrypt"],deprecated="auto")


class CreateUserRequest(BaseModel):
    username:str
    email:str
    first_name:str
    last_name:str
    password:str
    role:str


def create_access_token(username:str,user_id:int,role:str,expires_delta:timedelta):
    payload={'sub':username,'id':user_id,'role':role}
    expires=datetime.now(timezone.utc)+expires_delta
    payload.update({'exp':expires})
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)



def authenticate_user(username:str,password:str,db):
    user=db.query(User).filter(User.username==username)
    if not user:
        return False
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
    return user




@router.post("/",status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency,create_user_request:CreateUserRequest):
    user=User(
        username=create_user_request.username,
        email=create_user_request.email,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        is_active=True,
        hashed_password=bcrypt_context.hash(create_user_request.password))
    db.add(user)
    db.commit()





@router.post("/token")
async def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],
                                 db:db_dependency):
    user=authenticate_user(form_data.username,form_data.password,db)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect username or password")
    token=create_access_token(user.username, user.id,user.role,timedelta(minutes=60))
    return {"access_token":token,"token_type":"bearer"}



