import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests

from dashboard.views import funding_landscape, stage_coverage, sector_mapping, alerts, recommender, auth

st.set_page_config(page_title="Startup Policy Dashboard", layout="wide", page_icon="📊")

if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    auth.render_login()
else:
    st.sidebar.title("Navigation")
    st.sidebar.markdown(f"**Logged in as:**<br>{st.session_state.profile.get('company_name', 'Startup')}", unsafe_allow_html=True)
    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.session_state.profile = None
        st.rerun()
        
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Go to", ["Funding Landscape", "Stage Coverage", "Sector Mapping", "Application Alerts", "Scheme Recommender"])

    if page == "Funding Landscape":
        funding_landscape.render()
    elif page == "Stage Coverage":
        stage_coverage.render()
    elif page == "Sector Mapping":
        sector_mapping.render()
    elif page == "Application Alerts":
        alerts.render()
    elif page == "Scheme Recommender":
        recommender.render()
