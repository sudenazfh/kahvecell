"""Request/response shapes. Pydantic validates every incoming body against these."""

import uuid

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models import Role

PHONE_FIELD = Field(pattern=r"^5\d{9}$", examples=["5551234567"],
                    description="10 haneli GSM numarası, başında 0 olmadan")


class PhoneIn(BaseModel):
    phone_number: str = PHONE_FIELD


class VerifyOtpIn(BaseModel):
    phone_number: str = PHONE_FIELD
    code: str = Field(pattern=r"^\d{4}$", examples=["1234"])


class RefreshIn(BaseModel):
    refresh_token: str


class Preferences(BaseModel):
    coffee: list[str] = Field(default_factory=list, examples=[["latte", "türk kahvesi"]])
    allergens: list[str] = Field(default_factory=list, examples=[["laktoz"]])


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=100, examples=["Ayşe Yılmaz"])
    email: str | None = Field(None, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                              examples=["ayse@example.com"])
    preferences: Preferences | None = None


class RoleUpdate(BaseModel):
    role: Role


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    phone_number: str
    full_name: str | None
    email: str | None
    role: Role
    preferences: dict | None

    @computed_field
    @property
    def profile_completed(self) -> bool:
        return self.full_name is not None
