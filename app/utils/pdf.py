import re
import json
import random
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect, String

# ----------------- Helper: Simulated Barcode Flowable -----------------
def draw_simulated_barcode(text):
    d = Drawing(120, 30)
    d.add(Rect(0, 0, 120, 30, fillColor=colors.white, strokeColor=colors.white))
    random.seed(text)
    x = 10
    while x < 110:
        width = random.choice([1, 2, 3, 4])
        d.add(Rect(x, 8, width, 20, fillColor=colors.black, strokeColor=colors.black))
        x += width + random.choice([1, 2, 3])
    d.add(String(25, 0, text, fontName="Helvetica", fontSize=7, fillColor=colors.black))
    return d

# ----------------- ReportLab Markdown to Flowables -----------------
def markdown_to_flowables(text, styles):
    flowables = []
    if not text:
        return flowables
        
    lines = text.split('\n')
    in_table = False
    table_data = []
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('|'):
            if '---' in line:
                continue
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            processed_cells = []
            for cell in cells:
                cell_p = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cell)
                cell_p = re.sub(r'\*(.*?)\*', r'<i>\1</i>', cell_p)
                cell_style = ParagraphStyle(
                    'TableCellStyle',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=8,
                    leading=11,
                    textColor=colors.HexColor('#2D3748')
                )
                processed_cells.append(Paragraph(cell_p, cell_style))
                
            table_data.append(processed_cells)
            in_table = True
            continue
        else:
            if in_table:
                if table_data:
                    num_cols = len(table_data[0])
                    # Ensure all rows have exactly num_cols cells
                    for idx, row in enumerate(table_data):
                        if len(row) < num_cols:
                            table_data[idx] = row + [Paragraph("", styles['Normal'])] * (num_cols - len(row))
                        elif len(row) > num_cols:
                            table_data[idx] = row[:num_cols]
                            
                    col_widths = [522 / num_cols] * num_cols
                    if num_cols == 4:
                        col_widths = [110, 80, 80, 252]
                    
                    t = Table(table_data, colWidths=col_widths)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0B132B')),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                        ('BOTTOMPADDING', (0,0), (-1,0), 5),
                        ('TOPPADDING', (0,0), (-1,0), 5),
                        ('LEFTPADDING', (0,0), (-1,-1), 5),
                        ('RIGHTPADDING', (0,0), (-1,-1), 5),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
                        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
                    ]))
                    for i in range(num_cols):
                        table_data[0][i].style.textColor = colors.white
                        table_data[0][i].style.fontName = 'Helvetica-Bold'
                        
                    flowables.append(t)
                    flowables.append(Spacer(1, 8))
                table_data = []
                in_table = False
            
            if not line:
                flowables.append(Spacer(1, 6))
                continue
                
            if line.startswith('###'):
                header_text = line.replace('###', '').strip()
                header_text = re.sub(r'\*\*(.*?)\*\*', r'\1', header_text)
                flowables.append(Paragraph(header_text, styles['Heading3']))
                flowables.append(Spacer(1, 4))
            elif line.startswith('##'):
                header_text = line.replace('##', '').strip()
                header_text = re.sub(r'\*\*(.*?)\*\*', r'\1', header_text)
                flowables.append(Paragraph(header_text, styles['Heading2']))
                flowables.append(Spacer(1, 6))
            elif line.startswith('#'):
                header_text = line.replace('#', '').strip()
                header_text = re.sub(r'\*\*(.*?)\*\*', r'\1', header_text)
                flowables.append(Paragraph(header_text, styles['Heading1']))
                flowables.append(Spacer(1, 8))
            elif line.startswith('- ') or line.startswith('* '):
                bullet_text = line[2:].strip()
                processed_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
                processed_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', processed_text)
                flowables.append(Paragraph(f"&bull; {processed_text}", styles['CustomBullet']))
                flowables.append(Spacer(1, 3))
            else:
                processed_line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                processed_line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', processed_line)
                flowables.append(Paragraph(processed_line, styles['BodyText']))
                flowables.append(Spacer(1, 5))
                
    if in_table and table_data:
        num_cols = len(table_data[0])
        for idx, row in enumerate(table_data):
            if len(row) < num_cols:
                table_data[idx] = row + [Paragraph("", styles['Normal'])] * (num_cols - len(row))
            elif len(row) > num_cols:
                table_data[idx] = row[:num_cols]
        col_widths = [522 / num_cols] * num_cols
        if num_cols == 4:
            col_widths = [110, 80, 80, 252]
        t = Table(table_data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0B132B')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,0), 5),
            ('TOPPADDING', (0,0), (-1,0), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
        ]))
        for i in range(num_cols):
            table_data[0][i].style.textColor = colors.white
            table_data[0][i].style.fontName = 'Helvetica-Bold'
        flowables.append(t)
        flowables.append(Spacer(1, 8))
        
    return flowables

