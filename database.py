# database.py
# SQLAlchemy를 이용한 PostgreSQL 연결 설정 및 DB 세션 제공
# - DATABASE_URL은 .env에서 읽음 (postgresql+psycopg2://user:pw@host:port/dbname)

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL이 설정되지 않았습니다. .env 파일에 DATABASE_URL을 설정하세요.")

# create_engine: sync 사용 (psycopg2-binary 필요)
engine = create_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base 클래스 (모델이 상속)
Base = declarative_base()

# FastAPI Depends에서 사용할 DB 세션 generator
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
