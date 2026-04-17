import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from scrapers.base_scraper import supabase

def run_change_detection():
    # Fetch all clean schemes
    res = supabase.table("schemes_clean").select("*").execute()
    schemes = res.data
    
    # Ideally, we query latest from scheme_versions to get the last hash, or we just compare existing fields
    # Here is a naive MVP approach based on content_hash changes
    for schema in schemes:
        # Check if there is an existing version for this scheme
        versions_res = supabase.table("scheme_versions").select("*").eq("scheme_id", schema["id"]).order("changed_at", desc=True).limit(1).execute()
        
        should_insert = False
        old_values = {}
        
        if not versions_res.data:
            # First time seeing this scheme
            should_insert = True
        else:
            last_version = versions_res.data[0]
            # Since content hash is updated in the silver layer, we compare the current schema against last version 'new_values'
            if last_version.get("new_values", {}).get("content_hash") != schema.get("content_hash"):
                should_insert = True
                old_values = last_version.get("new_values", {})
                
        if should_insert:
            changed_fields = []
            if old_values:
                for k, v in schema.items():
                    if old_values.get(k) != v:
                        changed_fields.append(k)
            else:
                changed_fields = ["all"]
                
            try:
                supabase.table("scheme_versions").insert({
                    "scheme_id": schema["id"],
                    "scheme_name": schema["scheme_name"],
                    "ministry": schema["ministry"],
                    "changed_fields": changed_fields,
                    "old_values": old_values,
                    "new_values": schema
                }).execute()
                print(f"Change detected and logged for {schema['scheme_name']}")
            except Exception as e:
                print(f"Failed to log change detection for {schema['scheme_name']}: {e}")

if __name__ == "__main__":
    run_change_detection()
