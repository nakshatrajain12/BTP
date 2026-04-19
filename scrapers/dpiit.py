import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import insert_into_bronze

url = "https://dpiit.gov.in"

async def scrape_dpiit():
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Simulated extraction since actual DPIIT scheme layout requires deep inspection
            title = soup.title.string if soup.title else "DPIIT portal"
            
            # Find any announcement block
            announcements = [a.text.strip() for a in soup.find_all('a') if 'scheme' in a.text.lower()]
            
            raw_data = {
                "title": title,
                "announcements": announcements,
                "html_snippet": str(soup.body)[:15000] # just an example for MVP
            }
            insert_into_bronze(url, raw_data)
    except Exception as e:
        print(f"Failed to scrape DPIIT: {e}")
