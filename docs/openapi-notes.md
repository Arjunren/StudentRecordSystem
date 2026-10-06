# API Guide

FastAPI serves the generated OpenAPI document at `/openapi.json` and interactive Swagger UI at `/docs`.

Authentication uses `Authorization: Bearer <token>`.

Main resources:

- `POST /api/auth/login`, `POST /api/auth/logout`
- `POST /api/users` for administrator-created teacher/admin accounts
- `GET|POST /api/students`, `GET|PUT /api/students/{id}`
- `GET|POST /api/courses`
- `GET|POST /api/enrollments`, `PATCH /api/enrollments/{id}/grade`
- `GET /api/dashboard`

Collection endpoints use `page`, `limit`, and `search`; enrollment lists may filter by `term`.
