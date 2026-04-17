import streamlit as st
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

def render_login():
    st.markdown("<h1 style='text-align: center;'>Welcome to Gov-Dash</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Your intelligent startup policy engine.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login")
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Log In", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    
                    # Fetch profile
                    profile_res = supabase.table("startup_profiles").select("*").eq("id", res.user.id).execute()
                    if profile_res.data:
                        st.session_state.profile = profile_res.data[0]
                    else:
                        st.session_state.profile = None
                        
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
                    
        with tab2:
            st.subheader("Create your Startup Profile")
            st.markdown("We'll use this to build **zero-click recommendations** for your dashboard.")
            signup_email = st.text_input("Email", key="signup_email")
            signup_pwd = st.text_input("Password", type="password", key="signup_password")
            
            company_name = st.text_input("Company/Project Name")
            sector = st.selectbox("Primary Sector", ["deeptech", "agritech", "biotech", "defense", "saas", "fintech", "edtech", "hardware"])
            stage = st.selectbox("Startup Stage", ["idea", "prototype", "early_revenue", "scale_up"])
            state = st.selectbox("State / Location", ["Pan-India", "Karnataka", "Kerala", "Maharashtra", "Odisha", "Rajasthan", "Delhi"])
            
            if st.button("Create Account", use_container_width=True):
                try:
                    res = supabase.auth.sign_up({"email": signup_email, "password": signup_pwd})
                    if res.user:
                        st.session_state.user = res.user
                        
                        profile_data = {
                            "id": res.user.id,
                            "email": signup_email,
                            "company_name": company_name,
                            "sector": sector,
                            "stage": stage,
                            "geographic_restriction": state
                        }
                        
                        supabase.table("startup_profiles").insert(profile_data).execute()
                        st.session_state.profile = profile_data
                        
                        st.success("Account successfully created!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Signup failed: {e}")
