import logging
import time
import logging

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from Database import init_postgres_pool, close_postgres_pool

logger = logging.getLogger("uvicorn.access")
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(name)s: %(message)s')

class LogAccessMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        log_message = (
            f'{request.client.host}:{request.client.port} - '
            f'"{request.method} {request.url.path}" '
            f'{response.status_code} - '
            f'{process_time:.4f}s'
        )
        logger.info(log_message)

        return response

load_dotenv()

app = FastAPI(
    title="Capstone API",
    version="1.0.0",
    description="API for user authentication and management."
)

@app.on_event("startup")
async def startup_event():
    await init_postgres_pool()

@app.on_event("shutdown")
async def shutdown_event():
    await close_postgres_pool()

try:
    from Router import user_router

    app.include_router(user_router, prefix="/user", tags=["user"])
except ImportError:
    print("WARNING: Không tìm thấy Router.py. API endpoints không khả dụng.")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Chào mừng đến với Capstone API. Truy cập /docs để xem tài liệu."}
