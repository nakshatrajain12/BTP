import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import insert_into_bronze

url = "https://www.sidbi.in/"

async def scrape_sidbi():
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.title.string if soup.title else "SIDBI portal"
            
            schemes = [a.text.strip() for a in soup.find_all('a') if 'scheme' in a.text.lower() or 'fund' in a.text.lower()]
            
            raw_data = {
                "title": title,
                "schemes": schemes,
                "html_snippet": str(soup.body)[:15000]
            }
            insert_into_bronze(url, raw_data)
    except Exception as e:
        print(f"Failed to scrape SIDBI: {e}")
