import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.dpiit import scrape_dpiit
from scrapers.sidbi import scrape_sidbi
from scrapers.startup_india import scrape_startup_india
from scrapers.meity import scrape_meity
from scrapers.dst import scrape_dst
from scrapers.msme import scrape_msme
from scrapers.kerala_startup import scrape_kerala_startup
from scrapers.startup_odisha import scrape_startup_odisha

async def run_all_scrapers():
    print("Starting all scrapers...")
    await scrape_dpiit()
    await scrape_sidbi()
    await scrape_startup_india()
    await scrape_meity()
    await scrape_dst()
    await scrape_msme()
    await scrape_kerala_startup()
    await scrape_startup_odisha()
    print("Scraping completed.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_all_scrapers())
