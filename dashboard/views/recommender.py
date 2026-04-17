import streamlit as st
import requests
import json

def render():
    st.header("✨ Zero-Click Recommender")
    st.write("We automatically matched the best schemes to your Startup Profile using Gemini AI.")
    
    if "profile" in st.session_state and st.session_state.profile:
        prof = st.session_state.profile
        st.info(f"**Your Profile:** {prof.get('stage').title()} Stage | {prof.get('sector').title()} Sector | {prof.get('geographic_restriction').title()}")
        
        sector = prof.get('sector')
        stage = prof.get('stage')
        state = prof.get('geographic_restriction')
    else:
        st.warning("No profile found. Please update your profile settings.")
        sector = "Deeptech"
        stage = "Idea"
        state = "Pan-India"
    
    with st.spinner("Analyzing schemes with Gemini AI..."):
        try:
            res = requests.post("http://localhost:8000/recommend", json={
                "sector": sector,
                "stage": stage,
                "state": state
            })
            
            if res.status_code == 200:
                recs = res.json().get("recommendations", [])
                if isinstance(recs, str):
                    try:
                        recs = json.loads(recs)
                    except:
                        pass
                        
                if not recs:
                    st.write("No matching schemes found right now. Check back later!")
                else:
                    for i, r in enumerate(recs):
                        name = r.get("name", "Unknown Scheme")
                        reason = r.get("reason", "No reason provided")
                        url = r.get("application_url", "#")
                        
                        st.subheader(f"{i+1}. {name}")
                        st.write(f"**Why it fits:** {reason}")
                        st.markdown(f"[Apply Here]({url})")
                        st.divider()
            else:
                st.error(f"Failed to get recommendations: {res.text}")
        except Exception as e:
            st.error(f"Error connecting to recommender API: {e}")
