"""Sync database helpers for scraper processes."""
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://euautos:dev_password@localhost:5432/euautos",
)

engine = create_engine(DATABASE_URL_SYNC, echo=False)
Session = sessionmaker(bind=engine)


def upsert_vehicle(session, vehicle_data: dict):
    """Insert or update a vehicle based on (source, source_id) unique constraint."""
    now = datetime.utcnow()
    vehicle_data["last_seen_at"] = now

    if vehicle_data.get("uvp_eur") and vehicle_data.get("price_eur"):
        vehicle_data["savings_eur"] = vehicle_data["uvp_eur"] - vehicle_data["price_eur"]
        if vehicle_data["uvp_eur"] > 0:
            vehicle_data["savings_pct"] = round(
                (vehicle_data["savings_eur"] / vehicle_data["uvp_eur"]) * 100, 2
            )

    columns = ", ".join(vehicle_data.keys())
    placeholders = ", ".join(f":{k}" for k in vehicle_data.keys())
    update_cols = ", ".join(
        f"{k} = EXCLUDED.{k}"
        for k in vehicle_data.keys()
        if k not in ("source", "source_id")
    )

    sql = text(f"""
        INSERT INTO vehicles ({columns})
        VALUES ({placeholders})
        ON CONFLICT (source, source_id)
        DO UPDATE SET {update_cols}
    """)

    session.execute(sql, vehicle_data)
    session.commit()


def deactivate_stale_vehicles(session, source: str, hours=48):
    """Mark vehicles as inactive if not seen in the last N hours."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    session.execute(
        text("""
            UPDATE vehicles
            SET is_active = FALSE
            WHERE source = :source
              AND last_seen_at < :cutoff
              AND is_active = TRUE
        """),
        {"source": source, "cutoff": cutoff},
    )
    session.commit()
