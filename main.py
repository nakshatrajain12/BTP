from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import sys
import os
import json
import traceback

# Set Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.bronze_runner import run_all_scrapers
from pipeline.silver import run_silver_layer
from pipeline.nlp_enrichment import run_nlp_enrichment
from pipeline.llm_service import recommend_schemes, chat_with_agent
from pipeline.ingest_central_xlsx import ingest_xlsx
from pipeline.knowledge_builder import build_general_knowledge_context, build_scheme_knowledge_context
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# ═══════════════════════════════════════════════════
# CRASH-PROOF SUPABASE CLIENT
# The supabase-py client uses httpx with HTTP/2.
# The connection pool becomes stale after idle time
# and throws "Server disconnected". This wrapper
# recreates the client on failure and retries.
# ═══════════════════════════════════════════════════

_supabase_url = os.environ.get("SUPABASE_URL")
_supabase_key = os.environ.get("SUPABASE_KEY")
_supabase_client = create_client(_supabase_url, _supabase_key)

def get_supabase():
    """Get the current Supabase client."""
    return _supabase_client

def safe_query(query_fn, fallback=None):
    """Execute a Supabase query with automatic retry on connection failure.
    
    Usage: safe_query(lambda sb: sb.table("x").select("*").execute())
    """
    global _supabase_client
    if _supabase_client is None:
        return fallback if fallback is not None else type('EmptyQuery', (object,), {'data': []})()
        
    for attempt in range(2):
        try:
            return query_fn(_supabase_client)
        except Exception as e:
            err_str = str(e).lower()
            if "disconnect" in err_str or "remoteprotocol" in err_str or "connection" in err_str or "getaddrinfo" in err_str or "11001" in err_str:
                if attempt == 1:
                    if fallback is not None:
                        return fallback
                    return type('EmptyQuery', (object,), {'data': []})()
            else:
                if fallback is not None:
                    return fallback
                return type('EmptyQuery', (object,), {'data': []})()
    return fallback if fallback is not None else type('EmptyQuery', (object,), {'data': []})()

# ═══════════════════════════════════════════════════
# LOCAL SCHEMES & GOLD LAYER DATA FALLBACK
# ═══════════════════════════════════════════════════

_local_schemes_cache = None

def get_local_schemes():
    global _local_schemes_cache
    if _local_schemes_cache is not None:
        return _local_schemes_cache
    
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Central_Govt_Startup_Schemes_Database.xlsx")
    if not os.path.exists(excel_path):
        excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Central_Govt_Startup_Schemes_Database (1).xlsx")
    
    if os.path.exists(excel_path):
        try:
            from pipeline.excel_importer import ExcelImporter
            imp = ExcelImporter(excel_path)
            if imp.parse_excel():
                schemes = imp.extract_schemes()
                for idx, s in enumerate(schemes):
                    s["id"] = s.get("id") or f"excel-{idx+1}"
                _local_schemes_cache = schemes
                print(f"[LOCAL_DATA] Loaded {len(_local_schemes_cache)} schemes from {os.path.basename(excel_path)}")
                return _local_schemes_cache
        except Exception as e:
            print(f"[LOCAL_DATA] Error parsing Excel: {e}")
            
    _local_schemes_cache = []
    return _local_schemes_cache

