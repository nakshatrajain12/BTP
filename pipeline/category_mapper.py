CATEGORY_MAP = {
    "grant": "Funding", "equity": "Funding", "seed": "Funding", "matching grant": "Funding", "funding": "Funding", "fund": "Funding", "financial": "Funding", "money": "Funding",
    "incubation": "Incubation", "accelerator": "Incubation", "mentorship": "Incubation", "co-working": "Incubation", "infrastructure": "Incubation", "program": "Incubation", "support": "Incubation",
    "tax": "Tax Benefit", "exemption": "Tax Benefit", "rebate": "Tax Benefit", "holiday": "Tax Benefit", "gst": "Tax Benefit", "waiver": "Tax Benefit", 
    "loan": "Credit Support", "credit": "Credit Support", "guarantee": "Credit Support", "debt": "Credit Support", "lending": "Credit Support", "collateral": "Credit Support", "interest": "Credit Support"
}
VALID_CATEGORIES = ["Funding", "Incubation", "Tax Benefit", "Credit Support"]

def normalize_category(category: str, funding_type: str = "") -> str:
    """Maps freeform category/funding_type to a canonical Category"""
    s = str(category or "").lower().strip()
    f = str(funding_type or "").lower().strip()
    
    # Try mapping category first
    for k, v in CATEGORY_MAP.items():
        if k in s:
            return v
            
    # Fallback to mapping funding_type
    for k, v in CATEGORY_MAP.items():
        if k in f:
            return v
            
    # Default fallback
    return "Funding"
