from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Course


async def get_current_student(request: Request, db: Session = Depends(get_db)) -> Student:
    """Dependency to retrieve the logged-in student session and prevent unauthorized access."""
    roll_number = request.session.get("roll_number")
    if not roll_number:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student not logged in",
        )
    student = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student data not found in DB",
        )
    return student


async def get_current_teacher_course(request: Request, db: Session = Depends(get_db)) -> Course:
    """Dependency to authenticate teacher sessions based on course code."""
    course_code = request.session.get("course_code")
    if not course_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Teacher not logged in",
        )
    course = db.query(Course).filter(Course.code == course_code).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Course context not found",
        )
    return course


def require_student_owner(roll_number: str, request: Request):
    """Enforce IDOR protection: roll numbers must match the currently active session."""
    session_roll = request.session.get("roll_number")
    if session_roll != roll_number:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot access records of other students.",
        )
