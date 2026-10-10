from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from .config import CATEGORIES


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=100)


class LoginIn(BaseModel):
    email: str
    password: str


class ActivityIn(BaseModel):
    activity_type: str
    quantity: float = Field(gt=0, le=10_000_000)
    activity_date: Optional[date] = None
    notes: str = Field(default="", max_length=500)


class FactorIn(BaseModel):
    category: str
    activity_type: str = Field(pattern=r"^[a-z0-9_]+$", max_length=60)
    label: str
    unit: str
    factor_kg_per_unit: float = Field(ge=0)
    source: str = ""

    @field_validator("category")
    @classmethod
    def valid_category(cls, v):
        if v not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}")
        return v


class FactorUpdate(BaseModel):
    label: Optional[str] = None
    factor_kg_per_unit: Optional[float] = Field(default=None, ge=0)
    source: Optional[str] = None
    active: Optional[bool] = None


class TargetIn(BaseModel):
    category: Optional[str] = None  # None = overall total
    limit_kg: float = Field(gt=0, le=10_000_000)

    @field_validator("category")
    @classmethod
    def valid_category(cls, v):
        if v is not None and v not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}")
        return v
