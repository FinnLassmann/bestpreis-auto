from datetime import date, datetime
from sqlalchemy import (
    String, Integer, Numeric, Text, Boolean, Date, DateTime,
    ARRAY, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint("source", "source_id"),
        Index("idx_vehicles_brand", "brand"),
        Index("idx_vehicles_price", "price_eur"),
        Index("idx_vehicles_availability", "availability"),
        Index("idx_vehicles_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50))
    source_id: Mapped[str] = mapped_column(String(100))
    source_url: Mapped[str] = mapped_column(Text)

    brand: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    variant: Mapped[str | None] = mapped_column(String(200))
    trim_line: Mapped[str | None] = mapped_column(String(100))
    body_type: Mapped[str | None] = mapped_column(String(50))

    fuel_type: Mapped[str | None] = mapped_column(String(50))
    gearbox: Mapped[str | None] = mapped_column(String(50))
    power_kw: Mapped[int | None] = mapped_column(Integer)
    power_ps: Mapped[int | None] = mapped_column(Integer)
    engine_cc: Mapped[int | None] = mapped_column(Integer)

    mileage_km: Mapped[int | None] = mapped_column(Integer)
    first_reg_date: Mapped[date | None] = mapped_column(Date)
    availability: Mapped[str | None] = mapped_column(String(50))
    color: Mapped[str | None] = mapped_column(String(100))

    price_eur: Mapped[float | None] = mapped_column(Numeric(10, 2))
    uvp_eur: Mapped[float | None] = mapped_column(Numeric(10, 2))
    savings_eur: Mapped[float | None] = mapped_column(Numeric(10, 2))
    savings_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))

    image_urls = mapped_column(ARRAY(Text), default=list)

    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(50))
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[str | None] = mapped_column(String(45))
