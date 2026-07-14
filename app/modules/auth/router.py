from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db_session
from app.core.security import get_auth_provider
from app.modules.auth.schemas import OTPSendRequest, OTPVerifyRequest, AuthResponse, GoogleLoginRequest
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_auth_service() -> AuthService:
    return AuthService(auth_provider=get_auth_provider())

@router.post("/otp/send", response_model=dict)
async def send_otp(
    request: OTPSendRequest,
    db: AsyncSession = Depends(get_db_session),
    service: AuthService = Depends(get_auth_service)
):
    """
    Send OTP code to email.
    """
    await service.send_otp(db, email=request.email)
    return {"data": {"message": "OTP sent successfully"}, "error": None}

@router.post("/otp/verify", response_model=dict)
async def verify_otp(
    request: OTPVerifyRequest,
    db: AsyncSession = Depends(get_db_session),
    service: AuthService = Depends(get_auth_service)
):
    """
    Verify email OTP and return backend JWT token.
    """
    result = await service.verify_login(db, email=request.email, otp=request.otp)
    return {"data": AuthResponse(**result).model_dump(), "error": None}

@router.post("/google", response_model=dict)
async def login_with_google(
    request: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db_session),
    service: AuthService = Depends(get_auth_service)
):
    """
    Verify Google Firebase ID Token and return backend JWT token.
    """
    result = await service.login_with_google(db, id_token=request.id_token)
    return {"data": AuthResponse(**result).model_dump(), "error": None}

