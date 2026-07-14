from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db_session
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedError
import structlog

logger = structlog.get_logger(__name__)

security = HTTPBearer()

def get_token_payload(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = decode_access_token(credentials.credentials)
        return payload
    except ValueError as e:
        logger.warning("invalid_token", error=str(e))
        raise UnauthorizedError("Invalid or expired token")

def get_current_user_id(payload: dict = Depends(get_token_payload)) -> str:
    """Returns the user ID (UUID as string) from the token. Note that for 'unregistered' this might be 'none'"""
    user_id = payload.get("sub")
    if not user_id:
        # Fallback for temporary token
        return payload.get("email", "unknown")
    return user_id

def require_role(role: str):
    def role_checker(payload: dict = Depends(get_token_payload)):
        if payload.get("role") != role:
            raise UnauthorizedError(f"Requires {role} role")
        return payload
    return role_checker

def require_doctor(payload: dict = Depends(require_role("doctor"))) -> str:
    """Returns doctor UUID as string"""
    return payload["sub"]

def require_patient(payload: dict = Depends(require_role("patient"))) -> str:
    """Returns patient UUID as string"""
    return payload["sub"]
