import streamlit as st
import re
from collections import Counter


def compute_bleu_1gram(reference: str, candidate: str) -> float:
    """
    Computes a simplified unigram BLEU score between reference and candidate texts.
    Uses pure Python (no NLTK dependency required).
    """
    ref_tokens = re.findall(r'\w+', reference.lower())
    cand_tokens = re.findall(r'\w+', candidate.lower())

    if not cand_tokens or not ref_tokens:
        return 0.0

    ref_counts = Counter(ref_tokens)
    cand_counts = Counter(cand_tokens)

    # Clipped counts: min of candidate count and reference count for each word
    clipped = sum(min(cand_counts[w], ref_counts.get(w, 0)) for w in cand_counts)
    total_cand = sum(cand_counts.values())

    precision = clipped / total_cand if total_cand > 0 else 0.0

    # Brevity penalty
    bp = 1.0
    if len(cand_tokens) < len(ref_tokens):
        import math
        bp = math.exp(1 - len(ref_tokens) / len(cand_tokens)) if len(cand_tokens) > 0 else 0.0

    return round(bp * precision, 4)


def compute_overlap_score(text1: str, text2: str) -> float:
    """
    Computes Jaccard-like overlap between two texts.
    """
    tokens1 = set(re.findall(r'\w+', text1.lower()))
    tokens2 = set(re.findall(r'\w+', text2.lower()))

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1 & tokens2
    union = tokens1 | tokens2

    return round(len(intersection) / len(union), 4)


