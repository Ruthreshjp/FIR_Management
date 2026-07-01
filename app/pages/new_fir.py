import streamlit as st
import re


def show():
    # ── Page Header ──
    st.markdown("""
    <div class="page-eyebrow">NEW COMPLAINT INTAKE</div>
    <div class="page-title">Draft a First Information Report</div>
    <hr class="page-header-rule">
    """, unsafe_allow_html=True)

    # ── Complaint Form ──
    with st.form("fir_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Complainant Name", placeholder="e.g. Rajesh Kumar")
        with col2:
            email = st.text_input("Email", placeholder="e.g. rajesh@example.com")

        # Automatically inherit from Profile
        station = st.session_state.get("profile_station", "Central Station")
        district = st.session_state.get("profile_district", "Metropolis")

        complaint = st.text_area(
            "Complaint Description",
            height=180,
            placeholder="Describe the incident in plain English. Include dates, times, locations, and what happened..."
        )

        submitted = st.form_submit_button("Generate FIR")

    if not submitted:
        return

    # ── Validation ──
    missing = [label for label, val in [("Name", name), ("Email", email), ("Complaint", complaint)] if not val.strip()]
    if missing:
        st.error(f"Please fill in: {', '.join(missing)}")
        return

    # ── Stepper (starts at step 1 active) ──
    stepper_container = st.empty()
    _render_stepper(stepper_container, current=1)

    # ── Pipeline columns: main + sidebar status ──
    col_main, col_side = st.columns([2, 1])

    with col_side:
        agent_area = st.empty()

    # Placeholders for dynamic updates
    main_status = st.empty()

    # ── Run agent pipeline ──
    from app.agents.orchestrator import Orchestrator
    orchestrator = Orchestrator()

    facts_text = ""
    sections_text = ""
    draft_text = ""
    final_record = None
    current_agent = ""
    step_count = 0

    agent_states = {
        "Intake Agent": ("pending", "Waiting..."),
        "Legal Agent": ("pending", "Waiting..."),
        "Drafting Agent": ("pending", "Waiting..."),
    }

    for step in orchestrator.generate_fir(name, email, station, district, complaint):
        agent = step.get("agent", "")
        stype = step.get("type", "")
        msg = step.get("message", "")

        if stype in ("status", "header"):
            step_count += 1
            current_agent = agent

            # Update agent states
            for a in agent_states:
                if a == agent:
                    agent_states[a] = ("active", msg)
                elif agent_states[a][0] == "active":
                    agent_states[a] = ("done", "Completed")

            # Update stepper
            if "Intake" in agent:
                _render_stepper(stepper_container, current=1)
            elif "Legal" in agent:
                _render_stepper(stepper_container, current=2)
            elif "Drafting" in agent:
                _render_stepper(stepper_container, current=3)

            # Update sidebar agent status
            _render_agent_status(agent_area, agent_states)
            
            # Show active spinner in main area
            with main_status:
                st.spinner(f"{agent}: {msg}...")

        elif stype == "thought":
            main_status.empty()  # Clear status when thought completes
            if agent == "Intake Agent":
                facts_text = msg
                agent_states["Intake Agent"] = ("done", "Facts extracted")
            elif agent == "Legal Agent":
                sections_text = msg
                agent_states["Legal Agent"] = ("done", "Sections matched")
            elif agent == "Drafting Agent":
                draft_text = msg
                agent_states["Drafting Agent"] = ("done", "Draft ready")

        elif stype == "error":
            main_status.error(f"{agent}: {msg}")
            st.error(f"{agent}: {msg}")

        elif stype == "pipeline_complete":
            final_record = step.get("fir_record")

    # Final stepper state
    _render_stepper(stepper_container, current=4)
    for a in agent_states:
        if agent_states[a][0] != "done":
            agent_states[a] = ("done", "Completed")
    _render_agent_status(agent_area, agent_states)

    # ── Results ──
    with col_main:
        # Extracted Facts
        if facts_text:
            facts_html = _parse_facts_to_grid(facts_text)
            st.markdown(f"""
            <div class="afir-panel">
                <div class="afir-panel-head">
                    <h3>Extracted Facts</h3>
                    <span class="hint">AI-parsed from complaint</span>
                </div>
                <div class="afir-panel-body">
                    {facts_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Matched Legal Sections
        if sections_text:
            cards_html = _parse_sections_to_cards(sections_text)
            st.markdown(f"""
            <div class="afir-panel">
                <div class="afir-panel-head">
                    <h3>Matched Legal Sections</h3>
                    <span class="hint">Ranked by semantic + reasoning match</span>
                </div>
                <div class="afir-panel-body">
                    {cards_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Draft Editor
        if draft_text:
            fir_num = final_record.get("fir_number", "DRAFT") if final_record else "DRAFT"

            # Maintain session state for the editable draft to avoid losing edits on reruns
            if "edited_draft" not in st.session_state or st.session_state.get("draft_num") != fir_num:
                st.session_state["edited_draft"] = draft_text
                st.session_state["draft_num"] = fir_num

            st.markdown(f"""
            <div class="afir-panel">
                <div class="afir-panel-head">
                    <h3>FIR Draft Editor</h3>
                    <span class="hint">Review and refine AI draft</span>
                </div>
                <div class="afir-panel-body" style="padding-bottom:12px;">
            """, unsafe_allow_html=True)

            st.session_state["edited_draft"] = st.text_area(
                "Edit Draft",
                value=st.session_state["edited_draft"],
                height=300,
                label_visibility="collapsed"
            )

            # Let user save or finalize
            col_save, col_finalize, _ = st.columns([1, 2, 3])
            with col_save:
                if st.button("Save Updates", use_container_width=True):
                    if final_record:
                        try:
                            from app.database.connection import Database
                            db = Database()
                            db.update_fir(fir_num, {"draft": st.session_state["edited_draft"]})
                            st.success("Changes saved.")
                        except Exception:
                            st.warning("Could not save to database (offline mode).")
            with col_finalize:
                if st.button("Finalize & Issue FIR", use_container_width=True, type="primary"):
                    if final_record:
                        with st.spinner("Issuing FIR via Blockchain..."):
                            try:
                                from app.database.connection import Database
                                db = Database()
                                
                                # 1. Update draft
                                final_record["draft"] = st.session_state["edited_draft"]
                                db.update_fir(fir_num, {"draft": final_record["draft"]})
                                
                                # 2. Blockchain Recording
                                from app.tools.blockchain_tool import record_on_blockchain
                                tx_hash = record_on_blockchain(fir_num, final_record["draft"])
                                final_record["tx_hash"] = tx_hash
                                db.update_fir(fir_num, {"tx_hash": tx_hash, "status": "Under Investigation"})
                                
                                # 3. Generate PDF (Now with tx_hash)
                                from app.pdf.generator import create_fir_pdf
                                pdf_bytes = create_fir_pdf(final_record)
                                
                                # 4. Send Email
                                from app.tools.email_tool import send_fir_pdf_email
                                email_sent = send_fir_pdf_email(
                                    final_record.get("complainant_email", ""),
                                    final_record.get("complainant_name", "Citizen"),
                                    fir_num,
                                    pdf_bytes
                                )
                                
                                st.success(f"FIR {fir_num} officially issued! Blockchain TX: {tx_hash}")
                                if email_sent:
                                    st.info(f"Email sent to {final_record.get('complainant_email', '')}")
                            except Exception as e:
                                st.error(f"Error finalizing FIR: {e}")

            st.markdown("</div></div>", unsafe_allow_html=True)
            
            # Ensure the final record (and thus PDF) uses the edited draft
            if final_record:
                final_record["draft"] = st.session_state["edited_draft"]

    # ── PDF Download ──
    if final_record:
        st.markdown("<hr class='page-header-rule'>", unsafe_allow_html=True)
        col_dl, _ = st.columns([1, 2])
        with col_dl:
            try:
                from app.pdf.generator import create_fir_pdf
                pdf_bytes = create_fir_pdf(final_record)
                st.download_button(
                    label="⬇ Download Official PDF",
                    data=pdf_bytes,
                    file_name=f"{final_record['fir_number'].replace('/', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")


# ─────────────────────────────────────────────
# HELPER: Stepper
# ─────────────────────────────────────────────
def _render_stepper(container, current: int):
    """Render the 4-step progress stepper. current = 1..4 (active step)."""
    steps = [
        ("Intake", "Extract facts"),
        ("Legal Matching", "Map sections"),
        ("Drafting", "Generate FIR"),
        ("Finalize", "Export PDF"),
    ]
    parts = []
    for i, (label, desc) in enumerate(steps, 1):
        if i < current:
            cls = "done"
            circle = "✓"
        elif i == current:
            cls = "active"
            circle = str(i)
        else:
            cls = "pending"
            circle = str(i)
        parts.append(f"""
        <div class="step {cls}">
            <div class="step-circle">{circle}</div>
            <div class="step-label">
                <span class="step-name">{label}</span>
                <span class="step-desc">{desc}</span>
            </div>
        </div>
        """)
        if i < len(steps):
            line_cls = "done" if i < current else ""
            parts.append(f'<div class="step-line {line_cls}"></div>')

    container.markdown(f'<div class="stepper">{"".join(parts)}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPER: Agent Status Sidebar
# ─────────────────────────────────────────────
def _render_agent_status(container, states: dict):
    """Render agent status dots in the sidebar panel."""
    html = """
    <div class="afir-panel">
        <div class="afir-panel-head"><h3>Pipeline Status</h3></div>
        <div class="afir-panel-body" id="pipeline-agents">
    """
    for agent_name, (state, task) in states.items():
        html += f"""
        <div class="agent-status">
            <div class="agent-dot {state}"></div>
            <div>
                <div class="agent-name">{agent_name}</div>
                <div class="agent-task">{task}</div>
            </div>
        </div>
        """
    html += "</div></div>"
    container.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPER: Parse facts text → fact-grid HTML
# ─────────────────────────────────────────────
def _parse_facts_to_grid(text: str) -> str:
    """
    Parse the AI-returned facts text into a grid of fact cards.
    Looks for key-value patterns like  '**Key:** Value'  or  'Key: Value'.
    Falls back to rendering as a single panel if no structure found.
    """
    facts = []

    # Try markdown bold pattern with optional list item
    for m in re.finditer(r'(?:-\s*)?\*\*(.+?)\*\*[:\s]+(.+)$', text, re.MULTILINE):
        facts.append((m.group(1).strip(), m.group(2).strip()))

    # Fallback: plain Key: Value
    if not facts:
        for m in re.finditer(r'^(?:-\s*)?([A-Z][\w\s]+):\s*(.+)$', text, re.MULTILINE):
            facts.append((m.group(1).strip(), m.group(2).strip()))

    if not facts:
        # No structure found — render as-is
        return f'<div class="fact"><div class="fact-val">{text}</div></div>'

    cards = []
    for key, val in facts:
        # Flag cards for sensitive items (minor, POCSO)
        is_flag = any(w in key.lower() for w in ("minor", "pocso", "child", "victim age"))
        flag_cls = " flag" if is_flag else ""
        cards.append(f"""
        <div class="fact{flag_cls}">
            <div class="fact-key">{key}</div>
            <div class="fact-val">{val}</div>
        </div>
        """)

    return f'<div class="fact-grid">{"".join(cards)}</div>'


# ─────────────────────────────────────────────
# HELPER: Parse sections text → match-card HTML
# ─────────────────────────────────────────────
def _parse_sections_to_cards(text: str) -> str:
    """
    Parse the AI-returned legal sections text into match-card components.
    Looks for section references (BNS/IPC/POCSO + number) and surrounding text.
    """
    cards = []

    # Try to split by numbered items or section headers
    # Pattern: lines starting with a number, or containing BNS/IPC section refs
    blocks = re.split(r'\n(?=\d+\.\s|\*\*(?:BNS|IPC|POCSO))', text.strip())

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Extract act + section number
        sec_match = re.search(r'(BNS|IPC|POCSO)\s*(?:§|Section\s*)?\s*(\d+)', block, re.IGNORECASE)
        if not sec_match:
            # No section reference — render as plain text
            cards.append(f"""
            <div class="match-card">
                <div class="match-reason">{block}</div>
            </div>
            """)
            continue

        act = sec_match.group(1).upper()
        sec_num = sec_match.group(2)
        chip_cls = act.lower()

        # Try to extract a title (bold text or text after section number)
        title_match = re.search(r'(?:–|—|-|:)\s*(.+?)(?:\n|$)', block)
        title = title_match.group(1).strip() if title_match else ""
        # Clean markdown bold from title
        title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)

        # Try to extract confidence (percentage)
        conf_match = re.search(r'(\d{1,3})%', block)
        confidence = f"{conf_match.group(1)}% match" if conf_match else ""

        # Reasoning: everything after the first line
        lines = block.split('\n')
        reason_lines = []
        for line in lines[1:]:
            cleaned = line.strip().lstrip('- ').strip()
            if cleaned:
                reason_lines.append(cleaned)
        reason = ' '.join(reason_lines) if reason_lines else ""
        # Clean markdown
        reason = re.sub(r'\*\*(.+?)\*\*', r'\1', reason)

        conf_html = f'<span class="confidence">{confidence}</span>' if confidence else ""

        cards.append(f"""
        <div class="match-card">
            <div class="match-top">
                <div class="match-act">
                    <span class="act-chip {chip_cls}">{act}</span>
                    <span class="sec-num">Section {sec_num}</span>
                </div>
                {conf_html}
            </div>
            {"<div class='match-title'>" + title + "</div>" if title else ""}
            {"<div class='match-reason'>" + reason + "</div>" if reason else ""}
        </div>
        """)

    if not cards:
        # Fallback: render entire text in a single card
        return f"""
        <div class="match-card">
            <div class="match-reason">{text}</div>
        </div>
        """

    return "".join(cards)
