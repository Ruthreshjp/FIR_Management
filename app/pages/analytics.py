import streamlit as st
import plotly.graph_objects as go
from collections import Counter

# Plotly layout matching the warm paper palette
_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#5C6470", family="Inter"),
    margin=dict(t=30, b=30, l=30, r=30),
    colorway=["#A8362B", "#C75C4F", "#9C8049", "#3D6B4F", "#1B2B42", "#5C6470"],
)


def show():
    # ── Page Header ──
    st.markdown("""
    <div class="page-eyebrow">DATA INSIGHTS</div>
    <div class="page-title">Analytics</div>
    <hr class="page-header-rule">
    """, unsafe_allow_html=True)

    firs = _load_firs()
    if firs is None:
        return
    if not firs:
        st.info("No data available for analytics.")
        return

    # ── Row 1: Status donut + District bar ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-head"><h3>Case Status</h3></div>', unsafe_allow_html=True)

        status_counts = Counter(f.get("status", "Draft") for f in firs)
        fig = go.Figure(data=[go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            hole=0.5,
            textinfo="label+percent",
            textfont=dict(size=12, family="Inter"),
            marker=dict(colors=["#A8362B", "#9C8049", "#3D6B4F", "#C75C4F"]),
        )])
        fig.update_layout(**_LAYOUT, height=320, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-head"><h3>FIRs by District</h3></div>', unsafe_allow_html=True)

        district_counts = Counter(f.get("district", "Unknown") for f in firs)
        fig2 = go.Figure(data=[go.Bar(
            x=list(district_counts.values()),
            y=list(district_counts.keys()),
            orientation="h",
            marker_color="#A8362B",
            text=list(district_counts.values()),
            textposition="auto",
            textfont=dict(family="JetBrains Mono", size=11),
        )])
        fig2.update_layout(**_LAYOUT, height=320, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True)

    # ── Row 2: Station breakdown + Summary ──
    col3, col4 = st.columns(2)

    with col3:
        station_counts = Counter(f.get("police_station", "Unknown") for f in firs)

        if station_counts:
            max_val = max(station_counts.values())
            bars_html = ""
            for stn, count in station_counts.most_common(6):
                pct = int((count / max_val) * 100) if max_val else 0
                bars_html += f"""
                <div class="bar-row">
                    <div class="bar-top">
                        <span class="bar-name">{stn}</span>
                        <span class="bar-count">{count}</span>
                    </div>
                    <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
                </div>
                """
            
            st.markdown(f"""
            <div class="afir-panel">
                <div class="afir-panel-head"><h3>By Police Station</h3></div>
                <div class="afir-panel-body">
                    {bars_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="section-head"><h3>By Police Station</h3></div>', unsafe_allow_html=True)
            st.info("No station data.")

    with col4:
        st.markdown('<div class="section-head"><h3>Summary</h3></div>', unsafe_allow_html=True)

        total = len(firs)
        solved = sum(1 for f in firs if f.get("status") in ("Solved", "Closed"))
        rate = round((solved / total) * 100, 1) if total else 0
        active = sum(1 for f in firs if f.get("status") == "Under Investigation")

        st.metric("Total Cases", total)
        st.metric("Resolution Rate", f"{rate}%")
        st.metric("Active Investigations", active)


def _load_firs():
    try:
        from app.database.connection import Database
        db = Database()
        return db.get_all_firs()
    except Exception as e:
        st.warning(f"Database unavailable: {e}")
        return None
