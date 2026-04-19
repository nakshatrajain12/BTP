from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import date, datetime

class SchemeRecord(BaseModel):
    scheme_name: str
    ministry: str
    launch_year: Optional[int] = None
    status: Optional[str] = None
    category: Optional[str] = None
    source_url: str
    funding_type: Optional[str] = None
    max_funding_amount: Optional[int] = None
    total_budget_allocated: Optional[int] = None
    startups_funded_count: Optional[int] = None
    sector_eligibility: Optional[List[str]] = []
    startup_stage: Optional[List[str]] = []
    dpiit_required: Optional[bool] = None
    geographic_restriction: Optional[str] = None
    application_portal: Optional[str] = None
    application_deadline: Optional[date] = None
    processing_timeline: Optional[str] = None
    required_documents: Optional[List[str]] = []
    success_stories: Optional[str] = None
    sector_distribution: Optional[Dict[str, Any]] = None
    nlp_summary: Optional[str] = None
    
    # Decision Intelligence Fields
    equity_or_grant: Optional[str] = None # "Equity", "Grant", "Loan", "Debt", "Mixed"
    disbursement_structure: Optional[str] = None 
    next_deadline: Optional[date] = None # Used for auto-alerting upcoming cycles
