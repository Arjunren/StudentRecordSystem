from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    name: str
    role: Role
    is_active: bool
    created_at: datetime


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
    role: Role


class StudentCreate(BaseModel):
    student_number: str = Field(min_length=2, max_length=30)
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)
    date_of_birth: date | None = None
    program: str = Field(min_length=2, max_length=120)
    year_level: int = Field(ge=1, le=8)


class StudentUpdate(BaseModel):
    date_of_birth: date | None = None
    program: str = Field(min_length=2, max_length=120)
    year_level: int = Field(ge=1, le=8)


class StudentOut(BaseModel):
    id: int
    student_number: str
    user_id: int
    name: str
    email: str
    date_of_birth: date | None
    program: str
    year_level: int
    created_at: datetime
    updated_at: datetime


class CourseCreate(BaseModel):
    code: str = Field(min_length=2, max_length=30)
    title: str = Field(min_length=2, max_length=160)
    units: int = Field(ge=1, le=12)
    teacher_id: int | None = Field(default=None, ge=1)


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    title: str
    units: int
    teacher_id: int | None
    created_at: datetime


class EnrollmentCreate(BaseModel):
    student_id: int = Field(ge=1)
    course_id: int = Field(ge=1)
    term: str = Field(min_length=2, max_length=30)


class GradeUpdate(BaseModel):
    grade: float = Field(ge=0, le=100)


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    course_id: int
    term: str
    grade: float | None
    created_at: datetime
    updated_at: datetime


class PageMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int
