import io
import os
import re
import json
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, PageTemplate, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Circle

# Colors
BG_LABEL = colors.HexColor('#EEEEEE')
BG_ALT = colors.HexColor('#F7F7F7')
BLACK = colors.black

def draw_emblem():
    """Returns the logo image if present, otherwise a clean fallback drawing."""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "logo.jpg"),
        r"d:\auto_fir\frontend\public\logo.jpg",
        os.path.join(os.getcwd(), "frontend", "public", "logo.jpg")
    ]
    for logo_path in possible_paths:
        if os.path.exists(logo_path):
            try:
                return Image(logo_path, width=46, height=46)
            except Exception as e:
                print(f"Error loading emblem image: {e}")
                break
    d = Drawing(46, 46)
    d.add(Circle(23, 23, 22, strokeColor=BLACK, fillColor=None, strokeWidth=1))
    return d

def footer_canvas(canvas, doc, fir_number, station_name):
    """Draws the footer on every page."""
    canvas.saveState()
    canvas.setStrokeColor(BLACK)
    canvas.setLineWidth(0.5)
    canvas.line(30, 40, 565, 40)  # Horizontal rule matching margins

    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(colors.gray)

    # Left
    canvas.drawString(30, 28, f"Page {doc.page}")

    # Center
    center_text = f"FIR No. {fir_number} — {station_name}"
    canvas.drawCentredString(A4[0] / 2.0, 28, center_text)

    # Right
    right_text = "CONFIDENTIAL — FOR OFFICIAL USE ONLY"
    canvas.drawRightString(565, 28, right_text)

    canvas.restoreState()

