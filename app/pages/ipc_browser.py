import streamlit as st
import json
import os


def show():
    # ── Page Header ──
    st.markdown("""
    <div class="page-eyebrow">LEGAL REFERENCE</div>
    <div class="page-title">IPC & BNS Browser</div>
    <hr class="page-header-rule">
    """, unsafe_allow_html=True)
    
    # ── Toggle ──
    view_mode = st.radio(
        "Select Legal Code", 
        ["BNS (Bharatiya Nyaya Sanhita - 2023)", "IPC (Indian Penal Code - 1860)"], 
        horizontal=True
    )
    is_bns = view_mode.startswith("BNS")

    dataset = _load_dataset(is_bns)
    if not dataset:
        st.error("Legal dataset not found. Please ensure the data files are present.")
        return

    # ── Search ──
    query = st.text_input("Search by offense, section number, or keyword", placeholder="e.g. theft, 420, fraud...")

    if query:
        q = query.lower()
        filtered = [
            item for item in dataset
            if q in item.get("offense", "").lower()
            or q in item.get("section_number", "").lower()
            or q in item.get("description", "").lower()
        ]
    else:
        filtered = dataset

    st.markdown(f'<p class="text-muted">{len(filtered)} of {len(dataset)} sections</p>', unsafe_allow_html=True)

    # ── Results as styled cards ──
    act_name = "BNS" if is_bns else "IPC"
    act_class = act_name.lower()

    for item in filtered:  # Loop through all filtered items
        section_number = item.get("section_number", "—")
        offense = item.get("offense", "—")
        desc = item.get("description", "—")

        with st.expander(f"{act_name} {section_number}  ·  {offense}"):
            # Section tags
            st.markdown(f"""
            <div style="display:flex; gap:8px; margin-bottom:12px;">
                <span class="act-chip {act_class}">{act_name}</span>
                <span class="sec-num">Section {section_number}</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"**Description:** {desc}")


def _load_dataset(is_bns: bool):
    filename = "bns_sections.json" if is_bns else "ipc_sections.json"
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        # Convert schema to expected UI schema
        dataset = []
        for item in raw_data:
            offense_val = item.get("section_name") or item.get("offense")
            dataset.append({
                "offense": str(offense_val) if offense_val else "Unknown",
                "section_number": str(item.get("section_number") or "—"),
                "description": str(item.get("description") or "—"),
            })
        return dataset
    except Exception:
        return []