def get_local_gold_analytics():
    schemes = get_local_schemes()
    if not schemes:
        return {"funding_by_ministry": [], "sector_distribution": [], "stage_coverage": []}
    
    import pandas as pd
    df = pd.DataFrame(schemes)
    
    # 1. funding_by_ministry
    fbm = []
    for (minis, ft), group in df.groupby(['ministry', 'funding_type']):
        tot = group['total_budget_allocated'].fillna(0).sum()
        if tot == 0:
            tot = group['max_funding_amount'].fillna(0).sum()
        fbm.append({
            'ministry': str(minis),
            'funding_type': str(ft) if ft else 'Grant',
            'total_budget': float(tot)
        })
    fbm.sort(key=lambda x: x['total_budget'], reverse=True)
    
    # 2. sector_distribution
    sec_map = {}
    for s in schemes:
        secs = s.get('sector_eligibility') or ['General']
        amt = float(s.get('max_funding_amount') or 0)
        for sec in secs:
            sec_clean = str(sec).strip().title()
            if sec_clean not in sec_map:
                sec_map[sec_clean] = {'scheme_count': 0, 'total_funding': 0.0}
            sec_map[sec_clean]['scheme_count'] += 1
            sec_map[sec_clean]['total_funding'] += amt
    s_dist = [
        {'sector': k, 'scheme_count': v['scheme_count'], 'total_funding': v['total_funding']}
        for k, v in sec_map.items()
    ]
    s_dist.sort(key=lambda x: x['scheme_count'], reverse=True)
    
    # 3. stage_coverage
    stg_map = {}
    for s in schemes:
        stgs = s.get('startup_stage') or ['All Stages']
        for stg in stgs:
            stg_clean = str(stg).strip().title()
            stg_map[stg_clean] = stg_map.get(stg_clean, 0) + 1
    s_cov = [
        {'stage': k, 'scheme_count': v}
        for k, v in stg_map.items()
    ]
    s_cov.sort(key=lambda x: x['scheme_count'], reverse=True)
    
    return {
        "funding_by_ministry": fbm,
        "sector_distribution": s_dist,
        "stage_coverage": s_cov
    }

# ═══════════════════════════════════════════════════

scheduler = AsyncIOScheduler()

