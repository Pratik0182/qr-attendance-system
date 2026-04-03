import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    QR_SECRET_KEY: str = os.getenv("QR_SECRET_KEY", "change-me-qr-secret")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/attendance.db")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    DEFAULT_STUDENT_PASSWORD: str = os.getenv("DEFAULT_STUDENT_PASSWORD", "student123")
    DEFAULT_TEACHER_PASSWORD: str = os.getenv("DEFAULT_TEACHER_PASSWORD", "teacher123")
    SKIP_NETWORK_CHECK: bool = os.getenv("SKIP_NETWORK_CHECK", "false").lower() == "true"


settings = Settings()
