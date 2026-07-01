import os
import json
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import io

from app.database.connection import Database
from app.agents.orchestrator import Orchestrator
from app.pdf.generator import create_fir_pdf
from app.tools.blockchain_tool import record_on_blockchain
from app.tools.email_tool import send_fir_pdf_email

app = Flask(__name__)
CORS(app)

@app.route('/api/firs', methods=['GET'])
def get_firs():
    try:
        db = Database()
        firs = db.get_all_firs()
        return jsonify(firs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/firs/generate', methods=['POST'])
def generate_fir():
    data = request.json
    complainant_name = data.get('complainant_name')
    complainant_email = data.get('complainant_email')
    police_station = data.get('police_station')
    district = data.get('district')
    complaint_text = data.get('complaint_text')

    if not all([complainant_name, complainant_email, police_station, district, complaint_text]):
        return jsonify({"error": "Missing required fields"}), 400

    def generate_events():
        orchestrator = Orchestrator()
        try:
            for step in orchestrator.generate_fir(complainant_name, complainant_email, police_station, district, complaint_text):
                # Send SSE format
                yield f"data: {json.dumps(step)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'agent': 'System', 'type': 'error', 'message': str(e)})}\n\n"
            
    return Response(generate_events(), mimetype='text/event-stream')

@app.route('/api/firs/<fir_num>/finalize', methods=['PUT'])
def finalize_fir(fir_num):
    data = request.json
    draft = data.get('draft')
    
    if not draft:
        return jsonify({"error": "Draft text is required"}), 400
        
    try:
        db = Database()
        # Decode the URL-safe FIR number back to original (FIR/2026/... -> passed as FIR%2F...)
        decoded_fir_num = fir_num.replace('_', '/')
        
        db.update_fir(decoded_fir_num, {"draft": draft})
        
        # Blockchain Recording
        tx_hash = record_on_blockchain(decoded_fir_num, draft)
        db.update_fir(decoded_fir_num, {"tx_hash": tx_hash, "status": "Under Investigation"})
        
        # Send Email
        firs = db.get_all_firs()
        final_record = next((f for f in firs if f.get('fir_number') == decoded_fir_num), None)
        
        if final_record:
            pdf_bytes = create_fir_pdf(final_record)
            send_fir_pdf_email(
                final_record.get("complainant_email", ""),
                final_record.get("complainant_name", "Citizen"),
                decoded_fir_num,
                pdf_bytes
            )
            return jsonify({"status": "success", "tx_hash": tx_hash})
        else:
            return jsonify({"error": "FIR record not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/firs/<fir_num>/pdf', methods=['GET'])
def download_pdf(fir_num):
    try:
        db = Database()
        decoded_fir_num = fir_num.replace('_', '/')
        firs = db.get_all_firs()
        final_record = next((f for f in firs if f.get('fir_number') == decoded_fir_num), None)
        
        if final_record:
            pdf_bytes = create_fir_pdf(final_record)
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"{decoded_fir_num.replace('/', '_')}.pdf"
            )
        return jsonify({"error": "Not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
