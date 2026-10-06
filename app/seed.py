import os

from sqlalchemy import func, select

from app.auth import hash_password
from app.database import SessionLocal
from app.models import Role, Student, User


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def ensure_user(db, email: str, password: str, name: str, role: Role) -> User:
    user = db.scalar(select(User).where(func.lower(User.email) == email.lower()))
    if user:
        return user
    user = User(email=email.lower(), password_hash=hash_password(password), name=name, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def main() -> None:
    with SessionLocal() as db:
        admin = ensure_user(db, required("SEED_ADMIN_EMAIL"), required("SEED_ADMIN_PASSWORD"), "Development Admin", Role.ADMIN)
        ensure_user(db, required("SEED_TEACHER_EMAIL"), required("SEED_TEACHER_PASSWORD"), "Development Teacher", Role.TEACHER)
        student_user = ensure_user(db, required("SEED_STUDENT_EMAIL"), required("SEED_STUDENT_PASSWORD"), "Development Student", Role.STUDENT)
        if db.scalar(select(Student).where(Student.user_id == student_user.id)) is None:
            db.add(Student(student_number="DEV-0001", user_id=student_user.id, program="Computer Science", year_level=1, created_by=admin.id, updated_by=admin.id))
            db.commit()
    print("development data seeded")


if __name__ == "__main__":
    main()
