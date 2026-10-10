from .config import ADMIN_EMAIL, ADMIN_PASSWORD
from .models import EmissionFactor, Target, User
from .security import hash_password

# Illustrative factors (kg CO2e per unit). Admin can edit these via the API.
# Replace with official datasets (CEA India, EPA, DEFRA) and record source/version.
FACTORS = [
    ("electricity", "electricity_grid", "Grid electricity", "kWh", 0.82, "Approx. India grid average (CEA)"),
    ("fuel", "fuel_petrol", "Petrol", "litre", 2.31, "Approx. standard factor (EPA/IPCC)"),
    ("fuel", "fuel_diesel", "Diesel", "litre", 2.68, "Approx. standard factor (EPA/IPCC)"),
    ("fuel", "fuel_lpg", "LPG (cooking)", "kg", 2.98, "Approx. standard factor (IPCC)"),
    ("transport", "transport_car_petrol", "Car (petrol)", "km", 0.17, "Approx. DEFRA average"),
    ("transport", "transport_two_wheeler", "Two-wheeler", "km", 0.07, "Approx. DEFRA average"),
    ("transport", "transport_bus", "Bus", "km", 0.09, "Approx. DEFRA average"),
    ("transport", "transport_metro_train", "Metro / train", "km", 0.04, "Approx. DEFRA average"),
    ("transport", "transport_flight_domestic", "Flight (domestic)", "km", 0.26, "Approx. DEFRA average"),
    ("waste", "waste_landfill", "Waste to landfill", "kg", 0.45, "Approx. EPA WARM average"),
    ("waste", "waste_composted", "Waste composted", "kg", 0.10, "Approx. EPA WARM average"),
    ("other", "other_water", "Water supply", "m3", 0.34, "Approx. DEFRA average"),
]
# Default system thresholds (kg CO2e per month); None = overall total
THRESHOLDS = {None: 250, "electricity": 100, "fuel": 60, "transport": 80, "waste": 20}


def seed(db):
    if not db.query(User).filter_by(email=ADMIN_EMAIL).first():
        db.add(User(name="Admin", email=ADMIN_EMAIL,
                    password_hash=hash_password(ADMIN_PASSWORD), is_admin=True))
    if db.query(EmissionFactor).count() == 0:
        for cat, key, label, unit, val, src in FACTORS:
            db.add(EmissionFactor(category=cat, activity_type=key, label=label,
                                  unit=unit, factor_kg_per_unit=val, source=src))
    if db.query(Target).filter(Target.user_id.is_(None)).count() == 0:
        for cat, limit in THRESHOLDS.items():
            db.add(Target(user_id=None, category=cat, limit_kg=limit))
    db.commit()
