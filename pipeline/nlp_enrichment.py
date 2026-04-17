import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import supabase
from pipeline.llm_service import summarize_scheme

def run_nlp_enrichment():
    # Fetch schemes without a summary
    res = supabase.table("schemes_clean").select("*").is_("nlp_summary", "null").limit(20).execute()
    schemes = res.data
    
    for scheme in schemes:
        try:
            summary = summarize_scheme(scheme)
            supabase.table("schemes_clean").update({"nlp_summary": summary}).eq("id", scheme["id"]).execute()
            print(f"Updated summary for {scheme.get('scheme_name')}")
        except Exception as e:
            print(f"Failed to summarize scheme {scheme.get('scheme_name')}: {e}")

if __name__ == "__main__":
    run_nlp_enrichment()
