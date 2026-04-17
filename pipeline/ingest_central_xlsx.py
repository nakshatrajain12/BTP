import sys
import os
import openpyxl

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import supabase
from pipeline.stage_mapper import normalize_stages
from pipeline.category_mapper import normalize_category

def ingest_xlsx():
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Central_Govt_Startup_Schemes_Database (1).xlsx")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    try:
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active
        
        headers = [str(cell.value).strip().lower() if cell.value else "" for cell in ws[1]]
        print(f"Headers found: {headers}")

        # Map headers conceptually
        def get_col_idx(possible_names):
            for name in possible_names:
                for idx, h in enumerate(headers):
                    if name in h:
                        return idx
            return -1

        idx_name = get_col_idx(["scheme", "name"])
        idx_ministry = get_col_idx(["ministry", "dept", "department"])
        idx_type = get_col_idx(["type", "funding type"])
        idx_amount = get_col_idx(["amount", "max", "quantum"])
        idx_stage = get_col_idx(["stage"])
        idx_sector = get_col_idx(["sector"])
        idx_category = get_col_idx(["category"])
        idx_success = get_col_idx(["success", "story", "stories"])
        idx_url = get_col_idx(["url", "link"])
        idx_portal = get_col_idx(["portal", "apply"])

        inserted = 0
        updated = 0
        skipped = 0

        for row in ws.iter_rows(min_row=2):
            values = [cell.value for cell in row]
            if not values or not any(values):
                continue
                
            scheme_name = str(values[idx_name]).strip() if idx_name != -1 and values[idx_name] else ""
            if not scheme_name or scheme_name.lower() == "none":
                skipped += 1
                continue

            ministry = str(values[idx_ministry]).strip() if idx_ministry != -1 and values[idx_ministry] else "Central Government"
            raw_stage = str(values[idx_stage]).strip() if idx_stage != -1 and values[idx_stage] else ""
            stages = normalize_stages([s.strip() for s in raw_stage.split(',')] if raw_stage else [])
            
            raw_category = str(values[idx_category]).strip() if idx_category != -1 and values[idx_category] else ""
            funding_type = str(values[idx_type]).strip() if idx_type != -1 and values[idx_type] else ""
            category = normalize_category(raw_category, funding_type)
            
            raw_amount = values[idx_amount] if idx_amount != -1 else None
            max_amount = None
            try:
                if raw_amount:
                    # simplistic number parsing
                    amt_str = str(raw_amount).lower().replace(',', '').replace('₹', '').replace('rs', '').strip()
                    if "cr" in amt_str:
                        amt_str = amt_str.replace("cr", "").replace("crore", "").strip()
                        max_amount = int(float(amt_str) * 10000000)
                    elif "lakh" in amt_str or "l" in amt_str:
                        amt_str = amt_str.replace("lakh", "").replace("l", "").strip()
                        max_amount = int(float(amt_str) * 100000)
                    else:
                        import re
                        numbers = re.findall(r'\d+', amt_str)
                        if numbers:
                            max_amount = int("".join(numbers))
            except Exception:
                pass
            
            raw_sector = str(values[idx_sector]).strip() if idx_sector != -1 and values[idx_sector] else ""
            sectors = [s.strip() for s in raw_sector.split(',')] if raw_sector else []

            record = {
                "scheme_name": scheme_name[:250],
                "ministry": ministry[:250],
                "funding_type": funding_type[:250],
                "max_funding_amount": max_amount,
                "startup_stage": stages,
                "sector_eligibility": sectors,
                "category": category,
                "success_stories": str(values[idx_success]).strip() if idx_success != -1 and values[idx_success] else None,
                "source_url": str(values[idx_url]).strip() if idx_url != -1 and values[idx_url] else "https://www.startupindia.gov.in/",
                "application_portal": str(values[idx_portal]).strip() if idx_portal != -1 and values[idx_portal] else None,
                "geographic_restriction": "Pan-India",
                "status": "Active"
            }

            try:
                # Upsert based on unique constraint
                # Since Supabase python client doesn't return count easily on upsert with duplicate, we just execute
                supabase.table("schemes_clean").upsert(record, on_conflict="scheme_name, ministry").execute()
                inserted += 1
            except Exception as e:
                print(f"Error upserting row {scheme_name}: {e}")
                skipped += 1

        print(f"XLSX Ingestion Complete. Upserted: {inserted}, Skipped: {skipped}")

    except Exception as e:
        print(f"Failed to read XLSX file: {e}")

if __name__ == "__main__":
    ingest_xlsx()
