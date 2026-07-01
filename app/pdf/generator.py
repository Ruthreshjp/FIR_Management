import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER

def create_fir_pdf(fir_data: dict) -> bytes:
    """Generates a PDF buffer for the FIR."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=14
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = styles['Normal']
    
    story = []
    
    # Header
    story.append(Paragraph("FIRST INFORMATION REPORT", title_style))
    story.append(Paragraph("STATE POLICE DEPARTMENT - GOVERNMENT OF INDIA", ParagraphStyle(name='SubTitle', alignment=TA_CENTER)))
    story.append(Spacer(1, 20))
    
    # Metadata
    story.append(Paragraph(f"<b>FIR Number:</b> {fir_data.get('fir_number', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Date:</b> {fir_data.get('created_at', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>Complainant:</b> {fir_data.get('complainant_name', 'N/A')} ({fir_data.get('complainant_email', 'N/A')})", body_style))
    story.append(Paragraph(f"<b>Police Station:</b> {fir_data.get('police_station', 'N/A')}", body_style))
    story.append(Paragraph(f"<b>District/State:</b> {fir_data.get('district', 'N/A')}", body_style))
    story.append(Spacer(1, 15))
    
    # Facts
    story.append(Paragraph("1. Extracted Facts", heading_style))
    story.append(Paragraph(fir_data.get('facts', 'No facts provided.').replace('\n', '<br/>'), body_style))
    story.append(Spacer(1, 10))
    
    # Sections
    story.append(Paragraph("2. Legal Sections Applied", heading_style))
    story.append(Paragraph(fir_data.get('sections', 'No sections mapped.').replace('\n', '<br/>'), body_style))
    story.append(Spacer(1, 10))
    
    # Draft
    story.append(Paragraph("3. Formal Draft", heading_style))
    story.append(Paragraph(fir_data.get('draft', 'No draft generated.').replace('\n', '<br/>'), body_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
