import hmac
import hashlib
import json
import base64
import logging
from passlib.context import CryptContext
from app.config import settings

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return the hashed version of a plain password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hashed version."""
    return pwd_context.verify(plain_password, hashed_password)


def create_signed_token(payload: dict) -> str:
    """Create an HMAC-signed token for QR codes, replacing insecure eval()."""
    payload_json = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        settings.QR_SECRET_KEY.encode(),
        payload_json.encode(),
        hashlib.sha256,
    ).hexdigest()
    token_data = {"payload": payload, "sig": signature}
    return base64.urlsafe_b64encode(json.dumps(token_data).encode()).decode()


def verify_signed_token(token: str) -> dict:
    """Verify and decode an HMAC-signed token. Raises ValueError on failure."""
    try:
        decoded_bytes = base64.urlsafe_b64decode(token.encode())
        token_data = json.loads(decoded_bytes.decode())
        payload_json = json.dumps(token_data["payload"], sort_keys=True)
        expected_sig = hmac.new(
            settings.QR_SECRET_KEY.encode(),
            payload_json.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(token_data["sig"], expected_sig):
            logger.warning("Token signature mismatch detected.")
            raise ValueError("Invalid token signature")
        return token_data["payload"]
    except (json.JSONDecodeError, KeyError, base64.binascii.Error) as e:
        logger.warning(f"Failed to decode or verify token: {e}")
        raise ValueError(f"Invalid token format: {e}")
