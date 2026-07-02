import io
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, PageTemplate
from reportlab.lib import colors
from reportlab.lib.units import pt
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Circle, String

# Colors
BG_LABEL = colors.HexColor('#EEEEEE')
BG_ALT = colors.HexColor('#F7F7F7')
BLACK = colors.black

def draw_emblem() -> Drawing:
    """Draws a simple placeholder police emblem."""
    d = Drawing(50, 50)
    d.add(Circle(25, 25, 24, strokeColor=BLACK, fillColor=None, strokeWidth=1))
    d.add(Circle(25, 25, 18, strokeColor=BLACK, fillColor=None, strokeWidth=0.5))
    d.add(String(12, 25, "POLICE", fontSize=8, fontName="Helvetica-Bold"))
    d.add(String(22, 12, "*", fontSize=14, fontName="Helvetica"))
    return d

def footer_canvas(canvas, doc, fir_number, station_name):
    """Draws the footer on every page."""
    canvas.saveState()
    canvas.setStrokeColor(BLACK)
    canvas.setLineWidth(0.5)
    canvas.line(48*pt, 40*pt, 547*pt, 40*pt)  # Horizontal rule
    
    canvas.setFont("Times-Roman", 8)
    canvas.setFillColor(colors.gray)
    
    # Left
    canvas.drawString(48*pt, 28*pt, f"Page {doc.page} of ?") # ReportLab natively handles total pages with multi-pass if needed, but simple for now
    
    # Center
    center_text = f"FIR No. {fir_number} — {station_name}"
    canvas.drawCentredString(A4[0]/2.0, 28*pt, center_text)
    
    # Right
    right_text = "CONFIDENTIAL — FOR OFFICIAL USE ONLY"
    canvas.drawRightString(547*pt, 28*pt, right_text)
    
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

