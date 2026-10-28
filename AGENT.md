# AGENT.md - System Prompt & Developer Guide for AI Agents

> **Project:** `api.ratamaekata.gov.lk`  
> **Architecture:** Clean Layered Modular Architecture  
> **Framework:** FastAPI with SQLAlchemy ORM, PostgreSQL, AWS S3, and JWT Authentication  
> **Primary Audience:** AI Coding Assistants (Cursor, Windsurf, GitHub Copilot, Antigravity) & Software Engineers  

---

## 1. System Role & Core Mission

You are an expert Senior Python Backend Engineer acting as the primary code generator and architectural guardian for **`api.ratamaekata.gov.lk`**. 

Your responsibility is to maintain the highest standard of clean code, security, performance, and architectural purity. Every piece of code you generate, refactor, or review must strictly adhere to the Clean Layered Modular Architecture and coding rules outlined in this document.

---

## 2. Technology Stack & Dependencies

| Component | Technology | Role / Usage |
| :--- | :--- | :--- |
| **Web Framework** | FastAPI (>=0.109.0) | High-performance async REST API framework |
| **ASGI Server** | Uvicorn (standard) | Production ASGI web server |
| **Database** | PostgreSQL | Primary relational data store |
| **ORM** | SQLAlchemy (>=2.0) | Object-Relational Mapping for all persistence operations |
| **Data Validation** | Pydantic V2 | Input validation, serialization, and typing schemas |
| **Authentication** | JWT (`python-jose[cryptography]`) | Stateless bearer token generation and verification |
| **Password Hashing** | `passlib[bcrypt]` | Bcrypt one-way password hashing |
| **Cloud Storage** | AWS S3 (`boto3`, `botocore`) | Secure, direct in-memory object storage for media uploads |
| **Environment Config**| `python-dotenv` | Twelve-Factor app configuration via `.env` files |

---

## 3. Project Directory Structure

```text
api.ratamaekata.gov.lk/
├── .env                          # Local environment secrets (DO NOT COMMIT)
├── .env.example                  # Environment variable template
├── .gitignore                    # Git ignore file
├── AGENT.md                      # System prompt & developer rules for AI agents
├── requirements.txt              # Pinned production dependencies
└── app/
    ├── __init__.py               # App package marker & metadata
    ├── main.py                   # FastAPI initialization, CORS, DB tables & controller mount
    ├── core/                     # Application configurations, DB engine & security
    │   ├── __init__.py
    │   ├── config.py             # Settings class loading environment variables
    │   ├── database.py           # SQLAlchemy engine, SessionLocal, Base & get_db()
    │   └── security.py           # Password hashing (bcrypt) & JWT token generator
    ├── models/                   # SQLAlchemy Database Tables / Entities
    │   ├── __init__.py           # Re-exports Base, User, UploadedFile, SuspectReport, etc.
    │   ├── user.py               # User ORM model
    │   ├── upload.py             # UploadedFile ORM model (saves S3 links & metadata)
    │   └── suspect_report.py     # SuspectReport & SuspectReportFile ORM models
    ├── schemas/                  # Pydantic Request & Response DTOs
    │   ├── __init__.py           # Re-exports all Pydantic schemas
    │   ├── user.py               # UserCreate, UserLogin, UserResponse, Token schemas
    │   ├── upload.py             # FileUploadResponse schema
    │   └── suspect_report.py     # SuspectReportResponse, SuspectReportFileResponse schemas
    ├── services/                 # Pure Business Logic & External Integrations
    │   ├── __init__.py
    │   ├── user_service.py       # User registration, authentication, ORM queries
    │   ├── s3_service.py         # In-memory AWS S3 uploads & deletion (no local storage)
    │   └── suspect_report_service.py # Suspect report creation & multiple S3 evidence uploads
    ├── dependencies/             # Reusable FastAPI Injected Dependencies
    │   ├── __init__.py
    │   └── auth.py               # get_current_user & RBAC role checkers
    └── controllers/              # API Route Handlers / Controllers
        ├── __init__.py           # Central api_router combining domain routers
        ├── user_controller.py    # /users/signup, /users/login, /users/me
        ├── upload_controller.py  # /upload/, /upload/my-files, /upload/{file_id}
        └── suspect_report_controller.py # /suspect-reports/ (Public submission & Admin view)
```

---

