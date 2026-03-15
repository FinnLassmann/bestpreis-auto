"""Scraper for eu-fahrzeugboerse.de (APEG) vehicle listings."""
import asyncio
import logging
from playwright.async_api import async_playwright

from base import create_browser_context, safe_navigate, sleep_random, parse_german_number, parse_int_from_text
from db import Session, upsert_vehicle, deactivate_stale_vehicles

logger = logging.getLogger(__name__)

LISTING_URL = "https://eu-fahrzeugboerse.de/kunden/"
SOURCE = "apeg"

# TODO: These selectors need to be verified by inspecting eu-fahrzeugboerse.de in a browser.
# The site shows "Fahrzeuge werden geladen..." initially — wait for that to disappear.
SELECTORS = {
    "loading_indicator": "text=Fahrzeuge werden geladen",
    "vehicle_card": ".vehicle-item, .car-item, .fahrzeug-card, [data-fahrzeug]",
    "vehicle_link": "a[href*='/kunden/fahrzeug/'], a[href*='/kunden/detail/']",
    "next_page": ".pagination .next, a[rel='next'], .load-more",
    # Detail page selectors
    "title": "h1, .vehicle-title, .fahrzeug-titel",
    "price": ".price, .preis, [data-price]",
    "uvp_price": ".uvp, .listenpreis, .original-price",
    "image": ".gallery img, .fahrzeug-bilder img, .slider img",
    "spec_table": ".specifications, .fahrzeug-daten, .technische-daten",
    "availability": ".availability, .verfuegbarkeit, [data-availability]",
}


async def get_listing_urls(page) -> list[str]:
    """Extract all vehicle detail URLs from the APEG listing page."""
    urls = []

    await page.goto(LISTING_URL, wait_until="domcontentloaded", timeout=20000)

    # Wait for loading indicator to disappear
    try:
        await page.wait_for_selector(SELECTORS["loading_indicator"], state="hidden", timeout=15000)
    except Exception:
        logger.info("Loading indicator not found or already gone, proceeding...")

    # Wait for vehicle cards to appear
    try:
        await page.wait_for_selector(SELECTORS["vehicle_card"], timeout=15000)
    except Exception:
        logger.warning("No vehicle cards found on listing page")
        return urls

    while True:
        links = await page.eval_on_selector_all(
            SELECTORS["vehicle_link"],
            "els => els.map(e => e.href)",
        )
        for link in links:
            if link not in urls:
                urls.append(link)

        logger.info(f"Found {len(urls)} vehicle URLs so far...")

        # Check for next page / load more
        next_btn = await page.query_selector(SELECTORS["next_page"])
        if next_btn:
            await next_btn.click()
            await sleep_random(2, 4)
            await page.wait_for_load_state("domcontentloaded")
        else:
            break

    return urls


async def scrape_vehicle_detail(page, url: str) -> dict | None:
    """Scrape a single APEG vehicle detail page."""
    try:
        await safe_navigate(page, url, SELECTORS["title"])
    except Exception as e:
        logger.warning(f"Failed to load {url}: {e}")
        return None

    data = {
        "source": SOURCE,
        "source_url": url,
    }

    # Extract source_id from URL
    parts = url.rstrip("/").split("/")
    data["source_id"] = parts[-1] if parts else url

    # Title
    title_el = await page.query_selector(SELECTORS["title"])
    if title_el:
        title = (await title_el.inner_text()).strip()
        data["variant"] = title
        title_parts = title.split(" ", 2)
        if len(title_parts) >= 1:
            data["brand"] = title_parts[0]
        if len(title_parts) >= 2:
            data["model"] = title_parts[1]

    # Price
    price_el = await page.query_selector(SELECTORS["price"])
    if price_el:
        price_text = await price_el.inner_text()
        data["price_eur"] = parse_german_number(price_text)

    # UVP price
    uvp_el = await page.query_selector(SELECTORS["uvp_price"])
    if uvp_el:
        uvp_text = await uvp_el.inner_text()
        data["uvp_eur"] = parse_german_number(uvp_text)

    # Images
    image_els = await page.query_selector_all(SELECTORS["image"])
    image_urls = []
    for img in image_els:
        src = await img.get_attribute("src")
        if src and src.startswith("http"):
            image_urls.append(src)
    data["image_urls"] = image_urls

    # Availability
    avail_el = await page.query_selector(SELECTORS["availability"])
    if avail_el:
        avail_text = (await avail_el.inner_text()).strip().lower()
        if "lager" in avail_text or "sofort" in avail_text:
            data["availability"] = "lager"
        elif "vorlauf" in avail_text:
            data["availability"] = "vorlauf"
        elif "bestell" in avail_text:
            data["availability"] = "bestellung"
        else:
            data["availability"] = avail_text

    # Specs
    spec_el = await page.query_selector(SELECTORS["spec_table"])
    if spec_el:
        spec_text = await spec_el.inner_text()
        lines = spec_text.strip().split("\n")
        for line in lines:
            line_lower = line.lower().strip()
            if "kraftstoff" in line_lower:
                data["fuel_type"] = line.split(":")[-1].strip() if ":" in line else None
            elif "getriebe" in line_lower:
                data["gearbox"] = line.split(":")[-1].strip() if ":" in line else None
            elif "leistung" in line_lower or "kw" in line_lower:
                kw = parse_int_from_text(line)
                if kw:
                    data["power_kw"] = kw
                    data["power_ps"] = round(kw * 1.35962)
            elif "kilometer" in line_lower:
                data["mileage_km"] = parse_int_from_text(line)
            elif "farbe" in line_lower:
                data["color"] = line.split(":")[-1].strip() if ":" in line else None
            elif "karosserie" in line_lower:
                data["body_type"] = line.split(":")[-1].strip() if ":" in line else None
            elif "ausstattung" in line_lower or "trim" in line_lower:
                data["trim_line"] = line.split(":")[-1].strip() if ":" in line else None

    return data


async def scrape_apeg(limit: int | None = None, persist: bool = True):
    """Run the full APEG scrape pipeline."""
    logger.info("Starting APEG scrape...")

    async with async_playwright() as p:
        browser, context = await create_browser_context(p)
        page = await context.new_page()

        try:
            urls = await get_listing_urls(page)
            logger.info(f"Found {len(urls)} vehicles to scrape")

            if limit:
                urls = urls[:limit]

            session = Session() if persist else None
            scraped = 0

            for url in urls:
                await sleep_random(2, 4)
                vehicle_data = await scrape_vehicle_detail(page, url)

                if vehicle_data and persist and session:
                    try:
                        upsert_vehicle(session, vehicle_data)
                        scraped += 1
                        logger.info(f"Saved: {vehicle_data.get('variant', url)}")
                    except Exception as e:
                        logger.error(f"DB error for {url}: {e}")
                        session.rollback()
                elif vehicle_data:
                    scraped += 1
                    logger.info(f"Scraped (not persisted): {vehicle_data.get('variant', url)}")

            if persist and session:
                deactivate_stale_vehicles(session, SOURCE)
                session.close()

            logger.info(f"APEG scrape complete: {scraped}/{len(urls)} vehicles saved")

        finally:
            await browser.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(scrape_apeg(limit=5))
