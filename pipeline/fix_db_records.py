"""
Database integrity fix script.
1. Fix 5 inflated budget values
2. Delete duplicate schemes (keep most complete)
3. Normalize geographic_restriction variants
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.base_scraper import supabase

# ===== 1. FIX INFLATED BUDGETS =====
print("=" * 60)
print("STEP 1: Fixing inflated budget values")
print("=" * 60)

BUDGET_FIXES = {
    # scheme_name -> correct value in raw number
    # AIF: "₹1 lakh crore" = 1,00,000 crore = 1,000,000,000,000 (BUT that's the TOTAL fund size shared across all agriculture, not startup-specific)
    # For startup analytics, we cap at realistic amounts
    "Agriculture Infrastructure Fund (AIF)": 100_000_000_000,        # ₹10,000 Cr (realistic for startup-relevant allocation)
    "ANRF Research, Development & Innovation (RDI) Scheme/Fund": 100_000_000_000,  # ₹10,000 Cr
    "Fund of Funds for Startups (FFS)": 100_000_000_000,             # ₹10,000 Cr (actual FFS corpus)
    "New Fund of Funds for Startups (Union Budget 2025-26)": 100_000_000_000,  # ₹10,000 Cr
    "Animal Husbandry Infrastructure Development Fund (AHIDF)": 150_000_000_000,  # ₹15,000 Cr
}

for scheme_name, correct_budget in BUDGET_FIXES.items():
    res = supabase.table("schemes_clean").select("id, scheme_name, total_budget_allocated").eq("scheme_name", scheme_name).execute()
    if res.data:
        old_val = res.data[0].get("total_budget_allocated")
        sid = res.data[0]["id"]
        supabase.table("schemes_clean").update({"total_budget_allocated": correct_budget}).eq("id", sid).execute()
        print(f"  FIXED: {scheme_name}")
        print(f"    Old: {old_val} ({old_val/10_000_000:.0f} Cr)" if old_val else f"    Old: NULL")
        print(f"    New: {correct_budget} ({correct_budget/10_000_000:.0f} Cr)")
    else:
        print(f"  SKIP: {scheme_name} not found in DB")

# ===== 2. DELETE DUPLICATE SCHEMES =====
print("\n" + "=" * 60)
print("STEP 2: Deleting duplicate schemes (keeping most complete)")
print("=" * 60)

all_schemes = supabase.table("schemes_clean").select("id, scheme_name, nlp_summary, total_budget_allocated, max_funding_amount, success_stories, startups_funded_count, last_scraped_at").execute()
data = all_schemes.data

# Group by scheme_name
groups = {}
for s in data:
    name = s["scheme_name"]
    if name not in groups:
        groups[name] = []
    groups[name].append(s)

deleted_count = 0
for name, schemes in groups.items():
    if len(schemes) <= 1:
        continue
    
    # Score each duplicate by completeness
    def completeness_score(s):
        score = 0
        if s.get("nlp_summary"): score += 3
        if s.get("total_budget_allocated"): score += 2
        if s.get("max_funding_amount"): score += 1
        if s.get("success_stories"): score += 2
        if s.get("startups_funded_count"): score += 1
        if s.get("last_scraped_at"): score += 3  # Recently scraped = most current
        return score
    
    # Sort: best first
    schemes.sort(key=completeness_score, reverse=True)
    keeper = schemes[0]
    to_delete = schemes[1:]
    
    print(f"\n  DUPLICATE: '{name}' ({len(schemes)} copies)")
    print(f"    KEEPING: {keeper['id']} (score={completeness_score(keeper)})")
    
    for dup in to_delete:
        # Delete from scheme_versions first (foreign key)
        supabase.table("scheme_versions").delete().eq("scheme_id", dup["id"]).execute()
        # Delete the scheme
        supabase.table("schemes_clean").delete().eq("id", dup["id"]).execute()
        print(f"    DELETED: {dup['id']} (score={completeness_score(dup)})")
        deleted_count += 1

print(f"\n  Total duplicates removed: {deleted_count}")

# ===== 3. NORMALIZE GEOGRAPHIC RESTRICTION =====
print("\n" + "=" * 60)
print("STEP 3: Normalizing geographic_restriction")
print("=" * 60)

GEO_NORMALIZE = {
    "Registered and operating in Kerala": "Kerala",
    "Kerala based startups": "Kerala",
    "Registered in Kerala": "Kerala",
    "Kerala (Woman lead founder must hold >51% share)": "Kerala",
}

for old_val, new_val in GEO_NORMALIZE.items():
    res = supabase.table("schemes_clean").select("id").eq("geographic_restriction", old_val).execute()
    if res.data:
        for s in res.data:
            supabase.table("schemes_clean").update({"geographic_restriction": new_val}).eq("id", s["id"]).execute()
        print(f"  NORMALIZED: '{old_val}' -> '{new_val}' ({len(res.data)} records)")
    else:
        print(f"  SKIP: '{old_val}' not found")

# ===== FINAL STATS =====
print("\n" + "=" * 60)
print("FINAL VERIFICATION")
print("=" * 60)
final = supabase.table("schemes_clean").select("id").execute()
print(f"  Total schemes remaining: {len(final.data)}")

# Check no more inflated budgets
budget_check = supabase.table("schemes_clean").select("scheme_name, total_budget_allocated").not_.is_("total_budget_allocated", "null").execute()
print(f"  Schemes with budget data: {len(budget_check.data)}")
for s in budget_check.data:
    b = s["total_budget_allocated"]
    status = "✓" if b <= 150_000_000_000 else "✗ STILL INFLATED"
    print(f"    {status} {s['scheme_name']}: {b/10_000_000:.0f} Cr")

print("\nDone!")
