import httpx
from bs4 import BeautifulSoup
from scrapers.base_scraper import insert_into_bronze

PORTAL_URL = "https://startuptn.in"

async def scrape_startup_tn():
    """Scrapes scheme and grant announcements from StartupTN."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        async with httpx.AsyncClient(verify=False, timeout=30.0, headers=headers) as client:
            response = await client.get(PORTAL_URL)
            if response.status_code != 200:
                print(f"[StartupTN] Failed with HTTP status: {response.status_code}")
                return

            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title else "StartupTN Portal"

            # Parse relevant scheme and grant anchors
            schemes_found = []
            for link in soup.find_all("a", href=True):
                text = link.get_text(strip=True)
                if any(k in text.lower() for k in ["grant", "scheme", "fund", "seed", "tanseed", "subsidy"]):
                    href = link["href"]
                    full_url = href if href.startswith("http") else f"{PORTAL_URL}/{href.lstrip('/')}"
                    schemes_found.append({"title": text, "url": full_url})

            raw_data = {
                "portal_name": "StartupTN",
                "state": "Tamil Nadu",
                "page_title": title,
                "schemes_detected": schemes_found,
                "html_snippet": str(soup.body)[:15000]
            }

            insert_into_bronze(PORTAL_URL, raw_data)
            print(f"[StartupTN] Ingested {len(schemes_found)} candidate items into Bronze.")
    except Exception as e:
        print(f"[StartupTN Error] Scraper encountered an error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(scrape_startup_tn())

