from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Response, Query
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Boolean, and_, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
import datetime, qrcode, io, base64, os
from collections import defaultdict, OrderedDict
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

#db setup
if not os.path.exists('data'): os.makedirs('data')
DATABASE_URL = "sqlite:///./data/attendance.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#Models---------------------------------------
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String, unique=True, index=True)
    attendances = relationship("Attendance", back_populates="student")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    current_qr = Column(String, nullable=True) 
    qr_expiry = Column(DateTime, nullable=True)
    qr_date = Column(DateTime, nullable=True)
    attendances = relationship("Attendance", back_populates="course")

#reference
'''
class Course(Base):
    __tablename__ = "courses"
    id, code... qr expiry, current time data and attendance db
'''

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    date = Column(DateTime)
    present = Column(Boolean, default=False)
    marked_at = Column(DateTime, nullable=True)
    student = relationship("Student", back_populates="attendances")
    course = relationship("Course", back_populates="attendances")

#util to reset everything
def reset_database():
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM attendances"))
        db.execute(text("DELETE FROM students"))
        db.execute(text("DELETE FROM courses"))
        db.commit()

        #defaults
        courses = ["CSBB 251: Computer Architecture and Organization", "CSBB 252: Artificial Intelligence", "CSBB 254: Software Engineering", "HMBB 251: Professional Communication", "ECBB 254: Communication Systems", "CSPB 200: Project II"]
        for c in courses: db.add(Course(code=c))
        for i in range(66, 99): db.add(Student(roll_number=f"2312100{i:02d}"))
        db.commit() 
    finally: db.close()

def init_db(reset=False):
    insp = inspect(engine)
    if reset:
        Base.metadata.create_all(bind=engine)
        reset_database()
        return
    
    #check if tables exist
    if not insp.has_table("courses") or not insp.has_table("students"):
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            courses = ["CSBB 251: Computer Architecture and Organization", "CSBB 252: Artificial Intelligence", "CSBB 254: Software Engineering", "HMBB 251: Professional Communication", "ECBB 254: Communication Systems", "CSPB 200: Project II"]
            for c in courses:
                if not db.query(Course).filter(Course.code == c).first(): db.add(Course(code=c))
            
            for i in range(66, 99):
                if not db.query(Student).filter(Student.roll_number == f"2312100{i:02d}").first(): db.add(Student(roll_number=f"2312100{i:02d}"))
            db.commit()
        except: db.rollback()
        finally: db.close()
    else:
        #migration check for qr_date
        cols = {c['name'] for c in insp.get_columns('courses')}
        if 'qr_date' not in cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE courses ADD COLUMN qr_date DATETIME")) #fix for old db verison
                conn.commit()

init_db(reset=True)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def generate_qr(data: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

#Routes------------------------------
@app.get("/")
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

#removed about
#@app.get("/about", response_class=HTMLResponse)
#def about(request: Request):
#    return templates.TemplateResponse("about.html", {"request": request, "session_type": None, "role_info": "", "minimal_menu": True})

@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request, "session_type": None, "role_info": "", "minimal_menu": True})

@app.get("/logout")
def logout(): return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

#Students------------------------------------
@app.get("/student/login")
def student_login_page(request: Request):
    return templates.TemplateResponse("login_student.html", {"request": request})

@app.post("/student/login")
async def student_login(request: Request, roll_number: str = Form(...), db: Session = Depends(get_db)): #chek login
    #check if student exists
    st = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not st:
        return templates.TemplateResponse("login_student.html", {"request": request, "error": "Invalid roll number"})
    return RedirectResponse(url=f"/student/attendance/{roll_number}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/student/attendance/{roll_number}")
