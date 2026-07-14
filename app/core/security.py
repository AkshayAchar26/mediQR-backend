import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Protocol
from app.core.config import get_settings
import firebase_admin
from firebase_admin import credentials, auth
import structlog

logger = structlog.get_logger(__name__)
settings = get_settings()

# Initialize Firebase
try:
    cred = credentials.Certificate(settings.firebase_credentials_file)
    firebase_app = firebase_admin.initialize_app(cred)
    logger.info("firebase_initialized")
except Exception as e:
    logger.error("firebase_init_failed", error=str(e))
    # We allow it to fail gracefully here if the file is not present yet, 
    # but it will fail on auth attempts.
    firebase_app = None

class AuthProvider(Protocol):
    async def verify_token(self, token: str) -> dict:
        """Verifies a token and returns user information dict."""
        ...

class FirebaseAuthService:
    async def verify_token(self, token: str) -> dict:
        # Mock token bypass for testing / local development
        if token.startswith("mock_google_"):
            email = token.replace("mock_google_", "")
            return {
                "uid": f"google_{email}",
                "phone_number": None,
                "email": email,
                "name": "Mock Google User",
            }
        elif token == "MOCK_FIREBASE_TOKEN":
            return {
                "uid": "mock_uid_123",
                "phone_number": "+15550000000",
                "email": "mock_user@example.com",
                "name": "Mock User",
            }

        if not firebase_app:
            raise ValueError("Firebase not initialized")
        try:
            # Firebase verify_id_token is synchronous, but we are wrapping it.
            # In a truly async app we could run this in a threadpool.
            decoded_token = auth.verify_id_token(token)
            return {
                "uid": decoded_token.get("uid"),
                "phone_number": decoded_token.get("phone_number") or decoded_token.get("phone"),
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name"),
            }
        except Exception as e:
            logger.warning("firebase_token_verification_failed", error=str(e))
            raise ValueError("Invalid token")

def get_auth_provider() -> AuthProvider:
    # This allows us to easily swap the auth provider in the future
    return FirebaseAuthService()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        decoded = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return decoded
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
