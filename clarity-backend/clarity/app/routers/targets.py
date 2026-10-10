from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Target, User
from ..schemas import TargetIn
from ..security import current_user

router = APIRouter(prefix="/api/targets", tags=["Targets / Regulator"])


def target_out(t: Target):
    return {"id": t.id, "category": t.category or "total", "limit_kg": t.limit_kg,
            "scope": "system" if t.user_id is None else "personal"}


@router.get("")
def list_targets(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Target).filter((Target.user_id == user.id) | (Target.user_id.is_(None))).all()
    return [target_out(t) for t in rows]


@router.put("")
def set_target(body: TargetIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    """Create or update the caller's personal monthly target (kg CO2e) for a category or the total."""
    t = db.query(Target).filter_by(user_id=user.id, category=body.category).first()
    if t: t.limit_kg = body.limit_kg
    else:
        t = Target(user_id=user.id, category=body.category, limit_kg=body.limit_kg); db.add(t)
    db.commit(); db.refresh(t)
    return target_out(t)


@router.delete("/{target_id}", status_code=204)
def delete_target(target_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    t = db.query(Target).filter_by(id=target_id, user_id=user.id).first()
    if not t:
        raise HTTPException(404, "Target not found")
    db.delete(t); db.commit()
