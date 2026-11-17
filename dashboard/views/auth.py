import streamlit as st
import os
import json
from dotenv import load_dotenv

load_dotenv()

LOCAL_DB_FILE = os.path.join(os.path.dirname(__file__), "..", "local_users.json")

def load_local_users():
    if os.path.exists(LOCAL_DB_FILE):
        try:
            with open(LOCAL_DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_local_users(data):
    try:
        with open(LOCAL_DB_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

class MockUser:
    def __init__(self, id, email):
        self.id = id
        self.email = email

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
                if not email:
                    st.error("Please enter your email.")
                    return
                logged_in = False
                sb = get_supabase()
                if sb:
                    try:
                        res = sb.auth.sign_in_with_password({"email": email, "password": password})
                        if res and res.user:
                            st.session_state.user = res.user
                            profile_res = sb.table("startup_profiles").select("*").eq("id", res.user.id).execute()
                            if profile_res.data:
                                st.session_state.profile = profile_res.data[0]
                            else:
                                st.session_state.profile = {
                                    "company_name": email.split("@")[0],
                                    "email": email,
                                    "sector": "deeptech",
                                    "stage": "idea",
                                    "geographic_restriction": "Pan-India"
                                }
                            logged_in = True
                            st.rerun()
                    except Exception:
                        pass
                
                if not logged_in:
                    local_users = load_local_users()
                    if email in local_users:
                        user_info = local_users[email]
                        st.session_state.user = MockUser(id=email, email=email)
                        st.session_state.profile = user_info["profile"]
                        st.success("Logged in successfully (Local Mode)!")
                        st.rerun()
                    else:
                        profile_data = {
                            "id": email,
                            "email": email,
                            "company_name": email.split("@")[0].title() if "@" in email else "Founder",
                            "sector": "deeptech",
                            "stage": "idea",
                            "geographic_restriction": "Pan-India"
                        }
                        local_users[email] = {"password": password, "profile": profile_data}
                        save_local_users(local_users)
                        st.session_state.user = MockUser(id=email, email=email)
                        st.session_state.profile = profile_data
                        st.rerun()
                    
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
                if not signup_email:
                    st.error("Please enter an email.")
                    return
                
                profile_data = {
                    "id": signup_email,
                    "email": signup_email,
                    "company_name": company_name or "My Startup",
                    "sector": sector,
                    "stage": stage,
                    "geographic_restriction": state
                }
                
                created = False
                sb = get_supabase()
                if sb:
                    try:
                        res = sb.auth.sign_up({"email": signup_email, "password": signup_pwd})
                        if res and res.user:
                            profile_data["id"] = res.user.id
                            try:
                                sb.table("startup_profiles").insert(profile_data).execute()
                            except Exception:
                                pass
                            st.session_state.user = res.user
                            st.session_state.profile = profile_data
                            created = True
                            st.success("Account successfully created!")
                            st.rerun()
                    except Exception:
                        pass
                
                if not created:
                    local_users = load_local_users()
                    local_users[signup_email] = {
                        "password": signup_pwd,
                        "profile": profile_data
                    }
                    save_local_users(local_users)
                    
                    st.session_state.user = MockUser(id=signup_email, email=signup_email)
                    st.session_state.profile = profile_data
                    st.success("Account created successfully (Local Mode)!")
                    st.rerun()
