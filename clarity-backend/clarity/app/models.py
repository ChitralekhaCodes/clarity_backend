from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from .database import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=now)


class EmissionFactor(Base):
    """Emission factors are stored as data, not hard-coded (configurable factors)."""
    __tablename__ = "emission_factors"
    id = Column(Integer, primary_key=True)
    category = Column(String(30), nullable=False)
    activity_type = Column(String(60), unique=True, index=True, nullable=False)
    label = Column(String(120), nullable=False)
    unit = Column(String(20), nullable=False)
    factor_kg_per_unit = Column(Float, nullable=False)
    source = Column(String(200), default="")
    version = Column(Integer, default=1)
    active = Column(Boolean, default=True)


class Activity(Base):
    """Keeps a snapshot of the factor used so every calculation stays reproducible."""
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    factor_id = Column(Integer, ForeignKey("emission_factors.id"), nullable=False)
    category = Column(String(30), nullable=False)
    activity_type = Column(String(60), nullable=False)
    label = Column(String(120), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    factor_value = Column(Float, nullable=False)
    factor_version = Column(Integer, nullable=False)
    co2e_kg = Column(Float, nullable=False)
    activity_date = Column(Date, index=True, nullable=False)
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=now)


class Target(Base):
    """Monthly limit in kg CO2e. user_id NULL = system threshold; category NULL = overall total."""
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    category = Column(String(30), nullable=True)
    limit_kg = Column(Float, nullable=False)
