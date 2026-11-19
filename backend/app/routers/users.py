import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Role, User
from app.responses import AppError, ok
from app.schemas import ProfileUpdate, RoleUpdate, UserOut
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", summary="Giriş yapan kullanıcının profili")
def get_me(user: User = Depends(get_current_user)):
    return ok(UserOut.model_validate(user))


@router.patch("/me", summary="Profili tamamla / güncelle")
def update_me(body: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return ok(UserOut.model_validate(user))


@router.get("", summary="Tüm kullanıcılar (sadece Admin)")
def list_users(_: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    # ponytail: no pagination; add limit/offset once user count grows past a few hundred.
    users = db.scalars(select(User).order_by(User.created_at)).all()
    return ok([UserOut.model_validate(u) for u in users])


@router.patch("/{user_id}/role", summary="Kullanıcının rolünü değiştir (sadece Admin)")
def change_role(user_id: uuid.UUID, body: RoleUpdate,
                admin: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if target is None:
        raise AppError(404, "USER_NOT_FOUND", "Kullanıcı bulunamadı")
    if target.id == admin.id and body.role != Role.ADMIN:
        raise AppError(400, "CANNOT_DEMOTE_SELF", "Kendi admin yetkinizi kaldıramazsınız")
    target.role = body.role
    db.commit()
    db.refresh(target)
    return ok(UserOut.model_validate(target))
