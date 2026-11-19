"""Login business rules: OTP check, user creation on first login, token refresh."""

import hmac

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.responses import AppError
from app.security import decode_token, token_pair

# ponytail: fixed OTP per case section 11.2 (simulation); real SMS needs per-phone codes with expiry + attempt limits.
SIMULATED_OTP = "1234"


def verify_otp(db: Session, phone_number: str, code: str) -> tuple[User, dict]:
    if not hmac.compare_digest(code, SIMULATED_OTP):
        raise AppError(400, "INVALID_OTP", "Doğrulama kodu hatalı")

    user = db.scalar(select(User).where(User.phone_number == phone_number))
    if user is None:
        # Account is created only after the phone is proven, so nobody can register someone else's number.
        user = User(phone_number=phone_number)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user, token_pair(user.id)


def refresh_tokens(db: Session, refresh_token: str) -> dict:
    # ponytail: stateless refresh, old tokens stay valid until expiry; add a token table if logout-everywhere is needed.
    user_id = decode_token(refresh_token, "refresh")
    if db.get(User, user_id) is None:
        raise AppError(401, "INVALID_TOKEN", "Geçersiz oturum bilgisi")
    return token_pair(user_id)
