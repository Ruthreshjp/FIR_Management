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
        
        try:
            import json
            import re
            facts_dict = json.loads(facts)
            
            def extract_accused_count(form_accused_count: int, complaint_text: str) -> int:
                text = complaint_text.lower()
                patterns = [
                    r'(\w+)\s+(?:unknown\s+)?(?:persons?|men|people|individuals?|accused)',
                    r'group\s+of\s+(\w+)',
                    r'gang\s+of\s+(\w+)',
                    r'(\w+)\s+(?:motorcycles?|bikes?|cars?)\s+with',
                    r'(\w+)\s+(?:motorcycles?|bikes?)',
                    r'accompanied\s+by\s+(\w+)',
                ]
                word_to_num = {
                    'two': 2, 'three': 3, 'four': 4, 'five': 5,
                    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6
                }
                max_count = form_accused_count
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    for m in matches:
                        if m in word_to_num:
                            max_count = max(max_count, word_to_num[m])
                return max_count
            
            form_accused = len(data.get("accused", [])) + int(data.get("unknown_accomplices", 0) or 0)
            facts_dict["accused_count"] = extract_accused_count(max(form_accused, 1), data.get("complaint_text", ""))
            facts = json.dumps(facts_dict)
        except Exception as e:
            pass
            
        print(f"[Orchestrator] Intake Agent output (first 300 chars): {facts[:300]}")
        yield {"agent": "Intake Agent", "type": "thought", "message": facts}
        
        # 2. Legal Mapping
        yield {"agent": "Legal Agent", "type": "header", "message": "Mapping facts to IPC & BNS sections..."}
        sections = self.legal.run(facts, data)
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
            
        if "_id" in fir_record:
            fir_record["_id"] = str(fir_record["_id"])
            
        yield {"agent": "System", "type": "pipeline_complete", "fir_record": fir_record}
