import os
import json
import hashlib
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_url = os.environ.get("SUPABASE_URL") or "https://akmobppxfzdsspvztgmu.supabase.co"
_key = os.environ.get("SUPABASE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFrbW9icHB4Znpkc3Nwdnp0Z211Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTg1MzI0MSwiZXhwIjoyMDkxNDI5MjQxfQ.NCk9pusp48Fbp6WS5-dUncCq8CuuavNAIv2VQ2Nqe2s"
try:
    supabase: Client = create_client(_url, _key)
except Exception as e:
    supabase = None

def compute_hash(data: dict) -> str:
    stringified = json.dumps(data, sort_keys=True)
    return hashlib.sha256(stringified.encode('utf-8')).hexdigest()

def insert_into_bronze(source_url: str, raw_content: dict):
    content_hash = compute_hash(raw_content)
    try:
        supabase.table("schemes_raw").insert({
            "scraped_at": datetime.utcnow().isoformat(),
            "source_url": source_url,
            "raw_content": raw_content,
            "content_hash": content_hash
        }).execute()
        print(f"Inserted bronze record for {source_url}")
    except Exception as e:
        print(f"Error inserting to bronze: {e}")
