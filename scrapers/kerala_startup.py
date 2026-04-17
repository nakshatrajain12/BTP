from playwright.async_api import async_playwright
from scrapers.base_scraper import insert_into_bronze

url = "https://startupmission.kerala.gov.in"

async def scrape_kerala_startup():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            title = await page.title()
            insert_into_bronze(url, {"title": title})
            await browser.close()
    except Exception as e:
        print(f"Failed to scrape Kerala Startup: {e}")