def student_home(request: Request, roll_number: str, db: Session = Depends(get_db)):
    st = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not st: raise HTTPException(status_code=404, detail="Student not found")
    
    #get attendances
    atts = db.query(Attendance).filter(Attendance.student_id == st.id).all()
    
    #calendar logic
    today = datetime.datetime.now()
    m_start = datetime.datetime(today.year, today.month, 1)
    
    att_lookup = {a.date.strftime("%Y-%m-%d"): a.present for a in atts}
    
    days = []
    curr = m_start
    while curr.month == today.month:
        d_str = curr.strftime("%Y-%m-%d")
        stat = "no-class"
        if att_lookup.get(d_str) == True: stat = "present"
        elif att_lookup.get(d_str) == False: stat = "absent"
        
        days.append({"date": d_str, "day": curr.day, "status": stat})
        curr += datetime.timedelta(days=1)
    
    #stats per subject
    courses = db.query(Course).all()
    att_data = {}
    dates_subj = {}
    grouped = {}

    for c in courses:
        present = db.query(Attendance).filter(and_(
            Attendance.student_id == st.id,
            Attendance.course_id == c.id,
            Attendance.present == True
        )).all()
        
        d_present = [p.date.strftime('%Y-%m-%d') for p in present]
        dates_subj[c.code] = d_present

        #weird grouping logic
        tmp = defaultdict(list)
        for ds in d_present:
            dt = datetime.datetime.strptime(ds, '%Y-%m-%d')
            tmp[(dt.year, dt.month)].append(dt.day)
            
        ordered = OrderedDict()
        for ym in sorted(tmp.keys()):
            lbl = datetime.datetime(ym[0], ym[1], 1).strftime('%b %Y') #formmat date
            ordered[lbl] = sorted(tmp[ym])
        grouped[c.code] = ordered

        #calc percentage
        total = len(db.query(Attendance.date).filter(and_(
            Attendance.course_id == c.id, Attendance.present == True
        )).distinct().all())
        
        p_count = len(present)
        pct = (p_count / (total or 1)) * 100
        att_data[c.code] = {"total": total, "attended": p_count, "percentage": pct}

    return templates.TemplateResponse("student_attendance.html", {
        "request": request, "roll_number": roll_number, "attendances": atts,
        "calendar_data": {"month": today.strftime("%B %Y"), "days": days},
        "attendance_data": att_data, "present_dates_by_subject": dates_subj,
        "present_dates_by_subject_grouped": grouped,
        "session_type": "student", "role_info": f"Student: {roll_number}"
    })
@app.get("/student/scan-qr/{roll_number}")
def scan_qr_page(request: Request, roll_number: str):
    return templates.TemplateResponse("scan_qr.html", {
        "request": request, "roll_number": roll_number,
        "session_type": "student", "role_info": f"Student: {roll_number}"
    })

@app.post("/student/submit-attendance/{roll_number}")
async def submit_att(request: Request, roll_number: str, qr_token: str = Form(...), db: Session = Depends(get_db)):
    st = db.query(Student).filter(Student.roll_number == roll_number).first()
    if not st:
        return templates.TemplateResponse("scan_qr.html", {
            "request": request, "roll_number": roll_number, "error": "Student not found",
            "session_type": "student", "role_info": f"Student: {roll_number}"
        })

    client_ip = request.client.host
    try:
        #decode token
        raw = base64.urlsafe_b64decode(qr_token.encode()).decode()
        data = eval(raw.replace("'", '"')) #unsafe but whatever
        
        if datetime.datetime.now().timestamp() > data['e']:
             return templates.TemplateResponse("scan_qr.html", {
                "request": request, "roll_number": roll_number, "error": "QR expired",
                "session_type": "student", "role_info": f"Student: {roll_number}"
            })

        #network check
        def is_local(ip): return ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("172.")
        
        if is_local(client_ip) and is_local(data['ip']):
            if client_ip.split('.')[0:3] != data['ip'].split('.')[0:3]:
                return templates.TemplateResponse("scan_qr.html", {
                    "request": request, "roll_number": roll_number, "error": "Not on same network",
                    "session_type": "student", "role_info": f"Student: {roll_number}"
                })

        c = db.query(Course).filter(Course.code == data['c']).first()
        if not c:
             return templates.TemplateResponse("scan_qr.html", {
                "request": request, "roll_number": roll_number, "error": "Invalid QR Code",
                "session_type": "student", "role_info": f"Student: {roll_number}"
            })
            
        #mark it
        att = db.query(Attendance).filter(and_(
            Attendance.student_id == st.id, Attendance.course_id == c.id, Attendance.date == c.qr_date
        )).first()

        if att:
            att.present = True
            att.marked_at = datetime.datetime.now()
        else:
            db.add(Attendance(
                student_id=st.id, course_id=c.id, date=c.qr_date,
                present=True, marked_at=datetime.datetime.now()
            ))
        db.commit()
        
        return templates.TemplateResponse("scan_qr.html", {
            "request": request, "roll_number": roll_number, "success": "Attendance Marked!",
            "session_type": "student", "role_info": f"Student: {roll_number}"
        })

    except Exception as e:
        return templates.TemplateResponse("scan_qr.html", {
            "request": request, "roll_number": roll_number, "error": "Error processing QR",
            "session_type": "student", "role_info": f"Student: {roll_number}"
        })

