import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pipeline.schemas import SchemeRecord
from pipeline.llm_service import client
from pipeline.stage_mapper import normalize_stages
from pipeline.category_mapper import normalize_category
from scrapers.base_scraper import supabase

import time

def extract_structured_scheme(raw_content: str, source_url: str) -> list[SchemeRecord]:
    prompt = f"""
Extract all startup schemes from the following content. For each scheme, extract these fields: 
- scheme_name (string)
- ministry (string)
- launch_year (integer or null)
- status (string or null)
- category (string or null)
- funding_type (string or null)
- max_funding_amount (MUST be integer, convert '20 Lakhs' to 2000000, or null)
- total_budget_allocated (MUST be integer, convert '945 Crore' to 9450000000, or null)
- startups_funded_count (MUST be pure integer, e.g. 1000, or null)
- sector_eligibility (MUST be a strict JSON Array of strings)
- startup_stage (MUST be a strict JSON Array of strings)
- dpiit_required (boolean or null)
- geographic_restriction (string or null)
- application_portal (string or null)
- application_deadline (MUST be YYYY-MM-DD date string, or null if open year-round)
- processing_timeline (string or null)
- required_documents (MUST be a strict JSON Array of strings)
- success_stories (string or null)

Return as a pure JSON array of objects. Do not include markdown tags.
Source URL is {source_url}

Content: {str(raw_content)[:15000]}
"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-flash-latest',
                contents=prompt,
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
                
            data = json.loads(text)
            records = []
            for item in data:
                item['source_url'] = source_url
                if not item.get("scheme_name"):
                    continue
                if not item.get("ministry"):
                    item["ministry"] = "Unknown"
                
                # Apply canonical mappings
                item["startup_stage"] = normalize_stages(item.get("startup_stage") or [])
                item["category"] = normalize_category(item.get("category"), item.get("funding_type"))
                
                records.append(SchemeRecord(**item))
            return records
        except Exception as e:
            print(f"Attempt {attempt+1} failed extracting structured scheme: {e}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))  # Exponential backoff
            else:
                return []
    return []

def run_silver_layer():
    # Process unprocessed raw rows
    res = supabase.table("schemes_raw").select("*").execute()
    raw_rows = res.data
    
    # Ideally should process incrementally and track last_processed
    for row in raw_rows:
        source_url = row.get("source_url")
        raw_content = row.get("raw_content")
        records = extract_structured_scheme(str(raw_content), source_url)
        for rec in records:
            # Insert or Update into schemes_clean
            try:
                data_dict = rec.model_dump(exclude_none=True)
                # Ensure date is string if present
                if 'application_deadline' in data_dict and data_dict['application_deadline']:
                    data_dict['application_deadline'] = data_dict['application_deadline'].isoformat()
                    
                supabase.table("schemes_clean").upsert(data_dict, on_conflict="scheme_name, ministry").execute()
                print(f"Upserted {rec.scheme_name} into clean layer.")
            except Exception as e:
                print(f"Failed to upsert clean record: {e}")

if __name__ == "__main__":
    run_silver_layer()
