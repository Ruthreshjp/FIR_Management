import io
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, PageTemplate, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.graphics.shapes import Drawing, Circle, String

# Colors
BG_LABEL = colors.HexColor('#EEEEEE')
BG_ALT = colors.HexColor('#F7F7F7')
BLACK = colors.black

from reportlab.platypus import Image
import os

def draw_emblem():
    """Returns the new logo image."""
    logo_path = r"d:\auto_fir\frontend\public\logo.jpg"
    try:
        if not os.path.exists(logo_path):
            print(f"Logo not found at {logo_path}")
        return Image(logo_path, width=50, height=50)
    except Exception as e:
        print(f"Error drawing emblem image: {e}")
        # Fallback to simple placeholder if image not found
        from reportlab.graphics.shapes import Drawing, Circle, String
        d = Drawing(50, 50)
        from reportlab.lib import colors
        d.add(Circle(25, 25, 24, strokeColor=colors.black, fillColor=None, strokeWidth=1))
        return d

def footer_canvas(canvas, doc, fir_number, station_name):
    """Draws the footer on every page."""
    canvas.saveState()
    canvas.setStrokeColor(BLACK)
    canvas.setLineWidth(0.5)
    canvas.line(48, 40, 547, 40)  # Horizontal rule

    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(colors.gray)

    # Left
    canvas.drawString(48, 28, f"Page {doc.page}")

    # Center
    center_text = f"FIR No. {fir_number} — {station_name}"
    canvas.drawCentredString(A4[0] / 2.0, 28, center_text)

    # Right
    right_text = "CONFIDENTIAL — FOR OFFICIAL USE ONLY"
    canvas.drawRightString(547, 28, right_text)

    canvas.restoreState()