def show():
    # ── Page Header ──
    st.markdown("""
    <div class="page-eyebrow">QUALITY METRICS</div>
    <div class="page-title">FIR Quality Evaluation</div>
    <hr class="page-header-rule">
    """, unsafe_allow_html=True)

    # Load database safely
    try:
        from app.database.connection import Database
        try:
            db = Database()
            firs = db.get_all_firs()
        except Exception as e:
            st.warning(f"Database connection failed. Cannot load evaluation records. Error: {e}")
            return
    except Exception as e:
        st.warning(f"Database unavailable: {e}")
        firs = []


    # --- METHOD 1: Compare complaint to draft ---
    st.markdown('<div class="card-header">📐 Method 1: Complaint vs. Draft Relevance Comparison</div>', unsafe_allow_html=True)
    st.caption("Compares the original complaint to the AI-generated formal draft using BLEU-1 unigram precision and Jaccard overlap.")

    if not firs:
        st.info("No FIR records available. Load sample data or file a New FIR first.")
        return

    # Select FIR to evaluate
    fir_options = {f"{f.get('fir_number')} — {f.get('complainant_name', 'Unknown')}": f for f in firs}
    selected_label = st.selectbox("Select FIR to Evaluate", list(fir_options.keys()))
    selected_fir = fir_options[selected_label]

    complaint = selected_fir.get("complaint_text", "")
    facts = selected_fir.get("facts", "")
    draft = selected_fir.get("draft", "")
    sections = selected_fir.get("sections", "")

    if st.button("Run Evaluation Metrics"):
        if not complaint or not draft:
            st.warning("Selected FIR is missing complaint text or draft text.")
            return

        # Calculate metrics
        bleu_complaint_vs_draft = compute_bleu_1gram(complaint, draft)
        bleu_complaint_vs_facts = compute_bleu_1gram(complaint, facts)
        overlap_complaint_draft = compute_overlap_score(complaint, draft)
        overlap_facts_draft = compute_overlap_score(facts, draft)

        # Word counts
        complaint_words = len(re.findall(r'\w+', complaint))
        facts_words = len(re.findall(r'\w+', facts))
        draft_words = len(re.findall(r'\w+', draft))
        sections_words = len(re.findall(r'\w+', sections))

        # Expansion ratio
        expansion = round(draft_words / complaint_words, 2) if complaint_words > 0 else 0

        # Display metrics — stat strip
        st.markdown(f"""
        <div class="stat-strip">
            <div class="stat-card">
                <div class="stat-label">BLEU-1 (Complaint to Draft)</div>
                <div class="stat-value">{bleu_complaint_vs_draft:.4f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">BLEU-1 (Complaint to Facts)</div>
                <div class="stat-value">{bleu_complaint_vs_facts:.4f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Jaccard (Complaint & Draft)</div>
                <div class="stat-value">{overlap_complaint_draft:.4f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Jaccard (Facts & Draft)</div>
                <div class="stat-value">{overlap_facts_draft:.4f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="stat-strip">
            <div class="stat-card">
                <div class="stat-label">Complaint Words</div>
                <div class="stat-value">{complaint_words}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Facts Words</div>
                <div class="stat-value">{facts_words}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Draft Words</div>
                <div class="stat-value">{draft_words}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Expansion Ratio</div>
                <div class="stat-value">{expansion}x</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Interpretation
        st.markdown('<div class="card-header">📊 Score Interpretation</div>', unsafe_allow_html=True)

        quality_score = (bleu_complaint_vs_draft * 0.3 + overlap_complaint_draft * 0.3 + overlap_facts_draft * 0.4) * 100
        quality_score = min(round(quality_score, 1), 100)

        if quality_score >= 40:
            quality_label = "Excellent"
            quality_color = "var(--ok)"
            quality_desc = "The AI-generated draft strongly reflects the original complaint and extracted facts."
        elif quality_score >= 25:
            quality_label = "Good"
            quality_color = "var(--gold)"
            quality_desc = "The draft captures most key details from the complaint. Some coverage variations are expected from legal formalization."
        elif quality_score >= 15:
            quality_label = "Moderate"
            quality_color = "var(--seal-soft)"
            quality_desc = "The draft partially covers the complaint. Consider reviewing the agent outputs for completeness."
        else:
            quality_label = "Needs Review"
            quality_color = "var(--seal)"
            quality_desc = "Low overlap between complaint and draft. The AI may have deviated significantly."

        st.markdown(f"""
        <div class="afir-panel" style="border-left:4px solid {quality_color};">
            <div class="afir-panel-body">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-family:var(--serif); font-weight:600; font-size:1.3rem; color:var(--ink);">
                            Composite Quality Score: {quality_score}%
                        </div>
                        <div style="color:{quality_color}; font-weight:600; font-size:0.95rem; margin-top:4px;">{quality_label}</div>
                    </div>
                    <div style="width:70px; height:70px; border-radius:50%; border:4px solid {quality_color};
                                display:flex; align-items:center; justify-content:center;
                                font-size:1.1rem; font-weight:700; color:{quality_color}; font-family:var(--mono);">
                        {quality_score}
                    </div>
                </div>
                <div style="color:var(--slate); font-size:0.85rem; margin-top:10px;">{quality_desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- METHOD 2: Manual text comparison ---
    st.markdown('<div class="card-header" style="margin-top:28px;">🔬 Method 2: Custom Text Comparison Tool</div>', unsafe_allow_html=True)
    st.caption("Paste any reference text and candidate text to compute BLEU-1 and overlap scores.")

    manual_c1, manual_c2 = st.columns(2)
    with manual_c1:
        ref_text = st.text_area("Reference Text", height=150, placeholder="Paste original/reference text here...")
    with manual_c2:
        cand_text = st.text_area("Candidate Text", height=150, placeholder="Paste AI-generated/candidate text here...")

    if st.button("Compute BLEU & Overlap"):
        if ref_text.strip() and cand_text.strip():
            manual_bleu = compute_bleu_1gram(ref_text, cand_text)
            manual_overlap = compute_overlap_score(ref_text, cand_text)

            r_c1, r_c2 = st.columns(2)
            r_c1.metric("BLEU-1 Score", f"{manual_bleu:.4f}")
            r_c2.metric("Jaccard Overlap", f"{manual_overlap:.4f}")
        else:
            st.warning("Both text fields are required.")
