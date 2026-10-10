"""Calculation engine, regulator (targets/thresholds) and recommendation module."""
import json, urllib.request
from collections import defaultdict
from datetime import date
from .config import ANTHROPIC_API_KEY, AI_MODEL
from .models import Target, Activity


# ---------- Calculation engine ----------
def calculate_co2e(quantity: float, factor_kg_per_unit: float) -> float:
    """CO2e (kg) = activity quantity x emission factor."""
    return round(quantity * factor_kg_per_unit, 4)


def month_bounds(month: str | None):
    """'YYYY-MM' -> (first day, first day of next month, label). Defaults to current month."""
    if month:
        y, m = int(month[:4]), int(month[5:7])
    else:
        today = date.today()
        y, m = today.year, today.month
    start = date(y, m, 1)
    end = date(y + (m == 12), m % 12 + 1, 1)
    return start, end, f"{y:04d}-{m:02d}"


def summarize(activities):
    by_cat = defaultdict(float)
    for a in activities:
        by_cat[a.category] += a.co2e_kg
    by_cat = {k: round(v, 3) for k, v in by_cat.items()}
    return by_cat, round(sum(by_cat.values()), 3)


# ---------- Regulator ----------
def status_for(used: float, limit: float):
    pct = round(used / limit * 100, 1) if limit else 0.0
    status = "exceeded" if pct > 100 else "warning" if pct >= 80 else "ok"
    return pct, status


def evaluate_targets(db, user_id: int, by_cat: dict, total: float):
    """Personal targets override system thresholds for the same category."""
    effective = {}
    for t in db.query(Target).filter(Target.user_id.is_(None)):
        effective[t.category] = (t, "system")
    for t in db.query(Target).filter(Target.user_id == user_id):
        effective[t.category] = (t, "personal")
    results = []
    for cat, (t, source) in effective.items():
        used = total if cat is None else by_cat.get(cat, 0.0)
        pct, status = status_for(used, t.limit_kg)
        results.append({"category": cat or "total", "limit_kg": t.limit_kg, "used_kg": round(used, 3),
                        "percent": pct, "status": status, "source": source})
    return results


# ---------- Recommendations (rule-based, optional AI) ----------
TIPS = {
    "electricity": ["Switch to LED lighting and 5-star rated appliances.",
                    "Set AC to 24-26 C and switch off devices at the plug when idle.",
                    "Consider rooftop solar or a green-energy tariff."],
    "fuel": ["Combine errands into fewer trips and keep tyres properly inflated.",
             "Use a pressure cooker or induction cooktop to cut LPG use.",
             "Service your vehicle regularly for better mileage."],
    "transport": ["Replace short car trips with walking, cycling or metro.",
                  "Carpool or use public transport for daily commutes.",
                  "Avoid short-haul flights; prefer trains where possible."],
    "waste": ["Segregate waste and compost kitchen scraps.",
              "Avoid single-use plastics and buy only what you need.",
              "Recycle paper, metal and glass."],
    "other": ["Fix leaks and use water-efficient fixtures.",
              "Track this category closely and set a target for it."],
}


def recommend(by_cat: dict, total: float, target_results: list):
    recs = []
    if total <= 0:
        return [{"category": None, "message": "No activities logged for this month yet. Add some to get recommendations."}]
    flagged = {t["category"] for t in target_results if t["status"] != "ok"}
    top = sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)[:2]
    for cat, val in top:
        share = round(val / total * 100, 1)
        tips = TIPS.get(cat, TIPS["other"])
        n = 3 if cat in flagged else 2
        recs.append({"category": cat, "share_percent": share,
                     "message": f"{cat.title()} contributes {val} kg CO2e ({share}% of your total).",
                     "actions": tips[:n]})
    for t in target_results:
        if t["status"] == "exceeded" and t["category"] not in {c for c, _ in top} and t["category"] != "total":
            recs.append({"category": t["category"], "share_percent": None,
                         "message": f"{t['category'].title()} exceeded its monthly limit of {t['limit_kg']} kg.",
                         "actions": TIPS.get(t["category"], TIPS["other"])[:2]})
    return recs


def ai_explanation(by_cat: dict, total: float, target_results: list):
    """Optional: personalised explanation via Anthropic API. Returns None if unavailable."""
    if not ANTHROPIC_API_KEY or total <= 0:
        return None
    prompt = ("You are a sustainability assistant. In under 80 words, explain this monthly carbon footprint "
              f"(kg CO2e) and give 2 practical steps.\nCategories: {json.dumps(by_cat)}\nTotal: {total}\n"
              f"Target status: {json.dumps(target_results)}")
    body = json.dumps({"model": AI_MODEL, "max_tokens": 300,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "content-type": "application/json", "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())["content"][0]["text"]
    except Exception:
        return None


def trend(db, user_id: int, end_month: str, n: int = 6):
    """Total CO2e for the last n months ending at end_month."""
    y, m = int(end_month[:4]), int(end_month[5:7])
    months = []
    for i in range(n - 1, -1, -1):
        mm = m - i
        yy = y + (mm - 1) // 12
        mm = (mm - 1) % 12 + 1
        months.append(f"{yy:04d}-{mm:02d}")
    first, _, _ = month_bounds(months[0])
    _, last, _ = month_bounds(months[-1])
    acts = db.query(Activity).filter(Activity.user_id == user_id, Activity.activity_date >= first,
                                     Activity.activity_date < last).all()
    totals = defaultdict(float)
    for a in acts:
        totals[a.activity_date.strftime("%Y-%m")] += a.co2e_kg
    return [{"month": mo, "total_kg": round(totals.get(mo, 0.0), 3)} for mo in months]
