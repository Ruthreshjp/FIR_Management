import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Env checks ──
groq_key = os.getenv("GROQ_API_KEY")
mongo_uri = os.getenv("MONGODB_URI")

st.set_page_config(
    page_title="AutoFIR — AI-Powered FIR Generator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load global CSS (single source in app/styles.py) ──
from app.utils.helpers import load_custom_css
load_custom_css()

# ── Show env warnings inside app instead of blocking ──
_env_ok = True
if not groq_key:
    st.error("**GROQ_API_KEY** is not set. Add it to your `.env` file to enable AI features.")
    _env_ok = False
if not mongo_uri:
    st.warning("**MONGODB_URI** is not set. Database features (save / history / analytics) are disabled.")

# ── Import pages ──
from app.pages import dashboard, new_fir, fir_history, analytics, ipc_browser, evaluation, profile

# ── Sidebar ──
with st.sidebar:
    # Brand block — matches reference design
    st.markdown("""
    <div class="brand-block">
        <div class="brand-mark">
            <div class="brand-seal">FIR</div>
            <div>
                <div class="brand-title">AutoFIR</div>
                <span class="brand-sub">Case Drafting System</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    page_map = {
        "📊  Dashboard":    "Dashboard",
        "📝  New Complaint": "New FIR",
        "📁  Case History": "FIR History",
        "📈  Analytics":    "Analytics",
        "⚖️  IPC & BNS Browser": "IPC Browser",
        "📐  Evaluation":   "Evaluation",
        "👤  Profile & Station": "Profile",
    }

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Dashboard"

    st.markdown('<div class="nav-label">SYSTEM</div>', unsafe_allow_html=True)
    
    for label, page_id in page_map.items():
        if st.button(label, key=f"nav_{page_id}", use_container_width=True):
            st.session_state["current_page"] = page_id
            st.rerun()

    # Dynamically inject CSS for the active button based on nth-of-type
    active_idx = list(page_map.values()).index(st.session_state["current_page"]) + 1
    st.markdown(f"""
    <style>
    [data-testid="stSidebar"] div.stButton:nth-of-type({active_idx}) > button {{
        background: rgba(168,54,43,0.16) !important;
        color: var(--paper) !important;
        box-shadow: inset 3px 0 0 0 var(--seal) !important;
        border-radius: 0 6px 6px 0 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.divider()

    # Sidebar footer — system status
    groq_dot = "status-dot" if groq_key else "status-dot warn"
    groq_label = "Groq · connected" if groq_key else "Groq · not configured"
    mongo_dot = "status-dot" if mongo_uri else "status-dot warn"
    mongo_label = "MongoDB · synced" if mongo_uri else "MongoDB · offline"

    st.markdown(f"""
    <div class="sidebar-foot">
        <div><span class="{groq_dot}"></span>{groq_label}</div>
        <div style="margin-top:4px;"><span class="{mongo_dot}"></span>{mongo_label}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Route ──
page = st.session_state["current_page"]
if page == "Dashboard":
    dashboard.show()
elif page == "New FIR":
    new_fir.show()
elif page == "FIR History":
    fir_history.show()
elif page == "Analytics":
    analytics.show()
elif page == "IPC Browser":
    ipc_browser.show()
elif page == "Evaluation":
    evaluation.show()
elif page == "Profile":
    profile.show()