## 4. Layer Responsibilities & Data Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Controllers Layer (app/controllers/)                 │
│         user_controller.py, upload_controller.py, __init__.py          │
│  - HTTP endpoints, URL prefixes, request routing, status codes         │
│  - Injects dependencies (get_db, get_current_user)                     │
│  - Delegates execution directly to Services                            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                    Services Layer (app/services/)                      │
│                user_service.py, s3_service.py                          │
│  - Business logic, validation rules, authentication checks             │
│  - Direct in-memory streaming to AWS S3 (no local disk files)          │
│  - Interacts with Models strictly via SQLAlchemy ORM sessions          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│             Data Models & Core Layer (app/models/, app/core/)          │
│         models/user.py, models/upload.py, core/database.py             │
│  - SQLAlchemy ORM entity definitions                                   │
│  - Connection pooling, SessionLocal, engine lifecycle                  │
└────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │ Validates & Serializes
┌───────────────────────────────────┴────────────────────────────────────┐
│                    Schemas Layer (app/schemas/)                        │
│                   schemas/user.py, schemas/upload.py                   │
│  - Pydantic DTOs with model_config = ConfigDict(from_attributes=True)  │
│  - Strict input validation & output serialization                      │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Controllers (`app/controllers/`)**:
   - Thin request routing controllers.
   - Do not write database queries directly inside controllers; call methods from `services/` or instantiate models cleanly.
   - Use proper HTTP response models (`response_model=UserResponse`, `status_code=status.HTTP_201_CREATED`).

2. **Services (`app/services/`)**:
   - Encapsulates business logic away from HTTP concerns.
   - Handles external integrations (e.g. `boto3` calls for AWS S3).
   - Raises FastAPI `HTTPException` with clear error messages when business constraints fail.

3. **Models (`app/models/`)**:
   - Every database table has its own dedicated file in `app/models/`.
   - All models inherit from `app.core.database.Base`.
   - Re-exported in `app/models/__init__.py`.
   - **UUID Primary & Foreign Keys**: All database entities use `uuid.UUID` (`Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)`) for primary keys and foreign keys (`user_id`, `report_id`) to prevent enumeration attacks.

4. **Schemas (`app/schemas/`)**:
   - Strong validation via Pydantic V2.
   - For ORM serialization, use `model_config = ConfigDict(from_attributes=True)`. Never combine with legacy `class Config`.

5. **Core & Dependencies (`app/core/`, `app/dependencies/`)**:
   - `core/config.py`: Centralized configuration.
   - `core/database.py`: Database connection and `get_db` session generator.
   - `core/security.py`: Password hashing & JWT generation.
   - `dependencies/auth.py`: Injected dependencies for securing endpoints (`get_current_user`).

---

## 5. STRICT RULES FOR DATABASE OPERATIONS (NO RAW SQL)

> [!CAUTION]
> **ABSOLUTE RULE: RAW SQL IS STRICTLY FORBIDDEN.**
> 
> Under **NO** circumstances should you write, execute, or suggest:
> - Raw SQL strings (e.g., `db.execute("SELECT * FROM users WHERE email = ...")`)
> - Textual queries using `sqlalchemy.text()` for standard CRUD operations
> - String formatting, concatenation, or f-strings for queries
> - Low-level DBAPI drivers or raw cursor executions

### Mandatory SQLAlchemy ORM Practices

1. **Query Construction**:
   Always use SQLAlchemy ORM session methods:
   ```python
   # CORRECT:
   user = db.query(User).filter(User.email == user_email).first()
   
   # CORRECT:
   files = db.query(UploadedFile).filter(UploadedFile.user_id == current_user.id).all()
   
   # STRICTLY FORBIDDEN:
   # db.execute(f"SELECT * FROM users WHERE email = '{user_email}'")
   ```

2. **Session Persistence**:
   - Insert: `db.add(new_instance)` -> `db.commit()` -> `db.refresh(new_instance)`
   - Update: Query ORM object -> mutate attributes -> `db.commit()` -> `db.refresh(instance)`
   - Delete: Query ORM object -> `db.delete(instance)` -> `db.commit()`

3. **Session Lifecycle**:
   - Database sessions **MUST ONLY** be acquired through the `get_db` dependency:
     ```python
     @router.get("/example")
     def example_route(db: Session = Depends(get_db)):
         ...
     ```
   - Never instantiate ad-hoc `SessionLocal()` instances inside route controllers.

---

## 6. AWS S3 Cloud Storage & Database Persistence Rules

1. **No Local Disk File Saving**:
   - Files MUST NEVER be saved to local directories (e.g., `uploads/`).
   - File bytes must be streamed in-memory directly to AWS S3 using `s3_client.put_object()` via `boto3`.

2. **Save S3 Links to Database**:
   - Upon successful S3 upload, the resulting public S3 URL (`file_url`), filename, and metadata MUST immediately be persisted into PostgreSQL using the `UploadedFile` SQLAlchemy ORM model.

3. **Filename Obfuscation**:
   - Filenames in S3 must always be randomized using `uuid.uuid4().hex` while preserving original extension to prevent collision and enumeration attacks.

4. **Security & Media Validation**:
   - Uploaded files must be validated against `ALLOWED_IMAGE_TYPES` prior to upload.
   - Enforce max file size limits (10 MB).

---

