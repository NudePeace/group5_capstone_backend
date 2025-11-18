from motor.motor_asyncio import AsyncIOMotorClient
import asyncpg
from typing import Any, Optional
import os
from dotenv import load_dotenv
load_dotenv()

#POSTGRES
DB_HOST = os.getenv("DB_HOST", "localhost")
POSTGRES_USER = os.getenv("POSTGRES_USER", "default")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "default")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB_NAME = os.getenv("POSTGRES_DB", "capstone")

POSTGRES_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{POSTGRES_PORT}/{POSTGRES_DB_NAME}"
)

# MongoDB
MONGO_USER = os.getenv("MONGO_USER", "")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB_NAME = os.getenv("MONGO_DB", "capstone")

if MONGO_USER and MONGO_PASSWORD:
    MONGO_URL = (
        f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{DB_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource=admin"
    )
else:
    MONGO_URL = f"mongodb://{DB_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}"

db_postgres: Optional[asyncpg.Pool] = None


async def init_postgres_pool():
    global db_postgres
    try:
        db_postgres = await asyncpg.create_pool(POSTGRES_URL)
        print("PostgreSQL: 데이터베이스 연결 성공")
    except Exception as e:
        print(f"데이터베이스에 연결 실패: {e}")
        raise


async def close_postgres_pool():
    if db_postgres:
        await db_postgres.close()
        print("PostgreSQL: 데이터베이스 연결 종료")

CLIENT = AsyncIOMotorClient(MONGO_URL)
db_mongo = CLIENT[MONGO_DB_NAME]

async def check_mongo_connection():
    try:
        await db_mongo.client.server_info()
        print("MongoDB: 데이터베이스 연결 성공")
    except Exception as e:
        print(f"데이터베이스에 연결 실패: {e}")

async def execute_query(query: str, *args: Any) -> int:
    if not db_postgres:
        raise ConnectionError("PostgreSQL 연결 초기화하 지않았습니다")

    try:
        new_id = await db_postgres.fetchval(query, *args)
        return new_id if new_id is not None else 0

    except asyncpg.exceptions.UniqueViolationError:
        raise ValueError("이메일이 이미 사용되었습니다.")
    except Exception as e:
        print(f"쿼리 오류: {e}")
        raise
