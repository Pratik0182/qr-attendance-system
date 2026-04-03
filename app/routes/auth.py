from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Student, Course
from app.utils.security import verify_password

router = APIRouter(tags=["Auth"])


@router.post("/student/login")
async def student_login_action(
    request: Request,
    roll_number: str = Form(...),
    db: Session = Depends(get_db)
):
    # Note: In a production system, we'd check passwords. 
    # For now, we maintain the roll-only login but prepare it for secrets.
    st = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not st:
        from main import templates
        return templates.TemplateResponse(
            "login_student.html", {"request": request, "error": "Invalid roll number"}
        )
    
    # Store session
    request.session["roll_number"] = roll_number
    request.session["role"] = "student"
    return RedirectResponse(
        url=f"/student/attendance/{roll_number}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/teacher/login")
async def teacher_login_action(
    request: Request,
    course_code: str = Form(...),
    db: Session = Depends(get_db)
):
    c = db.query(Course).filter(Course.code == course_code).first()
    if not c:
        from main import templates
        return templates.TemplateResponse(
            "login_teacher.html", {"request": request, "error": "Invalid Course Selection"}
        )
    
    # Store session
    request.session["course_code"] = course_code
    request.session["role"] = "teacher"
    return RedirectResponse(
        url=f"/teacher/dashboard/{course_code}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/logout")
async def logout_action(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
