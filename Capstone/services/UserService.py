from AuthUtil import hash_password, create_access_token, verify_password
from Model.UserModel import UserRegisterRequest, UserLoginRequest, PasswordChangeRequest
from Database import execute_query
from typing import Dict, Any, Optional

async def check_existed_email(email: str) -> Dict[str, Any]:
    sql = """
    SELECT user_id FROM users WHERE email = $1;
    """
    used_email = await execute_query(sql, email)

    if used_email:
        return{
            "is_available": False,
            "message": "사용된 이메일"
        }
    return {
        "is_available": True,
        "message": "이메일을 사용할 수 있습니다"
    }

async def register_new_user(user_data: UserRegisterRequest) -> int:

    hashed_password = hash_password(user_data.password)
    sql = """
    INSERT INTO users (email, password)
    VALUES ($1, $2)
    RETURNING user_id;
    """
    try:
        user_id = await execute_query(sql,
                                             # user_data.username,
                                             user_data.email,
                                             hashed_password)
    except ValueError as e:
        raise ValueError(str(e))
    except Exception as e:
        raise Exception("회원가입이 완료되었습니다!")

    return user_id

async def authenticate_user(email: str, password: str):
    sql = "SELECT user_id, email, password FROM users WHERE email = $1;"

    # 1. Thực thi truy vấn
    user_results = await execute_query(sql, email)

    user_record = None

    if user_results:
        if isinstance(user_results, list) and len(user_results) > 0:
            # Trường hợp 1: Hàm trả về List of Records (Phổ biến)
            user_record = user_results[0]
        # Trường hợp 2: Hàm trả về trực tiếp một Record/Dictionary/Row object
        elif hasattr(user_results, 'get') or hasattr(user_results, 'keys'):
            user_record = user_results
        # Trường hợp 3: Trả về một đối tượng Record duy nhất (ví dụ: từ fetchone())
        elif not isinstance(user_results, (list, int, str, float)):
            user_record = user_results

    if not user_record:
        print("2. user_record: KHÔNG TÌM THẤY (Đảm bảo execute_query trả về row data)")
        return None

    hashed_password = user_record['password']

    if not verify_password(password, hashed_password):
        return None

    return {
        "user_id": user_record['user_id'],
        "email": user_record['email']
    }


async def login_for_access_token(email: str, password: str) -> Optional[str]:
    user = await authenticate_user(email, password)

    if not user:
        return None

    access_token = create_access_token(
        data={"sub": user['email'], "user_id": user['user_id']}
    )
    return access_token


