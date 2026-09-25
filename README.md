# AI-First CRM – HCP Module
-- An AI-first Customer Relationship Management system for managing
Healthcare Professional interactions.

# Tech Stack
Frontend: React

State Management: Redux

Backend: FastAPI

AI Agent: LangGraph

LLM: Groq

Database: PostgreSQL

Font: Inter

---> AI-first CRM backend for managing healthcare professionals (HCPs), interactions, follow-ups, and users. The implemented application is currently centered on a FastAPI + PostgreSQL CRUD API; the LangGraph/Groq AI assistant and React frontend are mostly planned structure rather than working code in the current repository.
Stack
Language(s): Python 98.5%, Mako 1.4%, Dockerfile 0.1%

Framework / runtime: FastAPI running with Uvicorn

Database: PostgreSQL 17 with asynchronous SQLAlchemy and Alembic migrations

Frontend: React/Redux/Vite structure, but the current frontend files are empty

Notable libraries: SQLAlchemy async ORM, asyncpg, Alembic, Pydantic Settings

# How it's organized
repository-structure
text
backend/
  app/
    main.py                 FastAPI application entry point
    api/
      router.py             Combines API routers
      v1/
# How it fits together: A request enters through backend/app/main.py, which mounts api_router under /api/v1. backend/app/api/router.py combines the authentication, users, HCP, interaction, and follow-up routers. Each endpoint uses FastAPI dependency injection from core/dependencies.py to create a service, and each service uses a repository to access PostgreSQL through an asynchronous SQLAlchemy session.

For example, an HCP request follows this path:

hcp-request-flow
text
HTTP request
  ↓
/api/v1/hcps
  ↓
backend/app/api/v1/hcps.py
  ↓
Main application flow
Application startup
backend/app/main.py creates the FastAPI application:

KrishnaRastogi2007 / ai-first-crm / backend / app / main.py

python
from fastapi import FastAPI

from app.core.config import settings
from app.api.router import api_router

app = FastAPI(title=settings.APP_NAME, version="1.0.0")
The root endpoint is:

Text

text
GET /
It returns the configured application name and environment.

Router registration
backend/app/api/router.py registers:

Text

text
auth.py
hcps.py
interactions.py
followups.py
users.py
These become available below the /api/v1 prefix.

# ----> Dependency creation
backend/app/core/dependencies.py creates the dependency chain:

Text

text
Database session
  ↓
Repository
  ↓
Service
  ↓
API endpoint
For example:

KrishnaRastogi2007 / ai-first-crm / backend / app / core / dependencies.py

python
def get_hcp_service(db: AsyncSession = Depends(get_db)):
    repository = HCPRepository(db)
    return HCPService(repository)
-----> Database session
backend/app/db/database.py creates an asynchronous SQLAlchemy engine using settings.DATABASE_URL. get_db() opens a session for each request and closes it afterward.

----> Service layer
A service converts validated request data into ORM models and decides which repository method to call. For example, HCPService.create_hcp() creates an HCP object and delegates persistence to HCPRepository.

---> Repository layer
Repositories contain database operations such as:

Text

text
get_all()
get_by_id()
create()
update()
delete()
For example, HCPRepository.get_by_id() executes a SQLAlchemy select(HCP).where(HCP.id == hcp_id) query.

Authentication flow
Registration and login are defined in backend/app/api/v1/auth.py.

The protected /users/me endpoint uses:

Text

text
Authorization: Bearer <token>
  ↓
OAuth2PasswordBearer
  ↓
decode_access_token()
  ↓
Extract user ID from token
  ↓
Load user from PostgreSQL
  ↓
Check user.is_active
  ↓
Return current user
The repository contains JWT-related dependency code, but the current dependency list does not include an obvious JWT library such as PyJWT or python-jose. Authentication may therefore require additional setup before it runs successfully.

Database migrations
Alembic migrations currently create:

Text

text
users
hcps
interactions
followups
backend/alembic/env.py imports these SQLAlchemy models and exposes Base.metadata to Alembic. The migration history includes:

migrations

text
7fdd800c1060_create_users_table.py
913242044bef_add_phone_to_users.py
54f4480cc8c9_create_hcps_table.py
dea444a279a2_create_interactions_table.py
12e77ae3b86a_create_followups_table.py
What is implemented versus planned
Area	Current state
FastAPI application	Implemented
PostgreSQL connection	Implemented
SQLAlchemy async sessions	Implemented
Alembic migrations	Implemented
User registration/login	Implemented at a basic level
HCP CRUD	Implemented
Interaction CRUD	Implemented
Follow-up CRUD	Implemented
User lookup	Implemented
React UI	Structure exists, source files are empty
Redux store	Empty placeholder files
AI chat endpoint	chat.py is empty
LangGraph agent	Planned directory, no working graph files found
Groq integration	Described in documentation, not implemented in current source
CRM AI tools	Described in documentation, not implemented in current source
Background workers	Planned, no working worker implementation found
Redis/object storage	Described in architecture documentation, not configured in the repository
Audit logging	Planned directory, no complete implementation found
Production reverse proxy/observability	Documentation only
The docs/Readme.md is an architecture/design document. It describes a future system with LangGraph, six CRM tools, Redis, object storage, workers, notifications, and observability. Those components should not be treated as part of the currently executable implementation yet.

How to run it
The shortest current backend path is:

backend-setup

bash
git clone https://github.com/KrishnaRastogi2007/ai-first-crm.git
cd ai-first-crm/backend

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
Create backend/.env. The current config.py requires these variables:

backend/.env

env
APP_NAME=AI-First CRM
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://crm_app:password@localhost:5432/ai_first_crm
JWT_SECRET_KEY=replace-with-a-long-random-secret
The committed .env.example currently contains DATABASE_URL, GROQ_API_KEY, and SECRET_KEY, but config.py actually requires APP_NAME, APP_ENV, and JWT_SECRET_KEY. Aligning .env.example with config.py would make onboarding clearer.

Start PostgreSQL using Docker Compose:

postgres

bash
cd backend
docker compose up -d
The compose file starts PostgreSQL 17 on port 5432 and expects:

backend-compose-env

env
POSTGRES_DB=ai_first_crm
POSTGRES_USER=crm_app
POSTGRES_PASSWORD=password
Run migrations:

alembic-migrations

bash
cd backend
alembic upgrade head
Start FastAPI:

fastapi-server

bash
uvicorn app.main:app --reload
If running from the repository root instead:

fastapi-server-from-root

bash
uvicorn --app-dir backend app.main:app --reload
Useful URLs:

Text

text
GET http://127.0.0.1:8000/
GET http://127.0.0.1:8000/docs
GET http://127.0.0.1:8000/api/v1/hcps
GET http://127.0.0.1:8000/api/v1/interactions
GET http://127.0.0.1:8000/api/v1/followups
GET http://127.0.0.1:8000/api/v1/users
There is currently no usable frontend startup command because frontend/package.json is empty. The React/Vite application needs to be completed before it can be run with npm install and npm run dev.