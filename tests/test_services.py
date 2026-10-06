from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Course, Enrollment, Role, Student, User
from app.services import AcademicService, StudentService


def make_db() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def seed_people(db: Session):
    admin = User(email="admin@test.local", password_hash="x", name="Admin", role=Role.ADMIN)
    teacher = User(email="teacher@test.local", password_hash="x", name="Teacher", role=Role.TEACHER)
    student_user = User(email="student@test.local", password_hash="x", name="Student", role=Role.STUDENT)
    db.add_all([admin, teacher, student_user])
    db.flush()
    student = Student(student_number="S-1", user_id=student_user.id, program="CS", year_level=1, created_by=admin.id, updated_by=admin.id)
    course = Course(code="CS101", title="Intro", units=3, teacher_id=teacher.id, created_by=admin.id)
    db.add_all([student, course])
    db.commit()
    return admin, teacher, student_user, student, course


def test_student_cannot_read_another_student() -> None:
    db = make_db()
    admin, _teacher, student_user, _student, _course = seed_people(db)
    other_user = User(email="other@test.local", password_hash="x", name="Other", role=Role.STUDENT)
    db.add(other_user)
    db.flush()
    other = Student(student_number="S-2", user_id=other_user.id, program="IT", year_level=1, created_by=admin.id, updated_by=admin.id)
    db.add(other)
    db.commit()
    try:
        StudentService(db).get(other.id, student_user)
        raise AssertionError("ownership check was not enforced")
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403


def test_teacher_can_grade_only_assigned_course() -> None:
    db = make_db()
    admin, teacher, _student_user, student, course = seed_people(db)
    enrollment = Enrollment(student_id=student.id, course_id=course.id, term="2026-1", created_by=admin.id, updated_by=admin.id)
    db.add(enrollment)
    db.commit()
    updated = AcademicService(db).grade(enrollment.id, 91.5, teacher)
    assert updated.grade == 91.5


def test_dashboard_calculates_student_average() -> None:
    db = make_db()
    admin, _teacher, student_user, student, course = seed_people(db)
    db.add(Enrollment(student_id=student.id, course_id=course.id, term="2026-1", grade=88, created_by=admin.id, updated_by=admin.id))
    db.commit()
    assert AcademicService(db).dashboard(student_user)["average_grade"] == 88
