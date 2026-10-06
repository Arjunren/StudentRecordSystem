CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(120) NOT NULL,
  role VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN','TEACHER','STUDENT')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX users_email_ci_idx ON users(LOWER(email));
CREATE TABLE auth_sessions (
  id VARCHAR(36) PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX auth_sessions_user_idx ON auth_sessions(user_id);
CREATE TABLE students (
  id BIGSERIAL PRIMARY KEY,
  student_number VARCHAR(30) NOT NULL UNIQUE,
  user_id BIGINT NOT NULL UNIQUE REFERENCES users(id) ON DELETE RESTRICT,
  date_of_birth DATE,
  program VARCHAR(120) NOT NULL,
  year_level INTEGER NOT NULL CHECK (year_level BETWEEN 1 AND 8),
  created_by BIGINT NOT NULL REFERENCES users(id),
  updated_by BIGINT NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE courses (
  id BIGSERIAL PRIMARY KEY,
  code VARCHAR(30) NOT NULL UNIQUE,
  title VARCHAR(160) NOT NULL,
  units INTEGER NOT NULL CHECK (units BETWEEN 1 AND 12),
  teacher_id BIGINT REFERENCES users(id),
  created_by BIGINT NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE enrollments (
  id BIGSERIAL PRIMARY KEY,
  student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
  course_id BIGINT NOT NULL REFERENCES courses(id) ON DELETE RESTRICT,
  term VARCHAR(30) NOT NULL,
  grade DOUBLE PRECISION CHECK (grade IS NULL OR (grade >= 0 AND grade <= 100)),
  created_by BIGINT NOT NULL REFERENCES users(id),
  updated_by BIGINT NOT NULL REFERENCES users(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(student_id, course_id, term)
);
CREATE INDEX enrollments_student_idx ON enrollments(student_id);
CREATE INDEX enrollments_course_idx ON enrollments(course_id);
CREATE INDEX enrollments_term_idx ON enrollments(term);
