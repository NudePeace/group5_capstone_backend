from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database import get_db
from models import User, PasswordResetCode
from smtp_utils import send_email_sync
from datetime import datetime, timedelta, timezone
import bcrypt
import random

router = APIRouter(prefix="/auth")

# ------------------------------
# Pydantic Models
# ------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordConfirm(BaseModel):
    email: EmailStr
    new_password: str

class ResetPasswordVerify(BaseModel):
    email: EmailStr
    code: str

# ----------------------------------------------------
# 이메일 중복 확인
# ----------------------------------------------------
@router.get("/check-email")
async def check_email(email: EmailStr, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == email).first()
    return {
        "available": exists is None,
        "message": "사용 가능한 이메일입니다." if not exists else "이미 사용 중인 이메일입니다."
    }


# ----------------------------------------------------
# 회원가입
# ----------------------------------------------------
@router.post("/register")
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.email == data.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="비밀번호는 8자 이상이어야 합니다.")

    hashed_pw = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    user = User(
        email=data.email,
        password=hashed_pw
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"success": True, "message": "회원가입 완료", "user_id": user.user_id}


# ----------------------------------------------------
# 로그인
# ----------------------------------------------------
@router.post("/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    email = data.email
    password = data.password
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

    request.session["user_id"] = str(user.user_id)
    request.session["email"] = user.email

    user.last_login = datetime.utcnow()
    db.commit()

    return {"success": True, "message": "로그인 성공"}


# ----------------------------------------------------
# 로그아웃
# ----------------------------------------------------
@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"success": True, "message": "로그아웃 완료"}


# ----------------------------------------------------
# 현재 로그인 사용자 정보
# ----------------------------------------------------
@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="유효하지 않은 사용자")

    return {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "last_login": user.last_login,
        "created_at": user.created_at
    }


# ----------------------------------------------------
# 비밀번호 변경 (로그인 상태)
# ----------------------------------------------------
@router.post("/change-password")
def change_password(request: Request, data: ChangePasswordRequest, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    if not bcrypt.checkpw(data.current_password.encode(), user.password.encode()):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")

    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="새 비밀번호는 8자 이상이어야 합니다.")

    hashed_pw = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode("utf-8")
    user.password = hashed_pw
    db.commit()

    return {"success": True, "message": "비밀번호가 변경되었습니다."}


# ----------------------------------------------------
# 비밀번호 찾기 - 인증코드 요청
# ----------------------------------------------------
@router.post("/password-reset/request")
def password_reset_request(data: ResetPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="등록되지 않은 이메일입니다.")

    code = str(random.randint(100000, 999999))
    expires = datetime.utcnow() + timedelta(minutes=5)

    entry = PasswordResetCode(email=data.email, code=code, expires_at=expires)
    db.add(entry)
    db.commit()

    background_tasks.add_task(
        send_email_sync,
        data.email,
        "[서비스명] 비밀번호 재설정 인증코드",
        f"인증코드: {code}\n5분 내에 입력하세요."
    )

    return {"success": True, "message": "인증코드가 이메일로 발송되었습니다."}


@router.post("/password-reset/verify-code")
def password_reset_verify_code(data: ResetPasswordVerify, db: Session = Depends(get_db)):
    record = (
        db.query(PasswordResetCode)
        .filter(PasswordResetCode.email == data.email, PasswordResetCode.code == data.code)
        .order_by(PasswordResetCode.created_at.desc())
        .first()
    )

    if not record:
        raise HTTPException(status_code=400, detail="잘못된 인증코드입니다.")

    if record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="인증코드가 만료되었습니다.")

    return {"success": True, "message": "인증코드가 확인되었습니다."}

# ----------------------------------------------------
# 비밀번호 찾기 - 인증코드 확인 + 비밀번호 재설정
# ----------------------------------------------------
@router.post("/password-reset/confirm")
def password_reset_confirm(data: ResetPasswordConfirm, db: Session = Depends(get_db)):
    record = (
        db.query(PasswordResetCode)
        .filter(PasswordResetCode.email == data.email)
        .order_by(PasswordResetCode.created_at.desc())
        .first()
    )

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="비밀번호는 8자 이상이어야 합니다.")

    hashed_pw = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode("utf-8")
    user.password = hashed_pw

    db.delete(record)
    db.commit()

    return {"success": True, "message": "비밀번호가 성공적으로 재설정되었습니다."}
