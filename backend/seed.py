"""
Seed script for the EU Neuwagen Marktplatz prototype.

Fetches real vehicle data from:
  1. audaris API (powers viscaal.de)
  2. eu-mayer.de (Autrado platform, HTML scraping)

Run standalone:  python seed.py
"""

import os
import re
import time
from datetime import datetime
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database import Base
from models import Vehicle

DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://euautos:dev_password@localhost:5432/euautos",
)

engine = create_engine(DATABASE_URL_SYNC, echo=False)

API_BASE = "https://api.audaris.de/v1/clients/1473/website-vehicles"
API_PARAMS = {
    "website": "5ea1e86b6d1e56a5036bcec8",
    "limit": 50,
}

FUEL_MAP = {
    "PETROL": "Benzin",
    "DIESEL": "Diesel",
    "ELECTRIC": "Elektro",
    "HYBRID": "Hybrid",
    "PLUG_IN_HYBRID": "Plug-in-Hybrid",
    "LPG": "LPG",
    "CNG": "CNG",
}

GEARBOX_MAP = {
    "MANUAL": "Schaltgetriebe",
    "AUTOMATIC": "Automatik",
    "SEMI_AUTOMATIC": "Halbautomatik",
}


def fetch_all_vehicles() -> list[dict]:
    """Paginate through the audaris API and return all vehicle dicts."""
    all_vehicles = []
    skip = 0
    while True:
        params = {**API_PARAMS, "skip": skip}
        print(f"  Fetching vehicles (skip={skip}) ...")
        resp = requests.get(API_BASE, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        items = data if isinstance(data, list) else data.get("items", data.get("data", []))
        if not items:
            break

        all_vehicles.extend(items)
        print(f"  Got {len(items)} vehicles (total so far: {len(all_vehicles)})")

        if len(items) < API_PARAMS["limit"]:
            break
        skip += API_PARAMS["limit"]

    return all_vehicles


def map_fuel(v: dict) -> str | None:
    """Extract fuel type from audaris vehicle dict."""
    engine_type = v.get("engineType") or ""
    if engine_type in FUEL_MAP:
        return FUEL_MAP[engine_type]

    fuels = v.get("fuels") or []
    if fuels:
        fuel = fuels[0] if isinstance(fuels[0], str) else fuels[0].get("type", "")
        if fuel in FUEL_MAP:
            return FUEL_MAP[fuel]

    return engine_type or None


def map_availability(v: dict) -> str:
    """Determine availability from usageState and related fields."""
    usage_state = (v.get("usageState") or "").upper()
    usage_types = v.get("usageTypes") or []

    if usage_state in ("NEW", "ONEDAYREGISTRATION") or "ONEDAYREGISTRATION" in usage_types:
        return "lager"

    delivery_days = v.get("deliveryDays")
    if delivery_days is not None and delivery_days <= 14:
        return "lager"
    if delivery_days is not None and delivery_days <= 60:
        return "vorlauf"

    return "lager"  # default for stock vehicles


def build_source_url(v: dict) -> str:
    """Construct the viscaal.de URL for a vehicle."""
    brand = (v.get("manufacturerName") or "").lower().replace(" ", "-")
    model = (v.get("modelName") or "").lower().replace(" ", "-")
    internal_id = v.get("vehicleClientInternalNumber") or v.get("_id", "")
    slug = v.get("slug") or ""

    if slug:
        return f"https://www.viscaal.de/angebote/{slug}/"

    return f"https://www.viscaal.de/angebote/{brand}/{model}/{internal_id}/"


def parse_date(date_str: str | None):
    """Parse a date string from the API into a date object."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
    except (ValueError, AttributeError):
        return None


def map_vehicle(v: dict) -> Vehicle:
    """Map an audaris API vehicle dict to a Vehicle ORM instance."""
    source_id = str(
        v.get("vehicleClientInternalNumber")
        or v.get("_id")
        or v.get("id")
        or ""
    )

    power_kw = v.get("enginePower")
    power_ps = round(power_kw * 1.35962) if power_kw else None

    # Extract image URLs (prefer "web" size)
    images = []
    for img in (v.get("images") or []):
        url = None
        if isinstance(img, dict):
            url = img.get("web") or img.get("large") or img.get("medium") or img.get("url")
        elif isinstance(img, str):
            url = img
        if url:
            images.append(url)

    now = datetime.utcnow()

    return Vehicle(
        source="viscaal",
        source_id=source_id,
        source_url=build_source_url(v),
        brand=v.get("manufacturerName"),
        model=v.get("modelName"),
        variant=(v.get("title") or "")[:200] or None,
        trim_line=None,  # not reliably parseable from title
        body_type=v.get("bodyType") or v.get("bodyName"),
        fuel_type=map_fuel(v),
        gearbox=GEARBOX_MAP.get((v.get("gearboxType") or "").upper()),
        power_kw=power_kw,
        power_ps=power_ps,
        engine_cc=v.get("engineSize"),
        mileage_km=v.get("mileage"),
        first_reg_date=parse_date(v.get("registration")),
        availability=map_availability(v),
        color=v.get("exteriorColorName"),
        price_eur=v.get("priceRetail"),
        uvp_eur=None,
        savings_eur=None,
        savings_pct=None,
        image_urls=images if images else None,
        scraped_at=now,
        last_seen_at=now,
        is_active=True,
    )


## ---------------------------------------------------------------------------
## EU-Mayer (Autrado platform) — HTML scraping
## ---------------------------------------------------------------------------

EU_MAYER_BASE = "https://www.eu-mayer.de"
EU_MAYER_SITEMAP = f"{EU_MAYER_BASE}/sitemap.xml"
EU_MAYER_SOURCE = "eu-mayer"

EU_MAYER_ALLOWED_BRANDS = {
    "volkswagen", "vw", "audi", "skoda", "škoda", "seat", "cupra",
    "hyundai", "kia", "dacia", "ford", "mg",
}

EU_MAYER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)",
}


def _eu_mayer_get(url: str) -> requests.Response:
    """GET with rate-limiting and headers."""
    time.sleep(1.5)
    resp = requests.get(url, headers=EU_MAYER_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp


def fetch_eu_mayer_listing_urls() -> list[str]:
    """Parse sitemap.xml to find listing page URLs for allowed brands."""
    print("  Fetching eu-mayer sitemap ...")
    resp = requests.get(EU_MAYER_SITEMAP, headers=EU_MAYER_HEADERS, timeout=30)
    resp.raise_for_status()

    root = ElementTree.fromstring(resp.content)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    listing_urls = []
    for loc in root.findall(".//s:url/s:loc", ns):
        url = loc.text
        if not url or "_alle.php" not in url:
            continue
        # Pattern: liste-{brand}-{model}-a__*_alle.php
        match = re.search(r"/liste-([a-zäöüß]+)-", url)
        if match and match.group(1) in EU_MAYER_ALLOWED_BRANDS:
            # Only take base URL (npage=1 is default), skip ?npage= variants
            if "npage=" not in url:
                listing_urls.append(url)

    print(f"  Found {len(listing_urls)} listing pages for allowed brands")
    return listing_urls


def fetch_eu_mayer_detail_urls(listing_url: str) -> list[str]:
    """Paginate through a listing page and collect all vehicle detail URLs."""
    detail_urls = []
    page_num = 1

    while True:
        url = listing_url if page_num == 1 else f"{listing_url}?npage={page_num}"
        try:
            resp = _eu_mayer_get(url)
        except requests.RequestException as e:
            print(f"    Failed to fetch listing page {url}: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        links = soup.find_all("a", href=re.compile(r"auto-.*-x__\d+\.php"))
        new_urls = []
        for a in links:
            href = a.get("href", "")
            if not href.startswith("http"):
                href = f"{EU_MAYER_BASE}/{href.lstrip('/')}"
            if href not in detail_urls and href not in new_urls:
                new_urls.append(href)

        if not new_urls:
            break

        detail_urls.extend(new_urls)

        # Check if there's a next page link
        next_link = soup.find("a", href=re.compile(rf"npage={page_num + 1}"))
        if not next_link:
            break
        page_num += 1

    return detail_urls


def parse_german_price(text: str) -> float | None:
    """Parse '21.000,– €' or '17.750,00 €' to float."""
    if not text:
        return None
    cleaned = text.replace("€", "").replace("*", "").strip()
    cleaned = cleaned.replace(",–", "").replace(",- ", "")
    # Remove dots (thousand separators), replace comma with dot (decimal)
    cleaned = re.sub(r"[^\d,]", "", cleaned)
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_power(text: str) -> tuple[int | None, int | None]:
    """Parse '85 kW (116 PS)' → (85, 116)."""
    kw_match = re.search(r"(\d+)\s*kW", text)
    ps_match = re.search(r"(\d+)\s*PS", text)
    kw = int(kw_match.group(1)) if kw_match else None
    ps = int(ps_match.group(1)) if ps_match else None
    if kw and not ps:
        ps = round(kw * 1.35962)
    return kw, ps


def parse_engine_cc(text: str) -> int | None:
    """Parse '1.498 ccm' → 1498."""
    match = re.search(r"([\d.]+)\s*ccm", text)
    if match:
        return int(match.group(1).replace(".", ""))
    return None


def parse_eu_mayer_availability(text: str) -> str:
    """Map delivery time text to availability enum."""
    lower = text.lower()
    if "sofort" in lower or "lager" in lower:
        return "lager"
    if "woche" in lower:
        return "vorlauf"
    if "monat" in lower:
        return "bestellung"
    return "bestellung"


def parse_eu_mayer_detail(html: str, url: str) -> dict | None:
    """Parse a eu-mayer vehicle detail page into a vehicle dict."""
    soup = BeautifulSoup(html, "lxml")

    # Title
    h1 = soup.find("h1")
    if not h1:
        return None
    title = h1.get_text(strip=True)
    # Clean marketing suffixes like "/ Festpreisgarantie* | kostenlose Lieferung!"
    clean_title = re.split(r"[/|]", title)[0].strip()

    parts = clean_title.split()
    brand = parts[0] if parts else None
    model = parts[1] if len(parts) >= 2 else None
    variant = " ".join(parts) if len(parts) >= 1 else None

    # Source ID from Fahrzeugnr. or URL
    source_id = None
    fnr_match = re.search(r"Fahrzeugnr\.?:?\s*(\d+)", soup.get_text())
    if fnr_match:
        source_id = fnr_match.group(1)
    else:
        url_id_match = re.search(r"x__(\d+)\.php", url)
        if url_id_match:
            source_id = url_id_match.group(1)

    if not source_id:
        return None

    # Price
    price_eur = None
    price_el = soup.find("span", class_="Gesamtpreis")
    if price_el:
        price_eur = parse_german_price(price_el.get_text())
    if price_eur is None:
        # Fallback: search for price pattern in text
        price_match = re.search(r"([\d.]+,[\d–-]+)\s*€\s*incl", soup.get_text())
        if price_match:
            price_eur = parse_german_price(price_match.group(1))

    # Specs
    fuel_type = None
    gearbox = None
    power_kw = None
    power_ps = None
    engine_cc = None
    body_type = None

    spec_list = soup.find("ul", class_="c-vehicle__attributes")
    if spec_list:
        for li in spec_list.find_all("li"):
            text = li.get_text(strip=True)
            if text.startswith("Kraftstoff"):
                fuel_type = text.replace("Kraftstoff", "").strip()
            elif text.startswith("Getriebe"):
                gearbox = text.replace("Getriebe", "").strip()
            elif text.startswith("Leistung"):
                power_kw, power_ps = parse_power(text)
            elif text.startswith("Hubraum"):
                engine_cc = parse_engine_cc(text)
            elif text.startswith("Kategorie"):
                body_type = text.replace("Kategorie", "").strip()

    # Images
    image_urls = []
    for a in soup.find_all("a", {"data-fancybox": True}):
        href = a.get("href", "")
        if "img.autrado.de" in href:
            image_urls.append(href)

    # Availability / Lieferzeit
    availability = "bestellung"
    lz_match = re.search(r"Lieferzeit:?\s*([^<\n]+)", soup.get_text())
    if lz_match:
        availability = parse_eu_mayer_availability(lz_match.group(1))

    now = datetime.utcnow()

    return {
        "source": EU_MAYER_SOURCE,
        "source_id": source_id,
        "source_url": url,
        "brand": brand,
        "model": model,
        "variant": variant[:200] if variant else None,
        "trim_line": None,
        "body_type": body_type,
        "fuel_type": fuel_type,
        "gearbox": gearbox,
        "power_kw": power_kw,
        "power_ps": power_ps,
        "engine_cc": engine_cc,
        "mileage_km": 0,  # Neuwagen
        "first_reg_date": None,
        "availability": availability,
        "color": None,
        "price_eur": price_eur,
        "uvp_eur": None,
        "savings_eur": None,
        "savings_pct": None,
        "image_urls": image_urls if image_urls else None,
        "scraped_at": now,
        "last_seen_at": now,
        "is_active": True,
    }


def fetch_eu_mayer_vehicles() -> list[dict]:
    """Scrape eu-mayer.de: sitemap → listing pages → detail pages → vehicle dicts."""
    listing_urls = fetch_eu_mayer_listing_urls()
    all_detail_urls = []

    for i, listing_url in enumerate(listing_urls):
        brand_model = re.search(r"/liste-(.+?)-a__", listing_url)
        label = brand_model.group(1) if brand_model else listing_url
        print(f"  [{i+1}/{len(listing_urls)}] Fetching listings for {label} ...")

        detail_urls = fetch_eu_mayer_detail_urls(listing_url)
        all_detail_urls.extend(detail_urls)
        print(f"    Found {len(detail_urls)} vehicles")

    # Deduplicate
    all_detail_urls = list(dict.fromkeys(all_detail_urls))
    print(f"\n  Total unique vehicle detail pages: {len(all_detail_urls)}")

    vehicles = []
    for i, detail_url in enumerate(all_detail_urls):
        if (i + 1) % 50 == 0:
            print(f"  Scraping detail page {i+1}/{len(all_detail_urls)} ...")
        try:
            resp = _eu_mayer_get(detail_url)
            vehicle = parse_eu_mayer_detail(resp.text, detail_url)
            if vehicle and vehicle.get("price_eur"):
                vehicles.append(vehicle)
        except requests.RequestException as e:
            print(f"  Failed to fetch {detail_url}: {e}")
            continue

    print(f"  Successfully parsed {len(vehicles)} eu-mayer vehicles")
    return vehicles


def seed():
    print(f"Connecting to database: {DATABASE_URL_SYNC}")
    Base.metadata.create_all(engine)
    print("Tables created / verified.")

    # --- Source 1: Viscaal (audaris API) ---
    print("\nFetching vehicles from audaris API (viscaal.de data) ...")
    raw_viscaal = fetch_all_vehicles()
    print(f"Fetched {len(raw_viscaal)} Viscaal vehicles.")
    viscaal_vehicles = [map_vehicle(v) for v in raw_viscaal]

    # --- Source 2: EU-Mayer (HTML scraping) ---
    print("\nFetching vehicles from eu-mayer.de ...")
    eu_mayer_dicts = fetch_eu_mayer_vehicles()

    with Session(engine) as session:
        deleted = session.query(Vehicle).delete()
        session.commit()
        print(f"\nCleared {deleted} existing vehicles.")

        # Insert Viscaal
        session.add_all(viscaal_vehicles)
        session.commit()
        print(f"Inserted {len(viscaal_vehicles)} Viscaal vehicles.")

        # Insert EU-Mayer
        eu_mayer_count = 0
        for vd in eu_mayer_dicts:
            try:
                vehicle = Vehicle(**vd)
                session.add(vehicle)
                session.commit()
                eu_mayer_count += 1
            except Exception as e:
                session.rollback()
                print(f"  Skipped eu-mayer vehicle {vd.get('source_id')}: {e}")
        print(f"Inserted {eu_mayer_count} EU-Mayer vehicles.")

        # Summary
        all_vehicles = session.query(Vehicle).filter(Vehicle.is_active == True).all()
        sources: dict[str, int] = {}
        brands: dict[str, int] = {}
        for v in all_vehicles:
            s = v.source or "Unknown"
            sources[s] = sources.get(s, 0) + 1
            b = v.brand or "Unknown"
            brands[b] = brands.get(b, 0) + 1

        print("\nSummary by source:")
        for source, count in sorted(sources.items()):
            print(f"  {source}: {count}")
        print("\nSummary by brand:")
        for brand, count in sorted(brands.items()):
            print(f"  {brand}: {count}")

    print("\nDone!")


if __name__ == "__main__":
    seed()
