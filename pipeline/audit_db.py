"""Full database audit script — checks all fields for anomalies."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.base_scraper import supabase

res = supabase.table("schemes_clean").select("scheme_name, ministry, total_budget_allocated, max_funding_amount, startup_stage, category, funding_type, sector_eligibility, geographic_restriction, status, launch_year").execute()
data = res.data
print(f"Total schemes: {len(data)}\n")

# Check for NULL/missing fields
fields = ["scheme_name","ministry","total_budget_allocated","max_funding_amount","startup_stage","category","funding_type","sector_eligibility","geographic_restriction","status","launch_year"]
for f in fields:
    nulls = sum(1 for s in data if not s.get(f))
    print(f"  {f}: {nulls}/{len(data)} NULL/empty")

print("\n=== BUDGET ANOMALIES (raw values) ===")
for s in data:
    b = s.get("total_budget_allocated") or 0
    name = s.get("scheme_name", "?")
    if b > 100_000_000_000:
        print(f"  INFLATED: {name} -> {b} ({b/10_000_000:.0f} Cr)")
    elif 0 < b < 100_000:
        print(f"  TOO SMALL: {name} -> {b}")

print("\n=== MAX FUNDING ANOMALIES ===")
for s in data:
    f = s.get("max_funding_amount") or 0
    name = s.get("scheme_name", "?")
    if f > 1_000_000_000:
        print(f"  HIGH: {name} -> {f} ({f/10_000_000:.0f} Cr)")

print("\n=== STAGE FIELD VALUES ===")
stages = {}
for s in data:
    for st in (s.get("startup_stage") or []):
        stages[st] = stages.get(st, 0) + 1
for k,v in sorted(stages.items(), key=lambda x:-x[1]):
    print(f"  {k}: {v}")

print("\n=== STATUS VALUES ===")
statuses = {}
for s in data:
    st = s.get("status", "NULL")
    statuses[st] = statuses.get(st, 0) + 1
for k,v in statuses.items():
    print(f"  {k}: {v}")

print("\n=== GEO RESTRICTION VALUES ===")
geos = {}
for s in data:
    g = s.get("geographic_restriction", "NULL")
    geos[g] = geos.get(g, 0) + 1
for k,v in sorted(geos.items(), key=lambda x:-x[1]):
    print(f"  {k}: {v}")

print("\n=== DUPLICATE SCHEME NAMES ===")
names = {}
for s in data:
    n = s.get("scheme_name", "?")
    names[n] = names.get(n, 0) + 1
for k,v in sorted(names.items(), key=lambda x:-x[1]):
    if v > 1:
        print(f"  DUPLICATE ({v}x): {k}")

print("\n=== SECTOR ELIGIBILITY VALUES ===")
sectors = {}
for s in data:
    for sec in (s.get("sector_eligibility") or []):
        sectors[sec] = sectors.get(sec, 0) + 1
for k,v in sorted(sectors.items(), key=lambda x:-x[1]):
    print(f"  {k}: {v}")

print("\n=== CATEGORY + FUNDING_TYPE cross check ===")
for s in data:
    cat = s.get("category", "")
    ft = (s.get("funding_type") or "").lower()
    name = s.get("scheme_name", "?")
    # Flag mismatches
    if cat == "Funding" and any(kw in ft for kw in ["loan", "credit", "guarantee", "collateral", "interest subvention"]):
        print(f"  MISMATCH: {name} -> category=Funding but funding_type={s.get('funding_type')}")
    if cat == "Incubation" and any(kw in ft for kw in ["grant", "equity"]):
        print(f"  MISMATCH: {name} -> category=Incubation but funding_type={s.get('funding_type')}")
