from pydantic import BaseModel, Field

class OTPSendRequest(BaseModel):
    email: str = Field(..., description="User email address")

class OTPVerifyRequest(BaseModel):
    email: str = Field(..., description="User email address")
    otp: str = Field(..., description="6-digit OTP code")

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(..., description="Firebase ID Token containing Google authentication credentials")

