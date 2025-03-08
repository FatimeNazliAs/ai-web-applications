from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


sqlite_file_name = "gemini_to_do_app.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)
SessionLocal=sessionmaker(autoflush=False,autocommit=False,bind=engine)

Base=declarative_base()
