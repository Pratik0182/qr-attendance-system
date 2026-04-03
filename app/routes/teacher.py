import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.database import get_db
from app.models import Student, Course, Attendance
from app.services.qr_service import generate_qr_image_b64
from app.utils.security import create_signed_token

router = APIRouter(prefix="/teacher", tags=["Teacher"])


@router.get("/dashboard/{course_code}", response_class=HTMLResponse)
async def teacher_dash(
    request: Request,
    course_code: str,
    db: Session = Depends(get_db),
):
    # Verifying course context
    course = db.query(Course).filter(Course.code == course_code).first()
    if not course:
        raise HTTPException(404, "Course not found")

    # Efficient attendance counting
    total_days = db.query(Attendance.date).filter(
        and_(Attendance.course_id == course.id, Attendance.present == True)
    ).distinct().count()

    attendance_counts = (
        db.query(Attendance.student_id, func.count(Attendance.id))
        .filter(and_(Attendance.course_id == course.id, Attendance.present == True))
        .group_by(Attendance.student_id)
        .all()
    )
    attendance_map = {sid: count for sid, count in attendance_counts}

    students = db.query(Student).all()
    records = []
    for s in students:
        cnt = attendance_map.get(s.id, 0)
        perc = (cnt / total_days * 100) if total_days > 0 else 0
        records.append({
            "roll_number": s.roll_number,
            "total": total_days,
            "attended": cnt,
            "percentage": perc
        })

    records.sort(key=lambda x: int(x["roll_number"]))
    
    from main import templates
    return templates.TemplateResponse(
        "teacher_dashboard.html",
        {
            "request": request,
            "course_code": course_code,
            "attendance_records": records,
            "session_type": "teacher",
            "role_info": f"Course Head: {course_code}"
        },
    )


@router.get("/qr-attendance/{course_code}", response_class=HTMLResponse)
async def qr_attendance_page(
    request: Request,
    course_code: str,
    attendance_date: str = Query(None),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.code == course_code).first()
    if not course: raise HTTPException(404)

    dt = datetime.datetime.strptime(attendance_date, "%Y-%m-%d") if attendance_date else (course.qr_date or datetime.datetime.now())
    selected_date_str = dt.strftime("%Y-%m-%d")

    records = []
    # Current session students
    att_list = db.query(Attendance).filter(
        and_(Attendance.course_id == course.id, Attendance.date == dt)
    ).all()
    att_map = {a.student_id: a for a in att_list}

    for s in db.query(Student).all():
        record = att_map.get(s.id)
        records.append({
            "roll_number": s.roll_number,
            "present": record.present if record else False,
            "time": record.marked_at.strftime("%H:%M:%S") if (record and record.present and record.marked_at) else None
        })
    records.sort(key=lambda x: int(x["roll_number"]))

    qr_b64 = None
    if course.current_qr and course.qr_expiry > datetime.datetime.now():
        qr_b64 = generate_qr_image_b64(course.current_qr)

    from main import templates
    return templates.TemplateResponse(
        "qr_attendance.html",
        {
            "request": request,
            "course_code": course_code,
            "selected_date": selected_date_str,
            "selected_date_display": dt.strftime("%d %B %Y"),
            "qr_code": qr_b64,
            "qr_expiry": course.qr_expiry.strftime("%H:%M:%S") if course.qr_expiry else None,
            "attendance_records": records,
            "session_type": "teacher",
            "role_info": f"Instructor: {course_code}"
        }
    )


@router.post("/generate-qr/{course_code}")
async def teacher_generate_qr(
    request: Request,
    course_code: str,
    attendance_date: str = Form(...),
    validity_seconds: int = Form(...),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.code == course_code).first()
    if not course: raise HTTPException(404)

    dt = datetime.datetime.strptime(attendance_date, "%Y-%m-%d")
    expiry_dt = datetime.datetime.now() + datetime.timedelta(seconds=validity_seconds)
    
    token_payload = {
        "t": int(datetime.datetime.now().timestamp()),
        "ip": request.client.host,
        "c": course_code,
        "e": int(expiry_dt.timestamp())
    }
    
    course.current_qr = create_signed_token(token_payload)
    course.qr_expiry = expiry_dt
    course.qr_date = dt
    db.commit()

    return RedirectResponse(
        url=f"/teacher/qr-attendance/{course_code}?attendance_date={attendance_date}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/manual-attendance/{course_code}", response_class=HTMLResponse)
async def manual_att_page(
    request: Request,
    course_code: str,
    attendance_date: str = Query(None),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.code == course_code).first()
    if not course: raise HTTPException(404)

    students_list = []
    if attendance_date:
        dt = datetime.datetime.strptime(attendance_date, "%Y-%m-%d")
        current_atts = db.query(Attendance).filter(
            and_(Attendance.course_id == course.id, Attendance.date == dt)
        ).all()
        att_map = {a.student_id: a.present for a in current_atts}
        for s in db.query(Student).all():
            students_list.append({
                "roll_number": s.roll_number,
                "is_present": att_map.get(s.id, False)
            })

    from main import templates
    return templates.TemplateResponse(
        "manual_attendance.html",
        {
            "request": request,
            "course_code": course_code,
            "attendance_date": attendance_date,
            "students": students_list,
            "session_type": "teacher",
            "role_info": f"Faculty: {course_code}"
        }
    )


@router.post("/manual-attendance/{course_code}")
async def teacher_set_manual_date(attendance_date: str = Form(...)):
    return RedirectResponse(
        url=f"?attendance_date={attendance_date}",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/mark-attendance/{course_code}")
async def teacher_save_manual_attendance(
    request: Request,
    course_code: str,
    attendance_date: str = Form(...),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.code == course_code).first()
    if not course: raise HTTPException(404)

    dt = datetime.datetime.strptime(attendance_date, "%Y-%m-%d")
    form_data = await request.form()

    # Bulk update/mark
    # First, clear existing for this specific date/course to simplify
    db.query(Attendance).filter(
        and_(Attendance.course_id == course.id, Attendance.date == dt)
    ).delete()
    db.commit()

    all_students = db.query(Student).all()
    for s in all_students:
        is_p = f"present_{s.roll_number}" in form_data
        db.add(Attendance(
            student_id=s.id,
            course_id=course.id,
            date=dt,
            present=is_p,
            marked_at=datetime.datetime.now() if is_p else None
        ))
    db.commit()

    return RedirectResponse(
        url=f"/teacher/manual-attendance/{course_code}?attendance_date={attendance_date}",
        status_code=status.HTTP_303_SEE_OTHER
    )