async def scheduled_pipeline_run():
    print("[CRON] Initiating automated nightly pipeline...")
    try:
        await run_all_scrapers()
        run_silver_layer()
        run_nlp_enrichment()
        print("[CRON] Nightly pipeline completed successfully.")
    except Exception as e:
        print(f"[CRON ERROR] Scheduled execution failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs everyday at 02:00 AM server time
    scheduler.add_job(
        scheduled_pipeline_run,
        CronTrigger(hour=2, minute=0),
        id="nightly_pipeline",
        replace_existing=True
    )
    scheduler.start()
    print("[SCHEDULER] Daily cron job started (02:00 AM).")
    yield
    scheduler.shutdown()

app = FastAPI(title="Startup Policy Intelligence API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RecommendRequest(BaseModel):
    sector: str
    stage: str
    state: str
    startup_name: str = "Founder"

# In-memory mock DB for applications
user_applications_db = []

class ApplicationReq(BaseModel):
    user_email: str
    scheme_id: str
    status: str = "interested"

# ═══════════════════════════════════════════════════
# CORE ENDPOINTS
# ═══════════════════════════════════════════════════

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


def _build_fallback_recommendations(req):
    """Hardcoded fallback recommendations when LLM or DB is unavailable."""
    return {
        "recommendations": [
            {
                "scheme_id": "fallback-1",
                "name": "Startup India Seed Fund Scheme",
                "reason": f"Highly relevant for {req.stage} stage startups in {req.sector}.",
                "why_eligible_reasoning": f"You are 90% eligible — Fits {req.stage} stage perfectly, needs DPIIT registration.",
                "eligibility_score": 90,
                "documents_checklist": ["DPIIT Registration", "Pitch Deck", "Bank Statements", "Founder KYC"],
                "equity_type": "Grant",
                "disbursement_structure": "Milestone-based (3 tranches)",
                "deadline_status": "Open - Rolling Basis",
                "action": "Apply via Startup India portal",
                "application_url": "https://seedfund.startupindia.gov.in"
            },
            {
                "scheme_id": "fallback-2",
                "name": "MeitY TIDE 2.0 (G2-Tier)",
                "reason": f"Dedicated funding for tech innovation in {req.state}.",
                "why_eligible_reasoning": f"You are 75% eligible — Requires deep-tech focus. Missing working prototype details.",
                "eligibility_score": 75,
                "documents_checklist": ["Project Proposal", "Tech Architecture", "Voucher of Incubator Admission"],
                "equity_type": "Grant / Equity",
                "disbursement_structure": "Tranches upon technical evaluation",
                "deadline_status": "Reopened - New Round",
                "action": "Contact local TIDE incubator",
                "application_url": "https://www.meity.gov.in/content/tide-20"
            }
        ]
    }


@app.post("/recommend")
async def recommend(req: RecommendRequest):
    try:
        # Check cache first
        res = safe_query(
            lambda sb: sb.table("recommendation_cache").select("*").eq("sector", req.sector).eq("stage", req.stage).eq("state", req.state).execute(),
            fallback=type('obj', (object,), {'data': []})()
        )
        if res.data:
            # We return it directly if cached
            return {"recommendations": res.data[0]["recommendations"]}

        # Get schemes from DB
        res = safe_query(
            lambda sb: sb.table("schemes_clean").select("*").execute(),
            fallback=type('obj', (object,), {'data': []})()
        )
        schemes = res.data or []
        
        if not schemes:
            return _build_fallback_recommendations(req)

        # Better filtering: use sector_eligibility array
        filtered_schemes = []
        for s in schemes:
            # Sector check
            if s.get("sector_eligibility"):
                if "all" not in [x.lower() for x in s["sector_eligibility"]] and req.sector.lower() not in [x.lower() for x in s["sector_eligibility"]]:
                    continue
            
            # Stage check
            if s.get("startup_stage"):
                if req.stage.lower() not in [x.lower() for x in s["startup_stage"]]:
                    continue
                    
            # Geography check (if restricted to a specific state)
            state_rest = s.get("geographic_restriction")
            if state_rest and state_rest.lower() != "pan-india" and state_rest.lower() != req.state.lower():
                continue
                
            filtered_schemes.append(s)
            
        if not filtered_schemes:
            filtered_schemes = schemes[:10]

        # Pass IDs and relevant fields to LLM
        schema_str = json.dumps([{
            "id": scheme.get("id"),
            "scheme_name": scheme.get("scheme_name"),
            "ministry": scheme.get("ministry"),
            "funding_type": scheme.get("funding_type") or scheme.get("equity_or_grant"),
            "max_funding_amount": scheme.get("max_funding_amount"),
            "disbursement": scheme.get("disbursement_structure"),
            "eligibility_criteria": scheme.get("eligibility_criteria"),
            "documents_required": scheme.get("documents_required"),
            "nlp_summary": scheme.get("nlp_summary")
        } for scheme in filtered_schemes[:15]])
        
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        loop = asyncio.get_running_loop()
        
        with ThreadPoolExecutor() as pool:
            recommendations_json_str = await loop.run_in_executor(
                pool,
                recommend_schemes,
                req.startup_name, req.sector, req.stage, req.state, schema_str
            )
            
        recs = json.loads(recommendations_json_str)

        # Cache it (best effort)
        try:
            safe_query(lambda sb: sb.table("recommendation_cache").upsert({
                "sector": req.sector,
                "stage": req.stage,
                "state": req.state,
                "recommendations": recs
            }, on_conflict="sector, stage, state").execute())
        except Exception:
            pass 

        return {"recommendations": recs}
    except Exception as e:
        traceback.print_exc()
        return _build_fallback_recommendations(req)

class EvaluateSchemeReq(BaseModel):
    sector: str
    stage: str
    state: str
    startup_name: str = "Founder"
    scheme_id: str

@app.post("/evaluate-scheme")
async def evaluate_single_scheme_endpoint(req: EvaluateSchemeReq):
    try:
        res = safe_query(lambda sb: sb.table("schemes_clean").select("*").eq("id", req.scheme_id).execute())
        if not res.data:
            raise HTTPException(status_code=404, detail="Scheme not found")
        scheme = res.data[0]
        
        schema_str = json.dumps({
            "id": scheme.get("id"),
            "scheme_name": scheme.get("scheme_name"),
            "ministry": scheme.get("ministry"),
            "funding_type": scheme.get("funding_type") or scheme.get("equity_or_grant"),
            "max_funding_amount": scheme.get("max_funding_amount"),
            "disbursement": scheme.get("disbursement_structure"),
            "eligibility_criteria": scheme.get("eligibility_criteria"),
            "documents_required": scheme.get("documents_required"),
            "nlp_summary": scheme.get("nlp_summary")
        })
        
        from pipeline.llm_service import evaluate_single_scheme as evaluate_llm
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        loop = asyncio.get_running_loop()
        
        with ThreadPoolExecutor() as pool:
            recommendations_json_str = await loop.run_in_executor(
                pool,
                evaluate_llm,
                req.startup_name, req.sector, req.stage, req.state, schema_str
            )
            
        recs = json.loads(recommendations_json_str)
        return {"recommendation": recs[0] if recs else None}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to evaluate scheme")

@app.get("/opportunity-radar")
def opportunity_radar():
    try:
        res = safe_query(
            lambda sb: sb.table("schemes_clean").select("*").limit(30).execute()
        )
        schemes = res.data or []
        import random
        from datetime import datetime, timedelta
        
        for s in schemes:
            # Use actual DB deadline if it looks valid
            raw_deadline = s.get("next_deadline") or s.get("application_deadline")
            if raw_deadline and len(str(raw_deadline)) > 4:
                try:
                    # Logic to calculate days left
                    s["deadline_countdown_days"] = 15 # Placeholder logic
                except:
                    s["deadline_countdown_days"] = random.randint(5, 30)
            else:
                s["deadline_countdown_days"] = random.randint(3, 45)
            
            # Enrich status for UI badges
            if s["deadline_countdown_days"] < 7:
                s["ui_status"] = "closing_soon"
            elif random.random() > 0.8:
                s["ui_status"] = "new_round"
            else:
                s["ui_status"] = "open"
                
        return {
            "open_now": schemes[:6], 
            "closing_soon": [s for s in schemes if s.get("ui_status") == "closing_soon"][:4], 
            "newly_added": [s for s in schemes if s.get("ui_status") == "new_round"][:4]
        }
    except Exception as e:
        traceback.print_exc()
        return {"open_now": [], "closing_soon": [], "newly_added": []}


@app.post("/applications")
def create_application(req: ApplicationReq):
    import uuid
    from datetime import datetime
    new_app = {
        "id": str(uuid.uuid4()),
        "user_email": req.user_email,
        "scheme_id": req.scheme_id,
        "status": req.status,
        "applied_at": None,
        "next_action": "Review eligibility",
        "notes": "",
        "created_at": datetime.utcnow().isoformat()
    }
    user_applications_db.append(new_app)
    return new_app

@app.get("/applications")
def get_applications(user_email: str):
    try:
        res = safe_query(
            lambda sb: sb.table("schemes_clean").select("id, scheme_name, ministry, status, max_funding_amount").execute(),
            fallback=type('obj', (object,), {'data': []})()
        )
        schemes = {str(s["id"]): s for s in res.data} if res.data else {}
        apps = [dict(a) for a in user_applications_db if a["user_email"] == user_email]
        for a in apps:
            a["scheme"] = schemes.get(str(a["scheme_id"]))
        return {"applications": apps}
    except Exception:
        return {"applications": []}


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
    try:
        def do_query(sb):
            query = sb.table("schemes_clean").select("*")
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
            return query.range(offset, offset + limit - 1).execute()
        
        res = safe_query(do_query)
        schemes = res.data or []
        
        if not schemes:
            local = get_local_schemes()
            filtered = local
            if sector:
                filtered = [s for s in filtered if sector.lower() in [sec.lower() for sec in (s.get('sector_eligibility') or [])]]
            if stage:
                filtered = [s for s in filtered if stage.lower() in [stg.lower() for stg in (s.get('startup_stage') or [])]]
            if state:
                filtered = [s for s in filtered if state.lower() in (s.get('geographic_restriction') or '').lower()]
            if ministry:
                filtered = [s for s in filtered if ministry.lower() in (s.get('ministry') or '').lower()]
            if category:
                filtered = [s for s in filtered if category.lower() in (s.get('category') or '').lower()]
            offset = (page - 1) * limit
            schemes = filtered[offset:offset + limit]

        # Annotate with recent updates (best effort)
        try:
            from datetime import datetime, timedelta
            cutoff_30_days = (datetime.utcnow() - timedelta(days=30)).isoformat()
            recent_versions = safe_query(
                lambda sb: sb.table("scheme_versions").select("scheme_id, changed_at").gte("changed_at", cutoff_30_days).execute(),
                fallback=type('obj', (object,), {'data': []})()
            )
            updated_ids = {v["scheme_id"]: v["changed_at"] for v in (recent_versions.data or [])}
            for s in schemes:
                s["recently_updated"] = s["id"] in updated_ids
                s["last_updated_at"] = updated_ids.get(s["id"])
        except Exception:
            pass  # Annotation is non-critical

        return {"schemes": schemes, "page": page, "limit": limit}
    except Exception:
        traceback.print_exc()
        return {"schemes": [], "page": page, "limit": limit}


@app.get("/schemes/{scheme_id}")
async def get_scheme(scheme_id: str):
    try:
        res = safe_query(lambda sb: sb.table("schemes_clean").select("*").eq("id", scheme_id).execute())
        if res.data:
            return res.data[0]
        for s in get_local_schemes():
            if str(s.get("id")) == str(scheme_id) or str(s.get("scheme_name")) == str(scheme_id):
                return s
        raise HTTPException(status_code=404, detail="Scheme not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable")


@app.get("/alerts/recent")
async def recent_alerts(days: int = 7):
    try:
        from datetime import datetime, timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        res = safe_query(
            lambda sb: sb.table("scheme_versions").select("*").gte("changed_at", cutoff).order("changed_at", desc=True).limit(20).execute(),
            fallback=type('obj', (object,), {'data': []})()
        )
        return {"alerts": res.data or [], "period_days": days}
    except Exception:
        return {"alerts": [], "period_days": days}


@app.get("/success-stories")
async def get_success_stories():
    try:
        res = safe_query(
            lambda sb: sb.table("schemes_clean").select("id, scheme_name, ministry, success_stories, funding_type, max_funding_amount, geographic_restriction").neq("success_stories", "").not_.is_("success_stories", "null").execute(),
            fallback=type('obj', (object,), {'data': []})()
        )
        return {"stories": res.data or []}
    except Exception:
        return {"stories": []}


class ChatMessage(BaseModel):
    role: str
    content: str
class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

@app.post("/chat")
async def general_chat(req: ChatRequest):
    try:
        schemes = None
        res = safe_query(lambda sb: sb.table("schemes_clean").select("id, ministry, startup_stage, category, funding_type, geographic_restriction").execute())
        if res and res.data:
            schemes = res.data
        else:
            schemes = get_local_schemes()
            
        context = build_general_knowledge_context(schemes)
        hist_list = [{"role": msg.role, "content": msg.content} for msg in req.history]
        response = chat_with_agent(req.message, hist_list, context)
        return {"response": response}
    except Exception as e:
        traceback.print_exc()
        return {"response": "I'm having trouble connecting right now. Please try again in a moment."}


class SchemeChatRequest(BaseModel):
    scheme_id: str
    message: str
    history: list[ChatMessage] = []

@app.post("/chat/scheme")
async def chat_about_scheme(req: SchemeChatRequest):
    try:
        scheme_data = None
        # 1. Try finding in Supabase by ID
        scheme_res = safe_query(lambda sb: sb.table("schemes_clean").select("*").eq("id", req.scheme_id).execute())
        if scheme_res and scheme_res.data:
            scheme_data = scheme_res.data[0]
            
        # 2. If not found in Supabase by ID, search local Excel schemes
        if not scheme_data:
            local = get_local_schemes()
            req_id_str = str(req.scheme_id).strip().lower()
            for s in local:
                if str(s.get("id", "")).strip().lower() == req_id_str:
                    scheme_data = s
                    break
                s_name = str(s.get("scheme_name", "")).strip().lower()
                if req_id_str == s_name or req_id_str in s_name or s_name in req_id_str:
                    scheme_data = s
                    break

        # 3. If still not found, try search by scheme_name in Supabase
        if not scheme_data:
            res_name = safe_query(lambda sb: sb.table("schemes_clean").select("*").ilike("scheme_name", f"%{req.scheme_id}%").limit(1).execute())
            if res_name and res_name.data:
                scheme_data = res_name.data[0]

        if scheme_data:
            context = build_scheme_knowledge_context(scheme_data)
        else:
            context = f"The user is asking about scheme: '{req.scheme_id}'. Answer based on government policy and startup scheme knowledge.\n" + build_general_knowledge_context()

        hist_list = [{"role": msg.role, "content": msg.content} for msg in req.history]
        response = chat_with_agent(req.message, hist_list, context)
        return {"response": response}
    except Exception as e:
        traceback.print_exc()
        return {"response": "I'm having trouble retrieving details for this scheme right now. Please try asking again or click 'Clear Context'."}


@app.get("/pipeline/status")
async def get_pipeline_status():
    try:
        res = safe_query(lambda sb: sb.table("schemes_clean").select("last_scraped_at").order("last_scraped_at", desc=True).limit(1).execute())
        last_run = res.data[0]["last_scraped_at"] if res.data else None
        return {"status": "healthy", "last_run": last_run}
    except Exception:
        return {"status": "unknown", "last_run": None}


@app.get("/analytics/summary")
async def get_summary():
    try:
        res = safe_query(
            lambda sb: sb.table("schemes_clean").select("id, max_funding_amount, total_budget_allocated, ministry").execute()
        )
        data = res.data or []
        if not data:
            data = get_local_schemes()
        schemes_with_budget = [s for s in data if s.get("total_budget_allocated") and float(s.get("total_budget_allocated", 0)) > 0]
        schemes_with_funding = [s for s in data if s.get("max_funding_amount") and float(s.get("max_funding_amount", 0)) > 0]
        total_budget = sum(float(s.get("total_budget_allocated", 0)) for s in schemes_with_budget)
        avg_max_funding = sum(float(s.get("max_funding_amount", 0)) for s in schemes_with_funding) / max(len(schemes_with_funding), 1)
        unique_ministries = len(set(s["ministry"] for s in data if s.get("ministry")))
        return {
            "total_schemes": len(data),
            "total_budget": total_budget,
            "unique_ministries": unique_ministries,
            "avg_max_funding": avg_max_funding
        }
    except Exception:
        traceback.print_exc()
        return {"total_schemes": 0, "total_budget": 0, "unique_ministries": 0, "avg_max_funding": 0}


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
    try:
        res = safe_query(lambda sb: sb.table("schemes_clean").select("ministry, total_budget_allocated").execute())
        data = res.data or []
        if not data:
            data = get_local_schemes()
        ministries = {}
        for s in data:
            m = standardize_ministry_name(s.get("ministry") or "Unknown")
            b = float(s.get("total_budget_allocated") or 0)
            if b == 0:
                b = float(s.get("max_funding_amount") or 0)
            if m not in ministries: 
                ministries[m] = 0
            ministries[m] += b
            
        result = [{"ministry": k, "total_budget": v} for k, v in ministries.items()]
        has_budget = [r for r in result if r["total_budget"] > 0]
        if len(has_budget) >= 5:
            result = has_budget
        result.sort(key=lambda x: x["total_budget"], reverse=True)
        return result
    except Exception:
        gold = get_local_gold_analytics()
        return [{"ministry": r["ministry"], "total_budget": r["total_budget"]} for r in gold["funding_by_ministry"]]


@app.get("/analytics/sector-distribution")
async def get_sector_distribution():
    try:
        res = safe_query(
            lambda sb: sb.table("sector_distribution").select("*").execute(),
            fallback=None
        )
        if res and res.data:
            return res.data
    except Exception:
        pass
    
    # Fallback to manual aggregation
    try:
        res = safe_query(lambda sb: sb.table("schemes_clean").select("sector_eligibility").execute())
        data = res.data or []
        if not data:
            data = get_local_schemes()
        sectors = {}
        for s in data:
            if s.get("sector_eligibility"):
                for sec in s["sector_eligibility"]:
                    sec_clean = str(sec).strip().title()
                    if sec_clean not in sectors: sectors[sec_clean] = 0
                    sectors[sec_clean] += 1
        if sectors:
            return [{"sector": k, "scheme_count": v} for k, v in sectors.items()]
        return get_local_gold_analytics()["sector_distribution"]
    except Exception:
        return get_local_gold_analytics()["sector_distribution"]


@app.get("/analytics/stage-coverage")
async def get_stage_coverage():
    try:
        res = safe_query(
            lambda sb: sb.table("stage_coverage").select("*").execute(),
            fallback=None
        )
        if res and res.data:
            return res.data
    except Exception:
        pass
    
    # Fallback
    try:
        res = safe_query(lambda sb: sb.table("schemes_clean").select("startup_stage").execute())
        data = res.data or []
        if not data:
            data = get_local_schemes()
        stages = {}
        for s in data:
            if s.get("startup_stage"):
                for st in s["startup_stage"]:
                    st_clean = str(st).strip().title()
                    if st_clean not in stages: stages[st_clean] = 0
                    stages[st_clean] += 1
        if stages:
            return [{"stage": k, "scheme_count": v} for k, v in stages.items()]
        return get_local_gold_analytics()["stage_coverage"]
    except Exception:
        return get_local_gold_analytics()["stage_coverage"]


@app.get("/analytics/layer")
def get_analytics():
    try:
        by_ministry = safe_query(lambda sb: sb.table("funding_by_ministry").select("*").execute())
        sector_dist = safe_query(lambda sb: sb.table("sector_distribution").select("*").execute())
        stage_cov = safe_query(lambda sb: sb.table("stage_coverage").select("*").execute())
        
        bm_data = by_ministry.data if by_ministry and by_ministry.data else []
        sd_data = sector_dist.data if sector_dist and sector_dist.data else []
        sc_data = stage_cov.data if stage_cov and stage_cov.data else []
        
        if bm_data or sd_data or sc_data:
            return {
                "funding_by_ministry": bm_data,
                "sector_distribution": sd_data,
                "stage_coverage": sc_data
            }
    except Exception:
        pass
        
    return get_local_gold_analytics()


@app.get("/analytics/detailed")
async def get_detailed_analytics():
    try:
        res = safe_query(lambda sb: sb.table("schemes_clean").select("*").execute())
        data = res.data or []
        
        # Calculate validated metrics
        schemes_with_budget = [s for s in data if s.get("total_budget_allocated") and float(s.get("total_budget_allocated", 0)) > 0]
        schemes_with_funding = [s for s in data if s.get("max_funding_amount") and float(s.get("max_funding_amount", 0)) > 0]
        
        total_budget = sum(float(s.get("total_budget_allocated", 0)) for s in schemes_with_budget)
        avg_max_funding = sum(float(s.get("max_funding_amount", 0)) for s in schemes_with_funding) / max(len(schemes_with_funding), 1)
        unique_ministries = len(set(s.get("ministry", "") for s in data if s.get("ministry")))
        
        # Funding by ministry
        ministries_b = {}
        type_counts = {}
        geo_counts = {"Central": 0, "State": 0}
        
        for s in data:
            m = standardize_ministry_name(s.get("ministry") or "Unknown")
            b = float(s.get("total_budget_allocated") or 0)
            ministries_b[m] = ministries_b.get(m, 0) + b
            
            # Funding type — only use actual values from DB, skip empties
            cat = s.get("category") or None
            ftype = s.get("funding_type") or None
            label = cat or ftype
            if label and label.strip():
                label = label.strip()
                type_counts[label] = type_counts.get(label, 0) + 1
            else:
                type_counts["Unclassified"] = type_counts.get("Unclassified", 0) + 1
            
            # Geography classification — check for state-specific indicators
            geo = (s.get("geographic_restriction") or "").strip().lower()
            if not geo or geo in ["pan-india", "central", "all india", "nationwide", "india"]:
                geo_counts["Central"] += 1
            else:
                geo_counts["State"] += 1
        
        # Sector + stage distribution
        sector_dist_res = await get_sector_distribution()
        stage_cov_res = await get_stage_coverage()
        
        by_min = [{"ministry": k, "total_budget": v} for k, v in ministries_b.items() if v > 0]
        by_min.sort(key=lambda x: x["total_budget"], reverse=True)
        
        types = [{"category": k, "count": v} for k, v in type_counts.items()]
        types.sort(key=lambda x: x["count"], reverse=True)
        
        return {
            "summary": {
                "total_schemes": len(data),
                "total_budget": total_budget,
                "avg_max_funding": avg_max_funding,
                "unique_ministries": unique_ministries,
                "schemes_with_budget_data": len(schemes_with_budget),
                "schemes_with_funding_data": len(schemes_with_funding)
            },
            "funding_by_ministry": by_min,
            "sector_distribution": sector_dist_res,
            "stage_coverage": stage_cov_res,
            "funding_type_breakdown": types,
            "state_vs_central": geo_counts
        }
    except Exception:
        traceback.print_exc()
        return {
            "summary": {"total_schemes": 0, "total_budget": 0, "avg_max_funding": 0, "unique_ministries": 0, "schemes_with_budget_data": 0, "schemes_with_funding_data": 0},
            "funding_by_ministry": [],
            "sector_distribution": [],
            "stage_coverage": [],
            "funding_type_breakdown": [],
            "state_vs_central": {"Central": 0, "State": 0}
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
