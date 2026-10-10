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
from app.pdf.generator import create_fir_pdf as _create_fir_pdf_bytes

def create_fir_pdf(fir_data):
    """
    Takes a dictionary representing the FIR record and generates an in-memory PDF.
    Delegates to app.pdf.generator for complete Form II formatting without text overlaps.
    """
    pdf_bytes = _create_fir_pdf_bytes(fir_data)
    buffer = BytesIO(pdf_bytes)
    return buffer
