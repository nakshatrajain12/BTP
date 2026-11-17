import streamlit as st
import pandas as pd
import requests

def render():
    st.header("Stage Coverage")
    try:
        res = requests.get("http://localhost:8000/analytics/layer").json()
        if "stage_coverage" in res and res["stage_coverage"]:
            df = pd.DataFrame(res["stage_coverage"])
            chart_df = df.groupby("stage")["scheme_count"].sum().sort_values(ascending=False).head(15)
            st.subheader("Scheme Distribution by Startup Stage")
            st.bar_chart(chart_df)
            with st.expander("View Detailed Table"):
                st.dataframe(df)
        elif "fallback_aggregated" in res:
            df = pd.DataFrame(res["data"])
            if not df.empty and 'startup_stage' in df.columns:
                stages = []
                for idx, row in df.iterrows():
                    if row['startup_stage']:
                        for stage in row['startup_stage']:
                            stages.append(stage)
                if stages:
                    stage_df = pd.DataFrame(stages, columns=['stage']).value_counts().reset_index(name='count')
                    st.bar_chart(stage_df.set_index('stage'))
                else:
                    st.info("No stage data available.")
        else:
            st.info("No stage coverage data.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")
