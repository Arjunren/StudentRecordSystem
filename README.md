# Student Record System

## Overview

A secure FastAPI system for student profiles, courses, enrollments, grades, and role-aware academic dashboards.

## Features

- Admin, teacher, and student roles with revocable JWT sessions
- Student records with ownership checks
- Course assignment, enrollment uniqueness, and grade validation
- Teachers can grade only their assigned courses
- Search, pagination, term filters, and role-aware reports
- PostgreSQL migrations, seed accounts, Docker, tests, and generated OpenAPI

## Technology Stack

Python 3.12+, FastAPI, SQLAlchemy 2, PostgreSQL, psycopg 3, Pydantic, PyJWT, and Argon2 password hashing.

## Requirements

Python 3.12+ and PostgreSQL 14+, or Docker with Compose.

## Installation

```bash
git clone https://github.com/Arjunren/student-record-system.git
cd student-record-system
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

PowerShell activation: `.venv\Scripts\Activate.ps1` and `Copy-Item .env.example .env`.

## Environment Variables

Configure `DATABASE_URL`, a unique `JWT_SECRET` of at least 32 characters, `JWT_EXPIRY_MINUTES`, `ALLOWED_ORIGINS`, and the development-only `SEED_*` values documented in `.env.example`.

## Database Setup

```bash
python -m app.migrate
python -m app.seed
```

## Running the Application

```bash
uvicorn app.main:app --reload
```

Docker:

```bash
docker compose up -d db
docker compose --profile tools run --rm migrate
docker compose --profile tools run --rm seed
docker compose up -d api
```

## Running Tests

```bash
ruff check .
pytest -q
```

CI also applies migrations to a real PostgreSQL 17 service.

## Default Development Accounts

- Admin: `admin@example.com` / `AdminPass123!`
- Teacher: `teacher@example.com` / `TeacherPass123!`
- Student: `student@example.com` / `StudentPass123!`

## API Endpoints

Swagger UI is available at `/docs`. See `docs/openapi-notes.md` for the route summary.

## Folder Structure

`app/models.py` defines persistence, `repositories.py` data access, `services.py` business rules, `api.py` routes, `auth.py` authentication, `migrations/` SQL, and `tests/` service tests.

## Security Notes

Passwords use Argon2 and are never serialized. Tokens require an active database session and logout revokes them. Roles and student ownership are enforced server-side. Grade operations verify teacher-course ownership. Queries are SQLAlchemy-parameterized, inputs are Pydantic-validated, login attempts are rate-limited, CORS is allowlisted, and errors are sanitized.

## Known Limitations

- API-only with no transcript PDF generation or bulk CSV import.
- Courses do not model schedules, prerequisites, or classrooms.
- GPA rules vary by institution; this project reports percentage averages only.
