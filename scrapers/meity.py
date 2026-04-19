import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import insert_into_bronze

url = "https://www.meity.gov.in/"

async def scrape_meity():
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else "MeitY portal"
            schemes = [a.text.strip() for a in soup.find_all('a') if 'scheme' in a.text.lower()]
            insert_into_bronze(url, {"title": title, "schemes": schemes, "content": str(soup.body)[:15000]})
    except Exception as e:
        print(f"Failed to scrape MeitY: {e}")
