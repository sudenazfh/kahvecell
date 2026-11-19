from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.responses import ok
from app.schemas import PhoneIn, RefreshIn, UserOut, VerifyOtpIn
from app.services import auth as auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/register", summary="1) GSM numarası gönder, OTP iste")
def register(body: PhoneIn):
    # Simulation: no SMS is sent, the code is always 1234. Works for new and returning users.
    return ok({"otp_sent": True, "phone_number": body.phone_number,
               "message": "Doğrulama kodu gönderildi (simülasyon: 1234)"})


@router.post("/verify-otp", summary="2) OTP doğrula, token al")
def verify_otp(body: VerifyOtpIn, db: Session = Depends(get_db)):
    user, tokens = auth_service.verify_otp(db, body.phone_number, body.code)
    return ok({**tokens, "user": UserOut.model_validate(user)})


@router.post("/refresh", summary="Süresi dolan access token'ı yenile")
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    return ok(auth_service.refresh_tokens(db, body.refresh_token))