def make_table(data, col_widths, label_idx=0):
    """Helper to create a standard styled row table."""
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (label_idx, 0), (label_idx, -1), 'Times-Bold'),
        ('FONTSIZE', (label_idx, 0), (label_idx, -1), 9),
        ('FONTNAME', (1, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (1, 0), (-1, -1), 10),
        ('BACKGROUND', (label_idx, 0), (label_idx, -1), BG_LABEL),
        ('GRID', (0, 0), (-1, -1), 0.5, BLACK),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t

def safe_str(val, default="Not Provided"):
    if val is None or str(val).strip() == "":
        return default
    return str(val).strip()

def create_fir_pdf(fir_data: dict) -> bytes:
    buffer = io.BytesIO()

    # Extract needed fields
    fir_number = safe_str(fir_data.get('fir_number'))
    station = safe_str(fir_data.get('police_station', fir_data.get('officer_station')))
    district = safe_str(fir_data.get('district'))

    report_date = fir_data.get('created_at', '')
    date_str = "Not Provided"
    time_str = "Not Provided"
    if report_date:
        try:
            dt = datetime.datetime.fromisoformat(str(report_date).replace('Z', '+00:00'))
            date_str = dt.strftime("%d/%m/%Y")
            time_str = dt.strftime("%H:%M")
        except Exception:
            date_str = safe_str(fir_data.get('report_date'))

    # Setup Doc
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30, leftMargin=30,
        topMargin=36, bottomMargin=48
    )

    # Add page template for footer
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='fir_template', frames=frame, onPage=lambda c, d: footer_canvas(c, d, fir_number, station))
    doc.addPageTemplates([template])

    # Paragraph styles
    p_body = ParagraphStyle('FIRBody', fontName='Times-Roman', fontSize=10, leading=14)
    p_justified = ParagraphStyle('FIRJustified', parent=p_body, alignment=TA_JUSTIFY)
    p_bold = ParagraphStyle('FIRBold', fontName='Times-Bold', fontSize=10)
    p_title = ParagraphStyle('FIRTitle', fontName='Helvetica-Bold', fontSize=16, alignment=TA_CENTER, spaceAfter=2)
    p_subtitle = ParagraphStyle('FIRSub', fontName='Times-Roman', fontSize=9, alignment=TA_CENTER)

    story = []

    # ─────────────────────────────────────────────────────
    # HEADER BLOCK
    # ─────────────────────────────────────────────────────
    header_left = [
        draw_emblem(),
        Paragraph("POLICE", ParagraphStyle('H_TN', fontName='Helvetica-Bold', fontSize=13, alignment=TA_CENTER))
    ]

    header_center = [
        Spacer(1, 10),
        Paragraph("FIRST INFORMATION REPORT", p_title),
        Paragraph("(Under Section 173 BNSS / Section 154 CrPC)", p_subtitle)
    ]

    header_right = [
        Paragraph(f"<b>FIR No.:</b> <font name='Courier'>{fir_number}</font>", p_body),
        Paragraph(f"<b>Date:</b> <font name='Courier'>{date_str}</font>", p_body),
        Paragraph(f"<b>Time:</b> <font name='Courier'>{time_str}</font>", p_body),
        Paragraph(f"<b>District:</b> {district}", p_body),
        Paragraph(f"<b>Police Station:</b> {station}", p_body)
    ]

    header_table = Table([[header_left, header_center, header_right]], colWidths=[100, 286, 149])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, BLACK),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    p_table = ParagraphStyle('FIRTable', fontName='Times-Roman', fontSize=10, leading=12)
    p_table_small = ParagraphStyle('FIRTableSmall', fontName='Times-Roman', fontSize=8, leading=10)

    # ─────────────────────────────────────────────────────
    # SECTION 1: Act & Sections
    # ─────────────────────────────────────────────────────
    ipc_data = fir_data.get('ipc_sections', [])
    bns_data = fir_data.get('bns_sections', [])
    other_data = fir_data.get('other_sections', [])
    
    act_data = [["S.No", "Act", "Section", "Offense"]]
    s_no = 1
    
    def add_section_data(data_list, act_label):
        nonlocal s_no
        for s in data_list:
            sec = safe_str(s.get("section_number", s.get("section", "")))
            title = safe_str(s.get("title", s.get("offense", "")))
            act_data.append([str(s_no), act_label, Paragraph(sec, p_table_small), Paragraph(title, p_table_small)])
            s_no += 1

    if bns_data: add_section_data(bns_data, "BNS")
    if ipc_data: add_section_data(ipc_data, "IPC")
    if other_data: 
        for s in other_data:
            act = safe_str(s.get("act", ""))
            sec = safe_str(s.get("section_number", s.get("section", "")))
            title = safe_str(s.get("title", s.get("offense", "")))
            act_data.append([str(s_no), act, Paragraph(sec, p_table_small), Paragraph(title, p_table_small)])
            s_no += 1
            
    if len(act_data) == 1:
        act_data.append(["Not Provided", "Not Provided", "Not Provided", "Not Provided"])
        
    act_inner = Table(act_data, colWidths=[30, 40, 50, 275])
    act_inner.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, BLACK),
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    
    s1 = make_table([["1. ACT & SECTION(S):", act_inner]], [140, 395])
    story.append(s1)

    # ─────────────────────────────────────────────────────
    # SECTION 2: Occurrence
    # ─────────────────────────────────────────────────────
    inc_date = safe_str(fir_data.get('incident_date'))
    inc_time = safe_str(fir_data.get('incident_time'))
    day = "Not Provided"
    if inc_date != "Not Provided":
        try:
            dt = datetime.datetime.fromisoformat(inc_date.replace('Z', '+00:00'))
            day = dt.strftime("%A")
            inc_date = dt.strftime("%d/%m/%Y")
        except:
            pass

    s2_inner = Table([
        [f"Day: {day}", f"Date From: {inc_date}", "Date To: Not Provided"],
        [f"Time From: {inc_time}", "Time To: Not Provided", ""]
    ], colWidths=[130, 130, 135])
    s2_inner.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2)
    ]))
    s2 = make_table([["2. OCCURRENCE OF OFFENCE:", s2_inner]], [140, 395])
    story.append(s2)

    # ─────────────────────────────────────────────────────
    # SECTIONS 3-8
    # ─────────────────────────────────────────────────────
    info_type = safe_str(fir_data.get('information_type', 'Written'))
    
    s3 = make_table([["3. INFORMATION RECEIVED AT P.S.:", f"Date: {date_str}      Time: {time_str}      Type: {info_type}"]], [140, 395])
    story.append(s3)

    s4 = make_table([["4. GENERAL DIARY REFERENCE:", "Entry No.: Not Provided      Time: Not Provided"]], [140, 395])
    story.append(s4)

    s5 = make_table([["5. TYPE OF INFORMATION:", info_type]], [140, 395])
    story.append(s5)

    loc = safe_str(fir_data.get('incident_location'))
    landmark = safe_str(fir_data.get('incident_landmark'), default="")
    if landmark and landmark != "Not Provided":
        loc += f" (Near: {landmark})"
        
    s6_inner = Table([
        [Paragraph(f"Address: {loc}", p_table)],
        ["Distance from P.S.: Not Provided"],
        ["Direction from P.S.: Not Provided"],
        ["Beat No.: Not Provided"]
    ], colWidths=[395])
    s6_inner.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    s6 = make_table([["6. PLACE OF OCCURRENCE:", s6_inner]], [140, 395])
    story.append(s6)

    s7 = make_table([["7. OUTSIDE P.S. LIMITS:", "Yes / No: Not Provided      If Yes: Not Provided"]], [140, 395])
    story.append(s7)

    s8 = make_table([["8. BEAT NO.:", "Not Provided"]], [140, 395])
    story.append(s8)

    # ─────────────────────────────────────────────────────
    # SECTION 9: Accused
    # ─────────────────────────────────────────────────────
    s9_data = [["S.No", "Name", "Father's/Husband's Name", "Age", "Sex", "Address", "Identifying Marks"]]
    accused_list = fir_data.get('accused', [])
    
    if not accused_list:
        # Fallback to older single-field format if array is empty
        acc_name = safe_str(fir_data.get('accused_name'))
        comp_gender = safe_str(fir_data.get('complainant_gender')).lower()
        acc_sex = "Male" if comp_gender == "female" else "Not Provided"
        acc_desc = safe_str(fir_data.get('accused_description'))
        acc_veh = safe_str(fir_data.get('accused_vehicle'), default="")
        remarks = acc_veh if acc_veh and acc_veh != "Not Provided" else "Not Provided"
        if acc_desc and acc_desc != "Not Provided":
            remarks = f"{acc_desc} / {remarks}"
        s9_data.append(["1", Paragraph(acc_name, p_table_small), "Not Provided", "Not Provided", acc_sex, "Not Provided", Paragraph(remarks, p_table_small)])
    else:
        for idx, acc in enumerate(accused_list):
            name = safe_str(acc.get("name"))
            fname = safe_str(acc.get("father_name") or acc.get("husband_name"))
            age = safe_str(acc.get("age"))
            sex = safe_str(acc.get("sex"))
            address = safe_str(acc.get("address"))
            marks = safe_str(acc.get("identifying_marks"))
            s9_data.append([
                str(idx + 1),
                Paragraph(name, p_table_small),
                Paragraph(fname, p_table_small),
                Paragraph(age, p_table_small),
                Paragraph(sex, p_table_small),
                Paragraph(address, p_table_small),
                Paragraph(marks, p_table_small)
            ])

    s9_inner = Table(s9_data, colWidths=[20, 50, 70, 25, 25, 120, 85])
    s9_inner.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, BLACK),
        ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]))
    s9 = make_table([["9. DETAILS OF ACCUSED:", s9_inner]], [140, 395])
    story.append(s9)

    # ─────────────────────────────────────────────────────
    # SECTIONS 10-14
    # ─────────────────────────────────────────────────────
    delay = safe_str(fir_data.get('delay_reason'))
    s10 = make_table([["10. REASONS FOR DELAY:", Paragraph(delay, p_table)]], [140, 395])
    story.append(s10)

    # Properties
    props = fir_data.get('properties', [])
    if not props:
        s11 = make_table([["11. PROPERTIES STOLEN / INVOLVED:", "Not Provided"]], [140, 395])
        s12 = make_table([["12. TOTAL VALUE OF PROPERTY:", "Not Provided"]], [140, 395])
    else:
        p_data = [["S.No", "Description", "Estimated Value (₹)", "Remarks"]]
        for idx, p in enumerate(props):
            if isinstance(p, dict):
                desc = safe_str(p.get('description'))
                val = safe_str(p.get('value'))
            elif isinstance(p, (list, tuple)) and len(p) >= 2:
                desc = safe_str(p[0])
                val = safe_str(p[1])
            else:
                desc = safe_str(p)
                val = "Not Provided"

            p_data.append([str(idx + 1), Paragraph(desc, p_table), val, "Not Provided"])

        p_inner = Table(p_data, colWidths=[30, 206, 80, 79])
        p_inner.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, BLACK),
            ('BACKGROUND', (0, 0), (-1, 0), BG_ALT),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        s11 = make_table([["11. PROPERTIES STOLEN / INVOLVED:", p_inner]], [140, 395])
        s12 = make_table([["12. TOTAL VALUE OF PROPERTY:", "See above"]], [140, 395])

    story.append(s11)
    story.append(s12)

    s13 = make_table([["13. INQUEST REPORT / U.D. CASE NO.:", "Not Provided"]], [140, 395])
    story.append(s13)

    s14 = make_table([["14. FIRST MEDICAL EXAMINATION:", "Not Provided"]], [140, 395])
    story.append(s14)

    # ─────────────────────────────────────────────────────
    # SECTION 15: Complainant
    # ─────────────────────────────────────────────────────
    c_name = safe_str(fir_data.get('complainant_name'))
    c_add = safe_str(fir_data.get('complainant_address'))
    c_phone = safe_str(fir_data.get('complainant_phone'))
    
    id_type = safe_str(fir_data.get('complainant_id_type'), default="")
    id_num = safe_str(fir_data.get('complainant_id_number'), default="")
    if id_type and id_num and id_type != "Not Provided" and id_num != "Not Provided":
        c_id = f"{id_type} - {id_num}"
    elif id_num and id_num != "Not Provided":
        c_id = id_num
    else:
        c_id = "Not Provided"

    c_inner = Table([
        [Paragraph(f"Name: {c_name}", p_table), Paragraph("Father's/Husband's Name: Not Provided", p_table)],
        ["Age/DOB: Not Provided", "Nationality: Indian"],
        [Paragraph(f"UID/Aadhaar: {c_id}", p_table), "Occupation: Not Provided"],
        [Paragraph(f"Address: {c_add}", p_table), Paragraph(f"Phone: {c_phone}", p_table)]
    ], colWidths=[190, 205])
    c_inner.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    s15 = make_table([["15. COMPLAINANT / INFORMANT:", c_inner]], [140, 395])
    story.append(s15)

    # ─────────────────────────────────────────────────────
    # SECTION 16: Action Taken
    # ─────────────────────────────────────────────────────
    off_name = safe_str(fir_data.get('officer_name'))
    off_rank = safe_str(fir_data.get('officer_rank'))

    s16_text = f"Case registered and taken up for investigation. Investigation assigned to {off_name}, {off_rank}, {station}."
    s16 = make_table([["16. DETAILS OF ACTION TAKEN:", Paragraph(s16_text, p_body)]], [140, 395])
    story.append(s16)

    # ─────────────────────────────────────────────────────
    # PAGE 2: Signatures & Statement
    # ─────────────────────────────────────────────────────
    story.append(PageBreak())

    # 17. Signatures
    s17_left = [
        Paragraph("Signature / Thumb Impression of Complainant", p_bold),
        Spacer(1, 30),
        Paragraph("___________________________________", p_body),
        Paragraph(f"Name: {c_name}", p_body),
        Paragraph(f"Date: {date_str}", p_body)
    ]
    s17_right = [
        Paragraph("Signature of Officer-in-Charge", p_bold),
        Spacer(1, 30),
        Paragraph("___________________________________", p_body),
        Paragraph(f"Name: {off_name}", p_body),
        Paragraph(f"Rank: {off_rank}", p_body),
        Paragraph(f"Police Station: {station}", p_body)
    ]

    s17_table = Table([[s17_left, s17_right]], colWidths=[268, 267])
    s17_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.5, BLACK),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(s17_table)
    story.append(Spacer(1, 15))

    # Narrative / Statement Box JSON Parsing
    raw_draft = safe_str(fir_data.get('draft'))
    prayer_text = safe_str(fir_data.get('action_requested', 'Not Provided'))
    
    import json
    try:
        parsed_draft = json.loads(raw_draft)
        if isinstance(parsed_draft, dict):
            draft_text = parsed_draft.get("narrative", raw_draft)
            if "prayer" in parsed_draft:
                prayer_text = parsed_draft["prayer"]
    except Exception:
        draft_text = raw_draft
        
    draft_text = draft_text.replace('\n', '<br/>')
    prayer_text = prayer_text.replace('\n', '<br/>')

    narrative_title = Paragraph(
        "STATEMENT / GIST OF FIR",
        ParagraphStyle('NTitle', fontName='Times-Bold', alignment=TA_CENTER, fontSize=11, spaceAfter=8)
    )
    narrative_body = Paragraph(draft_text, p_justified)

    narr_table = Table([[narrative_title, ""], [narrative_body, ""]], colWidths=[535, 0])
    narr_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (0, 0)),
        ('SPAN', (0, 1), (0, 1)),
        ('BOX', (0, 0), (0, -1), 1, BLACK),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    story.append(narr_table)
    story.append(Spacer(1, 15))
    
    # Prayer / Action Requested Box
    prayer_title = Paragraph(
        "Prayer / Action Requested",
        ParagraphStyle('PTitle', fontName='Times-Bold', alignment=TA_LEFT, fontSize=10, spaceAfter=4)
    )
    prayer_body = Paragraph(prayer_text, p_body)
    
    prayer_table = Table([[prayer_title, ""], [prayer_body, ""]], colWidths=[535, 0])
    prayer_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (0, 0)),
        ('SPAN', (0, 1), (0, 1)),
        ('BOX', (0, 0), (0, -1), 1, BLACK),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
    ]))
    story.append(prayer_table)

    # Build the PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
