import csv, io
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Activity, User
from ..security import current_user
from ..services import (month_bounds, summarize, evaluate_targets, recommend, ai_explanation, trend)

router = APIRouter(prefix="/api", tags=["Dashboard & Reports"])


def _month_data(db, user, month):
    try:
        start, end, label = month_bounds(month)
    except Exception:
        raise HTTPException(422, "month must be in YYYY-MM format")
    acts = (db.query(Activity).filter(Activity.user_id == user.id, Activity.activity_date >= start,
                                      Activity.activity_date < end)
            .order_by(Activity.activity_date).all())
    by_cat, total = summarize(acts)
    return acts, by_cat, total, label


@router.get("/dashboard")
def dashboard(month: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    acts, by_cat, total, label = _month_data(db, user, month)
    targets = evaluate_targets(db, user.id, by_cat, total)
    breakdown = [{"category": c, "co2e_kg": v, "share_percent": round(v / total * 100, 1) if total else 0}
                 for c, v in sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)]
    return {"month": label, "total_kg": total, "activity_count": len(acts), "category_breakdown": breakdown,
            "targets": targets, "alerts": [t for t in targets if t["status"] != "ok"],
            "recommendations": recommend(by_cat, total, targets),
            "ai_summary": ai_explanation(by_cat, total, targets),
            "trend": trend(db, user.id, label),
            "disclaimer": "Values are estimates based on user input and configured emission factors, "
                          "not certified environmental measurements."}


@router.get("/report/csv")
def report_csv(month: str | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    acts, _, total, label = _month_data(db, user, month)
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["date", "category", "activity", "quantity", "unit", "factor_kg_per_unit", "factor_version", "co2e_kg"])
    for a in acts:
        w.writerow([a.activity_date, a.category, a.label, a.quantity, a.unit, a.factor_value, a.factor_version, a.co2e_kg])
    w.writerow([]); w.writerow(["TOTAL", "", "", "", "", "", "", total])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename=clarity_{label}.csv"})