#Teacher----------------------------------------
@app.get("/teacher/login")
def teacher_login_page(request: Request):
    return templates.TemplateResponse("login_teacher.html", {"request": request})

@app.post("/teacher/login")
async def teacher_login(request: Request, course_code: str = Form(...), db: Session = Depends(get_db)):
    c = db.query(Course).filter(Course.code == course_code).first()
    if not c:
        return templates.TemplateResponse("login_teacher.html", {"request": request, "error": "Invalid Course"})
    return RedirectResponse(url=f"/teacher/dashboard/{course_code}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/teacher/dashboard/{course_code}")
def teacher_dash(request: Request, course_code: str, db: Session = Depends(get_db)):
    c = db.query(Course).filter(Course.code == course_code).first()
    if not c: raise HTTPException(404, "Course not found")
    
    total_days = len(db.query(Attendance.date).filter(and_(
        Attendance.course_id == c.id, Attendance.present == True
    )).distinct().all())
    
    students = db.query(Student).all()
    recs = []
    
    for s in students:
        cnt = db.query(Attendance).filter(and_(
            Attendance.student_id == s.id, Attendance.course_id == c.id, Attendance.present == True
        )).count()
        recs.append({
            "roll_number": s.roll_number, "total": total_days, "attended": cnt,
            "percentage": (cnt/total_days*100) if total_days > 0 else 0
        })
    
    recs.sort(key=lambda x: int(x["roll_number"]))
    return templates.TemplateResponse("teacher_dashboard.html", {
        "request": request, "course_code": course_code, "attendance_records": recs,
        "session_type": "teacher", "role_info": f"Teacher: {course_code}"
    })
@app.get("/teacher/manual-attendance/{course_code}")
def manual_att(request: Request, course_code: str, attendance_date: str = None, db: Session = Depends(get_db)):
    c = db.query(Course).filter(Course.code == course_code).first()
    if not c: raise HTTPException(404, "Course not found")
    
    sts = []
    if attendance_date:
        d = datetime.datetime.strptime(attendance_date, "%Y-%m-%d")
        for s in db.query(Student).all():
            a = db.query(Attendance).filter(and_(
                Attendance.student_id == s.id, Attendance.course_id == c.id, Attendance.date == d
            )).first()
            sts.append({"roll_number": s.roll_number, "is_present": a.present if a else False})
            
    return templates.TemplateResponse("manual_attendance.html", {
        "request": request, "course_code": course_code, "attendance_date": attendance_date,
        "students": sts, "session_type": "teacher", "role_info": f"Teacher: {course_code}"
    })

@app.post("/teacher/manual-attendance/{course_code}")
async def set_att_date(request: Request, course_code: str, attendance_date: str = Form(...)): #sett date
    return RedirectResponse(
        url=f"/teacher/manual-attendance/{course_code}?attendance_date={attendance_date}",
        status_code=status.HTTP_303_SEE_OTHER
    )

