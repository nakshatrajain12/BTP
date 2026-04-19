import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import insert_into_bronze

url = "https://birac.nic.in"

async def scrape_birac():
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            insert_into_bronze(url, {"title": soup.title.string if soup.title else "BIRAC portal", "content": str(soup.body)[:15000]})
    except Exception as e:
        print(f"Failed to scrape BIRAC: {e}")
