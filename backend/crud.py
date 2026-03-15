from datetime import datetime, timedelta
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from models import Vehicle, Lead


async def get_vehicles(
    db: AsyncSession,
    brand: str | None = None,
    model: str | None = None,
    fuel_type: str | None = None,
    gearbox: str | None = None,
    body_type: str | None = None,
    availability: str | None = None,
    source: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    sort: str = "price_asc",
    page: int = 1,
    limit: int = 24,
) -> tuple[list[Vehicle], int]:
    query = select(Vehicle).where(Vehicle.is_active == True)

    if brand:
        query = query.where(func.lower(Vehicle.brand) == brand.lower())
    if model:
        query = query.where(func.lower(Vehicle.model) == model.lower())
    if fuel_type:
        query = query.where(func.lower(Vehicle.fuel_type) == fuel_type.lower())
    if gearbox:
        query = query.where(func.lower(Vehicle.gearbox) == gearbox.lower())
    if body_type:
        query = query.where(func.lower(Vehicle.body_type) == body_type.lower())
    if availability:
        query = query.where(func.lower(Vehicle.availability) == availability.lower())
    if source and source != "all":
        query = query.where(Vehicle.source == source)
    if price_min is not None:
        query = query.where(Vehicle.price_eur >= price_min)
    if price_max is not None:
        query = query.where(Vehicle.price_eur <= price_max)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    sort_map = {
        "price_asc": Vehicle.price_eur.asc(),
        "price_desc": Vehicle.price_eur.desc(),
        "savings_desc": Vehicle.savings_eur.desc().nulls_last(),
        "scraped_at_desc": Vehicle.scraped_at.desc(),
    }
    query = query.order_by(sort_map.get(sort, Vehicle.price_eur.asc()))
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    return result.scalars().all(), total


async def get_vehicle(db: AsyncSession, vehicle_id: int) -> Vehicle | None:
    result = await db.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    return result.scalar_one_or_none()


async def get_filter_options(
    db: AsyncSession,
    brand: str | None = None,
    model: str | None = None,
    fuel_type: str | None = None,
    gearbox: str | None = None,
    body_type: str | None = None,
    availability: str | None = None,
    source: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
) -> dict:
    def _apply_filters(q):
        if brand:
            q = q.where(func.lower(Vehicle.brand) == brand.lower())
        if model:
            q = q.where(func.lower(Vehicle.model) == model.lower())
        if fuel_type:
            q = q.where(func.lower(Vehicle.fuel_type) == fuel_type.lower())
        if gearbox:
            q = q.where(func.lower(Vehicle.gearbox) == gearbox.lower())
        if body_type:
            q = q.where(func.lower(Vehicle.body_type) == body_type.lower())
        if availability:
            q = q.where(func.lower(Vehicle.availability) == availability.lower())
        if source and source != "all":
            q = q.where(Vehicle.source == source)
        if price_min is not None:
            q = q.where(Vehicle.price_eur >= price_min)
        if price_max is not None:
            q = q.where(Vehicle.price_eur <= price_max)
        return q

    async def distinct_values(column):
        q = (
            select(distinct(column))
            .where(Vehicle.is_active == True)
            .where(column.isnot(None))
        )
        q = _apply_filters(q)
        result = await db.execute(q.order_by(column))
        return [r for r in result.scalars().all()]

    return {
        "brands": await distinct_values(Vehicle.brand),
        "models": await distinct_values(Vehicle.model),
        "fuel_types": await distinct_values(Vehicle.fuel_type),
        "gearboxes": await distinct_values(Vehicle.gearbox),
        "body_types": await distinct_values(Vehicle.body_type),
        "availabilities": await distinct_values(Vehicle.availability),
        "sources": await distinct_values(Vehicle.source),
    }


async def get_stats(db: AsyncSession) -> dict:
    total = (await db.execute(
        select(func.count()).where(Vehicle.is_active == True)
    )).scalar() or 0

    source_counts = (await db.execute(
        select(Vehicle.source, func.count())
        .where(Vehicle.is_active == True)
        .group_by(Vehicle.source)
    )).all()

    last_updated = (await db.execute(
        select(func.max(Vehicle.last_seen_at))
    )).scalar()

    return {
        "total_vehicles": total,
        "by_source": {row[0]: row[1] for row in source_counts},
        "last_updated": last_updated,
    }


async def create_lead(db: AsyncSession, lead_data: dict) -> Lead:
    lead = Lead(**lead_data)
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


async def count_recent_leads(db: AsyncSession, ip_address: str) -> int:
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    result = await db.execute(
        select(func.count())
        .where(Lead.ip_address == ip_address)
        .where(Lead.created_at >= one_hour_ago)
    )
    return result.scalar() or 0
