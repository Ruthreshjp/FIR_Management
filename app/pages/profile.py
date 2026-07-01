import streamlit as st
import datetime

def show():
    # ── Page Header ──
    st.markdown("""
    <div class="page-eyebrow">SETTINGS & CONTEXT</div>
    <div class="page-title">Profile & Station</div>
    <hr class="page-header-rule">
    """, unsafe_allow_html=True)

    # ── Initialize Defaults ──
    if "officer_name" not in st.session_state:
        st.session_state.officer_name = "Inspector R. Kumar"
    if "officer_rank" not in st.session_state:
        st.session_state.officer_rank = "Station House Officer"
    if "officer_badge" not in st.session_state:
        st.session_state.officer_badge = "TN-POL-4921"
    
    if "profile_station" not in st.session_state:
        st.session_state.profile_station = "Central Station"
    if "profile_district" not in st.session_state:
        st.session_state.profile_district = "Metropolis"
    if "profile_state" not in st.session_state:
        st.session_state.profile_state = "State"

    # ── Forms ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-head"><h3>Officer Details</h3></div>', unsafe_allow_html=True)
        with st.form("officer_form"):
            o_name = st.text_input("Full Name", value=st.session_state.officer_name)
            o_rank = st.text_input("Rank / Designation", value=st.session_state.officer_rank)
            o_badge = st.text_input("Badge / ID Number", value=st.session_state.officer_badge)
            if st.form_submit_button("Update Officer Profile"):
                st.session_state.officer_name = o_name
                st.session_state.officer_rank = o_rank
                st.session_state.officer_badge = o_badge
                st.success("Officer profile updated.")

    with col2:
        st.markdown('<div class="section-head"><h3>Station Details</h3></div>', unsafe_allow_html=True)
        with st.form("station_form"):
            s_name = st.text_input("Station Name", value=st.session_state.profile_station)
            s_dist = st.text_input("District", value=st.session_state.profile_district)
            s_state = st.text_input("State", value=st.session_state.profile_state)
            if st.form_submit_button("Update Station Profile"):
                st.session_state.profile_station = s_name
                st.session_state.profile_district = s_dist
                st.session_state.profile_state = s_state
                st.success("Station details updated. Future FIRs will use these details.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Performance Overview ──
    st.markdown('<div class="section-head"><h3>Performance Overview</h3></div>', unsafe_allow_html=True)
    
    # Safely load DB stats
    total, pending, closed = 0, 0, 0
    try:
        from app.database.connection import Database
        db = Database()
        firs = db.get_all_firs()
        total = len(firs)
        closed = sum(1 for f in firs if f.get("status") in ("Solved", "Closed"))
        pending = total - closed
    except Exception:
        pass

    st.markdown(f"""
    <div class="stat-strip">
        <div class="stat-card">
            <div class="stat-label">Total FIRs Filed</div>
            <div class="stat-value">{total}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Cases Pending</div>
            <div class="stat-value">{pending}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Cases Solved / Closed</div>
            <div class="stat-value">{closed}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Recognitions</div>
            <div class="stat-value">1</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Personnel Roster ──
    st.markdown('<div class="section-head"><h3>Personnel Roster</h3></div>', unsafe_allow_html=True)
    
    try:
        from app.database.connection import Database
        db = Database()
        
        # We use session state to track edits if DB is offline.
        if "personnel_data" not in st.session_state:
            st.session_state.personnel_data = [
                {"Name": st.session_state.officer_name, "Rank": st.session_state.officer_rank, "Badge No": st.session_state.officer_badge, "Contact": "9876543210"},
                {"Name": "A. Sharma", "Rank": "Sub-Inspector", "Badge No": "TN-POL-1102", "Contact": "9876543211"},
                {"Name": "V. Iyer", "Rank": "Constable", "Badge No": "TN-POL-3490", "Contact": "9876543212"},
                {"Name": "S. Reddy", "Rank": "Constable", "Badge No": "TN-POL-3491", "Contact": "9876543213"},
            ]

        edited_df = st.data_editor(
            st.session_state.personnel_data,
            num_rows="dynamic",
            use_container_width=True,
            key="personnel_editor"
        )
        st.session_state.personnel_data = edited_df

        if db.client is None:
            st.info("Database offline. Personnel changes are stored locally in session and will reset on reload.")
    except Exception as e:
        st.warning(f"Failed to load roster: {e}")
