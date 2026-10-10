from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import EmissionFactor, Target, User
from ..schemas import FactorIn, FactorUpdate, TargetIn
from ..security import admin_user
from .activities import factor_out
from .targets import target_out

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/factors")
def all_factors(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    return [factor_out(f) for f in db.query(EmissionFactor).order_by(EmissionFactor.category).all()]


@router.post("/factors", status_code=201)
def create_factor(body: FactorIn, db: Session = Depends(get_db), _: User = Depends(admin_user)):
    if db.query(EmissionFactor).filter_by(activity_type=body.activity_type).first():
        raise HTTPException(409, "activity_type already exists")
    f = EmissionFactor(**body.model_dump())
    db.add(f); db.commit(); db.refresh(f)
    return factor_out(f)


@router.put("/factors/{factor_id}")
def update_factor(factor_id: int, body: FactorUpdate, db: Session = Depends(get_db), _: User = Depends(admin_user)):
    f = db.get(EmissionFactor, factor_id)
    if not f:
        raise HTTPException(404, "Factor not found")
    data = body.model_dump(exclude_none=True)
    if "factor_kg_per_unit" in data and data["factor_kg_per_unit"] != f.factor_kg_per_unit:
        f.version += 1  # old activities keep their stored snapshot of the earlier version
    for k, v in data.items():
        setattr(f, k, v)
    db.commit(); db.refresh(f)
    return factor_out(f)


@router.put("/thresholds")
def set_system_threshold(body: TargetIn, db: Session = Depends(get_db), _: User = Depends(admin_user)):
    t = db.query(Target).filter(Target.user_id.is_(None), Target.category == body.category).first()
    if t: t.limit_kg = body.limit_kg
    else:
        t = Target(user_id=None, category=body.category, limit_kg=body.limit_kg); db.add(t)
    db.commit(); db.refresh(t)
    return target_out(t)


@router.get("/users")
def users(db: Session = Depends(get_db), _: User = Depends(admin_user)):
    return [{"id": u.id, "name": u.name, "email": u.email, "is_admin": u.is_admin} for u in db.query(User).all()]
