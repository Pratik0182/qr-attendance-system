from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    attendances = relationship("Attendance", back_populates="student")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    teacher_name = Column(String, nullable=True, default="Faculty")
    teacher_password_hash = Column(String, nullable=False)
    current_qr = Column(String, nullable=True)
    qr_expiry = Column(DateTime, nullable=True)
    qr_date = Column(DateTime, nullable=True)
    attendances = relationship("Attendance", back_populates="course")


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "date", name="uix_student_course_date"),
    )
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    present = Column(Boolean, default=False)
    marked_at = Column(DateTime, nullable=True)
    student = relationship("Student", back_populates="student")
    course = relationship("Course", back_populates="attendances")


# Fix backref in Attendance
Student.attendances = relationship("Attendance", back_populates="student")
Attendance.student = relationship("Student", back_populates="attendances")
