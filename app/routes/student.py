import datetime
from collections import defaultdict, OrderedDict
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.config import settings
from app.database import get_db
from app.models import Student, Attendance, Course
from app.utils.dependencies import require_student_owner
from app.utils.security import verify_signed_token
from app.utils.network import validate_same_network

router = APIRouter(prefix="/student", tags=["Student"])


@router.get("/attendance/{roll_number}", response_class=HTMLResponse)
async def student_home(
    request: Request,
    roll_number: str,
    db: Session = Depends(get_db),
):
    require_student_owner(roll_number, request)

    st = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not st:
        raise HTTPException(status_code=404, detail="Student not found")

    # Stats per subject
    courses = db.query(Course).all()
    # Aggregated stats to avoid N+1 problem
    attendance_data_list = (
        db.query(Attendance.course_id, Attendance.present)
        .filter(Attendance.student_id == st.id)
        .all()
    )

    attendance_stats = defaultdict(lambda: {"attended": 0, "total": 0})
    for cid, is_p in attendance_data_list:
        if is_p:
            attendance_stats[cid]["attended"] += 1

    # Total classes per subject (from all student attendances for that course)
    # This matches the original logic but could be optimized
    total_classes = (
        db.query(Attendance.course_id, Attendance.date)
        .filter(Attendance.present == True)
        .distinct()
        .all()
    )
    totals_map = defaultdict(set)
    for cid, date_val in total_classes:
        totals_map[cid].add(date_val)

    att_data = {}
    present_dates_by_subject_grouped = {}

    for c in courses:
        subject_attended = attendance_stats[c.id]["attended"]
        subject_total = len(totals_map[c.id])
        pct = (subject_attended / (subject_total or 1)) * 100
        att_data[c.code] = {
            "total": subject_total,
            "attended": subject_attended,
            "percentage": pct,
        }

        # Present dates grouping for calendar/list
        p_dates = (
            db.query(Attendance.date)
            .filter(
                and_(
                    Attendance.student_id == st.id,
                    Attendance.course_id == c.id,
                    Attendance.present == True,
                )
            )
            .all()
        )
        tmp = defaultdict(list)
        for row in p_dates:
            dt = row.date
            tmp[(dt.year, dt.month)].append(dt.day)

        ordered = OrderedDict()
        for ym in sorted(tmp.keys()):
            lbl = datetime.datetime(ym[0], ym[1], 1).strftime("%b %Y")
            ordered[lbl] = sorted(tmp[ym])
        present_dates_by_subject_grouped[c.code] = ordered

    from main import templates # Templates need to be available

    return templates.TemplateResponse(
        "student_attendance.html",
        {
            "request": request,
            "roll_number": roll_number,
            "attendance_data": att_data,
            "present_dates_by_subject_grouped": present_dates_by_subject_grouped,
            "session_type": "student",
            "role_info": f"Student ID: {roll_number}",
        },
    )


@router.get("/attendance-data/{roll_number}")
async def get_attendance_json(
    request: Request,
    roll_number: str,
    year: int,
    month: int,
    db: Session = Depends(get_db),
):
    """JSON API for the calendar component."""
    require_student_owner(roll_number, request)
    st = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not st:
        return JSONResponse(status_code=404, content={"error": "Not found"})

    # Filter attendance for month
    start = datetime.datetime(year, month, 1)
    if month == 12:
        end = datetime.datetime(year + 1, 1, 1)
    else:
        end = datetime.datetime(year, month + 1, 1)

    atts = (
        db.query(Attendance)
        .filter(
            and_(
                Attendance.student_id == st.id,
                Attendance.date >= start,
                Attendance.date < end,
            )
        )
        .all()
    )

    days = []
    for a in atts:
        status = "present" if a.present else "absent"
        days.append({"day": a.date.day, "status": status})

    return {"days": days}


@router.get("/scan-qr/{roll_number}", response_class=HTMLResponse)
async def scan_qr_page(request: Request, roll_number: str):
    require_student_owner(roll_number, request)
    from main import templates
    return templates.TemplateResponse(
        "scan_qr.html",
        {
            "request": request,
            "roll_number": roll_number,
            "session_type": "student",
            "role_info": f"Student: {roll_number}",
        },
    )


@router.post("/submit-attendance/{roll_number}")
async def submit_attendance(
    request: Request,
    roll_number: str,
    qr_token: str = Form(...),
    db: Session = Depends(get_db),
):
    require_student_owner(roll_number, request)
    st = db.query(Student).filter(Student.roll_number == roll_number).first()
    from main import templates

    try:
        data = verify_signed_token(qr_token)
        # data = {"t": timestamp, "ip": creator_ip, "c": course_code, "e": expiry}

        if datetime.datetime.now().timestamp() > data["e"]:
            return templates.TemplateResponse(
                "scan_qr.html",
                {
                    "request": request,
                    "roll_number": roll_number,
                    "error": "QR code has expired.",
                },
            )

        # Subnet check if security settings allow/require it
        client_ip = request.client.host
        if not settings.SKIP_NETWORK_CHECK and not validate_same_network(client_ip, data["ip"]):
            return templates.TemplateResponse(
                "scan_qr.html",
                {"request": request, "roll_number": roll_number, "error": "Not on the same network subnet as the instructor."},
            )

        course = db.query(Course).filter(Course.code == data["c"]).first()
        if not course:
            return templates.TemplateResponse(
                "scan_qr.html",
                {"request": request, "roll_number": roll_number, "error": "Invalid course QR."},
            )

        # Mark attendance
        att = (
            db.query(Attendance)
            .filter(
                and_(
                    Attendance.student_id == st.id,
                    Attendance.course_id == course.id,
                    Attendance.date == course.qr_date,
                )
            )
            .first()
        )

        if att:
            att.present = True
            att.marked_at = datetime.datetime.now()
        else:
            db.add(
                Attendance(
                    student_id=st.id,
                    course_id=course.id,
                    date=course.qr_date,
                    present=True,
                    marked_at=datetime.datetime.now(),
                )
            )
        db.commit()

        return templates.TemplateResponse(
            "scan_qr.html",
            {
                "request": request,
                "roll_number": roll_number,
                "success": "Attendance successfully marked!",
            },
        )

    except ValueError as e:
        return templates.TemplateResponse(
            "scan_qr.html",
            {"request": request, "roll_number": roll_number, "error": f"Invalid QR: {str(e)}"},
        )
