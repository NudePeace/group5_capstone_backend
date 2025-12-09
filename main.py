# main.py
# FastAPI 애플리케이션 진입점
# - CORS 설정
# - 세션 미들웨어 등록 (Starlette SessionMiddleware 사용)
# - 라우터 등록
# - DB 모델 테이블 생성

import os
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# 로컬 .env 파일 로드
load_dotenv()

from database import Base, engine  # DB 모델/엔진
import auth  # auth.router 포함

# DB 테이블 자동 생성 (개발용)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Auth Service (FastAPI + PostgreSQL + Session)")

# CORS 설정
# 개발 중에는 localhost 포트를 허용. 운영에서는 정확한 도메인만 허용해야 함.
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,   # 세션 쿠키를 전달하려면 True
    allow_methods=["*"],
    allow_headers=["*"],
)

# 세션 미들웨어 등록
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY가 설정되지 않았습니다. .env 파일에 SECRET_KEY를 설정하세요.")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY
)

# 인증 라우터 등록
app.include_router(auth.router)

# uvicorn으로 실행:
# uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
