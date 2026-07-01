from datetime import datetime
from app.agents.intake_agent import IntakeAgent
from app.agents.legal_agent import LegalAgent
from app.agents.drafting_agent import DraftingAgent
from app.database.connection import Database

class Orchestrator:
    def __init__(self):
        self.intake = IntakeAgent()
        self.legal = LegalAgent()
        self.drafting = DraftingAgent()
        
    def generate_fir(self, complainant_name: str, complainant_email: str, police_station: str, district: str, complaint_text: str):
        """
        Coordinates the 3 agents in sequence, manages state, and yields progress.
        Yields dictionaries with step status and finally the complete FIR record.
        """
        yield {"agent": "System", "type": "status", "message": "Initializing pipeline..."}
        
        # 1. Intake
        yield {"agent": "Intake Agent", "type": "header", "message": "Extracting facts from complaint..."}
        facts = self.intake.run(complaint_text)
        yield {"agent": "Intake Agent", "type": "thought", "message": facts}
        
        # 2. Legal Mapping
        yield {"agent": "Legal Agent", "type": "header", "message": "Mapping facts to IPC & BNS sections..."}
        sections = self.legal.run(facts)
        yield {"agent": "Legal Agent", "type": "thought", "message": sections}
        
        # 3. Drafting
        yield {"agent": "Drafting Agent", "type": "header", "message": "Drafting formal FIR document..."}
        draft = self.drafting.run(facts, sections)
        yield {"agent": "Drafting Agent", "type": "thought", "message": draft}
        
        # 4. Save to Database
        yield {"agent": "System", "type": "status", "message": "Saving FIR to database..."}
        fir_record = {
            "fir_number": f"FIR/{datetime.now().strftime('%Y/%m%d%H%M%S')}",
            "complainant_name": complainant_name,
            "complainant_email": complainant_email,
            "police_station": police_station,
            "district": district,
            "complaint_text": complaint_text,
            "facts": facts,
            "sections": sections,
            "draft": draft,
            "status": "Draft",
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        
        try:
            db = Database()
            db.insert_fir(fir_record)
        except Exception as e:
            yield {"agent": "System", "type": "error", "message": f"Database save failed: {str(e)}"}
            
        yield {"agent": "System", "type": "pipeline_complete", "fir_record": fir_record}
