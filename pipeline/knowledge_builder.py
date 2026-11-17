import json
from scrapers.base_scraper import supabase

def build_general_knowledge_context(schemes: list | None = None) -> str:
    try:
        # Fetch data for insights if not supplied
        if schemes is None:
            try:
                schemes_res = supabase.table("schemes_clean").select("id, ministry, startup_stage, category, funding_type, geographic_restriction").execute()
                schemes = schemes_res.data or []
            except Exception:
                schemes = []
            if not schemes:
                try:
                    from main import get_local_schemes
                    schemes = get_local_schemes()
                except Exception:
                    schemes = []
        
        total_schemes = len(schemes)
        if total_schemes == 0:
            return "Indian Government Startup Policy Knowledge Base: Covers core central initiatives including Startup India Seed Fund Scheme (SISFS), MeitY TIDE 2.0, Fund of Funds for Startups (FFS), Credit Guarantee Scheme (CGSS), Atal Innovation Mission (AIM), and MUDRA."

        ministry_counts = {}
        stage_counts = {"Idea": 0, "Prototype": 0, "Early Revenue": 0, "Scale-up": 0}
        type_counts = {"Funding": 0, "Incubation": 0, "Tax Benefit": 0, "Credit Support": 0}
        geo_counts = {"Central": 0, "State": 0}

        for s in schemes:
            m = s.get("ministry") or "Unknown"
            ministry_counts[m] = ministry_counts.get(m, 0) + 1
            
            for stg in (s.get("startup_stage") or []):
                if stg in stage_counts:
                    stage_counts[stg] += 1
                    
            cat = s.get("category")
            if cat in type_counts:
                type_counts[cat] += 1
                
            geo = s.get("geographic_restriction", "").lower()
            if "pan-india" in geo or "central" in geo:
                geo_counts["Central"] += 1
            else:
                geo_counts["State"] += 1

        top_ministries = sorted(ministry_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        idea_proto = stage_counts["Idea"] + stage_counts["Prototype"]
        total_stg_tags = sum(stage_counts.values())
        early_stage_underserved = idea_proto / getattr(total_stg_tags, 'real', 1) < 0.3 if total_stg_tags > 0 else True
        underserved_text = "Yes, early stage startups are underserved." if early_stage_underserved else "No, sufficient early stage schemes exist."

        context = f"""
        Platform Analytics & Intelligence Report:
        - Total registered schemes: {total_schemes}
        - Top 5 active ministries: {', '.join([f'{m} ({c})' for m,c in top_ministries])}
        - Startup Stage Coverage: Idea ({stage_counts['Idea']}), Prototype ({stage_counts['Prototype']}), Early Revenue ({stage_counts['Early Revenue']}), Scale-up ({stage_counts['Scale-up']})
        - Underserved Analysis: Are early-stage (Idea/Prototype) startups underserved? {underserved_text}
        - Scheme Categories Split: Funding ({type_counts['Funding']}), Incubation ({type_counts['Incubation']}), Tax Benefit ({type_counts['Tax Benefit']}), Credit Support ({type_counts['Credit Support']})
        - State vs Central Schemes: Central ({geo_counts['Central']}), State ({geo_counts['State']})
        """
        return context
    except Exception as e:
        return f"Error retrieving analytics data: {e}"

def build_scheme_knowledge_context(scheme: dict) -> str:
    """Formats full specific scheme data for the local LLM agent to focus only on this scheme."""
    
    if not scheme:
        return "Scheme data not provided or not found."
        
    s_name = scheme.get("scheme_name", "Unknown Scheme")
    details = []
    
    for key, val in scheme.items():
        if val and key not in ["id", "content_hash", "last_scraped_at", "last_summarised_hash", "raw_content"]:
            formatted_key = key.replace("_", " ").title()
            # formatting array data nicely
            if isinstance(val, list):
                val = ", ".join(val)
            details.append(f"{formatted_key}: {val}")
            
    context = f"Scheme Name: {s_name}\n"
    context += "All detailed fields:\n" + "\n".join(details)
    return context
