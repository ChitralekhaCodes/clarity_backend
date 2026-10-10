from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Activity, EmissionFactor, User
from ..schemas import ActivityIn
from ..security import current_user
from ..services import calculate_co2e

router = APIRouter(prefix="/api", tags=["Activities & Factors"])


def factor_out(f: EmissionFactor):
    return {"id": f.id, "category": f.category, "activity_type": f.activity_type, "label": f.label,
            "unit": f.unit, "factor_kg_per_unit": f.factor_kg_per_unit, "source": f.source,
            "version": f.version, "active": f.active}


def activity_out(a: Activity):
    """Includes the full calculation trail (quantity x factor = CO2e) for transparency."""
    return {"id": a.id, "date": a.activity_date.isoformat(), "category": a.category,
            "activity_type": a.activity_type, "label": a.label, "quantity": a.quantity, "unit": a.unit,
            "factor_kg_per_unit": a.factor_value, "factor_version": a.factor_version,
            "co2e_kg": a.co2e_kg, "notes": a.notes,
            "calculation": f"{a.quantity} {a.unit} x {a.factor_value} kg/{a.unit} = {a.co2e_kg} kg CO2e"}


@router.get("/factors")
def list_factors(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(EmissionFactor).filter_by(active=True).order_by(EmissionFactor.category).all()
    return [factor_out(f) for f in rows]


@router.post("/activities", status_code=201)
def add_activity(body: ActivityIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    f = db.query(EmissionFactor).filter_by(activity_type=body.activity_type, active=True).first()
    if not f:
        raise HTTPException(404, "Unknown or inactive activity_type. See GET /api/factors")
    when = body.activity_date or date.today()
    if when > date.today():
        raise HTTPException(422, "activity_date cannot be in the future")
    a = Activity(user_id=user.id, factor_id=f.id, category=f.category, activity_type=f.activity_type,
                 label=f.label, quantity=body.quantity, unit=f.unit, factor_value=f.factor_kg_per_unit,
                 factor_version=f.version, co2e_kg=calculate_co2e(body.quantity, f.factor_kg_per_unit),
                 activity_date=when, notes=body.notes)
    db.add(a); db.commit(); db.refresh(a)
    return activity_out(a)


@router.get("/activities")
def list_activities(category: str | None = None, start: date | None = None, end: date | None = None,
                    limit: int = Query(100, le=500), db: Session = Depends(get_db),
                    user: User = Depends(current_user)):
    q = db.query(Activity).filter(Activity.user_id == user.id)
    if category: q = q.filter(Activity.category == category)
    if start: q = q.filter(Activity.activity_date >= start)
    if end: q = q.filter(Activity.activity_date <= end)
    rows = q.order_by(Activity.activity_date.desc(), Activity.id.desc()).limit(limit).all()
    return [activity_out(a) for a in rows]


@router.delete("/activities/{activity_id}", status_code=204)
def delete_activity(activity_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = db.query(Activity).filter_by(id=activity_id, user_id=user.id).first()
    if not a:
        raise HTTPException(404, "Activity not found")
    db.delete(a); db.commit()