@app.post("/teacher/mark-attendance/{course_code}")
async def mark_manual(request: Request, course_code: str, attendance_date: str = Form(...), db: Session = Depends(get_db)):
    c = db.query(Course).filter(Course.code == course_code).first()
    if not c: raise HTTPException(404, "Course not found")
    
    d = datetime.datetime.strptime(attendance_date, "%Y-%m-%d")
    form = await request.form()
    
    #reset for this date
    db.query(Attendance).filter(and_(
        Attendance.course_id == c.id, Attendance.date == d
    )).delete(synchronize_session=False)
    db.commit()
    
    for s in db.query(Student).all():
        is_p = f"present_{s.roll_number}" in form
        db.add(Attendance(
            student_id=s.id, course_id=c.id, date=d, present=is_p, marked_at=datetime.datetime.now()
        ))
    db.commit()
    
    return RedirectResponse(
        url=f"/teacher/manual-attendance/{course_code}?attendance_date={attendance_date}",
        status_code=status.HTTP_303_SEE_OTHER
    )
@app.get("/teacher/qr-attendance/{course_code}")
def qr_att_page(request: Request, course_code: str, attendance_date: str = Query(None), db: Session = Depends(get_db)):
    c = db.query(Course).filter(Course.code == course_code).first()
    if not c: raise HTTPException(404, "Not found")
    
    if attendance_date: dt = datetime.datetime.strptime(attendance_date, "%Y-%m-%d")
    elif c.qr_date: dt = c.qr_date
    else: dt = datetime.datetime.now()
    
    sel_date = dt.strftime("%Y-%m-%d")
    disp_date = dt.strftime("%d %B %Y")
    
    recs = []
    if c.qr_date:
        today = c.qr_date
        for s in db.query(Student).all():
            a = db.query(Attendance).filter(and_(
                Attendance.student_id == s.id, Attendance.course_id == c.id, Attendance.date == today
            )).first()
            recs.append({
                "roll_number": s.roll_number, "present": a.present if a else False,
                "time": a.marked_at.strftime("%H:%M:%S") if (a and a.present) else None
            })
        recs.sort(key=lambda x: int(x["roll_number"]))

    qr = None
    if c.current_qr and c.qr_expiry > datetime.datetime.now():
        qr = generate_qr(c.current_qr)
        
    return templates.TemplateResponse("qr_attendance.html", {
        "request": request, "course_code": course_code, "selected_date": sel_date,
        "qr_code": qr, "selected_date_display": disp_date,
        "qr_expiry": c.qr_expiry.strftime("%H:%M:%S") if c.qr_expiry else None,
        "attendance_records": recs, "session_type": "teacher", "role_info": f"Teacher: {course_code}"
    })

@app.post("/teacher/generate-qr/{course_code}")
async def generate_qr_endpoint(request: Request, course_code: str, attendance_date: str = Form(...), validity_seconds: int = Form(...), db: Session = Depends(get_db)):
    c = db.query(Course).filter(Course.code == course_code).first()
    if not c: raise HTTPException(404, "Not found")
    
    ip = request.client.host
    d = datetime.datetime.strptime(attendance_date, "%Y-%m-%d")
    exp = datetime.datetime.now() + datetime.timedelta(seconds=validity_seconds)
    
    tok = {
        "t": int(datetime.datetime.now().timestamp()),
        "ip": ip, "c": course_code, "e": int(exp.timestamp())
    }
    
    c.current_qr = base64.urlsafe_b64encode(str(tok).encode()).decode()
    c.qr_expiry = exp
    c.qr_date = d
    db.commit() #saving qr details
    
    return RedirectResponse(
        url=f"/teacher/qr-attendance/{course_code}?attendance_date={attendance_date}",
        status_code=status.HTTP_303_SEE_OTHER
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