# ----------------- Main PDF Generator Function -----------------
def create_fir_pdf(fir_data):
    """
    Takes a dictionary representing the FIR record and generates an in-memory PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'FIRTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0A0F24'),
        alignment=1,
        spaceAfter=2
    )
    
    subtitle_style = ParagraphStyle(
        'FIRSub',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#4A5568'),
        alignment=1,
        spaceAfter=12
    )
    
    section_heading = ParagraphStyle(
        'FIRSecHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0A0F24'),
        spaceBefore=10,
        spaceAfter=5,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'FIRBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1A202C'),
        spaceBefore=2,
        spaceAfter=2
    )
    
    bullet_style = ParagraphStyle(
        'FIRBullet',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1A202C'),
        leftIndent=15,
        spaceBefore=1,
        spaceAfter=1
    )
    
    meta_label_style = ParagraphStyle(
        'FIRMetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#0A0F24')
    )
    
    meta_val_style = ParagraphStyle(
        'FIRMetaVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#2D3748')
    )

    styles['Heading1'] = title_style
    styles['Heading2'] = section_heading
    styles['Heading3'] = section_heading
    styles['BodyText'] = body_style
    styles['CustomBullet'] = bullet_style
    
    story = []
    
    # 1. Header Banner & Barcode
    fir_no = fir_data.get("fir_number", "DRAFT")
    header_data = [
        [
            Paragraph("<b>STATE POLICE DEPARTMENT</b><br/>GOVERNMENT OF INDIA", meta_label_style),
            draw_simulated_barcode(fir_no)
        ]
    ]
    header_table = Table(header_data, colWidths=[4*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("FIRST INFORMATION REPORT", title_style))
    story.append(Paragraph("(Record of Information Under Section 154 CrPC / Section 173 BNSS, 2023)", subtitle_style))
    
    # --- Helper to handle empty fields ---
    def get_val(key, default="Not Provided"):
        val = fir_data.get(key)
        if val is None or str(val).strip() == "":
            return default
        return str(val).strip()

    # 2. Incident Details Table
    story.append(Paragraph("1. INCIDENT DETAILS", section_heading))
    incident_date = get_val("incident_date")
    incident_time = get_val("incident_time")
    incident_location = get_val("incident_location")
    police_station = get_val("incident_station", get_val("police_station"))
    district = get_val("incident_district", get_val("district"))
    
    inc_data = [
        [Paragraph("Date of Occurrence:", meta_label_style), Paragraph(incident_date, meta_val_style)],
        [Paragraph("Time of Occurrence:", meta_label_style), Paragraph(incident_time, meta_val_style)],
        [Paragraph("Place of Occurrence:", meta_label_style), Paragraph(incident_location, meta_val_style)],
        [Paragraph("Police Station:", meta_label_style), Paragraph(police_station, meta_val_style)],
        [Paragraph("District:", meta_label_style), Paragraph(district, meta_val_style)]
    ]
    
    inc_table = Table(inc_data, colWidths=[2.0*inch, 5.2*inch])
    inc_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(inc_table)
    story.append(Spacer(1, 10))

    # 3. Complainant Details Table
    story.append(Paragraph("2. COMPLAINANT / INFORMANT DETAILS", section_heading))
    
    comp_name = get_val("complainant_name")
    comp_father = get_val("complainant_father_name")
    comp_age = get_val("complainant_age")
    comp_gender = get_val("complainant_gender")
    comp_occ = get_val("complainant_occupation")
    comp_phone = get_val("complainant_phone")
    comp_email = get_val("complainant_email")
    comp_address = get_val("complainant_address")
    
    id_type = get_val("complainant_id_type", "")
    id_num = get_val("complainant_id_number", "")
    id_proof = f"{id_type} {id_num}".strip()
    if not id_proof: id_proof = "Not Provided"

    comp_data = [
        [Paragraph("Name:", meta_label_style), Paragraph(comp_name, meta_val_style), Paragraph("Age/Gender:", meta_label_style), Paragraph(f"{comp_age} / {comp_gender}", meta_val_style)],
        [Paragraph("Father/Husband Name:", meta_label_style), Paragraph(comp_father, meta_val_style), Paragraph("Occupation:", meta_label_style), Paragraph(comp_occ, meta_val_style)],
        [Paragraph("Phone:", meta_label_style), Paragraph(comp_phone, meta_val_style), Paragraph("Email:", meta_label_style), Paragraph(comp_email, meta_val_style)],
        [Paragraph("ID Proof:", meta_label_style), Paragraph(id_proof, meta_val_style), Paragraph("", meta_label_style), Paragraph("", meta_val_style)],
        [Paragraph("Address:", meta_label_style), Paragraph(comp_address, meta_val_style), Paragraph("", meta_label_style), Paragraph("", meta_val_style)]
    ]
    
    comp_table = Table(comp_data, colWidths=[1.5*inch, 2.1*inch, 1.5*inch, 2.1*inch])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('SPAN', (1, 4), (3, 4)) # Span address across remaining cols
    ]))
    
    # Handle complainant photo if present
    complainant_photo = fir_data.get("complainant_photo")
    if complainant_photo:
        try:
            if isinstance(complainant_photo, bytes):
                img_data = BytesIO(complainant_photo)
            elif isinstance(complainant_photo, str) and complainant_photo.startswith("data:image"):
                import base64
                header, encoded = complainant_photo.split(",", 1)
                img_data = BytesIO(base64.b64decode(encoded))
            else:
                img_data = complainant_photo
                
            photo_flowable = Image(img_data, width=1.0*inch, height=1.0*inch)
            side_table = Table([[comp_table, photo_flowable]], colWidths=[6.0*inch, 1.2*inch])
            side_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            story.append(side_table)
        except Exception:
            story.append(comp_table)
    else:
        story.append(comp_table)
        
    story.append(Spacer(1, 10))

    # 4. Accused Details
    story.append(Paragraph("3. DETAILS OF KNOWN / SUSPECTED / UNKNOWN ACCUSED", section_heading))
    accused_list = fir_data.get("accused_list", [])
    if not accused_list:
        # Fallback to old format if present
        acc_name = get_val("accused_name", "")
        if acc_name and acc_name != "Not Provided":
            accused_list = [{"name": acc_name, "address": get_val("accused_description", "")}]
            
    if not accused_list:
        story.append(Paragraph("Not Provided / Unknown", body_style))
    else:
        acc_data = [[Paragraph("<b>S.No</b>", meta_label_style), Paragraph("<b>Name</b>", meta_label_style), Paragraph("<b>Age/Gender</b>", meta_label_style), Paragraph("<b>Relation</b>", meta_label_style), Paragraph("<b>Address / Details</b>", meta_label_style)]]
        for i, acc in enumerate(accused_list):
            name = acc.get("name", "") or "Not Provided"
            age = acc.get("age", "")
            gender = acc.get("gender", "")
            age_gender = f"{age} {gender}".strip() or "Not Provided"
            rel = acc.get("relation", "") or "Not Provided"
            addr = acc.get("address", "") or "Not Provided"
            
            acc_data.append([
                Paragraph(str(i+1), meta_val_style),
                Paragraph(name, meta_val_style),
                Paragraph(age_gender, meta_val_style),
                Paragraph(rel, meta_val_style),
                Paragraph(addr, meta_val_style)
            ])
            
        acc_table = Table(acc_data, colWidths=[0.5*inch, 1.5*inch, 1.0*inch, 1.2*inch, 3.0*inch])
        acc_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(acc_table)
        
    story.append(Spacer(1, 10))
    
    # 5. Witness Details
    story.append(Paragraph("4. DETAILS OF WITNESSES", section_heading))
    witnesses_list = fir_data.get("witnesses_list", [])
    if not witnesses_list:
        story.append(Paragraph("Not Provided", body_style))
    else:
        wit_data = [[Paragraph("<b>S.No</b>", meta_label_style), Paragraph("<b>Name</b>", meta_label_style), Paragraph("<b>Phone</b>", meta_label_style), Paragraph("<b>Address</b>", meta_label_style)]]
        for i, wit in enumerate(witnesses_list):
            name = wit.get("name", "") or "Not Provided"
            phone = wit.get("phone", "") or "Not Provided"
            addr = wit.get("address", "") or "Not Provided"
            wit_data.append([
                Paragraph(str(i+1), meta_val_style),
                Paragraph(name, meta_val_style),
                Paragraph(phone, meta_val_style),
                Paragraph(addr, meta_val_style)
            ])
        wit_table = Table(wit_data, colWidths=[0.5*inch, 2.0*inch, 1.5*inch, 3.2*inch])
        wit_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(wit_table)
    
    story.append(Spacer(1, 10))
    
    # 6. Incident Facts / Narrative
    story.append(Paragraph("5. STATEMENT / GIST OF FIR", section_heading))
    try:
        draft_str = str(fir_data.get("draft", "{}")).strip()
        if draft_str.startswith("```json"):
            draft_str = draft_str[7:]
        if draft_str.endswith("```"):
            draft_str = draft_str[:-3]
        draft_json = json.loads(draft_str)
        narrative = draft_json.get("narrative", fir_data.get("facts", "Not Provided"))
        prayer = draft_json.get("prayer", "")
    except Exception as e:
        print("PDF rendering JSON parse error on draft:", e)
        # If it's not valid JSON, it might just be raw text
        narrative = fir_data.get("draft", fir_data.get("facts", "Not Provided"))
        prayer = ""
        
    story.append(Paragraph(narrative, body_style))
    story.append(Spacer(1, 10))
    
    if prayer:
        story.append(Paragraph("<b>Action Requested:</b> " + prayer, body_style))
        story.append(Spacer(1, 10))
    
    # 7. Legal Sections
    story.append(Paragraph("6. LEGAL PROVISIONS INVOKED", section_heading))
    
    def render_section_list(title, sec_list):
        if not sec_list: return
        story.append(Paragraph(f"<b>{title}</b>", body_style))
        for sec in sec_list:
            if isinstance(sec, dict):
                act = sec.get('act', '')
                num = sec.get('section_number', '')
                off = sec.get('offense', '')
                story.append(Paragraph(f"&bull; {act} {num} - {off}", bullet_style))
            else:
                story.append(Paragraph(f"&bull; {sec}", bullet_style))
        story.append(Spacer(1, 8))
        
    render_section_list("BNS Sections", fir_data.get("bns_sections", []))
    render_section_list("IPC Sections", fir_data.get("ipc_sections", []))
    render_section_list("Other Sections", fir_data.get("other_sections", []))
    
    # 8. Case Notes History (if any)
    notes = fir_data.get("case_notes", [])
    if notes:
        story.append(Spacer(1, 8))
        story.append(Paragraph("7. CASE JOURNAL UPDATES (INVESTIGATION TRACKING)", section_heading))
        notes_table_data = [[Paragraph("<b>Date/Time</b>", meta_label_style), Paragraph("<b>Officer</b>", meta_label_style), Paragraph("<b>Progress Journal Notes</b>", meta_label_style)]]
        
        for n in notes:
            # Parse timestamp to clean format
            ts_str = n.get("timestamp", "")
            try:
                dt_obj = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                ts_str = dt_obj.strftime("%d-%m-%Y %H:%M")
            except Exception:
                pass
            notes_table_data.append([
                Paragraph(ts_str, meta_val_style),
                Paragraph(n.get("officer", "Officer"), meta_val_style),
                Paragraph(n.get("note", ""), meta_val_style)
            ])
            
        notes_table = Table(notes_table_data, colWidths=[1.3*inch, 1.3*inch, 4.6*inch])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(notes_table)

    # 7. Signatures
    story.append(Spacer(1, 20))
    sig_data = [
        [
            Paragraph("_____________________________<br/>Signature of Complainant / Informant", meta_label_style),
            Paragraph("_____________________________<br/>Signature of Station Duty Officer", meta_label_style)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[3.6*inch, 3.6*inch])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    
    # Keep signatures block together
    story.append(KeepTogether(sig_table))
    
    doc.build(story)
    buffer.seek(0)
    return buffer
