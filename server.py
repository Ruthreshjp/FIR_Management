import os
import json
from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
import io

from app.database.connection import Database
from app.agents.orchestrator import Orchestrator
from app.pdf.generator import create_fir_pdf

app = Flask(__name__)
CORS(app)

from app.retrieval.chroma_store import initialize_chroma_store, collection

@app.route('/api/firs', methods=['GET'])
def get_firs():
    try:
        db = Database()
        firs = db.get_all_firs()
        
        # Calculate summary
        open_this_month = 0
        pending_review = 0
        now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        
        for f in firs:
            status = f.get('status', '').lower()
            if status in ('draft', 'in review', 'pending review'):
                pending_review += 1
                
            created_at = f.get('created_at')
            if created_at:
                try:
                    dt = __import__("datetime").datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if dt.year == now.year and dt.month == now.month:
                        open_this_month += 1
                except:
                    pass

        # Get ChromaDB count
        initialize_chroma_store()
        total_sections = 0
        try:
            total_sections = collection.count()
        except:
            pass
            
        summary = {
            "open_this_month": open_this_month,
            "pending_review": pending_review,
            "total_sections_indexed": total_sections
        }
        
        return jsonify({
            "firs": firs,
            "summary": summary
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from app.utils.date_parser import resolve_relative_dates

@app.route('/api/firs/generate', methods=['POST'])
def generate_fir():
    data = request.json
    
    # Required fields validation
    required = ['complainant_name', 'complainant_address', 'complainant_city', 'complainant_phone', 'incident_location', 'incident_date', 'incident_time', 'complaint_text']
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    # Parse and format the explicit incident_date
    from datetime import datetime
    try:
        data['incident_date'] = datetime.strptime(data['incident_date'], "%Y-%m-%d").strftime("%d %B %Y")
    except ValueError:
        pass # keep as is if parsing fails

    def generate_events():
        orchestrator = Orchestrator()
        try:
            for step in orchestrator.generate_fir(data):
                # Send SSE format
                yield f"data: {json.dumps(step)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'agent': 'System', 'type': 'error', 'message': str(e)})}\n\n"
            
    return Response(generate_events(), mimetype='text/event-stream')

from app.retrieval.chroma_store import search_legal_sections

@app.route('/api/laws', methods=['GET'])
def get_laws():
    try:
        act = request.args.get('act', 'ALL').upper()
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 25))
        search = request.args.get('search', '').strip()
        
        ipc_path = os.path.join("data", "processed", "ipc_sections.json")
        bns_path = os.path.join("data", "processed", "bns_sections.json")
        
        ipc_data = json.load(open(ipc_path, 'r', encoding='utf-8')) if os.path.exists(ipc_path) else []
        bns_data = json.load(open(bns_path, 'r', encoding='utf-8')) if os.path.exists(bns_path) else []
        
        # Format the records to be consistent
        def format_record(r, act_name):
            return {
                "act": act_name,
                "section_number": r.get('Section', ''),
                "section_name": r.get('Offense', r.get('offense', r.get('Description', r.get('description', '')))),
                "description": r.get('Punishment', r.get('punishment', '')),
                "cognizable": r.get('Cognizable', r.get('cognizable', '')),
                "bailable": r.get('Bailable', r.get('bailable', '')),
                "corresponding_section": r.get('Corresponding Section', r.get('corresponding_section', ''))
            }

        if search:
            results = search_legal_sections(search, top_k=20)
            formatted = [format_record(r, 'BNS' if 'BNS' in str(r.get('Section','')) else 'IPC') for r in results]
            if act != 'ALL':
                formatted = [r for r in formatted if r['act'] == act]
            return jsonify({
                "total": len(formatted),
                "page": 1,
                "counts": {"ipc": len(ipc_data), "bns": len(bns_data), "all": len(ipc_data)+len(bns_data)},
                "results": formatted
            })
            
        # Combine all based on filter
        combined = []
        if act in ('IPC', 'ALL'):
            combined.extend([format_record(r, 'IPC') for r in ipc_data])
        if act in ('BNS', 'ALL'):
            combined.extend([format_record(r, 'BNS') for r in bns_data])
            
        total = len(combined)
        
        # Paginate
        start = (page - 1) * limit
        end = start + limit
        paginated = combined[start:end]
        
        return jsonify({
            "total": total,
            "page": page,
            "counts": {"ipc": len(ipc_data), "bns": len(bns_data), "all": len(ipc_data)+len(bns_data)},
            "results": paginated
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from collections import Counter
from datetime import datetime
import statistics

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        db = Database()
        firs = db.get_all_firs()
        
        # 1. FIRs Per Month
        month_counts = Counter()
        for f in firs:
            created_at = f.get('created_at', '')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    month_str = dt.strftime("%b %Y")
                    month_counts[month_str] += 1
                except:
                    pass
        # Sort chronologically if needed, but for simplicity, we'll just return as is
        firs_per_month = [{"month": k, "count": v} for k, v in month_counts.items()]
        
        # 2. Top Sections
        section_counts = Counter()
        section_labels = {}
        for f in firs:
            sections = f.get('sections', [])
            if isinstance(sections, str):
                continue
            for s in sections:
                if isinstance(s, dict):
                    sec = s.get('section', '')
                    if sec:
                        section_counts[sec] += 1
                        section_labels[sec] = s.get('title', 'Unknown Offense')
                    
        top_sections = [{"section": k, "label": section_labels.get(k, ''), "count": v} 
                        for k, v in section_counts.most_common(5)]
                        
        # 3. Status Breakdown
        status_counts = Counter(f.get('status', 'Draft').lower() for f in firs)
        status_breakdown = {
            "draft": status_counts.get("draft", 0),
            "review": status_counts.get("in review", 0) + status_counts.get("pending review", 0),
            "filed": status_counts.get("finalized", 0) + status_counts.get("filed", 0) + status_counts.get("under investigation", 0)
        }
        
        # 4. Average Draft Time
        avg_draft_time = 142 # Fallback/stub if we don't have enough data
        
        return jsonify({
            "firs_per_month": firs_per_month,
            "top_sections": top_sections,
            "status_breakdown": status_breakdown,
            "avg_draft_time_seconds": avg_draft_time
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        
        mock_hash = "0xmockhash1234567890abcdef"
        
        db.update_fir(decoded_fir_num, {
            "status": "Finalized",
            "draft": draft,
            "tx_hash": mock_hash,
            "updated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        })
        
        return jsonify({
            "status": "success",
            "message": "FIR finalized successfully",
            "tx_hash": mock_hash
        })
            
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
    app.run(port=5000, debug=True, use_reloader=False, threaded=True)
