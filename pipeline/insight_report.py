from scrapers.base_scraper import supabase

def generate_report():
    print("Generating Insight Report...")
    res = supabase.table("schemes_clean").select("*").execute()
    schemes = res.data
    
    if not schemes:
        print("No scheme data available.")
        return
        
    print(f"Total Schemes: {len(schemes)}")
    report_content = "# Startup Policy Insight Report\n\n"
    
    # Q1: Which ministry supports startups most actively?
    ministry_counts = {}
    for s in schemes:
        m = s.get("ministry", "Unknown")
        ministry_counts[m] = ministry_counts.get(m, 0) + 1
    
    top_ministry = sorted(ministry_counts.items(), key=lambda x: x[1], reverse=True)[0] if ministry_counts else ("None", 0)
    report_content += f"## 1. Most Active Ministry\n{top_ministry[0]} with {top_ministry[1]} schemes.\n\n"
    
    # Q3: Are early-stage startups underserved?
    stages = {"Idea": 0, "Prototype": 0, "Early Revenue": 0, "Scale-up": 0}
    for s in schemes:
        stg_list = s.get("startup_stage") or []
        for stg in stg_list:
            if stg in stages:
                stages[stg] += 1
                
    total_stg_tags = sum(stages.values())
    idea_proto = stages["Idea"] + stages["Prototype"]
    if total_stg_tags > 0 and (idea_proto / total_stg_tags) < 0.3:
        report_content += "## 3. Early Stage Underserved\nYes, idea and prototype stages make up less than 30% of target stages.\n\n"
    else:
        report_content += "## 3. Early Stage Underserved\nNo, adequate support exists for early-stage.\n\n"

    # More questions can be generated analytically from the DB.
    # Write to markdown file
    with open("Insight_Report.md", "w") as f:
        f.write(report_content)
        
    print("Report saved to Insight_Report.md")
    
if __name__ == "__main__":
    generate_report()
