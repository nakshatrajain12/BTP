import httpx
from scrapers.base_scraper import insert_into_bronze

url = "https://api.startupindia.gov.in/sih/api/noauth/network/schemes"

async def scrape_startup_india_api():
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                insert_into_bronze(url, {"title": "Startup India API", "content": str(data)[:15000]})
            else:
                insert_into_bronze(url, {"title": "Startup India API", "content": str(response.text)[:15000]})
    except Exception as e:
        print(f"Failed to scrape Startup India API: {e}")