def create_fir_pdf(fir_data: dict) -> bytes:
    buffer = io.BytesIO()
    
    # Extract needed fields
    fir_number = fir_data.get('fir_number', 'N/A')
    station = fir_data.get('police_station', fir_data.get('officer_station', 'Unknown PS'))
    district = fir_data.get('district', 'Unknown District')
    
    report_date = fir_data.get('created_at', '')
    date_str = ""
    time_str = ""
    if report_date:
        try:
            dt = datetime.datetime.fromisoformat(report_date.replace('Z', '+00:00'))
            date_str = dt.strftime("%d/%m/%Y")
            time_str = dt.strftime("%H:%M")
        except:
            date_str = fir_data.get('report_date', 'N/A')
            time_str = "N/A"
            
    # Setup Doc
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=48*pt, leftMargin=48*pt,
        topMargin=36*pt, bottomMargin=48*pt # extra bottom margin for footer
    )
    
    # Add page template for footer
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id='normal')
    template = PageTemplate(id='test', frames=frame, onPage=lambda c, d: footer_canvas(c, d, fir_number, station))
    doc.addPageTemplates([template])
    
    styles = getSampleStyleSheet()
    p_body = ParagraphStyle('FIRBody', fontName='Times-Roman', fontSize=10, leading=14)
    p_justified = ParagraphStyle('FIRJustified', parent=p_body, alignment=TA_JUSTIFY)
    p_bold = ParagraphStyle('FIRBold', fontName='Times-Bold', fontSize=10)
    p_title = ParagraphStyle('FIRTitle', fontName='Helvetica-Bold', fontSize=16, alignment=TA_CENTER, spaceAfter=2)
    p_subtitle = ParagraphStyle('FIRSub', fontName='Times-Roman', fontSize=9, alignment=TA_CENTER)
    
    story = []
    
    # -----------------------------------------------------
    # HEADER BLOCK
    # -----------------------------------------------------
    header_left = [
        draw_emblem(),
        Paragraph("TAMIL NADU POLICE", ParagraphStyle('H_TN', fontName='Helvetica-Bold', fontSize=13)),
        Paragraph(station, ParagraphStyle('H_ST', fontName='Times-Roman', fontSize=9))
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
    
    header_table = Table([[header_left, header_center, header_right]], colWidths=[130*pt, 220*pt, 149*pt])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 1, BLACK),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    
    # -----------------------------------------------------
    # SECTION 1: Act & Sections
    # -----------------------------------------------------
    sec_data = fir_data.get('sections', [])
    if isinstance(sec_data, str):
        sec_text = sec_data.replace('\n', '<br/>')
    else:
        sec_text = "<br/>".join([f"{s.get('act', 'Act')} - {s.get('section', '')} ({s.get('title', '')})" if isinstance(s, dict) else str(s) for s in sec_data])
    if not sec_text:
        sec_text = "None provided"
        
    s1 = make_table([["1. ACT & SECTION(S):", Paragraph(sec_text, p_body)]], [120*pt, 379*pt])
    story.append(s1)
    
    # -----------------------------------------------------
    # SECTION 2: Occurrence
    # -----------------------------------------------------
    inc_date = fir_data.get('incident_date', '—')
    inc_time = fir_data.get('incident_time', '—')
    s2_inner = Table([
        [f"Day: —", f"Date From: {inc_date}", f"Date To: —"],
        [f"Time From: {inc_time}", f"Time To: —", ""]
    ], colWidths=[120*pt, 130*pt, 119*pt])
    s2_inner.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Times-Roman'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2)
    ]))
    s2 = make_table([["2. OCCURRENCE OF OFFENCE:", s2_inner]], [120*pt, 379*pt])
    story.append(s2)
    
    # -----------------------------------------------------
    # SECTIONS 3-8
    # -----------------------------------------------------
    s3 = make_table([["3. INFORMATION RECEIVED AT P.S.:", f"Date: {date_str}   Time: {time_str}   Type: Written"]], [120*pt, 379*pt])
    story.append(s3)
    
    s4 = make_table([["4. GENERAL DIARY REFERENCE:", "Entry No. ______   Time: ______"]], [120*pt, 379*pt])
    story.append(s4)
    
    s5 = make_table([["5. TYPE OF INFORMATION:", Paragraph("<b>Written</b> / Oral", p_body)]], [120*pt, 379*pt])
    story.append(s5)
    
    loc = fir_data.get('incident_location', '—')
    landmark = fir_data.get('incident_landmark', '')
    if landmark: loc += f" (Near: {landmark})"
    s6_inner = Table([
        [f"Address: {loc}"],
        ["Distance from P.S.: —"],
        ["Direction from P.S.: —"]
    ], colWidths=[369*pt])
    s6_inner.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Times-Roman'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    s6 = make_table([["6. PLACE OF OCCURRENCE:", s6_inner]], [120*pt, 379*pt])
    story.append(s6)
    
    s7 = make_table([["7. OUTSIDE P.S. LIMITS (IF YES, NAME OF P.S.):", "Yes / No   |   If Yes: _______________"]], [120*pt, 379*pt])
    story.append(s7)
    
    s8 = make_table([["8. BEAT NO.:", ""]], [120*pt, 379*pt])
    story.append(s8)
    
    # -----------------------------------------------------
    # SECTION 9: Accused
    # -----------------------------------------------------
    acc_name = fir_data.get('accused_name', 'Unknown')
    if not acc_name: acc_name = "Unknown"
    
    comp_gender = fir_data.get('complainant_gender', '').lower()
    acc_sex = "Male" if comp_gender == "female" else "—" # placeholder logic
    acc_desc = fir_data.get('accused_description', '—')
    acc_veh = fir_data.get('accused_vehicle', '—')
    remarks = acc_veh if acc_veh else "—"
    if not acc_desc: acc_desc = "—"
    
    s9_data = [
        ["S.No.", "Name", "Father's Name", "Age", "Sex", "Nationality", "Address", "Identifying Marks/Remarks"],
        ["1.", acc_name, "—", "—", acc_sex, "Indian", "—", f"{acc_desc} / {remarks}"]
    ]
    s9_inner = Table(s9_data, colWidths=[25*pt, 70*pt, 60*pt, 25*pt, 30*pt, 50*pt, 40*pt, 69*pt])
    s9_inner.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Times-Roman'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, BLACK),
        ('BACKGROUND', (0,0), (-1,0), BG_ALT),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    
    s9 = make_table([["9. DETAILS OF KNOWN / SUSPECTED ACCUSED:", s9_inner]], [120*pt, 379*pt])
    story.append(s9)
    
    # -----------------------------------------------------
    # SECTIONS 10-14
    # -----------------------------------------------------
    s10 = make_table([["10. REASONS FOR DELAY IN REPORTING:", "None"]], [120*pt, 379*pt])
    story.append(s10)
    
    # Properties
    props = fir_data.get('properties', [])
    if not props:
        s11 = make_table([["11. PARTICULARS OF PROPERTIES STOLEN / INVOLVED:", "Not Applicable"]], [120*pt, 379*pt])
        s12 = make_table([["12. TOTAL VALUE OF PROPERTIES STOLEN:", "Not Ascertained"]], [120*pt, 379*pt])
    else:
        # Assuming props is list of dicts or tuples
        p_data = [["S.No.", "Description", "Estimated Value (₹)", "Remarks"]]
        total_val = 0
        has_val = False
        for idx, p in enumerate(props):
            if isinstance(p, dict):
                desc = p.get('description', '')
                val = str(p.get('value', ''))
            elif isinstance(p, (list, tuple)) and len(p) >= 2:
                desc = p[0]
                val = p[1]
            else:
                desc = str(p)
                val = "—"
            
            p_data.append([str(idx+1)+".", desc, val, "—"])
        
        p_inner = Table(p_data, colWidths=[30*pt, 180*pt, 80*pt, 79*pt])
        p_inner.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Times-Roman'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.5, BLACK),
            ('BACKGROUND', (0,0), (-1,0), BG_ALT),
        ]))
        s11 = make_table([["11. PARTICULARS OF PROPERTIES STOLEN / INVOLVED:", p_inner]], [120*pt, 379*pt])
        s12 = make_table([["12. TOTAL VALUE OF PROPERTIES STOLEN:", "₹ See above"]], [120*pt, 379*pt])
        
    story.append(s11)
    story.append(s12)
    
    s13 = make_table([["13. INQUEST REPORT / POST MORTEM EXAMINATION REPORT:", "Not Applicable"]], [120*pt, 379*pt])
    story.append(s13)
    
    s14 = make_table([["14. FIRST MEDICAL EXAMINATION OF THE INJURED:", "Not Applicable"]], [120*pt, 379*pt])
    story.append(s14)
    
    # -----------------------------------------------------
    # SECTION 15: Complainant
    # -----------------------------------------------------
    c_name = fir_data.get('complainant_name', '—')
    c_add = fir_data.get('complainant_address', '—')
    c_phone = fir_data.get('complainant_phone', '—')
    c_id = f"{fir_data.get('complainant_id_type', '—')} - {fir_data.get('complainant_id_number', '')}".strip(" -")
    if not c_id: c_id = "—"
    
    c_inner = Table([
        [f"Name: {c_name}"],
        ["Father's/Husband's Name: —"],
        ["Date of Birth: —"],
        ["Nationality: Indian"],
        [f"Passport / ID No.: {c_id}"],
        ["Occupation: —"],
        [f"Address: {c_add}"],
        [f"Phone: {c_phone}"]
    ], colWidths=[369*pt])
    c_inner.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Times-Roman'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    
    s15 = make_table([["15. COMPLAINANT / INFORMANT:", c_inner]], [120*pt, 379*pt])
    story.append(s15)
    
    # -----------------------------------------------------
    # SECTION 16: Action Taken
    # -----------------------------------------------------
    off_name = fir_data.get('officer_name', '—')
    off_rank = fir_data.get('officer_rank', '—')
    
    s16_text = f"Case registered and taken up for investigation. Investigation assigned to {off_name}, {off_rank}, {station}."
    s16 = make_table([["16. DETAILS OF ACTION TAKEN SINCE FIRST INFORMATION:", Paragraph(s16_text, p_body)]], [120*pt, 379*pt])
    story.append(s16)
    
    # -----------------------------------------------------
    # SECTION 17: Signatures
    # -----------------------------------------------------
    s17_left = [
        Paragraph("Signature / Left Thumb Impression of Complainant", p_bold),
        Spacer(1, 30),
        Paragraph("___________________________________", p_body),
        Paragraph(f"Name: {c_name}", p_body),
        Paragraph(f"Date: {date_str}", p_body)
    ]
    s17_right = [
        Paragraph("Signature of Officer-in-Charge", p_bold),
        Spacer(1, 30),
        Paragraph("___________________________________", p_body),
        Paragraph(f"{off_name}", p_body),
        Paragraph(f"{off_rank}", p_body),
        Paragraph(f"{station}", p_body)
    ]
    
    s17_table = Table([[s17_left, s17_right]], colWidths=[250*pt, 249*pt])
    s17_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 0.5, BLACK),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(s17_table)
    story.append(Spacer(1, 15))
    
    # -----------------------------------------------------
    # NARRATIVE BOX
    # -----------------------------------------------------
    draft_text = fir_data.get('draft', 'No draft generated.')
    # Pre-process markdown slightly if it exists, simple replacement
    draft_text = draft_text.replace('\n', '<br/>').replace('**', '<b>').replace('**', '</b>')
    
    narrative_title = Paragraph("STATEMENT / GIST OF FIR", ParagraphStyle('NTitle', fontName='Times-Bold', alignment=TA_CENTER, fontSize=11, spaceAfter=8))
    narrative_body = Paragraph(draft_text, p_justified)
    
    narr_table = Table([[ [narrative_title, narrative_body] ]], colWidths=[499*pt])
    narr_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, BLACK),
        ('LEFTPADDING', (0,0), (-1,-1), 15),
        ('RIGHTPADDING', (0,0), (-1,-1), 15),
        ('TOPPADDING', (0,0), (-1,-1), 15),
        ('BOTTOMPADDING', (0,0), (-1,-1), 15),
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
    ]))
    story.append(narr_table)
    
    # Build
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
