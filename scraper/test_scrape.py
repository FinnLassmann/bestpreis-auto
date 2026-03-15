"""CLI tool for testing scrapers."""
import argparse
import asyncio
import logging


def main():
    parser = argparse.ArgumentParser(description="Test scraper for EU car marketplace")
    parser.add_argument("--source", choices=["viscaal", "apeg"], required=True)
    parser.add_argument("--limit", type=int, default=5, help="Max vehicles to scrape")
    parser.add_argument("--persist", action="store_true", help="Save to database")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.source == "viscaal":
        from viscaal import scrape_viscaal
        asyncio.run(scrape_viscaal(limit=args.limit, persist=args.persist))
    elif args.source == "apeg":
        from apeg import scrape_apeg
        asyncio.run(scrape_apeg(limit=args.limit, persist=args.persist))


if __name__ == "__main__":
    main()