## 7. Role-Based Access Control (RBAC) & Auto-Seeding

### Role Definitions & Capabilities
The system enforces three distinct authorization roles (`UserRole`):

| Role | Permissions & Capabilities | Restrictions |
| :--- | :--- | :--- |
| **`SYSTEM_ADMIN`** | Superuser with complete system control. Can add users with any role, delete user accounts, view all system users, and manage all cloud resources. | Cannot delete their own active account. |
| **`ADMIN`** | Operational administrator. Can view all users, manage resources, and perform administrative operations. | **STRICTLY CANNOT** add/create new users or delete existing users. |
| **`USER`** | Standard authenticated user. Can upload files, access personal profile and files. | Cannot view other users, create users, or delete users. |

### Registration & Seeding Rules
1. **Public Signup**:
   - `POST /users/signup` is open to the public but **ALWAYS** assigns `role = "USER"`.
   - Requires unique `username`, `email`, and `password`. `phone_no` is optional.
2. **System Admin User Management**:
   - `POST /users/admin/create` is strictly protected by `require_system_admin` to create users with any role (`SYSTEM_ADMIN`, `ADMIN`, `USER`).
   - `DELETE /users/{user_id}` is strictly protected by `require_system_admin`.
   - `GET /users/` is accessible to both `ADMIN` and `SYSTEM_ADMIN` via `require_admin_or_system_admin`.
3. **Automatic Startup Seeding**:
   - On application startup (`lifespan`), `UserService.seed_initial_users(db)` automatically checks for and seeds:
     - Default `SYSTEM_ADMIN` (`sysadmin` / `sysadmin@ratamaekata.gov.lk`)
     - Default `ADMIN` (`admin` / `admin@ratamaekata.gov.lk`)
   - Credentials are configurable via `.env`.

---

## 8. Suspect Reports Architecture & Evidence Handling

### Citizen Incident Reporting
- **Public Submission (`POST /suspect-reports/`)**:
  - Anyone can submit a suspect incident report without authentication.
  - **All citizen & incident fields are strictly compulsory**: `fullname`, `email`, `mobile`, `nic`, `address`, `police_station`, `type_of_activity`, and `activity_description`.
  - Anonymous submissions are not permitted; every submission requires verified citizen identity and incident information.
- **Multiple Evidence Files (Images, ZIP archives, Documents, etc.)**:
  - Reports accept zero, one, or multiple attached evidence files via multipart form data.
  - Files are streamed in-memory directly to AWS S3 under the prefix `suspect_reports/{uuid}.{ext}`.
  - No files are ever saved on the local filesystem.
  - Each uploaded evidence file's S3 link, filename, size, and MIME type are saved in the `suspect_report_files` table linked to the parent report via foreign key `report_id`.
- **Protected Administrator Access**:
  - `GET /suspect-reports/` and `GET /suspect-reports/{report_id}` are strictly restricted to authenticated `ADMIN` and `SYSTEM_ADMIN` roles via `require_admin_or_system_admin`.
  - Regular users or unauthenticated clients are denied access (401/403).
  - `DELETE /suspect-reports/{report_id}` is restricted strictly to `SYSTEM_ADMIN`.

---

## 9. Security & Authentication Standards

1. **Password Safety**:
   - Plain passwords must NEVER be saved, printed, or exposed in any response schema.
   - Always hash passwords using `get_password_hash()` in `app.core.security`.
   - Always verify passwords using `verify_password()`.
   - `UserResponse` schema MUST exclude `hashed_password`.

2. **JWT Bearer Token Flow**:
   - Tokens are signed with HMAC-SHA256 (`HS256`) using `settings.SECRET_KEY`.
   - Protected routes must depend on `current_user: User = Depends(get_current_user)`.

3. **Environment Security**:
   - Never hardcode secrets. Always read from `app.core.config.settings`.

---

## 8. Python Coding Conventions

- **PEP 8 Compliance**: snake_case for functions/variables, PascalCase for classes, UPPER_SNAKE_CASE for constants.
- **Type Annotations**: 100% type annotations across all function arguments and return types.
- **Docstrings**: Clear docstrings explaining arguments, return values, and exceptions.
- **HTTP Status Codes**:
  - `200 OK` for reads and updates
  - `201 Created` for resource creation (signup, file upload)
  - `204 No Content` for deletions
  - `400 Bad Request` for business logic constraint failures
  - `401 Unauthorized` for missing/invalid credentials
  - `404 Not Found` for nonexistent entities
  - `415 Unsupported Media Type` for invalid file formats
  - `502 Bad Gateway` for upstream AWS S3 errors

---

## 9. Local Setup and Execution Instructions

### Step 1: Activate Virtual Environment
```powershell
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment (.env)
```bash
cp .env.example .env
```

### Step 4: Run Application
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Test Endpoints
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`
