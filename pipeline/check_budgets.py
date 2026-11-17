import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.base_scraper import supabase

res = supabase.table("schemes_clean").select("scheme_name, ministry, total_budget_allocated").not_.is_("total_budget_allocated", "null").execute()
total = 0
for s in res.data:
    b = s["total_budget_allocated"]
    total += b
    print(f"  {s['scheme_name']}: {b/10_000_000:.0f} Cr ({s['ministry']})")
print(f"\nRaw sum: {total/10_000_000:.0f} Cr ({total})")
