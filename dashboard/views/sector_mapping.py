import streamlit as st
import pandas as pd
import requests

def render():
    st.header("Sector Mapping")
    try:
        res = requests.get("http://localhost:8000/analytics/layer").json()
        if "sector_distribution" in res and res["sector_distribution"]:
            df = pd.DataFrame(res["sector_distribution"])
            chart_df = df.groupby("sector")["scheme_count"].sum().sort_values(ascending=False).head(15)
            st.subheader("Top Sectors by Scheme Count")
            st.bar_chart(chart_df)
            with st.expander("View Detailed Table"):
                st.dataframe(df)
        elif "fallback_aggregated" in res:
            df = pd.DataFrame(res["data"])
            if not df.empty and 'sector_eligibility' in df.columns:
                sectors = []
                for idx, row in df.iterrows():
                    if row['sector_eligibility']:
                        sectors.extend(row['sector_eligibility'])
                if sectors:
                    sec_df = pd.DataFrame(sectors, columns=['sector']).value_counts().reset_index(name='count')
                    st.bar_chart(sec_df.set_index('sector'))
                else:
                    st.info("No sector data available.")
        else:
            st.info("No sector distribution data.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
