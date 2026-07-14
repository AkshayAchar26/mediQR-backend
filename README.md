# MediQR Backend

A **FastAPI** backend for the MediQR prescription management system. It handles doctor/patient authentication, prescription management, QR code generation & claiming, dose tracking, and AI-powered OCR for prescription images.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [Database Models](#database-models)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
- [Database Migrations](#database-migrations)
- [Authentication Flow](#authentication-flow)
- [Project Structure](#project-structure)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.139+ |
| Language | Python 3.12+ |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL (via Supabase) |
| DB Driver | asyncpg |
| Migrations | Alembic |
| Auth | Firebase Admin SDK + custom JWT (PyJWT) |
| AI / OCR | Google Gemini 2.5 Flash (`google-genai`) |
| File Storage | Supabase Storage |
| Package Manager | `uv` |
| Server | Uvicorn |
| Logging | structlog |
| Validation | Pydantic v2 |

---

## Architecture Overview

The backend follows a **modular layered architecture**:

```
app/
├── core/           # Cross-cutting concerns (config, security, deps, AI, storage)
├── db/
│   ├── base.py     # SQLAlchemy async session factory
│   └── models/     # ORM models
└── modules/        # Feature modules (each has router, service, repository, schemas)
    ├── auth/
    ├── doctors/
    ├── patients/
    ├── prescriptions/
    ├── qr/
    ├── doses/
    └── ocr/
```

Each module follows the **Repository Pattern**:
- **Router** — HTTP endpoints, request/response handling
- **Service** — Business logic
- **Repository** — Database access (SQLAlchemy queries)
- **Schemas** — Pydantic request/response models

---

## Database Models

### `doctors`
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | String | Doctor's full name |
| `email` | String (unique) | Email address |
| `phone` | String (unique) | Phone number |
| `hospital_or_clinic` | String | Workplace |
| `expertise` | String[] | List of specializations |
| `certificate_url` | String? | URL to uploaded certificate |
| `verified_status` | String | `pending` / `verified` / `rejected` |
| `created_at` | Timestamp | Record creation time |

### `patients`
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | String | Patient's full name |
| `email` | String (unique) | Email address |
| `phone` | String (unique) | Phone number |
| `dob` | Date? | Date of birth |
| `created_at` | Timestamp | Record creation time |

### `prescriptions`
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `doctor_id` | UUID (FK) | Issuing doctor |
| `patient_id` | UUID? (FK) | Claiming patient (null until claimed) |
| `hospital_or_clinic` | String | Where issued |
| `till_date` | Date | Prescription validity end date |
| `notes` | String? | Optional doctor notes |
| `status` | String | `unclaimed` / `claimed` |
| `created_at` | Timestamp | Record creation time |

### `medicines`
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `prescription_id` | UUID (FK) | Parent prescription (cascade delete) |
| `name` | String | Medicine name |
| `dosage` | String | e.g., `500mg` |
| `times_per_day` | Time[] | Array of scheduled times (e.g., `["08:00:00", "20:00:00"]`) |
| `instructions` | String? | Special instructions |
| `created_at` | Timestamp | Record creation time |

### `email_otps`
| Column | Type | Description |
|---|---|---|
| `email` | String (PK) | Email address |
| `otp` | String | 6-digit OTP code |
| `expires_at` | Timestamp | OTP expiry |
| `created_at` | Timestamp | Record creation time |

### `prescription_qr`
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `prescription_id` | UUID (FK) | Associated prescription |
| `token` | String (unique) | One-time claim token |
| `status` | String | `active` / `claimed` / `expired` |
| `expires_at` | Timestamp | Token expiry |
| `claimed_by` | UUID? (FK) | Patient who claimed it |
| `claimed_at` | Timestamp? | Claim timestamp |
| `created_at` | Timestamp | Record creation time |

### `patient_history_qr`
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `patient_id` | UUID (FK) | Owning patient |
| `token` | String (unique) | Shareable token |
| `scope` | String | `all` or `selected` |
| `scope_prescription_ids` | UUID[]? | Specific prescriptions to share |
| `status` | String | `active` / `expired` |
| `expires_at` | Timestamp | Token expiry |
| `created_at` | Timestamp | Record creation time |

### `history_access_logs`
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `patient_history_qr_id` | UUID (FK) | Which QR was used |
| `doctor_id` | UUID (FK) | Doctor who accessed |
| `accessed_at` | Timestamp | Access timestamp |

### `dose_logs`
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `medicine_id` | UUID (FK) | Associated medicine (cascade delete) |
| `scheduled_datetime` | Timestamp | When the dose is scheduled |
| `marked_status` | String? | `taken` / `taken_late` (null = pending) |
| `marked_at` | Timestamp? | When it was marked |
| `created_at` | Timestamp | Record creation time |

---

## API Endpoints

All endpoints are prefixed with `/api/v1`. Interactive docs: **`http://localhost:8000/api/v1/docs`**

### Auth `/api/v1/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/otp/send` | None | Send OTP to email |
| `POST` | `/auth/otp/verify` | None | Verify OTP, receive JWT |
| `POST` | `/auth/google` | None | Login via Google Firebase ID token |

### Doctors `/api/v1/doctors`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/doctors/register` | Unregistered JWT | Register a new doctor profile |
| `GET` | `/doctors/me` | Doctor JWT | Get own doctor profile |
| `PATCH` | `/doctors/me` | Doctor JWT | Update own doctor profile |

### Patients `/api/v1/patients`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/patients/register` | Unregistered JWT | Register a new patient profile |
| `GET` | `/patients/me` | Patient JWT | Get own patient profile |
| `PATCH` | `/patients/me` | Patient JWT | Update own patient profile |

### Prescriptions `/api/v1/prescriptions`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/prescriptions` | Doctor JWT | Create a new prescription |
| `GET` | `/prescriptions/mine` | Doctor JWT | List doctor's own prescriptions |
| `GET` | `/prescriptions` | Patient JWT | List patient's claimed prescriptions |
| `GET` | `/prescriptions/{id}` | Doctor or Patient JWT | Get a single prescription by ID |

### QR Codes `/api/v1/qr`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/qr/prescription/{prescription_id}` | Doctor JWT | Generate a one-time prescription QR token |
| `POST` | `/qr/prescription/claim` | Patient JWT | Claim a prescription via QR token |
| `POST` | `/qr/history` | Patient JWT | Generate a history-sharing QR token |
| `POST` | `/qr/history/claim` | Doctor JWT | Scan patient's history QR and view prescriptions |
| `GET` | `/qr/history/access-logs` | Patient JWT | View who accessed your history QR |

### Doses `/api/v1/doses`

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/doses?prescription_id=<uuid>` | Patient JWT | List all doses for a prescription with status |
| `POST` | `/doses/{dose_log_id}/mark-taken` | Patient JWT | Mark a dose as taken (server evaluates on-time vs late) |

### OCR `/api/v1/ocr`

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/ocr/upload` | Any JWT | Upload a prescription image for AI extraction |
| `GET` | `/ocr/{source_id}` | Any JWT | Get extracted data for review |
| `PATCH` | `/ocr/{source_id}` | Doctor JWT | Edit AI-extracted JSON if corrections needed |
| `POST` | `/ocr/{source_id}/confirm` | Doctor JWT | Confirm extraction and create official prescription |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |

---

## Environment Variables

Create a `.env` file in the `backend/` directory. **Never commit this file.**

```env
# App
ENVIRONMENT=development

# PostgreSQL via Supabase
DATABASE_URL=postgresql+asyncpg://postgres:<password>@db.<project-ref>.supabase.co:5432/postgres

# Supabase (for file storage)
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
SUPABASE_SECRET_KEY=sb_secret_...
SUPABASE_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json

# JWT (internal backend token)
JWT_SECRET=change-me-in-production
# JWT_ALGORITHM defaults to HS256, expiry defaults to 7 days

# Firebase (service account JSON for verifying Firebase ID tokens)
FIREBASE_CREDENTIALS_FILE=../mediqr-917f9-firebase-adminsdk-fbsvc-ab41a12577.json

# Google Gemini AI (for OCR)
GEMINI_API_KEY=your-gemini-api-key
```

> **Warning:** The `JWT_SECRET` must be a long, random, unpredictable string in production. Never use the default value.

---

## Getting Started

### Prerequisites

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) package manager
- A running PostgreSQL database (Supabase recommended)
- Firebase project with a service account JSON file
- Google Gemini API key

### 1. Install dependencies

```bash
cd backend
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in all variables in .env
```

### 3. Run database migrations

```bash
uv run alembic upgrade head
```

### 4. Start the development server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using the virtual environment directly:

```bash
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Base URL:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/api/v1/docs`
- **OpenAPI JSON:** `http://localhost:8000/api/v1/openapi.json`
- **Health Check:** `http://localhost:8000/health`

---

## Scripts

All commands should be run from the `backend/` directory.

### Run Development Server

```bash
# Using uv (recommended)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Using the venv directly (Windows)
.venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Using the venv directly (macOS / Linux)
.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> `--reload` watches for file changes and auto-restarts the server (dev only). Remove it in production.

### Run Production Server

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Install Dependencies

```bash
# Install all dependencies (reads pyproject.toml + uv.lock)
uv sync

# Add a new package
uv add <package-name>

# Remove a package
uv remove <package-name>
```

### Database Migrations

```bash
# Apply all pending migrations (run this on first setup and after pulling changes)
uv run alembic upgrade head

# Auto-generate a new migration from model changes
uv run alembic revision --autogenerate -m "short description of change"

# Rollback the last migration
uv run alembic downgrade -1

# Rollback all migrations
uv run alembic downgrade base

# View migration history
uv run alembic history --verbose

# Show current migration version
uv run alembic current
```

### Run Tests

```bash
# Run end-to-end tests
uv run python test_e2e.py

# Run OCR tests
uv run python test_ocr.py

# Get a test JWT token (useful for manual API testing)
uv run python get_test_token.py
```

### Useful One-liners

```bash
# Check the health endpoint
curl http://localhost:8000/health

# Open Swagger UI in browser (Windows)
start http://localhost:8000/api/v1/docs

# Open Swagger UI in browser (macOS)
open http://localhost:8000/api/v1/docs
```

---

## Database Migrations

This project uses **Alembic** for database migrations.

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Create a new migration after changing models
uv run alembic revision --autogenerate -m "description of change"

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history
```

---

## Authentication Flow

The app supports **two login methods**:

### 1. Email OTP Flow
```
POST /auth/otp/send   { email }
  → Sends a 6-digit OTP to the email
POST /auth/otp/verify { email, otp }
  → Returns a backend JWT with role: "unregistered" (if new user)
     or role: "doctor"/"patient" (if existing user)
```

### 2. Google Sign-In Flow
```
POST /auth/google { id_token }   (Firebase ID Token from the app)
  → Verifies token with Firebase Admin SDK
  → Returns a backend JWT
```

### JWT Token Roles

| Role | Description |
|---|---|
| `unregistered` | Authenticated but no profile yet — must call `/doctors/register` or `/patients/register` |
| `doctor` | Fully registered doctor |
| `patient` | Fully registered patient |

All protected endpoints expect an `Authorization: Bearer <token>` header.

### Development Mock Tokens

For local testing without Firebase:
- `mock_google_<email>` — Simulates a Google login for the given email
- `MOCK_FIREBASE_TOKEN` — Returns a fixed mock user

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory, middleware, router registration
│   ├── core/
│   │   ├── config.py        # Pydantic settings (reads from .env)
│   │   ├── security.py      # Firebase token verification, JWT create/decode
│   │   ├── deps.py          # FastAPI dependency injection (require_doctor, require_patient)
│   │   ├── exceptions.py    # Custom exception classes and handlers
│   │   ├── logging.py       # structlog setup
│   │   ├── ai.py            # Gemini Vision AI integration (OCR)
│   │   └── storage.py       # Supabase Storage file upload
│   ├── db/
│   │   ├── base.py          # Async SQLAlchemy engine + session
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── users.py     # Doctor, Patient, EmailOTP models
│   │       ├── prescriptions.py  # Prescription, Medicine models
│   │       ├── qr.py        # PrescriptionQR, PatientHistoryQR, HistoryAccessLog
│   │       ├── doses.py     # DoseLog model
│   │       └── sources.py   # PrescriptionSource model (OCR upload tracking)
│   └── modules/
│       ├── auth/            # OTP send/verify, Google login
│       ├── doctors/         # Doctor registration and profile
│       ├── patients/        # Patient registration and profile
│       ├── prescriptions/   # Prescription CRUD
│       ├── qr/              # QR token generation and claiming
│       ├── doses/           # Dose listing and marking
│       └── ocr/             # Image upload, AI extraction, confirm to prescription
├── migrations/              # Alembic migration scripts
├── alembic.ini              # Alembic configuration
├── pyproject.toml           # Project metadata and dependencies
├── .env                     # Local environment variables (git-ignored)
└── .python-version          # Python version pin (for uv)
```
