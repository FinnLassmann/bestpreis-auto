"""Scraper for eu-mayer.de vehicle listings (Autrado platform).

Uses requests + BeautifulSoup (server-rendered HTML, no JS needed).

Run standalone:  python eu_mayer.py --limit 5
"""
import argparse
import logging
import re
import time
from datetime import datetime
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

from db import Session, upsert_vehicle, deactivate_stale_vehicles

logger = logging.getLogger(__name__)

BASE_URL = "https://www.eu-mayer.de"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
SOURCE = "eu-mayer"

ALLOWED_BRANDS = {
    "volkswagen", "vw", "audi", "skoda", "škoda", "seat", "cupra",
    "hyundai", "kia", "dacia", "ford", "mg",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)",
}


def _get(url: str) -> requests.Response:
    """GET with rate-limiting and headers."""
    time.sleep(1.5)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp


def get_listing_urls() -> list[str]:
    """Parse sitemap.xml to find listing page URLs for allowed brands."""
    logger.info("Fetching sitemap ...")
    resp = requests.get(SITEMAP_URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    root = ElementTree.fromstring(resp.content)
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    urls = []
    for loc in root.findall(".//s:url/s:loc", ns):
        url = loc.text
        if not url or "_alle.php" not in url:
            continue
        match = re.search(r"/liste-([a-zäöüß]+)-", url)
        if match and match.group(1) in ALLOWED_BRANDS and "npage=" not in url:
            urls.append(url)

    logger.info(f"Found {len(urls)} listing pages for allowed brands")
    return urls


def get_detail_urls(listing_url: str) -> list[str]:
    """Paginate through a listing page and collect vehicle detail URLs."""
    detail_urls = []
    page_num = 1

    while True:
        url = listing_url if page_num == 1 else f"{listing_url}?npage={page_num}"
        try:
            resp = _get(url)
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch listing {url}: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        links = soup.find_all("a", href=re.compile(r"auto-.*-x__\d+\.php"))
        new_urls = []
        for a in links:
            href = a.get("href", "")
            if not href.startswith("http"):
                href = f"{BASE_URL}/{href.lstrip('/')}"
            if href not in detail_urls and href not in new_urls:
                new_urls.append(href)

        if not new_urls:
            break

        detail_urls.extend(new_urls)

        next_link = soup.find("a", href=re.compile(rf"npage={page_num + 1}"))
        if not next_link:
            break
        page_num += 1

    return detail_urls


def _parse_german_price(text: str) -> float | None:
    """Parse '21.000,– €' or '17.750,00 €' to float."""
    if not text:
        return None
    cleaned = text.replace("€", "").replace("*", "").strip()
    cleaned = cleaned.replace(",–", "").replace(",- ", "")
    cleaned = re.sub(r"[^\d,]", "", cleaned)
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_power(text: str) -> tuple[int | None, int | None]:
    """Parse '85 kW (116 PS)' → (85, 116)."""
    kw_match = re.search(r"(\d+)\s*kW", text)
    ps_match = re.search(r"(\d+)\s*PS", text)
    kw = int(kw_match.group(1)) if kw_match else None
    ps = int(ps_match.group(1)) if ps_match else None
    if kw and not ps:
        ps = round(kw * 1.35962)
    return kw, ps


def _parse_engine_cc(text: str) -> int | None:
    """Parse '1.498 ccm' → 1498."""
    match = re.search(r"([\d.]+)\s*ccm", text)
    if match:
        return int(match.group(1).replace(".", ""))
    return None


def _parse_availability(text: str) -> str:
    """Map delivery time text to availability enum."""
    lower = text.lower()
    if "sofort" in lower or "lager" in lower:
        return "lager"
    if "woche" in lower:
        return "vorlauf"
    return "bestellung"


def parse_detail(html: str, url: str) -> dict | None:
    """Parse a vehicle detail page into a vehicle data dict."""
    soup = BeautifulSoup(html, "lxml")

    h1 = soup.find("h1")
    if not h1:
        return None
    title = h1.get_text(strip=True)
    clean_title = re.split(r"[/|]", title)[0].strip()

    parts = clean_title.split()
    brand = parts[0] if parts else None
    model = parts[1] if len(parts) >= 2 else None
    variant = " ".join(parts) if parts else None

    # Source ID
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
        price_eur = _parse_german_price(price_el.get_text())
    if price_eur is None:
        price_match = re.search(r"([\d.]+,[\d–-]+)\s*€\s*incl", soup.get_text())
        if price_match:
            price_eur = _parse_german_price(price_match.group(1))

    # Specs
    fuel_type = gearbox = body_type = None
    power_kw = power_ps = engine_cc = None

    spec_list = soup.find("ul", class_="c-vehicle__attributes")
    if spec_list:
        for li in spec_list.find_all("li"):
            text = li.get_text(strip=True)
            if text.startswith("Kraftstoff"):
                fuel_type = text.replace("Kraftstoff", "").strip()
            elif text.startswith("Getriebe"):
                gearbox = text.replace("Getriebe", "").strip()
            elif text.startswith("Leistung"):
                power_kw, power_ps = _parse_power(text)
            elif text.startswith("Hubraum"):
                engine_cc = _parse_engine_cc(text)
            elif text.startswith("Kategorie"):
                body_type = text.replace("Kategorie", "").strip()

    # Images
    image_urls = []
    for a in soup.find_all("a", {"data-fancybox": True}):
        href = a.get("href", "")
        if "img.autrado.de" in href:
            image_urls.append(href)

    # Availability
    availability = "bestellung"
    lz_match = re.search(r"Lieferzeit:?\s*([^<\n]+)", soup.get_text())
    if lz_match:
        availability = _parse_availability(lz_match.group(1))

    return {
        "source": SOURCE,
        "source_id": source_id,
        "source_url": url,
        "brand": brand,
        "model": model,
        "variant": variant[:200] if variant else None,
        "body_type": body_type,
        "fuel_type": fuel_type,
        "gearbox": gearbox,
        "power_kw": power_kw,
        "power_ps": power_ps,
        "engine_cc": engine_cc,
        "mileage_km": 0,
        "availability": availability,
        "color": None,
        "price_eur": price_eur,
        "uvp_eur": None,
        "savings_eur": None,
        "savings_pct": None,
        "image_urls": image_urls if image_urls else None,
    }


def scrape_eu_mayer(limit: int | None = None, persist: bool = True):
    """Run the full EU-Mayer scrape pipeline."""
    logger.info("Starting EU-Mayer scrape ...")

    listing_urls = get_listing_urls()
    all_detail_urls = []

    for i, listing_url in enumerate(listing_urls):
        brand_model = re.search(r"/liste-(.+?)-a__", listing_url)
        label = brand_model.group(1) if brand_model else listing_url
        logger.info(f"[{i+1}/{len(listing_urls)}] Fetching listings for {label} ...")

        detail_urls = get_detail_urls(listing_url)
        all_detail_urls.extend(detail_urls)
        logger.info(f"  Found {len(detail_urls)} vehicles")

    # Deduplicate
    all_detail_urls = list(dict.fromkeys(all_detail_urls))
    logger.info(f"Total unique detail pages: {len(all_detail_urls)}")

    if limit:
        all_detail_urls = all_detail_urls[:limit]
        logger.info(f"Limited to {limit} vehicles")

    session = Session() if persist else None
    scraped = 0

    for i, detail_url in enumerate(all_detail_urls):
        try:
            resp = _get(detail_url)
            vehicle_data = parse_detail(resp.text, detail_url)
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch {detail_url}: {e}")
            continue

        if not vehicle_data or not vehicle_data.get("price_eur"):
            continue

        if persist and session:
            try:
                upsert_vehicle(session, vehicle_data)
                scraped += 1
                logger.info(f"Saved: {vehicle_data.get('variant', detail_url)}")
            except Exception as e:
                logger.error(f"DB error for {detail_url}: {e}")
                session.rollback()
        else:
            scraped += 1
            logger.info(f"Scraped (not persisted): {vehicle_data.get('variant', detail_url)}")

    if persist and session:
        deactivate_stale_vehicles(session, SOURCE)
        session.close()

    logger.info(f"EU-Mayer scrape complete: {scraped}/{len(all_detail_urls)} vehicles saved")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(description="Scrape eu-mayer.de vehicles")
    parser.add_argument("--limit", type=int, default=None, help="Max vehicles to scrape")
    args = parser.parse_args()

    scrape_eu_mayer(limit=args.limit)
