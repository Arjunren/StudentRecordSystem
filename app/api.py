from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import (
    bearer,
    check_login_rate,
    dummy_hash,
    get_current_user,
    hash_password,
    issue_token,
    require_roles,
    revoke_token,
    verify_password,
)
from app.database import get_db
from app.models import Course, Role, User
from app.schemas import (
    CourseCreate,
    CourseOut,
    EnrollmentCreate,
    EnrollmentOut,
    GradeUpdate,
    LoginIn,
    StudentCreate,
    StudentUpdate,
    UserCreate,
    UserOut,
)
from app.services import AcademicService, StudentService, commit_or_conflict

router = APIRouter(prefix="/api")


@router.post("/auth/login")
def login(data: LoginIn, request: Request, db: Annotated[Session, Depends(get_db)]) -> dict:
    check_login_rate(request)
    user = db.scalar(select(User).where(func.lower(User.email) == str(data.email).lower()))
    if user is None:
        verify_password(data.password, dummy_hash)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect")
    if not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect")
    return {"data": {"access_token": issue_token(db, user), "token_type": "Bearer", "user": UserOut.model_validate(user)}}


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    _user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    revoke_token(db, credentials.credentials)


@router.post("/users", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    _admin: Annotated[User, Depends(require_roles(Role.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    if data.role == Role.STUDENT:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Create students through /api/students")
    user = User(email=str(data.email).lower(), password_hash=hash_password(data.password), name=data.name.strip(), role=data.role)
    db.add(user)
    commit_or_conflict(db, "Email already exists")
    db.refresh(user)
    return {"data": UserOut.model_validate(user)}


@router.get("/students")
def list_students(
    _viewer: Annotated[User, Depends(require_roles(Role.ADMIN, Role.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
    search: str = Query(default="", max_length=120),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    return StudentService(db).list(search, page, limit)


@router.post("/students", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_student(
    data: StudentCreate,
    admin: Annotated[User, Depends(require_roles(Role.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return {"data": StudentService(db).create(data, admin)}


@router.get("/students/{student_id}", response_model=dict)
def get_student(
    student_id: int,
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return {"data": StudentService(db).get(student_id, actor)}


@router.put("/students/{student_id}", response_model=dict)
def update_student(
    student_id: int,
    data: StudentUpdate,
    admin: Annotated[User, Depends(require_roles(Role.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return {"data": StudentService(db).update(student_id, data, admin)}


@router.get("/courses")
def list_courses(
    _actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    search: str = Query(default="", max_length=120),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    filters = (Course.code.ilike(f"%{search}%")) | (Course.title.ilike(f"%{search}%"))
    total = db.scalar(select(func.count()).select_from(Course).where(filters)) or 0
    items = db.scalars(select(Course).where(filters).order_by(Course.code).offset((page - 1) * limit).limit(limit)).all()
    return {"data": [CourseOut.model_validate(item) for item in items], "meta": {"page": page, "limit": limit, "total": total, "total_pages": ceil(total / limit)}}


@router.post("/courses", status_code=status.HTTP_201_CREATED)
def create_course(
    data: CourseCreate,
    admin: Annotated[User, Depends(require_roles(Role.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return {"data": CourseOut.model_validate(AcademicService(db).create_course(data, admin))}


@router.get("/enrollments")
def list_enrollments(
    actor: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    term: str | None = Query(default=None, max_length=30),
) -> dict:
    items = AcademicService(db).list_enrollments(actor, term)
    return {"data": [EnrollmentOut.model_validate(item) for item in items]}


@router.post("/enrollments", status_code=status.HTTP_201_CREATED)
def create_enrollment(
    data: EnrollmentCreate,
    admin: Annotated[User, Depends(require_roles(Role.ADMIN))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return {"data": EnrollmentOut.model_validate(AcademicService(db).enroll(data, admin))}


@router.patch("/enrollments/{enrollment_id}/grade")
def update_grade(
    enrollment_id: int,
    data: GradeUpdate,
    actor: Annotated[User, Depends(require_roles(Role.ADMIN, Role.TEACHER))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return {"data": EnrollmentOut.model_validate(AcademicService(db).grade(enrollment_id, data.grade, actor))}


@router.get("/dashboard")
def dashboard(
    actor: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]
) -> dict:
    return {"data": AcademicService(db).dashboard(actor)}
