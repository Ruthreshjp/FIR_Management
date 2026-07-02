import os
from app.pdf.generator import create_fir_pdf

def generate_test_pdf():
    sample_data = {
        "complainant_name": "RUTHRESH J P",
        "complainant_address": "D.NO:4/24, GOUNDAR STREET, KADACHANALLUR, KUMARAPALAYAM, NAMAKKAL",
        "complainant_phone": "+91 790 407 3237",
        "incident_date": "01/07/2026",
        "incident_time": "19:00",
        "incident_location": "Near Market Road Intersection, Kumarapalayam",
        "accused_name": "Unknown",
        "accused_description": "black motorcycle rider",
        "properties": [
            ("Gold Chain", "₹25,000"),
            ("Not recovered", "")
        ],
        "sections": [
            "BNS 303 — Theft", 
            "BNS 115 — Voluntarily Causing Hurt",
            "IPC 379 — Theft (Ref)", 
            "IPC 323 — Hurt (Ref)"
        ],
        "officer_name": "INSPECTOR RAJ",
        "officer_rank": "Sub-Inspector",
        "officer_station": "Central Police Station, Desk 04",
        "district": "Namakkal",
        "fir_number": "142/2026",
        "draft": "The complainant while returning home from work was approached by an unknown individual riding a black motorcycle near the Market Road intersection in Kumarapalayam at approximately 19:00 hours on 01 July 2026. The suspect forcibly snatched the complainant's gold chain from his possession and subsequently pushed the complainant to the ground causing injury to the right arm. The suspect fled the scene before the complainant could record the vehicle registration number. No witnesses were present at the time of the incident."
    }
    
    pdf_bytes = create_fir_pdf(sample_data)
    
    out_path = os.path.join(os.path.dirname(__file__), "data", "sample_output_fir.pdf")
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)
        
    print(f"Generated test PDF successfully at: {out_path}")

if __name__ == "__main__":
    generate_test_pdf()
