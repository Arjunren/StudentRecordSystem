import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "0123456789abcdef0123456789abcdef")
