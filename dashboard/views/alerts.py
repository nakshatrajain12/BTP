import streamlit as st
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

def render():
    st.header("Application Alerts")
    
    st.subheader("Recent Policy Changes")
    try:
        from datetime import datetime, timedelta
        seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        
        # We need to query scheme_versions
        res = supabase.table("scheme_versions").select("*").gte("changed_at", seven_days_ago).order("changed_at", desc=True).limit(20).execute()
        
        if res.data:
            for item in res.data:
                st.markdown(f"**{item['scheme_name']}** (Changed: {item['changed_at'][:10]})")
                st.write(f"Modified fields: {', '.join(item['changed_fields'])}")
                st.divider()
        else:
            st.info("No policy changes detected in the last 7 days.")
            
    except Exception as e:
        st.error(f"Could not load alerts: {e}")
