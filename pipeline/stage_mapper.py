STAGE_MAP = {
    "idea": "Idea", "ideation": "Idea", "concept": "Idea", "pre-seed": "Idea", "seed": "Idea",
    "prototype": "Prototype", "mvp": "Prototype", "poc": "Prototype", "proof of concept": "Prototype", "development": "Prototype",
    "early revenue": "Early Revenue", "revenue": "Early Revenue", "validation": "Early Revenue", "early traction": "Early Revenue", "commercialization": "Early Revenue", "early-stage": "Early Revenue",
    "scale-up": "Scale-up", "scaling": "Scale-up", "growth": "Scale-up", "expansion": "Scale-up", "series a": "Scale-up", "late stage": "Scale-up"
}
VALID_STAGES = ["Idea", "Prototype", "Early Revenue", "Scale-up"]

def normalize_stage(stage: str) -> str:
    """Takes a raw stage string and returns a canonical Stage"""
    if not stage:
        return "Idea" # Default to Idea if empty
    s = stage.lower().strip()
    # Try exact match first
    if s in STAGE_MAP:
        return STAGE_MAP[s]
    # Try partial match
    for k, v in STAGE_MAP.items():
        if k in s:
            return v
    # If no match found, default to Idea
    return "Idea"

def normalize_stages(stages: list[str]) -> list[str]:
    """Takes a list of raw stages and returns a deduplicated list of canonical stages"""
    if not stages:
        return []
    normalized = set()
    for s in stages:
        if s:
            normalized.add(normalize_stage(s))
    return list(normalized)
