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
        print(f"[Orchestrator] Intake Agent output (first 300 chars): {facts[:300]}")
        yield {"agent": "Intake Agent", "type": "thought", "message": facts}
        
        # 2. Legal Mapping
        yield {"agent": "Legal Agent", "type": "header", "message": "Mapping facts to IPC & BNS sections..."}
        sections = self.legal.run(facts)
        print(f"[Orchestrator] Legal Agent output (full):\n{sections}")
        yield {"agent": "Legal Agent", "type": "thought", "message": sections}
        
        # 3. Drafting
        yield {"agent": "Drafting Agent", "type": "header", "message": "Drafting formal FIR document..."}
        draft = self.drafting.run(facts, sections, data)
        print(f"[Orchestrator] Drafting Agent output (first 300 chars): {draft[:300]}")
        yield {"agent": "Drafting Agent", "type": "thought", "message": draft}
        
        # 4. Save to Database
        yield {"agent": "System", "type": "status", "message": "Saving FIR to database..."}
        
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
            fir_id = db.insert_fir(fir_record)
            print(f"[Orchestrator] FIR saved successfully with ID: {fir_id}")
            yield {"agent": "System", "type": "status", "message": "FIR saved successfully!"}
        except Exception as e:
            print(f"[Orchestrator] Database save error: {e}")
            yield {"agent": "System", "type": "error", "message": f"Database save failed: {str(e)}"}
            
        yield {"agent": "System", "type": "pipeline_complete", "fir_record": fir_record}
