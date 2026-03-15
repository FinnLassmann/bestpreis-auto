"""APScheduler-based daily scraper runner."""
import asyncio
import logging
from apscheduler.schedulers.blocking import BlockingScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_scrapers():
    """Run all scrapers sequentially."""
    from viscaal import scrape_viscaal
    from apeg import scrape_apeg
    from eu_mayer import scrape_eu_mayer

    logger.info("Starting scheduled scrape run...")

    try:
        asyncio.run(scrape_viscaal())
        logger.info("Viscaal scrape completed successfully")
    except Exception as e:
        logger.error(f"Viscaal scrape failed: {e}")

    try:
        asyncio.run(scrape_apeg())
        logger.info("APEG scrape completed successfully")
    except Exception as e:
        logger.error(f"APEG scrape failed: {e}")

    try:
        scrape_eu_mayer()
        logger.info("EU-Mayer scrape completed successfully")
    except Exception as e:
        logger.error(f"EU-Mayer scrape failed: {e}")

    logger.info("Scheduled scrape run finished")


if __name__ == "__main__":
    logger.info("Scraper scheduler starting...")

    # Run once on startup
    run_scrapers()

    # Schedule daily at 02:00
    scheduler = BlockingScheduler()
    scheduler.add_job(run_scrapers, "cron", hour=2, minute=0)
    logger.info("Scheduled daily scrape at 02:00. Waiting...")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
