import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.base_scraper import supabase
from pipeline.category_mapper import normalize_category

def migrate_categories():
    print("Migrating categories mapped in db...")
    res = supabase.table("schemes_clean").select("id, category, funding_type").execute()
    schemes = res.data

    updated = 0
    for s in schemes:
        old_cat = s.get("category")
        f_type = s.get("funding_type", "")
        new_cat = normalize_category(old_cat, f_type)
        
        # If changed, update
        if old_cat != new_cat:
            try:
                supabase.table("schemes_clean").update({"category": new_cat}).eq("id", s["id"]).execute()
                updated += 1
            except Exception as e:
                print(f"Failed to update scheme {s['id']}: {e}")
                
    print(f"Successfully updated {updated} scheme categories.")

if __name__ == "__main__":
    migrate_categories()
