import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import insert_into_bronze

AIM_URL = "https://aim.gov.in"

async def scrape_aim_niti():
    """Scrapes programs and challenges from NITI Aayog Atal Innovation Mission."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        async with httpx.AsyncClient(verify=False, timeout=30.0, headers=headers) as client:
            response = await client.get(AIM_URL)
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title else "Atal Innovation Mission"

            announcements = []
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                if any(word in text.lower() for word in ["aic", "cic", "scale", "fellowship", "grant", "challenge"]):
                    announcements.append({"title": text, "href": a["href"]})

            raw_data = {
                "portal_name": "Atal Innovation Mission (AIM)",
                "organization": "NITI Aayog",
                "page_title": title,
                "announcements": announcements,
                "html_snippet": str(soup.body)[:15000]
            }

            insert_into_bronze(AIM_URL, raw_data)
            print(f"[AIM NITI] Ingested {len(announcements)} announcements into Bronze.")
    except Exception as e:
        print(f"[AIM NITI Error] Scraper encountered an error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(scrape_aim_niti())

