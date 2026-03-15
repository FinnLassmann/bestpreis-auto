"""Shared Playwright utilities for all scrapers."""
import asyncio
import random
import re

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]


async def create_browser_context(playwright):
    """Create a browser context with a randomized user agent."""
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent=random.choice(USER_AGENTS),
        viewport={"width": 1920, "height": 1080},
        locale="de-DE",
    )
    return browser, context


async def safe_navigate(page, url, wait_selector=None, timeout=15000):
    """Navigate to a URL and optionally wait for a selector."""
    await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
    if wait_selector:
        await page.wait_for_selector(wait_selector, timeout=timeout)


async def sleep_random(min_s=2.0, max_s=4.0):
    """Random sleep for rate limiting."""
    await asyncio.sleep(random.uniform(min_s, max_s))


def extract_text(element_handle):
    """Extract trimmed text from an element, or None."""
    if element_handle is None:
        return None
    text = element_handle
    if isinstance(text, str):
        text = text.strip()
        return text if text else None
    return None


def parse_german_number(text):
    """Parse a German-formatted number: dots=thousands, comma=decimal.
    '24.990,00' -> 24990.0
    '150' -> 150.0
    """
    if not text:
        return None
    cleaned = re.sub(r"[^\d.,]", "", text)
    if not cleaned:
        return None
    cleaned = cleaned.replace(".", "")
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_int_from_text(text):
    """Extract first integer from text. '150 kW' -> 150."""
    if not text:
        return None
    match = re.search(r"\d+", text.replace(".", ""))
    return int(match.group()) if match else None
