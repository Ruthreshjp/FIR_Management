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
        
    def generate_fir(self, data: dict):
        """
        Coordinates the 3 agents in sequence, manages state, and yields progress.
        Yields dictionaries with step status and finally the complete FIR record.
        """
        yield {"agent": "System", "type": "status", "message": "Initializing pipeline..."}
        
        # 1. Intake
        yield {"agent": "Intake Agent", "type": "header", "message": "Extracting facts from complaint..."}
        facts = self.intake.run(data)
        yield {"agent": "Intake Agent", "type": "thought", "message": facts}
        
        # 2. Legal Mapping
        yield {"agent": "Legal Agent", "type": "header", "message": "Mapping facts to IPC & BNS sections..."}
        sections = self.legal.run(facts)
        yield {"agent": "Legal Agent", "type": "thought", "message": sections}
        
        # 3. Drafting
        yield {"agent": "Drafting Agent", "type": "header", "message": "Drafting formal FIR document..."}
        draft = self.drafting.run(facts, sections, data)
        yield {"agent": "Drafting Agent", "type": "thought", "message": draft}
        
        # 4. Save to Database
        yield {"agent": "System", "type": "status", "message": "Saving FIR to database..."}
        
        # Ensure fir_record includes all the new fields from data
        fir_record = {
            "fir_number": f"FIR/{datetime.now().strftime('%Y/%m%d%H%M%S')}",
            "facts": facts,
            "sections": sections,
            "draft": draft,
            "status": "Draft",
            "created_at": datetime.now().isoformat()
        }
        # Merge all incoming data fields into the record
        fir_record.update(data)

        
        try:
            db = Database()
            db.insert_fir(fir_record)
        except Exception as e:
            yield {"agent": "System", "type": "error", "message": f"Database save failed: {str(e)}"}
            
        yield {"agent": "System", "type": "pipeline_complete", "fir_record": fir_record}
