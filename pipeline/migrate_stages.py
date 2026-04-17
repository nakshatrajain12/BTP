import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import supabase
from pipeline.stage_mapper import normalize_stages

def migrate_stages():
    print("Migrating stages mapped in db...")
    res = supabase.table("schemes_clean").select("id, startup_stage").execute()
    schemes = res.data

    updated = 0
    for s in schemes:
        old_stages = s.get("startup_stage") or []
        new_stages = normalize_stages(old_stages)
        
        # If changed, update
        if set(old_stages) != set(new_stages):
            try:
                supabase.table("schemes_clean").update({"startup_stage": new_stages}).eq("id", s["id"]).execute()
                updated += 1
            except Exception as e:
                print(f"Failed to update scheme {s['id']}: {e}")
                
    print(f"Successfully updated {updated} scheme stages.")

if __name__ == "__main__":
    migrate_stages()
