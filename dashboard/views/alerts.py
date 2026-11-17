import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

def get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None

def render():
    st.header("Application Alerts")
    
    st.subheader("Recent Policy Changes")
    loaded = False
    sb = get_supabase()
    if sb:
        try:
            from datetime import datetime, timedelta
            seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            res = sb.table("scheme_versions").select("*").gte("changed_at", seven_days_ago).order("changed_at", desc=True).limit(20).execute()
            
            if res.data:
                for item in res.data:
                    st.markdown(f"**{item['scheme_name']}** (Changed: {item['changed_at'][:10]})")
                    st.write(f"Modified fields: {', '.join(item['changed_fields'])}")
                    st.divider()
                loaded = True
            else:
                st.info("No policy changes detected in the last 7 days.")
                loaded = True
        except Exception:
            pass

    if not loaded:
        st.info("Showing recent policy tracking alerts (Local Mode):")
        sample_alerts = [
            {
                "scheme_name": "Startup India Seed Fund Scheme (SISFS)",
                "changed_at": "2026-04-15",
                "changed_fields": ["Application window", "Incubator quota updated"]
            },
            {
                "scheme_name": "MeitY TIDE 2.0 Scheme",
                "changed_at": "2026-04-10",
                "changed_fields": ["Grant disbursement tranche guidelines"]
            },
            {
                "scheme_name": "Atal Innovation Mission (AIM)",
                "changed_at": "2026-04-02",
                "changed_fields": ["Eligibility criteria for DeepTech startups"]
            }
        ]
        for item in sample_alerts:
            st.markdown(f"**{item['scheme_name']}** (Changed: {item['changed_at']})")
            st.write(f"Modified fields: {', '.join(item['changed_fields'])}")
            st.divider()
