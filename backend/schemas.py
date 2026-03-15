from datetime import date, datetime
from pydantic import BaseModel, EmailStr


class VehicleOut(BaseModel):
    id: int
    source: str
    source_id: str
    source_url: str
    brand: str | None = None
    model: str | None = None
    variant: str | None = None
    trim_line: str | None = None
    body_type: str | None = None
    fuel_type: str | None = None
    gearbox: str | None = None
    power_kw: int | None = None
    power_ps: int | None = None
    engine_cc: int | None = None
    mileage_km: int | None = None
    first_reg_date: date | None = None
    availability: str | None = None
    color: str | None = None
    price_eur: float | None = None
    uvp_eur: float | None = None
    savings_eur: float | None = None
    savings_pct: float | None = None
    image_urls: list[str] = []
    scraped_at: datetime
    last_seen_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class VehicleListResponse(BaseModel):
    items: list[VehicleOut]
    total_count: int
    page: int
    limit: int


class FilterOptions(BaseModel):
    brands: list[str]
    models: list[str]
    fuel_types: list[str]
    gearboxes: list[str]
    body_types: list[str]
    availabilities: list[str]
    sources: list[str]


class StatsResponse(BaseModel):
    total_vehicles: int
    by_source: dict[str, int]
    last_updated: datetime | None


class LeadCreate(BaseModel):
    vehicle_id: int
    name: str
    email: str
    phone: str | None = None
    message: str | None = None


class LeadOut(BaseModel):
    id: int
    vehicle_id: int
    name: str
    email: str
    phone: str | None = None
    message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
