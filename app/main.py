from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.exceptions import AppError, app_error_handler, general_exception_handler
from app.core.logging import setup_logging
from app.modules.auth.router import router as auth_router
from app.modules.doctors.router import router as doctors_router
from app.modules.patients.router import router as patients_router
from app.modules.prescriptions.router import router as prescriptions_router
from app.modules.qr.router import router as qr_router
from app.modules.doses.router import router as doses_router
from app.modules.ocr.router import router as ocr_router

setup_logging()

app = FastAPI(
    title="MediQR API",
    description="Backend API for Prescription QR App",
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(doctors_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")
app.include_router(prescriptions_router, prefix="/api/v1")
app.include_router(qr_router, prefix="/api/v1")
app.include_router(doses_router, prefix="/api/v1")
app.include_router(ocr_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}
