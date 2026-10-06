from math import ceil

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import Course, Enrollment, Role, Student, User
from app.repositories import EnrollmentRepository, StudentRepository
from app.schemas import CourseCreate, EnrollmentCreate, StudentCreate, StudentOut, StudentUpdate


def commit_or_conflict(db: Session, message: str = "Record conflicts with existing data") -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, message) from None


def student_dict(student: Student, user: User) -> StudentOut:
    return StudentOut(
        id=student.id,
        student_number=student.student_number,
        user_id=user.id,
        name=user.name,
        email=user.email,
        date_of_birth=student.date_of_birth,
        program=student.program,
        year_level=student.year_level,
        created_at=student.created_at,
        updated_at=student.updated_at,
    )


class StudentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = StudentRepository(db)

    def create(self, data: StudentCreate, actor: User) -> StudentOut:
        user = User(
            email=str(data.email).lower(),
            password_hash=hash_password(data.password),
            name=data.name.strip(),
            role=Role.STUDENT,
        )
        self.db.add(user)
        self.db.flush()
        student = Student(
            student_number=data.student_number.strip().upper(),
            user_id=user.id,
            date_of_birth=data.date_of_birth,
            program=data.program.strip(),
            year_level=data.year_level,
            created_by=actor.id,
            updated_by=actor.id,
        )
        self.db.add(student)
        commit_or_conflict(self.db, "Email or student number already exists")
        self.db.refresh(student)
        return student_dict(student, user)

    def list(self, search: str, page: int, limit: int) -> dict:
        rows, total = self.repo.list(search.strip(), page, limit)
        return {
            "data": [student_dict(student, user) for student, user in rows],
            "meta": {"page": page, "limit": limit, "total": total, "total_pages": ceil(total / limit)},
        }

    def get(self, student_id: int, actor: User) -> StudentOut:
        student = self.db.get(Student, student_id)
        if student is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
        if actor.role == Role.STUDENT and student.user_id != actor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot access another student")
        return student_dict(student, self.db.get_one(User, student.user_id))

    def update(self, student_id: int, data: StudentUpdate, actor: User) -> StudentOut:
        student = self.db.get(Student, student_id)
        if student is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
        student.date_of_birth = data.date_of_birth
        student.program = data.program.strip()
        student.year_level = data.year_level
        student.updated_by = actor.id
        self.db.commit()
        self.db.refresh(student)
        return student_dict(student, self.db.get_one(User, student.user_id))


class AcademicService:
    def __init__(self, db: Session):
        self.db = db

    def create_course(self, data: CourseCreate, actor: User) -> Course:
        if data.teacher_id is not None:
            teacher = self.db.get(User, data.teacher_id)
            if teacher is None or not teacher.is_active or teacher.role != Role.TEACHER:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "teacher_id must reference an active teacher")
        course = Course(
            code=data.code.strip().upper(),
            title=data.title.strip(),
            units=data.units,
            teacher_id=data.teacher_id,
            created_by=actor.id,
        )
        self.db.add(course)
        commit_or_conflict(self.db, "Course code already exists")
        self.db.refresh(course)
        return course

    def enroll(self, data: EnrollmentCreate, actor: User) -> Enrollment:
        if self.db.get(Student, data.student_id) is None or self.db.get(Course, data.course_id) is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Student or course does not exist")
        item = Enrollment(
            student_id=data.student_id,
            course_id=data.course_id,
            term=data.term.strip().upper(),
            created_by=actor.id,
            updated_by=actor.id,
        )
        self.db.add(item)
        commit_or_conflict(self.db, "Student is already enrolled in this course and term")
        self.db.refresh(item)
        return item

    def list_enrollments(self, actor: User, term: str | None) -> list[Enrollment]:
        return EnrollmentRepository(self.db).list_for_user(actor, term.upper() if term else None)

    def grade(self, enrollment_id: int, grade: float, actor: User) -> Enrollment:
        item = self.db.get(Enrollment, enrollment_id)
        if item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Enrollment not found")
        course = self.db.get_one(Course, item.course_id)
        if actor.role == Role.TEACHER and course.teacher_id != actor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Teachers can grade only their courses")
        item.grade = grade
        item.updated_by = actor.id
        self.db.commit()
        self.db.refresh(item)
        return item

    def dashboard(self, actor: User) -> dict:
        if actor.role == Role.STUDENT:
            grades = list(
                self.db.scalars(select(Enrollment.grade).join(Student).where(Student.user_id == actor.id)).all()
            )
            scored = [grade for grade in grades if grade is not None]
            return {"enrollments": len(grades), "graded": len(scored), "average_grade": sum(scored) / len(scored) if scored else None}
        if actor.role == Role.TEACHER:
            courses = self.db.scalar(select(func.count()).select_from(Course).where(Course.teacher_id == actor.id)) or 0
            enrollments = self.db.scalar(select(func.count()).select_from(Enrollment).join(Course).where(Course.teacher_id == actor.id)) or 0
            return {"courses": courses, "enrollments": enrollments}
        return {
            "students": self.db.scalar(select(func.count()).select_from(Student)) or 0,
            "courses": self.db.scalar(select(func.count()).select_from(Course)) or 0,
            "enrollments": self.db.scalar(select(func.count()).select_from(Enrollment)) or 0,
        }
