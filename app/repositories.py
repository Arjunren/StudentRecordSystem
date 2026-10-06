from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Course, Enrollment, Student, User


class StudentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list(self, search: str, page: int, limit: int) -> tuple[list[tuple[Student, User]], int]:
        filters = or_(
            Student.student_number.ilike(f"%{search}%"),
            Student.program.ilike(f"%{search}%"),
            User.name.ilike(f"%{search}%"),
            User.email.ilike(f"%{search}%"),
        )
        total = self.db.scalar(
            select(func.count()).select_from(Student).join(User, User.id == Student.user_id).where(filters)
        ) or 0
        rows = self.db.execute(
            select(Student, User)
            .join(User, User.id == Student.user_id)
            .where(filters)
            .order_by(Student.student_number)
            .offset((page - 1) * limit)
            .limit(limit)
        ).all()
        return list(rows), total


class EnrollmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user: User, term: str | None) -> list[Enrollment]:
        query = select(Enrollment).join(Student).join(Course)
        if user.role.value == "STUDENT":
            query = query.where(Student.user_id == user.id)
        elif user.role.value == "TEACHER":
            query = query.where(Course.teacher_id == user.id)
        if term:
            query = query.where(Enrollment.term == term)
        return list(self.db.scalars(query.order_by(Enrollment.created_at.desc())).all())
