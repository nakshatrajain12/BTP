from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Set Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.bronze_runner import run_all_scrapers
from pipeline.silver import run_silver_layer
from pipeline.nlp_enrichment import run_nlp_enrichment
from pipeline.llm_service import recommend_schemes, chat_with_agent
from pipeline.ingest_central_xlsx import ingest_xlsx
from pipeline.knowledge_builder import build_general_knowledge_context, build_scheme_knowledge_context
from scrapers.base_scraper import supabase
import json

app = FastAPI(title="Startup Policy Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

class RecommendRequest(BaseModel):
    sector: str
    stage: str
    state: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Startup Policy Intelligence API is running."}

@app.post("/pipeline/run-scrapers")
async def trigger_scraping(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_all_scrapers)
    return {"message": "Scraping triggered in background."}

@app.post("/pipeline/run-silver")
async def trigger_silver(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_silver_layer)
    return {"message": "Silver layer processing triggered in background."}

@app.post("/pipeline/run-nlp")
async def trigger_nlp(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_nlp_enrichment)
    return {"message": "NLP enrichment triggered in background."}

@app.post("/pipeline/ingest-xlsx")
async def trigger_ingest_xlsx(background_tasks: BackgroundTasks):
    background_tasks.add_task(ingest_xlsx)
    return {"message": "XLSX Ingestion triggered in background."}

@app.post("/recommend")
async def recommend(req: RecommendRequest):
    # Check cache first
    res = supabase.table("recommendation_cache").select("*").eq("sector", req.sector).eq("stage", req.stage).eq("state", req.state).execute()
    if res.data:
        return {"recommendations": res.data[0]["recommendations"]}

    # Filter base schemes using postgrest simple conditions or get all and filter in memory if few
    # Assuming schemes_clean has reasonable number for MVP
    res = supabase.table("schemes_clean").select("*").execute()
    schemes = res.data
    
    # Simple Python filter for MVP since we have complex array types
    filtered_schemes = []
    for s in schemes:
        if s.get("sector_eligibility") and req.sector not in s["sector_eligibility"]:
            continue
        if s.get("startup_stage") and req.stage not in s["startup_stage"]:
            continue
        if s.get("geographic_restriction") and s["geographic_restriction"] != req.state:
            continue
        filtered_schemes.append(s)
        
    if not filtered_schemes:
        # Fallback to general schemes or without strict filtering for demo if 0
        filtered_schemes = schemes[:10]

    schema_str = json.dumps([{
        k: v for k, v in scheme.items() if k in ["scheme_name", "ministry", "funding_type", "max_funding_amount", "startup_stage", "nlp_summary", "application_portal"]
    } for scheme in filtered_schemes[:20]])
    
    try:
        recommendations_json_str = recommend_schemes(req.sector, req.stage, req.state, schema_str)
        # Parse JSON
        if recommendations_json_str.startswith("```json"):
            recommendations_json_str = recommendations_json_str[7:-3]
        elif recommendations_json_str.startswith("```"):
            recommendations_json_str = recommendations_json_str[3:-3]
        recs = json.loads(recommendations_json_str)

        # Cache it
        supabase.table("recommendation_cache").upsert({
            "sector": req.sector,
            "stage": req.stage,
            "state": req.state,
            "recommendations": recs
        }, on_conflict="sector, stage, state").execute()

        return {"recommendations": recs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schemes")
async def list_schemes(
    sector: str | None = None,
    stage: str | None = None,
    state: str | None = None,
    ministry: str | None = None,
    category: str | None = None,
    page: int = 1,
    limit: int = 20
):
    query = supabase.table("schemes_clean").select("*")
    if sector:
        query = query.contains("sector_eligibility", [sector])
    if stage:
        query = query.contains("startup_stage", [stage])
    if state:
        query = query.eq("geographic_restriction", state)
    if ministry:
        query = query.eq("ministry", ministry)
    if category:
        query = query.eq("category", category)
    
    offset = (page - 1) * limit
    res = query.range(offset, offset + limit - 1).execute()
    schemes = res.data or []
    
    # Annotate with recent updates
    if schemes:
        from datetime import datetime, timedelta
        cutoff_30_days = (datetime.utcnow() - timedelta(days=30)).isoformat()
        recent_versions = supabase.table("scheme_versions") \
            .select("scheme_id, changed_at") \
            .gte("changed_at", cutoff_30_days) \
            .execute()
        updated_ids = {v["scheme_id"]: v["changed_at"] for v in recent_versions.data}
        for s in schemes:
            s["recently_updated"] = s["id"] in updated_ids
            s["last_updated_at"] = updated_ids.get(s["id"])

    return {"schemes": schemes, "page": page, "limit": limit}

@app.get("/schemes/{scheme_id}")
async def get_scheme(scheme_id: str):
    res = supabase.table("schemes_clean").select("*").eq("id", scheme_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return res.data[0]

@app.get("/alerts/recent")
async def recent_alerts(days: int = 7):
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    res = supabase.table("scheme_versions") \
        .select("*") \
        .gte("changed_at", cutoff) \
        .order("changed_at", desc=True) \
        .limit(20) \
        .execute()
    return {"alerts": res.data, "period_days": days}

@app.get("/success-stories")
async def get_success_stories():
    res = supabase.table("schemes_clean") \
        .select("id, scheme_name, ministry, success_stories, funding_type, max_funding_amount, geographic_restriction") \
        .neq("success_stories", "") \
        .not_.is_("success_stories", "null") \
        .execute()
    return {"stories": res.data}

class ChatMessage(BaseModel):
    role: str
    content: str
class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

@app.post("/chat")
async def general_chat(req: ChatRequest):
    context = build_general_knowledge_context()
    hist_list = [{"role": msg.role, "content": msg.content} for msg in req.history]
    response = chat_with_agent(req.message, hist_list, context)
    return {"response": response}

class SchemeChatRequest(BaseModel):
    scheme_id: str
    message: str
    history: list[ChatMessage] = []

@app.post("/chat/scheme")
async def chat_about_scheme(req: SchemeChatRequest):
    scheme = supabase.table("schemes_clean").select("*").eq("id", req.scheme_id).execute()
    if not scheme.data:
        raise HTTPException(status_code=404, detail="Scheme not found")
    context = build_scheme_knowledge_context(scheme.data[0])
    hist_list = [{"role": msg.role, "content": msg.content} for msg in req.history]
    response = chat_with_agent(req.message, hist_list, context)
    return {"response": response}

@app.get("/pipeline/status")
async def get_pipeline_status():
    res = supabase.table("schemes_clean").select("last_scraped_at").order("last_scraped_at", desc=True).limit(1).execute()
    last_run = res.data[0]["last_scraped_at"] if res.data else None
    return {
        "status": "healthy",
        "last_run": last_run
    }

@app.get("/analytics/summary")
async def get_summary():
    schemes = supabase.table("schemes_clean").select("id, max_funding_amount, total_budget_allocated, ministry").execute()
    data = schemes.data
    total_budget = sum((s.get("total_budget_allocated") or 0) for s in data)
    avg_funding = sum((s.get("max_funding_amount") or 0) for s in data) / max(len(data), 1)
    unique_ministries = len(set(s["ministry"] for s in data if "ministry" in s))
    return {
        "total_schemes": len(data),
        "total_budget": total_budget,
        "unique_ministries": unique_ministries,
        "avg_funding": avg_funding
    }

def standardize_ministry_name(name: str) -> str:
    if not name:
        return "Multiple/Other"
    
    # We only take the first primary ministry if separated by commas
    name = name.split(",")[0]
    name_lower = name.lower()
    
    if any(x in name_lower for x in ["meit", "electronics", "information technology", "it department"]):
        return "MeitY (Electronics & IT)"
    if "msme" in name_lower or "micro, small" in name_lower:
        return "Ministry of MSME"
    if "dpiit" in name_lower or "promotion of industry" in name_lower:
        return "DPIIT"
    if "science" in name_lower and "technology" in name_lower:
        return "Dept of Science & Technology (DST)"
    if "kerala" in name_lower:
        return "Kerala Startup Mission"
    if "odisha" in name_lower:
        return "Startup Odisha"
    if "education" in name_lower or "aicte" in name_lower:
        return "Ministry of Education"
    if "db" in name_lower or "biotechnology" in name_lower:
        return "Dept of Biotechnology (DBT)"
    if "niti aayog" in name_lower:
        return "NITI Aayog"
        
    # Return normalized casing if unmapped
    return name.strip().title()

@app.get("/analytics/funding-by-ministry")
async def get_funding_by_ministry():
    res = supabase.table("schemes_clean").select("ministry, total_budget_allocated").execute()
    ministries = {}
    for s in res.data:
        m = standardize_ministry_name(s.get("ministry") or "Unknown")
        b = float(s.get("total_budget_allocated") or 0)
        
        if m not in ministries: 
            ministries[m] = 0
        ministries[m] += b
        
    result = [{"ministry": k, "total_budget": v} for k, v in ministries.items()]
    # Filter out entries combined to 0 if there are lots of valid ones
    has_budget = [r for r in result if r["total_budget"] > 0]
    if len(has_budget) >= 5:
        result = has_budget
        
    # Sort highest budget first
    result.sort(key=lambda x: x["total_budget"], reverse=True)
    return result

@app.get("/analytics/sector-distribution")
async def get_sector_distribution():
    try:
        res = supabase.table("sector_distribution").select("*").execute()
        return res.data
    except Exception:
        # Fallback
        res = supabase.table("schemes_clean").select("sector_eligibility").execute()
        sectors = {}
        for s in res.data:
            if s.get("sector_eligibility"):
                for sec in s["sector_eligibility"]:
                    if sec not in sectors: sectors[sec] = 0
                    sectors[sec] += 1
        return [{"sector": k, "scheme_count": v} for k, v in sectors.items()]

@app.get("/analytics/stage-coverage")
async def get_stage_coverage():
    try:
        res = supabase.table("stage_coverage").select("*").execute()
        return res.data
    except Exception:
        # Fallback
        res = supabase.table("schemes_clean").select("startup_stage").execute()
        stages = {}
        for s in res.data:
            if s.get("startup_stage"):
                for st in s["startup_stage"]:
                    if st not in stages: stages[st] = 0
                    stages[st] += 1
        return [{"stage": k, "scheme_count": v} for k, v in stages.items()]

@app.get("/analytics/layer")
def get_analytics():
    # Return directly from materialized views or views
    # Standard supabase SDK doesn't natively query materialized views directly if RPC isn't set, 
    # but we can query them as tables if PostgREST allows it. Assuming it does:
    try:
        by_ministry = supabase.table("funding_by_ministry").select("*").execute()
        sector_dist = supabase.table("sector_distribution").select("*").execute()
        stage_cov = supabase.table("stage_coverage").select("*").execute()
        
        return {
            "funding_by_ministry": by_ministry.data,
            "sector_distribution": sector_dist.data,
            "stage_coverage": stage_cov.data
        }
    except Exception as e:
        # Fallback to manual aggregation if materialized views are not accessible/created
        res = supabase.table("schemes_clean").select("*").execute()
        schemes = res.data
        return {
            "fallback_aggregated": True,
            "total_schemes": len(schemes),
            "data": schemes
        }

@app.get("/analytics/detailed")
async def get_detailed_analytics():
    schemes_res = supabase.table("schemes_clean").select("*").execute()
    data = schemes_res.data or []
    
    total_budget = sum((s.get("total_budget_allocated") or 0) for s in data)
    avg_funding = sum((s.get("max_funding_amount") or 0) for s in data) / max(len(data), 1)
    unique_ministries = len(set(s.get("ministry", "") for s in data if s.get("ministry")))
    
    # Funding by ministry
    ministries_b = {}
    type_counts = {}
    geo_counts = {"Central": 0, "State": 0}
    
    for s in data:
        m = standardize_ministry_name(s.get("ministry") or "Unknown")
        b = float(s.get("total_budget_allocated") or 0)
        ministries_b[m] = ministries_b.get(m, 0) + b
        
        # Funding type
        f = s.get("category", s.get("funding_type", "Funding")) or "Funding"
        type_counts[f] = type_counts.get(f, 0) + 1
        
        geo = s.get("geographic_restriction", "").lower()
        if "pan-india" in geo or "central" in geo:
            geo_counts["Central"] += 1
        else:
            geo_counts["State"] += 1
    
    # Sector + stage distribution (using existing routes logic)
    sector_dist_res = await get_sector_distribution()
    stage_cov_res = await get_stage_coverage()
    
    by_min = [{"ministry": k, "total_budget": v} for k, v in ministries_b.items() if v > 0]
    by_min.sort(key=lambda x: x["total_budget"], reverse=True)
    
    types = [{"category": k, "count": v} for k, v in type_counts.items()]
    
    return {
        "summary": {
            "total_schemes": len(data),
            "total_budget": total_budget,
            "avg_funding": avg_funding,
            "unique_ministries": unique_ministries
        },
        "funding_by_ministry": by_min,
        "sector_distribution": sector_dist_res,
        "stage_coverage": stage_cov_res,
        "funding_type_breakdown": types,
        "state_vs_central": geo_counts
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
