import streamlit as st
import pandas as pd
import requests

def render():
    st.header("Funding Landscape")
    
    # Try getting from API
    try:
        res = requests.get("http://localhost:8000/analytics/layer").json()
        if "funding_by_ministry" in res:
            data = res["funding_by_ministry"]
            if data:
                df = pd.DataFrame(data)
                st.bar_chart(df.set_index("ministry")["total_budget"])
            else:
                st.info("No data yet in Gold Layer")
        elif "fallback_aggregated" in res:
            st.info("Showing raw fallback data because Gold Layer materialized views aren't populated.")
            df = pd.DataFrame(res["data"])
            if not df.empty:
                # Group by ministry
                ministry_df = df.groupby('ministry')['total_budget_allocated'].sum().reset_index()
                st.bar_chart(ministry_df.set_index('ministry'))
    except Exception as e:
        st.error(f"Error fetching data: {e}")
