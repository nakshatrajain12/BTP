from playwright.async_api import async_playwright
from scrapers.base_scraper import insert_into_bronze

url = "https://www.startupindia.gov.in"

async def scrape_startup_india():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            title = await page.title()
            # Extract links or details
            links = await page.evaluate('''() => {
                const anchors = Array.from(document.querySelectorAll('a'));
                return anchors.map(a => a.innerText).filter(t => t.toLowerCase().includes('scheme'));
            }''')
            
            raw_data = {
                "title": title,
                "schemes": links
            }
            insert_into_bronze(url, raw_data)
            await browser.close()
    except Exception as e:
        print(f"Failed to scrape Startup India: {e}")
