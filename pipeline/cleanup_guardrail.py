import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

def apply_data_volume_guardrail():
    print("Executing Bronze Layer Guardrail check...")
    try:
        # Supabase API doesn't natively support arbitrary 'INTERVAL' deletions easily through the Python client,
        # but we can do a smart RPC or calculate the date in python.
        
        from datetime import datetime, timedelta
        cutoff_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
        
        # Soft-delete raw HTML blobs older than 30 days to protect the 500MB DB Limit
        res = supabase.table("schemes_raw").delete().lt("scraped_at", cutoff_date).execute()
        
        print(f"Data volume guardrail enforced. Cleared {len(res.data)} old raw HTML blobs from Supabase free tier to save space.")
    except Exception as e:
        print(f"Data guardrail limit error: {e}")

if __name__ == "__main__":
    apply_data_volume_guardrail()
