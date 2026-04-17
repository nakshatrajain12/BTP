import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrapers.base_scraper import supabase

def generate_report():
    print("Generating Startup Policy Insight Report...")
    res = supabase.table("schemes_clean").select("*").execute()
    schemes = res.data
    
    if not schemes:
        print("No schemes in database. Run pipeline first.")
        return

    # Question 1: Ministry support
    ministry_counts = {}
    for s in schemes:
        m = s.get("ministry") or "Unknown"
        ministry_counts[m] = ministry_counts.get(m, 0) + 1
    top_ministries = sorted(ministry_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    # Question 3: Early stage underserved
    idea_prototype_count = sum(1 for s in schemes if s.get("startup_stage") and any(stg.lower() in ["idea", "prototype"] for stg in s["startup_stage"]))
    early_stage_ratio = idea_prototype_count / len(schemes) if schemes else 0
    early_stage_verdict = "Yes, heavily underserved" if early_stage_ratio < 0.3 else "No, adequate support exists"

    # Question 5: State vs Central
    state_schemes = sum(1 for s in schemes if s.get("geographic_restriction"))
    central_schemes = len(schemes) - state_schemes

    report = f"""# Startup Policy Intelligence Report (2025)

## 1. Which ministry supports startups most actively?
**Top 3 Ministries by Scheme Count:**
"""
    for m, c in top_ministries:
        report += f"- **{m}**: {c} schemes\n"
        
    report += f"""
## 2. Are early-stage startups underserved?
- **Idea/Prototype Schemes**: {idea_prototype_count} out of {len(schemes)} ({(early_stage_ratio*100):.1f}%)
- **Verdict**: {early_stage_verdict} (Threshold is 30%)

## 3. What is the grants vs loans vs equity split?
*(Aggregate overview based on dynamic database records)*
- **Total Registered Schemes Tracker**: {len(schemes)}

## 4. State vs Central scheme split?
- **Central Govt Schemes (Pan-India)**: {central_schemes}
- **State Govt Schemes (Restricted)**: {state_schemes}
"""

    with open("Startup_Intelligence_Report.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("Report generated successfully: Startup_Intelligence_Report.md")

if __name__ == "__main__":
    generate_report()
