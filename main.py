import os
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from app.config import settings
from app.database import engine, get_db, Base, SessionLocal
from app.models import Student, Course
from app.utils.security import hash_password
from app.routes import auth, student, teacher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Secure QR Attendance System", debug=settings.DEBUG)

# Session middleware for auth
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Static and Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates")

# Include Routers
app.include_router(auth.router)
app.include_router(student.router)
app.include_router(teacher.router)


@app.on_event("startup")
def startup_event():
    """Verify DB on startup without nuking it unless explicitly told."""
    insp = inspect(engine)
    if not insp.has_table("courses") or not insp.has_table("students"):
        logger.info("Initializing database for the first time...")
        Base.metadata.create_all(bind=engine)
        init_sample_data()
    else:
        logger.info("Schema verified. Ready.")


def init_sample_data():
    """Load default subjects and students with hashed passwords."""
    db = SessionLocal()
    try:
        courses = [
            "CSBB 251: Computer Architecture and Organization",
            "CSBB 252: Artificial Intelligence",
            "CSBB 254: Software Engineering",
            "HMBB 251: Professional Communication",
            "ECBB 254: Communication Systems",
            "CSPB 200: Project II"
        ]
        s_pwd = hash_password(settings.DEFAULT_STUDENT_PASSWORD)
        t_pwd = hash_password(settings.DEFAULT_TEACHER_PASSWORD)

        for c_code in courses:
            if not db.query(Course).filter(Course.code == c_code).first():
                db.add(Course(code=c_code, teacher_password_hash=t_pwd))
        
        for i in range(66, 99):
            roll = f"2312100{i:02d}"
            if not db.query(Student).filter(Student.roll_number == roll).first():
                db.add(Student(roll_number=roll, password_hash=s_pwd))
        
        db.commit()
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/student/login", response_class=HTMLResponse)
async def student_login_page(request: Request):
    return templates.TemplateResponse("login_student.html", {"request": request})


@app.get("/teacher/login", response_class=HTMLResponse)
async def teacher_login_page(request: Request, db: Session = Depends(get_db)):
    from app.models import Course
    courses = db.query(Course).order_by(Course.code).all()
    return templates.TemplateResponse("login_teacher.html", {"request": request, "courses": courses})


@app.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    role = request.session.get("role")
    session_type = role if role in ("student", "teacher") else None
    return templates.TemplateResponse(
        "contact.html",
        {
            "request": request,
            "session_type": session_type,
            "role_info": "Support",
            "roll_number": request.session.get("roll_number", ""),
            "course_code": request.session.get("course_code", ""),
        }
    )


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    role = request.session.get("role")
    session_type = role if role in ("student", "teacher") else None
    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "session_type": session_type,
            "role_info": "",
            "roll_number": request.session.get("roll_number", ""),
            "course_code": request.session.get("course_code", ""),
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
