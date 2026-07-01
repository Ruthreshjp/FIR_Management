import streamlit as st
from datetime import datetime


def show():
    # ── Page Header (eyebrow + serif title) ──
    today = datetime.now().strftime("%d %b %Y").upper()
    st.markdown(f"""
    <div class="page-eyebrow">{today} · STATION DESK</div>
    <div class="page-title">Dashboard</div>
    <hr class="page-header-rule">
    """, unsafe_allow_html=True)

    # Try loading data from MongoDB
    firs = _load_firs()

    # ── Stat Strip ──
    total = len(firs)
    draft = sum(1 for f in firs if f.get("status") == "Draft")
    investigating = sum(1 for f in firs if f.get("status") == "Under Investigation")
    resolved = sum(1 for f in firs if f.get("status") in ("Solved", "Closed"))

    st.markdown(f"""
    <div class="stat-strip">
        <div class="stat-card">
            <div class="stat-label">Total Cases</div>
            <div class="stat-value">{total}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Drafts</div>
            <div class="stat-value">{draft}
                {'<span class="stat-delta warn">needs review</span>' if draft > 0 else ''}
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Under Investigation</div>
            <div class="stat-value">{investigating}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Resolved / Closed</div>
            <div class="stat-value">{resolved}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not firs:
        # ── Empty State ──
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; background:var(--white); border:1px solid var(--line); border-radius:8px; margin-top:20px;">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--slate-light)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="margin-bottom:16px;">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="9" y1="15" x2="15" y2="15"></line>
            </svg>
            <h3 style="font-family:var(--serif); color:var(--ink); font-size:18px; margin-bottom:8px;">No FIRs yet</h3>
            <p style="font-family:var(--sans); color:var(--slate); font-size:14px; margin-bottom:20px;">Cases will appear here once a complaint is drafted.</p>
        </div>
        """, unsafe_allow_html=True)
        # Action button to navigate
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("+ New Complaint", use_container_width=True):
                st.session_state["current_page"] = "New FIR"
                st.rerun()
        return

    # ── Recent Case Docket ──
    st.markdown("""
    <div class="section-head">
        <h3>Recent Case Docket</h3>
        <span class="see-all">View full history <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -2px; margin-left: 2px;"><path d="m9 18 6-6-6-6"/></svg></span>
    </div>
    """, unsafe_allow_html=True)

    rows_html = []
    for f in firs[:10]:
        fir_num = f.get("fir_number", "—")
        complainant = f.get("complainant_name", "—")
        station = f.get("police_station", "—")
        status = f.get("status", "Draft")
        created = str(f.get("created_at", "—"))[:10]

        # Sections tags
        sections_raw = f.get("sections", "")
        tags_html = _build_section_tags(sections_raw)

        # Status pill
        pill_class = {
            "Draft": "draft",
            "Under Investigation": "review",
            "Solved": "filed",
            "Closed": "closed",
        }.get(status, "review")

        rows_html.append(f"""
        <div class="docket-row">
            <span class="case-no">{fir_num}</span>
            <div class="case-info">
                <div class="case-title">{complainant}</div>
                <div class="case-sub">{station} · {created}</div>
            </div>
            <div class="act-tags">{tags_html}</div>
            <span class="timestamp">{created}</span>
            <span class="pill {pill_class}">{status}</span>
        </div>
        """)

    docket_html = f"""
    <div class="docket">
        <div class="docket-row head">
            <span>Case No.</span>
            <span>Complainant / Details</span>
            <span>Sections</span>
            <span>Filed</span>
            <span>Status</span>
        </div>
        {''.join(rows_html)}
    </div>
    """
    st.markdown(docket_html, unsafe_allow_html=True)

    # ── Watermark ──
    st.markdown(
        '<div class="watermark">AutoFIR · Generated drafts require officer verification before filing</div>',
        unsafe_allow_html=True,
    )


def _build_section_tags(sections_text: str) -> str:
    """Parse sections text and return HTML tags for BNS/IPC/POCSO references."""
    if not sections_text:
        return ""

    import re
    tags = []
    # Look for patterns like "BNS 303", "IPC 379", "POCSO 12", "Section 303", etc.
    for match in re.finditer(r'(BNS|IPC|POCSO)\s*(?:§|Section\s*)?\s*(\d+)', sections_text, re.IGNORECASE):
        act = match.group(1).upper()
        num = match.group(2)
        css_class = act.lower()
        tags.append(f'<span class="tag {css_class}">{act} {num}</span>')

    # De-duplicate while preserving order
    seen = set()
    unique = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return "".join(unique[:4])  # max 4 tags per row


def _load_firs():
    """Safely attempt to load FIRs from the database."""
    try:
        from app.database.connection import Database
        db = Database()
        return db.get_all_firs()
    except Exception as e:
        return []
