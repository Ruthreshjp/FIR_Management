"""
AutoFIR — Centralised Design System
====================================
Every custom CSS rule lives here as a single constant.
Loaded once in helpers.py via  st.markdown(CUSTOM_CSS, …).

Design tokens are lifted directly from the HTML reference mockups
(design/ui/reference/autofir-dashboard.html  &  autofir-new-complaint.html).
"""

CUSTOM_CSS = """
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600;8..60,700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ═══════════════════════════════════════════
   DESIGN TOKENS
   ═══════════════════════════════════════════ */
:root {
    --ink:          #0F1B2D;
    --ink-soft:     #1B2B42;
    --paper:        #F7F5F0;
    --paper-dim:    #EFEBE2;
    --line:         #D8D3C8;
    --seal:         #A8362B;
    --seal-soft:    #C75C4F;
    --seal-hover:   #94302A;
    --slate:        #5C6470;
    --slate-light:  #8B9099;
    --gold:         #9C8049;
    --ok:           #3D6B4F;
    --white:        #FFFFFF;

    --serif:  'Source Serif 4', 'Georgia', serif;
    --sans:   'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    --mono:   'JetBrains Mono', 'Consolas', monospace;

    --radius:    10px;
    --radius-sm: 7px;
    --shadow:    0 1px 3px rgba(15,27,45,0.06);
    --shadow-md: 0 4px 12px rgba(15,27,45,0.08);
    --transition: all 0.18s ease;
}

/* ═══════════════════════════════════════════
   GLOBAL RESET — warm paper background
   ═══════════════════════════════════════════ */
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stMain"],
.main, .block-container {
    background-color: var(--paper-dim) !important;
    color: var(--ink) !important;
    -webkit-font-smoothing: antialiased;
}

/* Enforce font families on text elements without breaking icons */
[data-testid="stAppViewContainer"] p, 
[data-testid="stAppViewContainer"] a,
[data-testid="stAppViewContainer"] li,
.stMarkdownContainer {
    font-family: var(--sans);
}

/* Strongly restore Material Icons for any Streamlit icon spans */
span[class*="icon"], span[class*="material"], i[class*="icon"], i[class*="material"], svg, svg * {
    font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
}

/* Hard-override for native Streamlit toggle buttons */
[data-testid="stSidebarCollapseButton"] * {
    font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
}
[data-testid="stAppViewContainer"] h1 *,
[data-testid="stAppViewContainer"] h2 *,
[data-testid="stAppViewContainer"] h3 *,
[data-testid="stAppViewContainer"] h4 *,
[data-testid="stAppViewContainer"] h5 *,
[data-testid="stAppViewContainer"] h6 * {
    font-family: var(--serif) !important;
}

[data-testid="stHeader"] {
    background: var(--paper-dim) !important;
}

.block-container {
    padding: 2rem 2.5rem 3rem !important;
    max-width: 1200px !important;
}

/* ═══════════════════════════════════════════
   SIDEBAR — deep navy
   ═══════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background-color: var(--ink) !important;
    border-right: none !important;
    position: relative;
}
/* Gold edge line like the reference */
[data-testid="stSidebar"]::after {
    content: "";
    position: absolute;
    top: 0; right: 0; bottom: 0;
    width: 1px;
    background: linear-gradient(to bottom, transparent, rgba(156,128,73,0.4), transparent);
}
[data-testid="stSidebar"] .block-container {
    padding: 0.5rem 0.75rem !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
    color: rgba(247,245,240,0.72) !important;
    font-family: var(--sans) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--paper) !important;
    font-family: var(--serif) !important;
    font-weight: 600 !important;
}

/* Sidebar button nav items */
.nav-label {
    font-size: 10px !important;
    letter-spacing: 1.4px !important;
    text-transform: uppercase !important;
    color: rgba(247,245,240,0.35) !important;
    padding: 14px 12px 8px !important;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    justify-content: flex-start !important;
    padding: 10px 12px !important;
    border: none !important;
    border-radius: 6px !important;
    background: transparent !important;
    color: rgba(247,245,240,0.72) !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    transition: background 0.15s, color 0.15s !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.05) !important;
    color: var(--paper) !important;
}

/* Sidebar dividers */
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
    opacity: 1 !important;
}

/* ═══════════════════════════════════════════
   TYPOGRAPHY — serif headers, sans body, mono codes
   ═══════════════════════════════════════════ */
h1 {
    font-family: var(--serif) !important;
    font-size: 1.65rem !important;
    font-weight: 600 !important;
    color: var(--ink) !important;
    letter-spacing: 0.01em !important;
    line-height: 1.25 !important;
    margin-bottom: 0.15rem !important;
}
h2 {
    font-family: var(--serif) !important;
    font-size: 1.4rem !important;
    font-weight: 600 !important;
    color: var(--ink) !important;
}
h3 {
    font-family: var(--serif) !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: var(--ink) !important;
}
h4 {
    font-family: var(--serif) !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: var(--ink) !important;
}

/* Page captions */
[data-testid="stCaptionContainer"] {
    color: var(--slate-light) !important;
    font-size: 0.85rem !important;
    margin-bottom: 1.25rem !important;
}

/* ═══════════════════════════════════════════
   BUTTONS — seal primary, ghost outline
   ═══════════════════════════════════════════ */
.stButton > button,
.stFormSubmitButton > button {
    background-color: var(--seal) !important;
    color: var(--white) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--sans) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 9px 18px !important;
    transition: transform 0.1s, box-shadow 0.15s, background 0.15s !important;
    box-shadow: 0 1px 2px rgba(168,54,43,0.3) !important;
}
.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background-color: var(--seal-hover) !important;
    box-shadow: 0 2px 8px rgba(168,54,43,0.35) !important;
}
.stButton > button:active,
.stFormSubmitButton > button:active {
    transform: translateY(1px) !important;
}

/* Download button — ghost style */
.stDownloadButton > button {
    background-color: transparent !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--sans) !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}
.stDownloadButton > button:hover {
    background-color: var(--paper-dim) !important;
}

/* ═══════════════════════════════════════════
   INPUTS — warm paper fields
   ═══════════════════════════════════════════ */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div {
    background-color: var(--white) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    color: var(--ink) !important;
    font-family: var(--sans) !important;
    font-size: 14px !important;
    padding: 16px !important;
    line-height: 1.6 !important;
    transition: var(--transition) !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--seal) !important;
    box-shadow: 0 0 0 3px rgba(168,54,43,0.08) !important;
    outline: none !important;
}
[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label,
[data-testid="stRadio"] label,
[data-testid="stFileUploader"] label {
    color: var(--slate) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

/* Radio Button Colors (for toggle) */
.stRadio label, .stRadio p, .stRadio div[role="radiogroup"] label {
    color: var(--ink) !important;
}

/* ═══════════════════════════════════════════
   METRICS — warm cards with serif values
   ═══════════════════════════════════════════ */
[data-testid="stMetric"] {
    background-color: var(--paper) !important;
    border: 1px solid var(--line) !important;
    border-radius: var(--radius) !important;
    padding: 18px 20px !important;
    transition: var(--transition) !important;
}
[data-testid="stMetricLabel"] {
    color: var(--slate-light) !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    font-family: var(--sans) !important;
}
[data-testid="stMetricValue"] {
    color: var(--ink) !important;
    font-family: var(--serif) !important;
    font-weight: 600 !important;
    font-size: 1.8rem !important;
}
[data-testid="stMetricDelta"] {
    font-family: var(--mono) !important;
    font-size: 0.75rem !important;
}

/* ═══════════════════════════════════════════
   TABS
   ═══════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    border-bottom: 1px solid var(--line) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"] {
    color: var(--slate-light) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    font-family: var(--sans) !important;
    padding: 0.7rem 1.2rem !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    transition: var(--transition) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--ink) !important;
}
.stTabs [aria-selected="true"] {
    color: var(--seal) !important;
    border-bottom-color: var(--seal) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1rem !important;
}

/* ═══════════════════════════════════════════
   EXPANDERS
   ═══════════════════════════════════════════ */
.streamlit-expanderHeader,
[data-testid="stExpander"] summary {
    background-color: var(--paper) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    color: var(--ink) !important;
    font-weight: 500 !important;
    font-family: var(--sans) !important;
    transition: var(--transition) !important;
}
.streamlit-expanderHeader:hover,
[data-testid="stExpander"] summary:hover {
    border-color: var(--seal-soft) !important;
}
.streamlit-expanderContent,
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    border: 1px solid var(--line) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
    background-color: var(--paper) !important;
}

/* ═══════════════════════════════════════════
   DATAFRAMES
   ═══════════════════════════════════════════ */
[data-testid="stDataFrame"], .stDataFrame {
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    border: 1px solid var(--line) !important;
}

/* ═══════════════════════════════════════════
   DIVIDER
   ═══════════════════════════════════════════ */
hr {
    border-color: var(--line) !important;
    opacity: 0.6 !important;
    margin: 1.25rem 0 !important;
}

/* ═══════════════════════════════════════════
   ALERTS
   ═══════════════════════════════════════════ */
.stAlert {
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-family: var(--sans) !important;
}

/* ═══════════════════════════════════════════
   PROGRESS BAR
   ═══════════════════════════════════════════ */
.stProgress > div > div > div {
    background-color: var(--seal) !important;
}

/* ═══════════════════════════════════════════
   PLOTLY — transparent bg so paper shows
   ═══════════════════════════════════════════ */
.js-plotly-plot .plotly .main-svg {
    background: transparent !important;
}

/* ═══════════════════════════════════════════
   SCROLLBAR — warm tones
   ═══════════════════════════════════════════ */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #C9C3B6; border-radius: 8px; }

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: BRAND (sidebar header)
   ═══════════════════════════════════════════ */
.brand-block {
    padding: 22px 18px 18px;
}
.brand-mark {
    display: flex;
    align-items: center;
    gap: 10px;
}
.brand-seal {
    width: 34px; height: 34px;
    border: 1.5px solid var(--gold);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: var(--serif);
    font-size: 13px;
    font-weight: 600;
    color: var(--gold) !important;
    flex-shrink: 0;
}
.brand-title {
    font-family: var(--serif) !important;
    font-size: 18px !important;
    font-weight: 600 !important;
    color: var(--paper) !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}
.brand-sub {
    display: block;
    font-size: 10px !important;
    letter-spacing: 1.4px;
    text-transform: uppercase;
    color: var(--gold) !important;
    margin-top: 2px;
}

/* Sidebar footer */
.sidebar-foot {
    font-size: 11px !important;
    color: rgba(247,245,240,0.4) !important;
    line-height: 1.5;
    padding: 2px 0;
}
.sidebar-foot .status-dot {
    display: inline-block;
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--ok);
    margin-right: 6px;
    box-shadow: 0 0 0 3px rgba(61,107,79,0.2);
}
.sidebar-foot .status-dot.warn {
    background: var(--gold);
    box-shadow: 0 0 0 3px rgba(156,128,73,0.2);
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: PAGE HEADER (eyebrow pattern)
   ═══════════════════════════════════════════ */
.page-eyebrow {
    font-family: var(--mono) !important;
    font-size: 11px !important;
    letter-spacing: 0.5px;
    color: var(--slate-light) !important;
    margin-bottom: 4px;
    text-transform: uppercase;
}
.page-title {
    font-family: var(--serif) !important;
    font-size: 23px !important;
    font-weight: 600 !important;
    color: var(--ink) !important;
    margin: 0 0 4px 0 !important;
}
.page-header-rule {
    border: none;
    border-top: 1px solid var(--line);
    margin: 16px 0 24px 0;
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: STAT STRIP
   ═══════════════════════════════════════════ */
.stat-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: var(--line);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    overflow: hidden;
    margin-bottom: 28px;
}
.stat-card {
    background: var(--paper);
    padding: 20px 22px;
}
.stat-card .stat-label {
    font-family: var(--sans);
    font-size: 11px;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    color: var(--slate-light);
    margin-bottom: 10px;
    font-weight: 500;
}
.stat-card .stat-value {
    font-family: var(--serif);
    font-size: 30px;
    font-weight: 600;
    color: var(--ink);
    display: flex;
    align-items: baseline;
    gap: 8px;
    line-height: 1;
}
.stat-card .stat-delta {
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 500;
    color: var(--ok);
}
.stat-card .stat-delta.warn {
    color: var(--seal);
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: SECTION HEAD
   ═══════════════════════════════════════════ */
.section-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    margin-bottom: 16px;
}
.section-head h3 {
    font-family: var(--serif) !important;
    font-size: 17px !important;
    font-weight: 600 !important;
    margin: 0 !important;
}
.section-head .see-all {
    font-size: 12.5px;
    color: var(--seal);
    font-weight: 600;
    cursor: pointer;
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: DOCKET TABLE
   ═══════════════════════════════════════════ */
.docket {
    background: var(--paper);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    overflow: hidden;
    margin-bottom: 28px;
}
.docket-row {
    display: grid;
    grid-template-columns: 100px 1fr 160px 100px 100px;
    align-items: center;
    padding: 14px 22px;
    border-bottom: 1px solid var(--line);
    gap: 14px;
    transition: background 0.12s;
}
.docket-row:last-child { border-bottom: none; }
.docket-row.head {
    background: var(--paper-dim);
    padding: 11px 22px;
}
.docket-row.head span {
    font-family: var(--sans);
    font-size: 10.5px;
    letter-spacing: 0.7px;
    text-transform: uppercase;
    color: var(--slate-light);
    font-weight: 600;
}
.docket-row:not(.head):hover {
    background: #FBFAF7;
    cursor: pointer;
}

.case-no {
    font-family: var(--mono);
    font-size: 12.5px;
    color: var(--slate);
}
.case-info .case-title {
    font-family: var(--sans);
    font-size: 14px;
    font-weight: 600;
    color: var(--ink);
    margin-bottom: 2px;
}
.case-info .case-sub {
    font-family: var(--sans);
    font-size: 12px;
    color: var(--slate-light);
}

/* Status pills */
.pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: var(--sans);
    font-size: 11.5px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 20px;
    width: fit-content;
}
.pill::before {
    content: "";
    width: 6px; height: 6px;
    border-radius: 50%;
}
.pill.draft   { background: #EFEAE0; color: #8A6D2F; }
.pill.draft::before   { background: #C79A3D; }
.pill.review  { background: #E3E8F0; color: #3A5A8C; }
.pill.review::before  { background: #3A5A8C; }
.pill.filed   { background: #E2EBE4; color: var(--ok); }
.pill.filed::before   { background: var(--ok); }
.pill.closed  { background: #F0E2E2; color: var(--seal); }
.pill.closed::before  { background: var(--seal); }

/* Section tags */
.act-tags { display: flex; gap: 5px; flex-wrap: wrap; }
.tag {
    font-family: var(--mono);
    font-size: 10.5px;
    padding: 2px 7px;
    border-radius: 4px;
    border: 1px solid var(--line);
    color: var(--slate);
    display: inline-block;
}
.tag.bns   { border-color: #B7C4D9; color: #3A5A8C; }
.tag.ipc   { border-color: #D9C9B7; color: #8A6D2F; }
.tag.pocso { border-color: #D9B7BB; color: var(--seal); }

.timestamp {
    font-family: var(--sans);
    font-size: 12px;
    color: var(--slate-light);
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: PANEL
   ═══════════════════════════════════════════ */
.afir-panel {
    background: var(--paper);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    margin-bottom: 20px;
    overflow: hidden;
}
.afir-panel-head {
    padding: 16px 22px;
    border-bottom: 1px solid var(--line);
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.afir-panel-head h3 {
    font-family: var(--serif) !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    margin: 0 !important;
}
.afir-panel-head .hint {
    font-size: 11.5px;
    color: var(--slate-light);
}
.afir-panel-body {
    padding: 22px;
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: FACT GRID
   ═══════════════════════════════════════════ */
.fact-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 18px;
}
.fact {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 13px 15px;
}
.fact .fact-key {
    font-family: var(--sans);
    font-size: 10.5px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: var(--slate-light);
    margin-bottom: 5px;
}
.fact .fact-val {
    font-family: var(--sans);
    font-size: 13.5px;
    font-weight: 600;
    color: var(--ink);
}
.fact.flag {
    border-color: #D9B7BB;
    background: #FBF3F2;
}
.fact.flag .fact-val {
    color: var(--seal);
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: SECTION-MATCH CARDS
   ═══════════════════════════════════════════ */
.match-card {
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 16px 18px;
    margin-bottom: 12px;
    background: var(--white);
    position: relative;
}
.match-card:last-child { margin-bottom: 0; }
.match-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
}
.match-act {
    display: flex;
    align-items: center;
    gap: 8px;
}
.act-chip {
    font-family: var(--mono);
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 5px;
    display: inline-block;
}
.act-chip.bns   { background: #E3E8F0; color: #3A5A8C; }
.act-chip.ipc   { background: #EFEAE0; color: #8A6D2F; }
.act-chip.pocso { background: #F0E2E2; color: var(--seal); }
.sec-num {
    font-family: var(--serif);
    font-weight: 600;
    font-size: 15px;
    color: var(--ink);
}
.confidence {
    font-family: var(--mono);
    font-size: 11px;
    color: var(--ok);
    background: #E2EBE4;
    padding: 3px 8px;
    border-radius: 5px;
    white-space: nowrap;
}
.match-title {
    font-family: var(--sans);
    font-size: 13.5px;
    font-weight: 600;
    color: var(--ink);
    margin-bottom: 6px;
}
.match-reason {
    font-family: var(--sans);
    font-size: 12.5px;
    color: var(--slate);
    line-height: 1.55;
    border-left: 2px solid var(--line);
    padding-left: 10px;
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: STEPPER
   ═══════════════════════════════════════════ */
.stepper {
    display: flex;
    align-items: center;
    gap: 0;
    margin-bottom: 28px;
    background: var(--paper);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 16px 22px;
}
.step {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
}
.step-circle {
    width: 30px; height: 30px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: var(--mono);
    font-size: 12px;
    font-weight: 600;
    flex-shrink: 0;
    border: 1.5px solid var(--line);
    color: var(--slate-light);
    background: var(--paper);
}
.step.done .step-circle {
    background: var(--ok);
    border-color: var(--ok);
    color: white;
}
.step.active .step-circle {
    background: var(--seal);
    border-color: var(--seal);
    color: white;
    box-shadow: 0 0 0 4px rgba(168,54,43,0.15);
}
.step-label .step-name {
    font-family: var(--sans);
    font-weight: 600;
    font-size: 13px;
    color: var(--ink);
    display: block;
}
.step-label .step-desc {
    font-family: var(--sans);
    font-size: 11px;
    color: var(--slate-light);
}
.step.pending .step-label .step-name {
    color: var(--slate-light);
}
.step-line {
    flex: 1;
    height: 1px;
    background: var(--line);
    margin: 0 14px;
    min-width: 20px;
}
.step-line.done { background: var(--ok); }

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: AGENT STATUS
   ═══════════════════════════════════════════ */
.agent-status {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 11px 14px;
    border-radius: 8px;
    background: var(--white);
    border: 1px solid var(--line);
    margin-bottom: 10px;
}
.agent-status:last-child { margin-bottom: 0; }
.agent-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.agent-dot.done    { background: var(--ok); }
.agent-dot.active  { background: var(--seal); box-shadow: 0 0 0 4px rgba(168,54,43,0.15); animation: afir-pulse 1.6s infinite; }
.agent-dot.pending { background: var(--line); }
@keyframes afir-pulse { 0%,100%{opacity:1;} 50%{opacity:0.4;} }
.agent-name {
    font-family: var(--sans);
    font-size: 12.5px;
    font-weight: 600;
    color: var(--ink);
}
.agent-task {
    font-family: var(--sans);
    font-size: 11px;
    color: var(--slate-light);
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: DRAFT PREVIEW
   ═══════════════════════════════════════════ */
.preview-box {
    background: var(--white);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 18px;
    font-family: var(--serif);
    font-size: 12.5px;
    line-height: 1.7;
    color: var(--ink-soft);
}
.preview-box .stamp {
    text-align: center;
    margin-bottom: 12px;
    font-family: var(--mono);
    font-size: 10px;
    letter-spacing: 1px;
    color: var(--slate-light);
    border-bottom: 1px dashed var(--line);
    padding-bottom: 10px;
    text-transform: uppercase;
}
.preview-box p { margin-bottom: 10px; }
.sec-cite {
    font-family: var(--mono);
    font-size: 11px;
    background: var(--paper-dim);
    padding: 1px 5px;
    border-radius: 3px;
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: BAR CHART (section frequency)
   ═══════════════════════════════════════════ */
.bar-row { margin-bottom: 13px; }
.bar-row:last-child { margin-bottom: 0; }
.bar-top {
    display: flex;
    justify-content: space-between;
    font-size: 12.5px;
    margin-bottom: 6px;
}
.bar-top .bar-name { font-weight: 600; color: var(--ink); font-family: var(--sans); }
.bar-top .bar-count { font-family: var(--mono); color: var(--slate-light); }
.bar-track {
    height: 6px;
    background: var(--paper-dim);
    border-radius: 4px;
    overflow: hidden;
}
.bar-fill {
    height: 100%;
    border-radius: 4px;
    background: linear-gradient(90deg, var(--seal-soft), var(--seal));
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: ACTIVITY FEED
   ═══════════════════════════════════════════ */
.feed-item {
    display: flex;
    gap: 12px;
    padding: 11px 0;
    border-bottom: 1px solid var(--paper-dim);
}
.feed-item:last-child { border-bottom: none; padding-bottom: 0; }
.feed-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--gold);
    margin-top: 5px;
    flex-shrink: 0;
}
.feed-text {
    font-family: var(--sans);
    font-size: 12.5px;
    line-height: 1.5;
    color: var(--ink);
}
.feed-text b { font-weight: 600; }
.feed-time {
    font-family: var(--sans);
    font-size: 11px;
    color: var(--slate-light);
    margin-top: 2px;
}

/* ═══════════════════════════════════════════
   CUSTOM COMPONENT: WATERMARK
   ═══════════════════════════════════════════ */
.watermark {
    text-align: center;
    padding: 28px 0 8px;
    font-family: var(--mono);
    font-size: 10.5px;
    letter-spacing: 1px;
    color: var(--slate-light);
    text-transform: uppercase;
}

/* ═══════════════════════════════════════════
   UTILITY CLASSES (for markdown HTML blocks)
   ═══════════════════════════════════════════ */
.text-muted  { color: var(--slate-light) !important; font-size: 0.85rem; }
.text-seal   { color: var(--seal) !important; }
.text-mono   { font-family: var(--mono) !important; }
.text-serif  { font-family: var(--serif) !important; }
.mt-sm       { margin-top: 12px; }
.mb-sm       { margin-bottom: 12px; }
.mb-md       { margin-bottom: 24px; }

/* Card header (evaluation page) */
.card-header {
    font-family: var(--serif);
    font-size: 17px;
    font-weight: 600;
    color: var(--ink);
    margin-bottom: 12px;
}

/* ═══════════════════════════════════════════
   RESPONSIVE — 2-col docket
   ═══════════════════════════════════════════ */
@media (max-width: 768px) {
    .stat-strip { grid-template-columns: repeat(2, 1fr); }
    .fact-grid  { grid-template-columns: 1fr; }
    .docket-row { grid-template-columns: 80px 1fr 90px; }
    .docket-row span:nth-child(4),
    .docket-row span:nth-child(5) { display: none; }
}
</style>
"""
