from typing import Dict, Any
import logging

from fastapi import APIRouter, HTTPException, status
from services.UserService import register_new_user, check_existed_email, login_for_access_token
from Model.UserModel import UserRegisterRequest, UserLoginRequest

user_router = APIRouter(tags=["user"])

logger = logging.getLogger(__name__)

@user_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegisterRequest):

    try:
        user_id = await register_new_user(user_data)

        response_data = {
            "message": "계좌 등록이 성공했습니다!",
            "user_id": user_id
        }
        logger.info(f"SIGNUP SUCCESS: User {user_id} registered with email {user_data.email}")
        return response_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Server Error")

@user_router.get("/email-validation", status_code=status.HTTP_200_OK)
async def email_validation(email: str) -> Dict[str, Any]:
    try:
        result = await check_existed_email(email)
        logger.info(result)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal Server Error")


# @user_router.post("/login")
# async def login(user_data: UserLoginRequest):
#     token = await login_for_access_token(user_data.email, user_data.password)
#
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Sai email hoặc mật khẩu.",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     return {
#         "access_token": token,
#         "token_type": "bearer"
#     }