def clean_text(text: str) -> str:
    """Replaces Unicode special characters with plain ASCII equivalents to prevent ReportLab font square glyphs."""
    if not text:
        return ""
    replacements = {
        '—': '-', '–': '-', '‑': '-', '‐': '-',
        '“': '"', '”': '"', '‘': "'", '’': "'",
        '\xa0': ' ', '\u200b': '', '…': '...'
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text

def safe_str(val, default="Not Provided"):
    if val is None:
        return default
    s = str(val).strip()
    if s == "" or s.lower() in ("none", "null", "undefined"):
        return default
    return clean_text(s)

def parse_date_and_day(date_val):
    """Parses date string in various formats and returns (formatted_date, day_of_week)."""
    if not date_val or str(date_val).strip() in ("", "Not Provided", "None", "null"):
        return "Not Provided", "Not Provided"
    date_str = str(date_val).strip()
    for fmt in [
        "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", 
        "%d %B %Y", "%d %b %Y", "%Y/%m/%d",
        "%B %d, %Y", "%b %d, %Y"
    ]:
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.strftime("%d/%m/%Y"), dt.strftime("%A")
        except ValueError:
            pass
    try:
        dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y"), dt.strftime("%A")
    except Exception:
        pass
    return date_str, "Not Provided"

def make_table(data, col_widths, label_idx=0):
    """Helper to create a standard styled row table with automatic text wrapping."""
    p_label_style = ParagraphStyle('FIRTableLabel', fontName='Times-Bold', fontSize=8, leading=10)
    p_val_style = ParagraphStyle('FIRTableVal', fontName='Times-Roman', fontSize=8.5, leading=11)

    formatted_data = []
    for row in data:
        formatted_row = []
        for idx, cell in enumerate(row):
            if isinstance(cell, Table):
                formatted_row.append(cell)
            elif idx == label_idx:
                if isinstance(cell, str):
                    formatted_row.append(Paragraph(clean_text(cell), p_label_style))
                else:
                    formatted_row.append(cell)
            else:
                if isinstance(cell, str):
                    formatted_row.append(Paragraph(clean_text(cell), p_val_style))
                else:
                    formatted_row.append(cell)
        formatted_data.append(formatted_row)

    t = Table(formatted_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (label_idx, 0), (label_idx, -1), BG_LABEL),
        ('GRID', (0, 0), (-1, -1), 0.5, BLACK),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    return t

def create_fir_pdf(fir_data: dict) -> bytes:
    buffer = io.BytesIO()

    # Extract station & district with robust fallbacks
    fir_number = safe_str(fir_data.get('fir_number'), default="DRAFT")
    station = safe_str(
        fir_data.get('incident_station') or 
        fir_data.get('police_station') or 
        fir_data.get('officer_station') or 
        fir_data.get('station'),
        default="Not Provided"
    )
    district = safe_str(
        fir_data.get('incident_district') or 
        fir_data.get('district') or 
        fir_data.get('complainant_city'),
        default="Not Provided"
    )

    # Report Date / Time
    report_date_raw = fir_data.get('created_at') or fir_data.get('report_date') or ''
    date_str, _ = parse_date_and_day(report_date_raw)
    time_str = "Not Provided"
    if report_date_raw:
        try:
            dt = datetime.datetime.fromisoformat(str(report_date_raw).replace('Z', '+00:00'))
            time_str = dt.strftime("%H:%M")
        except Exception:
            time_str = safe_str(fir_data.get('report_time'), default="Not Provided")
    if date_str == "Not Provided":
        now = datetime.datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%H:%M")

    # Setup Doc (A4 printable width = 595.27 - 60 = 535.27)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30, leftMargin=30,
        topMargin=32, bottomMargin=46
    )

    # Add page template for footer
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='fir_template', frames=frame, onPage=lambda c, d: footer_canvas(c, d, fir_number, station))
    doc.addPageTemplates([template])

    # Standard Paragraph styles with explicit leading to PREVENT ANY TEXT OVERLAPPING
    p_body = ParagraphStyle('FIRBody', fontName='Times-Roman', fontSize=8.5, leading=11.5)
    p_justified = ParagraphStyle('FIRJustified', parent=p_body, alignment=TA_JUSTIFY, leading=12)
    p_bold = ParagraphStyle('FIRBold', fontName='Times-Bold', fontSize=8.5, leading=11.5)
    p_title = ParagraphStyle('FIRTitle', fontName='Helvetica-Bold', fontSize=13, leading=16, alignment=TA_CENTER, spaceAfter=1)
    p_subtitle = ParagraphStyle('FIRSub', fontName='Times-Roman', fontSize=8, leading=10, alignment=TA_CENTER)
    p_th_style = ParagraphStyle('FIRTH', fontName='Times-Bold', fontSize=7.5, leading=9.5, alignment=TA_CENTER)
    p_td_small = ParagraphStyle('FIRTDSmall', fontName='Times-Roman', fontSize=8, leading=10)
    p_td_small_center = ParagraphStyle('FIRTDSmallCenter', fontName='Times-Roman', fontSize=8, leading=10, alignment=TA_CENTER)
    p_hdr_right = ParagraphStyle('FIRHdrRight', fontName='Times-Roman', fontSize=8.5, leading=11)

    story = []

    # ─────────────────────────────────────────────────────
    # HEADER BLOCK
    # ─────────────────────────────────────────────────────
    header_left = [
        draw_emblem(),
        Paragraph("<b>STATE POLICE</b>", ParagraphStyle('H_TN', fontName='Helvetica-Bold', fontSize=9, leading=11, alignment=TA_CENTER))
    ]

    header_center = [
        Spacer(1, 4),
        Paragraph("<b>FIRST INFORMATION REPORT</b>", p_title),
        Paragraph("(Under Section 173 BNSS / Section 154 CrPC)", p_subtitle),
        Paragraph("<b>FORM - II</b> (See Rule 9)", ParagraphStyle('H_Form', fontName='Times-Italic', fontSize=7.5, leading=9.5, alignment=TA_CENTER))
    ]

    header_right = [
        Paragraph(f"<b>FIR No.:</b> <font name='Courier'>{fir_number}</font>", p_hdr_right),
        Paragraph(f"<b>Date:</b> {date_str}  <b>Time:</b> {time_str}", p_hdr_right),
        Paragraph(f"<b>District:</b> {district}", p_hdr_right),
        Paragraph(f"<b>Police Station:</b> {station}", p_hdr_right)
    ]

    header_table = Table([[header_left, header_center, header_right]], colWidths=[80, 280, 175])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, BLACK),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6))

    # Inner table available width:
    # Outer table colWidths = [168, 367], with 4pt padding on each side, inner width = 367
    INNER_WIDTH = 367

    # ─────────────────────────────────────────────────────
    # SECTION 1: Act & Sections
    # ─────────────────────────────────────────────────────
    ipc_data = list(fir_data.get('ipc_sections') or [])
    bns_data = list(fir_data.get('bns_sections') or [])
    other_data = list(fir_data.get('other_sections') or [])
    all_sections = fir_data.get('sections') or []

    # Fallback: if split lists are empty but `sections` exists, categorize them
    if not ipc_data and not bns_data and not other_data and all_sections:
        for s in all_sections:
            if isinstance(s, dict):
                act = str(s.get('act', '')).upper()
                if 'BNS' in act:
                    bns_data.append(s)
                elif 'IPC' in act:
                    ipc_data.append(s)
                else:
                    other_data.append(s)
            elif isinstance(s, str):
                if 'BNS' in s.upper():
                    bns_data.append({'act': 'BNS', 'section_number': s, 'offense': ''})
                elif 'IPC' in s.upper():
                    ipc_data.append({'act': 'IPC', 'section_number': s, 'offense': ''})
                else:
                    other_data.append({'act': 'Other', 'section_number': s, 'offense': ''})

    act_data = [[
        Paragraph("<b>S.No</b>", p_th_style),
        Paragraph("<b>Act</b>", p_th_style),
        Paragraph("<b>Section</b>", p_th_style),
        Paragraph("<b>Offense</b>", p_th_style)
    ]]
    s_no = 1

    def add_section_data(data_list, act_label):
        nonlocal s_no
        for s in data_list:
            if isinstance(s, dict):
                sec = safe_str(s.get("section_number") or s.get("section") or "")
                title = safe_str(s.get("title") or s.get("offense") or s.get("name") or "")
            else:
                sec = safe_str(str(s))
                title = ""
            act_data.append([
                Paragraph(str(s_no), p_td_small_center),
                Paragraph(act_label, p_td_small),
                Paragraph(sec, p_td_small),
                Paragraph(title, p_td_small)
            ])
            s_no += 1

    if bns_data: add_section_data(bns_data, "BNS")
    if ipc_data: add_section_data(ipc_data, "IPC")
    if other_data:
        for s in other_data:
            if isinstance(s, dict):
                act = safe_str(s.get("act", "Special Act"))
                sec = safe_str(s.get("section_number") or s.get("section") or "")
                title = safe_str(s.get("title") or s.get("offense") or "")
            else:
                act = "Special Act"
                sec = safe_str(str(s))
                title = ""
            act_data.append([
                Paragraph(str(s_no), p_td_small_center),
                Paragraph(act, p_td_small),
                Paragraph(sec, p_td_small),
                Paragraph(title, p_td_small)
            ])
            s_no += 1

    if len(act_data) == 1:
        act_data.append([
            Paragraph("1", p_td_small_center),
            Paragraph("BNSS / BNS", p_td_small),
            Paragraph("Under Inquiry", p_td_small),
            Paragraph("Applicable sections being determined", p_td_small)
        ])

    act_inner = Table(act_data, colWidths=[24, 45, 55, 243])
    act_inner.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BLACK),
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    s1 = make_table([["1. ACT & SECTION(S):", act_inner]], [168, INNER_WIDTH])
    story.append(s1)

    # ─────────────────────────────────────────────────────
    # SECTION 2: Occurrence
    # ─────────────────────────────────────────────────────
    raw_inc_date = fir_data.get('incident_date')
    inc_date_formatted, inc_day = parse_date_and_day(raw_inc_date)
    inc_time = safe_str(fir_data.get('incident_time'), default="Not Provided")

    s2_inner = Table([
        [
            Paragraph(f"<b>Day:</b> {inc_day}", p_td_small),
            Paragraph(f"<b>Date From:</b> {inc_date_formatted}", p_td_small),
            Paragraph("<b>Date To:</b> Prior to Report", p_td_small)
        ],
        [
            Paragraph(f"<b>Time From:</b> {inc_time}", p_td_small),
            Paragraph("<b>Time To:</b> As reported", p_td_small),
            Paragraph("", p_td_small)
        ]
    ], colWidths=[122, 122, 123])
    s2_inner.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    s2 = make_table([["2. OCCURRENCE OF OFFENCE:", s2_inner]], [168, INNER_WIDTH])
    story.append(s2)

    # ─────────────────────────────────────────────────────
    # SECTIONS 3-5: Information Received & GD Reference
    # ─────────────────────────────────────────────────────
    info_type = safe_str(
        fir_data.get('information_type') or 
        ('Voice / Speech Input' if str(fir_data.get('input_mode', '')).lower() == 'speech' else 'Written Complaint')
    )
    gd_ref = safe_str(
        fir_data.get('gd_entry') or 
        fir_data.get('gd_number') or 
        fir_data.get('general_diary_entry') or 
        fir_data.get('gd_ref'),
        default="Entry No.: Recorded in Station General Diary"
    )

    s3 = make_table([["3. INFORMATION RECEIVED:", Paragraph(f"Date: {date_str}  |  Time: {time_str}  |  Type: {info_type}", p_td_small)]], [168, INNER_WIDTH])
    story.append(s3)

    s4 = make_table([["4. GENERAL DIARY REFERENCE:", Paragraph(f"{gd_ref}  |  Time: {time_str}", p_td_small)]], [168, INNER_WIDTH])
    story.append(s4)

    s5 = make_table([["5. TYPE OF INFORMATION:", Paragraph(info_type, p_td_small)]], [168, INNER_WIDTH])
    story.append(s5)

    # ─────────────────────────────────────────────────────
    # SECTION 6: Place of Occurrence
    # ─────────────────────────────────────────────────────
    loc = safe_str(fir_data.get('incident_location'))
    landmark = safe_str(fir_data.get('incident_landmark'), default="")
    if landmark and landmark != "Not Provided":
        loc += f" (Landmark: {landmark})"

    dist_ps = safe_str(fir_data.get('distance_from_ps') or fir_data.get('ps_distance'), default="Within Jurisdiction")
    dir_ps = safe_str(fir_data.get('direction_from_ps') or fir_data.get('ps_direction'), default="Not Specified")
    beat_no = safe_str(fir_data.get('beat_no') or fir_data.get('incident_beat'), default="Not Provided")

    s6_inner = Table([
        [Paragraph(f"<b>Address:</b> {loc}", p_td_small)],
        [Paragraph(f"<b>Distance from P.S.:</b> {dist_ps}    <b>Direction from P.S.:</b> {dir_ps}    <b>Beat No.:</b> {beat_no}", p_td_small)]
    ], colWidths=[INNER_WIDTH])
    s6_inner.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    s6 = make_table([["6. PLACE OF OCCURRENCE:", s6_inner]], [168, INNER_WIDTH])
    story.append(s6)

    outside_ps = safe_str(fir_data.get('outside_ps_limits'), default="No")
    s7 = make_table([["7. OUTSIDE P.S. LIMITS:", Paragraph(f"Yes/No: {outside_ps}    (If Yes, Police Station: {station})", p_td_small)]], [168, INNER_WIDTH])
    story.append(s7)

    s8 = make_table([["8. BEAT NO.:", Paragraph(beat_no, p_td_small)]], [168, INNER_WIDTH])
    story.append(s8)

    # ─────────────────────────────────────────────────────
    # SECTION 9: Details of Accused
    # ─────────────────────────────────────────────────────
    # Wrap ALL table headers in Paragraph to PREVENT TEXT OVERLAPPING
    s9_header = [
        Paragraph("<b>S.No</b>", p_th_style),
        Paragraph("<b>Name</b>", p_th_style),
        Paragraph("<b>Father/Spouse</b>", p_th_style),
        Paragraph("<b>Age</b>", p_th_style),
        Paragraph("<b>Sex</b>", p_th_style),
        Paragraph("<b>Address</b>", p_th_style),
        Paragraph("<b>Marks/Details</b>", p_th_style)
    ]

    accused_raw = fir_data.get('accused_list') or fir_data.get('accused') or fir_data.get('accused_details') or []
    accused_items = []
    if isinstance(accused_raw, list):
        accused_items = [item for item in accused_raw if item]
    elif isinstance(accused_raw, dict):
        accused_items = [accused_raw]
    elif isinstance(accused_raw, str) and accused_raw.strip() and accused_raw.strip() != "Not Provided":
        accused_items = [{"name": accused_raw.strip()}]

    if not accused_items:
        acc_name = safe_str(fir_data.get('accused_name'), default="")
        if not acc_name or acc_name == "Not Provided":
            acc_name = safe_str(fir_data.get('accused'), default="Unknown Person(s)")
        
        acc_desc = safe_str(fir_data.get('accused_description'), default="")
        acc_veh = safe_str(fir_data.get('accused_vehicle'), default="")
        remarks_parts = []
        if acc_desc and acc_desc != "Not Provided": remarks_parts.append(acc_desc)
        if acc_veh and acc_veh != "Not Provided": remarks_parts.append(f"Veh: {acc_veh}")
        remarks = " / ".join(remarks_parts) if remarks_parts else "Not Provided"

        accused_items = [{
            "name": acc_name,
            "father_name": safe_str(fir_data.get('accused_father_name') or fir_data.get('accused_husband_name')),
            "age": safe_str(fir_data.get('accused_age')),
            "sex": safe_str(fir_data.get('accused_gender') or fir_data.get('accused_sex')),
            "address": safe_str(fir_data.get('accused_address')),
            "identifying_marks": remarks
        }]

    s9_data = [s9_header]
    for idx, acc in enumerate(accused_items):
        if isinstance(acc, str):
            name = safe_str(acc)
            fname = age = sex = address = marks = "Not Provided"
        elif isinstance(acc, dict):
            name = safe_str(acc.get("name") or acc.get("accused_name"))
            fname = safe_str(acc.get("father_name") or acc.get("husband_name") or acc.get("father_husband_name") or acc.get("relation"))
            age = safe_str(acc.get("age") or acc.get("accused_age"))
            sex = safe_str(acc.get("sex") or acc.get("gender") or acc.get("accused_gender"))
            address = safe_str(acc.get("address") or acc.get("accused_address"))
            marks = safe_str(acc.get("identifying_marks") or acc.get("description") or acc.get("marks") or acc.get("vehicle") or acc.get("accused_description"))
        else:
            name = safe_str(acc)
            fname = age = sex = address = marks = "Not Provided"

        s9_data.append([
            Paragraph(str(idx + 1), p_td_small_center),
            Paragraph(name, p_td_small),
            Paragraph(fname, p_td_small),
            Paragraph(age, p_td_small_center),
            Paragraph(sex, p_td_small_center),
            Paragraph(address, p_td_small),
            Paragraph(marks, p_td_small)
        ])

    s9_inner = Table(s9_data, colWidths=[20, 58, 65, 24, 24, 106, 70])
    s9_inner.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BLACK),
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    s9 = make_table([["9. DETAILS OF ACCUSED:", s9_inner]], [168, INNER_WIDTH])
    story.append(s9)

    # ─────────────────────────────────────────────────────
    # SECTIONS 10: Reasons for Delay
    # ─────────────────────────────────────────────────────
    delay = safe_str(fir_data.get('delay_reason') or fir_data.get('delay'), default="Reported Promptly / No Undue Delay")
    s10 = make_table([["10. REASONS FOR DELAY:", Paragraph(delay, p_td_small)]], [168, INNER_WIDTH])
    story.append(s10)

    # ─────────────────────────────────────────────────────
    # SECTIONS 11-12: Properties Stolen / Involved
    # ─────────────────────────────────────────────────────
    props_raw = fir_data.get('properties_list') or fir_data.get('properties') or []
    # Filter out empty entries
    props = []
    if isinstance(props_raw, list):
        for p in props_raw:
            if isinstance(p, dict) and any(v and str(v).strip() != "Not Provided" for v in p.values()):
                props.append(p)
            elif isinstance(p, str) and p.strip() and p.strip() != "Not Provided":
                props.append({"description": p.strip(), "value": "Not Provided"})
            elif isinstance(p, (list, tuple)) and len(p) >= 2:
                props.append({"description": str(p[0]), "value": str(p[1])})

    if not props:
        s11 = make_table([["11. PROPERTIES STOLEN / INVOLVED:", Paragraph("No properties reported stolen or involved", p_td_small)]], [168, INNER_WIDTH])
        s12 = make_table([["12. TOTAL VALUE OF PROPERTY:", Paragraph("Nil", p_td_small)]], [168, INNER_WIDTH])
    else:
        p_data = [[
            Paragraph("<b>S.No</b>", p_th_style),
            Paragraph("<b>Description</b>", p_th_style),
            Paragraph("<b>Est. Value</b>", p_th_style),
            Paragraph("<b>Recovery Status</b>", p_th_style)
        ]]
        total_val_num = 0
        has_numeric_val = False

        for idx, p in enumerate(props):
            desc = safe_str(p.get('item_name') or p.get('description') or p.get('name'))
            val = safe_str(p.get('value') or p.get('estimated_value'))
            rec = safe_str(p.get('recovered') or p.get('recovery_status'), default="Under Investigation")

            # Try to sum values
            cleaned_num = re.sub(r'[^\d.]', '', val)
            if cleaned_num:
                try:
                    total_val_num += float(cleaned_num)
                    has_numeric_val = True
                except:
                    pass

            p_data.append([
                Paragraph(str(idx + 1), p_td_small_center),
                Paragraph(desc, p_td_small),
                Paragraph(val, p_td_small),
                Paragraph(rec, p_td_small)
            ])

        p_inner = Table(p_data, colWidths=[24, 181, 81, 81])
        p_inner.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, BLACK),
            ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        s11 = make_table([["11. PROPERTIES STOLEN / INVOLVED:", p_inner]], [168, INNER_WIDTH])
        
        total_display = f"₹{total_val_num:,.2f}" if has_numeric_val else "As itemized in Section 11 above"
        s12 = make_table([["12. TOTAL VALUE OF PROPERTY:", Paragraph(total_display, p_td_small)]], [168, INNER_WIDTH])

    story.append(s11)
    story.append(s12)

    # ─────────────────────────────────────────────────────
    # SECTIONS 13-14: Inquest & Medical Examination
    # ─────────────────────────────────────────────────────
    inquest = safe_str(fir_data.get('inquest_report') or fir_data.get('ud_case_no'), default="Not Applicable")
    s13 = make_table([["13. INQUEST REPORT / U.D. CASE NO.:", Paragraph(inquest, p_td_small)]], [168, INNER_WIDTH])
    story.append(s13)

    # Extract user-provided medical examination details
    med_treat = safe_str(fir_data.get('medical_treatment'), default="")
    med_det = safe_str(fir_data.get('medical_details'), default="")
    if med_treat or med_det:
        med_summary_parts = []
        if med_treat and med_treat != "Not Provided": med_summary_parts.append(f"Treatment: {med_treat}")
        if med_det and med_det != "Not Provided": med_summary_parts.append(f"Details: {med_det}")
        med_summary = "  |  ".join(med_summary_parts) if med_summary_parts else "Not Provided"
    else:
        med_summary = "Not Required / None Reported at Time of FIR"

    s14 = make_table([["14. FIRST MEDICAL EXAMINATION:", Paragraph(med_summary, p_td_small)]], [168, INNER_WIDTH])
    story.append(s14)

    # ─────────────────────────────────────────────────────
    # SECTION 15: Complainant / Informant (FULLY POPULATED FROM FORM)
    # ─────────────────────────────────────────────────────
    c_name = safe_str(fir_data.get('complainant_name'))
    guardian_type = safe_str(fir_data.get('complainant_guardian_type'), default="Father")
    guardian_name = safe_str(
        fir_data.get('complainant_guardian_name') or 
        fir_data.get('complainant_father_name') or 
        fir_data.get('father_name'),
        default="Not Provided"
    )
    c_age = safe_str(fir_data.get('complainant_age'), default="Not Provided")
    c_gender = safe_str(fir_data.get('complainant_gender'), default="Not Provided")
    c_nat = safe_str(fir_data.get('complainant_nationality'), default="Indian")
    c_occ = safe_str(fir_data.get('complainant_occupation'), default="Not Provided")
    
    id_type = safe_str(fir_data.get('complainant_id_type'), default="")
    id_num = safe_str(fir_data.get('complainant_id_number'), default="")
    if id_type and id_num and id_type != "Not Provided" and id_num != "Not Provided":
        c_id = f"{id_type}: {id_num}"
    elif id_num and id_num != "Not Provided":
        c_id = id_num
    else:
        c_id = "Not Provided"

    c_add = safe_str(fir_data.get('complainant_address'))
    c_phone = safe_str(fir_data.get('complainant_phone'))
    c_email = safe_str(fir_data.get('complainant_email'), default="Not Provided")
    c_perm_add = safe_str(fir_data.get('complainant_permanent_address'), default=c_add)

    c_inner = Table([
        [
            Paragraph(f"<b>Name:</b> {c_name}", p_td_small), 
            Paragraph(f"<b>{guardian_type}'s Name:</b> {guardian_name}", p_td_small)
        ],
        [
            Paragraph(f"<b>Age:</b> {c_age}    <b>Gender:</b> {c_gender}", p_td_small), 
            Paragraph(f"<b>Nationality:</b> {c_nat}", p_td_small)
        ],
        [
            Paragraph(f"<b>ID Proof:</b> {c_id}", p_td_small), 
            Paragraph(f"<b>Occupation:</b> {c_occ}", p_td_small)
        ],
        [
            Paragraph(f"<b>Present Address:</b> {c_add}", p_td_small), 
            Paragraph(f"<b>Phone:</b> {c_phone}", p_td_small)
        ],
        [
            Paragraph(f"<b>Permanent Address:</b> {c_perm_add}", p_td_small), 
            Paragraph(f"<b>Email:</b> {c_email}", p_td_small)
        ]
    ], colWidths=[183, 184])
    c_inner.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    s15 = make_table([["15. COMPLAINANT / INFORMANT:", c_inner]], [168, INNER_WIDTH])
    story.append(s15)

    # ─────────────────────────────────────────────────────
    # SECTION 16: Action Taken
    # ─────────────────────────────────────────────────────
    off_name = safe_str(fir_data.get('officer_name') or fir_data.get('investigating_officer'), default="Duty Officer")
    off_rank = safe_str(fir_data.get('officer_rank'), default="Sub-Inspector")

    s16_text = f"Case registered under the cited sections and taken up for investigation. Investigation assigned to {off_name}, {off_rank}, {station}."
    s16 = make_table([["16. DETAILS OF ACTION TAKEN:", Paragraph(s16_text, p_td_small)]], [168, INNER_WIDTH])
    story.append(s16)

    # ─────────────────────────────────────────────────────
    # PAGE 2: Signatures, Statement / Gist of FIR & Prayer
    # ─────────────────────────────────────────────────────
    story.append(PageBreak())

    # 17. Signatures
    s17_left = [
        Paragraph("<b>Signature / Thumb Impression of Complainant</b>", p_td_small),
        Spacer(1, 24),
        Paragraph("___________________________________", p_td_small),
        Paragraph(f"<b>Name:</b> {c_name}", p_td_small),
        Paragraph(f"<b>Date:</b> {date_str}", p_td_small)
    ]
    s17_right = [
        Paragraph("<b>Signature of Officer-in-Charge</b>", p_td_small),
        Spacer(1, 24),
        Paragraph("___________________________________", p_td_small),
        Paragraph(f"<b>Name:</b> {off_name}", p_td_small),
        Paragraph(f"<b>Rank:</b> {off_rank}", p_td_small),
        Paragraph(f"<b>Police Station:</b> {station}", p_td_small)
    ]

    s17_table = Table([[s17_left, s17_right]], colWidths=[267, 268])
    s17_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.5, BLACK),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(s17_table)
    story.append(Spacer(1, 10))

    # Narrative / Statement Box JSON Parsing with full fallbacks
    raw_draft = safe_str(fir_data.get('draft'))
    prayer_text = safe_str(fir_data.get('action_requested') or fir_data.get('prayer'), default="")

    try:
        clean_draft = raw_draft
        if clean_draft.startswith("```json"): clean_draft = clean_draft[7:]
        if clean_draft.endswith("```"): clean_draft = clean_draft[:-3]
        parsed_draft = json.loads(clean_draft)
        if isinstance(parsed_draft, dict):
            draft_text = parsed_draft.get("narrative", raw_draft)
            if not prayer_text and "prayer" in parsed_draft:
                prayer_text = parsed_draft["prayer"]
        else:
            draft_text = raw_draft
    except Exception:
        draft_text = raw_draft

    # Fallback to complaint_text or facts if draft is empty or generic
    if not draft_text or draft_text == "Not Provided":
        draft_text = safe_str(fir_data.get('complaint_text') or fir_data.get('facts'), default="Detailed statement recorded as per oral/written complaint.")

    if not prayer_text or prayer_text == "Not Provided":
        prayer_text = "To take immediate legal action, register the FIR, investigate the matter, and recover the stolen/involved property or apprehend the accused."

    draft_text = clean_text(draft_text).replace('\n', '<br/>')
    prayer_text = clean_text(prayer_text).replace('\n', '<br/>')

    narrative_title = Paragraph(
        "<b>STATEMENT / GIST OF FIR</b>",
        ParagraphStyle('NTitle', fontName='Times-Bold', alignment=TA_CENTER, fontSize=10, leading=13, spaceAfter=6)
    )
    narrative_body = Paragraph(draft_text, p_justified)

    # Clean single-column Table with exact width to PREVENT BORDER AND TEXT OVERLAPS
    narr_table = Table([[narrative_title], [narrative_body]], colWidths=[535])
    narr_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, BLACK),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    story.append(narr_table)
    story.append(Spacer(1, 10))

    # Prayer / Action Requested Box
    prayer_title = Paragraph(
        "<b>Prayer / Action Requested:</b>",
        ParagraphStyle('PTitle', fontName='Times-Bold', alignment=TA_LEFT, fontSize=9, leading=12, spaceAfter=3)
    )
    prayer_body = Paragraph(prayer_text, p_body)

    prayer_table = Table([[prayer_title], [prayer_body]], colWidths=[535])
    prayer_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, BLACK),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    story.append(prayer_table)

    # ─────────────────────────────────────────────────────
    # WITNESSES DETAILS (If provided during complaint)
    # ─────────────────────────────────────────────────────
    witnesses_raw = fir_data.get('witnesses_list') or fir_data.get('witnesses') or []
    valid_witnesses = []
    if isinstance(witnesses_raw, list):
        for w in witnesses_raw:
            if isinstance(w, dict) and any(val and str(val).strip() != "Not Provided" for val in w.values()):
                valid_witnesses.append(w)
            elif isinstance(w, str) and w.strip() and w.strip() != "Not Provided":
                valid_witnesses.append({"name": w.strip()})

    if valid_witnesses:
        story.append(Spacer(1, 10))
        wit_title = Paragraph(
            "<b>WITNESS DETAILS RECORDED DURING COMPLAINT</b>",
            ParagraphStyle('WTitle', fontName='Times-Bold', alignment=TA_LEFT, fontSize=9, leading=12, spaceAfter=4)
        )
        wit_data = [[
            Paragraph("<b>S.No</b>", p_th_style),
            Paragraph("<b>Witness Name</b>", p_th_style),
            Paragraph("<b>Phone</b>", p_th_style),
            Paragraph("<b>Address / Information</b>", p_th_style)
        ]]
        for idx, wit in enumerate(valid_witnesses):
            w_name = safe_str(wit.get('name'))
            w_phone = safe_str(wit.get('phone'))
            w_addr = safe_str(wit.get('address'))
            wit_data.append([
                Paragraph(str(idx + 1), p_td_small_center),
                Paragraph(w_name, p_td_small),
                Paragraph(w_phone, p_td_small),
                Paragraph(w_addr, p_td_small)
            ])
        wit_inner = Table(wit_data, colWidths=[30, 140, 100, 245])
        wit_inner.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, BLACK),
            ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ]))
        wit_container = Table([[wit_title], [wit_inner]], colWidths=[535])
        wit_container.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, BLACK),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ]))
        story.append(wit_container)

    # Build the PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
