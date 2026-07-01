import streamlit as st
import re


def show():
    # ── Page Header ──
    st.markdown("""
    <div class="page-eyebrow">RECORDS</div>
    <div class="page-title">Case History</div>
    <hr class="page-header-rule">
    """, unsafe_allow_html=True)

    firs = _load_firs()
    if firs is None:
        return
    if not firs:
        st.info("No FIR records in the database yet.")
        return

    # ── Search / Filter Bar ──
    col_search, col_filter = st.columns([3, 1])
    with col_search:
        query = st.text_input("Search", placeholder="Search by name or FIR number...", label_visibility="collapsed")
    with col_filter:
        status_opt = st.selectbox("Status", ["All", "Draft", "Under Investigation", "Solved", "Closed"], label_visibility="collapsed")

    # Filter
    results = []
    for f in firs:
        if status_opt != "All" and f.get("status") != status_opt:
            continue
        if query:
            q = query.lower()
            if q not in f.get("fir_number", "").lower() and q not in f.get("complainant_name", "").lower():
                continue
        results.append(f)

    st.markdown(f'<p class="text-muted">{len(results)} of {len(firs)} records</p>', unsafe_allow_html=True)

    # ── Docket Table Header ──
    st.markdown("""
    <div class="docket">
        <div class="docket-row head">
            <span>Case No.</span>
            <span>Complainant / Details</span>
            <span>Sections</span>
            <span>Filed</span>
            <span>Status</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Records as expanders styled like docket rows ──
    for f in results:
        fir_num = f.get("fir_number", "—")
        status = f.get("status", "Draft")
        complainant = f.get("complainant_name", "—")
        station = f.get("police_station", "—")
        created = str(f.get("created_at", "—"))[:10]

        # Status pill class
        pill_class = {
            "Draft": "draft",
            "Under Investigation": "review",
            "Solved": "filed",
            "Closed": "closed",
        }.get(status, "review")

        # Section tags
        sections_raw = f.get("sections", "")
        tags_html = _build_section_tags(sections_raw)

        # Summary line for expander
        with st.expander(f"{fir_num}  ·  {complainant}  ·  {status}"):
            # Row preview in docket style
            st.markdown(f"""
            <div style="display:flex; gap:20px; align-items:center; margin-bottom:16px; padding-bottom:14px; border-bottom:1px solid var(--line);">
                <span class="case-no">{fir_num}</span>
                <div class="case-info" style="flex:1;">
                    <div class="case-title">{complainant}</div>
                    <div class="case-sub">{station} · {created}</div>
                </div>
                <div class="act-tags">{tags_html}</div>
                <span class="pill {pill_class}">{status}</span>
            </div>
            """, unsafe_allow_html=True)

            tab_info, tab_draft, tab_manage = st.tabs(["Details", "Draft", "Manage"])

            with tab_info:
                c1, c2 = st.columns(2)
                c1.markdown(f"**Complainant:** {f.get('complainant_name')}")
                c1.markdown(f"**Email:** {f.get('complainant_email')}")
                c1.markdown(f"**Police Station:** {f.get('police_station')}")
                c2.markdown(f"**District:** {f.get('district')}")
                c2.markdown(f"**Status:** {status}")
                c2.markdown(f"**Date:** {created}")
                st.divider()
                st.markdown("**Extracted Facts**")
                st.markdown(f.get("facts", "_No facts recorded._"))
                st.markdown("**Legal Sections**")
                st.markdown(f.get("sections", "_No sections recorded._"))

            with tab_draft:
                st.markdown(f.get("draft", "_No draft available._"))

            with tab_manage:
                try:
                    from app.database.connection import Database
                    db = Database()
                    new_status = st.selectbox(
                        "Update status",
                        ["Draft", "Under Investigation", "Solved", "Closed"],
                        index=["Draft", "Under Investigation", "Solved", "Closed"].index(status),
                        key=f"st_{f['_id']}"
                    )
                    if st.button("Save", key=f"sv_{f['_id']}"):
                        db.update_fir(fir_num, {"status": new_status})
                        st.success("Updated.")
                        st.rerun()
                except Exception:
                    st.warning("Database unavailable for updates.")

                st.divider()
                try:
                    from app.pdf.generator import create_fir_pdf
                    pdf_bytes = create_fir_pdf(f)
                    st.download_button("⬇ Download PDF", pdf_bytes, f"{fir_num.replace('/', '_')}.pdf", "application/pdf", key=f"dl_{f['_id']}")
                except Exception:
                    st.error("PDF generation failed.")


def _build_section_tags(sections_text: str) -> str:
    """Parse sections text and return HTML tags."""
    if not sections_text:
        return ""
    tags = []
    for match in re.finditer(r'(BNS|IPC|POCSO)\s*(?:§|Section\s*)?\s*(\d+)', sections_text, re.IGNORECASE):
        act = match.group(1).upper()
        num = match.group(2)
        css_class = act.lower()
        tags.append(f'<span class="tag {css_class}">{act} {num}</span>')
    seen = set()
    unique = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return "".join(unique[:4])


def _load_firs():
    try:
        from app.database.connection import Database
        db = Database()
        return db.get_all_firs()
    except Exception as e:
        st.warning(f"Database unavailable: {e}")
        return None
