from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Query, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, create_tables
from schemas import VehicleOut, VehicleListResponse, FilterOptions, StatsResponse, LeadCreate, LeadOut
import crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="Bestpreis Auto API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/vehicles", response_model=VehicleListResponse)
async def list_vehicles(
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
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    vehicles, total = await crud.get_vehicles(
        db,
        brand=brand,
        model=model,
        fuel_type=fuel_type,
        gearbox=gearbox,
        body_type=body_type,
        availability=availability,
        source=source,
        price_min=price_min,
        price_max=price_max,
        sort=sort,
        page=page,
        limit=limit,
    )
    return VehicleListResponse(
        items=vehicles,
        total_count=total,
        page=page,
        limit=limit,
    )


@app.get("/api/vehicles/{vehicle_id}", response_model=VehicleOut)
async def get_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    vehicle = await crud.get_vehicle(db, vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Fahrzeug nicht gefunden")
    return vehicle


@app.get("/api/filters", response_model=FilterOptions)
async def get_filters(
    brand: str | None = None,
    model: str | None = None,
    fuel_type: str | None = None,
    gearbox: str | None = None,
    body_type: str | None = None,
    availability: str | None = None,
    source: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_filter_options(
        db,
        brand=brand,
        model=model,
        fuel_type=fuel_type,
        gearbox=gearbox,
        body_type=body_type,
        availability=availability,
        source=source,
        price_min=price_min,
        price_max=price_max,
    )


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    return await crud.get_stats(db)


@app.post("/api/leads", response_model=LeadOut, status_code=201)
async def create_lead(
    lead: LeadCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"

    recent_count = await crud.count_recent_leads(db, ip)
    if recent_count >= 5:
        raise HTTPException(
            status_code=429,
            detail="Zu viele Anfragen. Bitte versuche es in einer Stunde erneut.",
        )

    vehicle = await crud.get_vehicle(db, lead.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Fahrzeug nicht gefunden")

    lead_data = lead.model_dump()
    lead_data["ip_address"] = ip
    return await crud.create_lead(db, lead_data)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
