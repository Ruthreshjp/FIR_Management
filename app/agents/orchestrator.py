from datetime import datetime
from app.agents.intake_agent import IntakeAgent
from app.agents.legal_agent import LegalAgent
from app.agents.drafting_agent import DraftingAgent
from app.agents.legal_verifier import verify_sections
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
        facts_raw = self.intake.run(data)
        
        try:
            import json
            facts_dict = json.loads(facts_raw)
            # Merge LLM-extracted flags into data
            for key in ["animal_involved", "human_hurt", "force_used", "property_taken", 
                        "cyber_method", "sexual_offence", "premeditated", "minor_involved", 
                        "accused_count", "weapon_used"]:
                if key in facts_dict:
                    data[key] = facts_dict[key]
            
            facts = facts_dict.get("facts", facts_raw)
        except Exception:
            facts = facts_raw
            
        try:
            import re
            
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
            data["accused_count"] = extract_accused_count(max(form_accused, 1), data.get("complaint_text", ""))
            
            # Extract premeditated flag
            complaint_lower = data.get("complaint_text", "").lower()
            premeditated_keywords = [
                "planned", "came with", "brought", "waiting for",
                "along with", "accompanied by", "group of",
                "approached on", "came on motorcycle", "came prepared",
                "came together", "assembled", "gathered", "coordinated",
                "two motorcycles", "came in a vehicle", "came in a car",
                "pre-planned", "conspired", "stopped me", "blocked my path",
                "surrounded", "demanded", "pointed", "gang", "armed with",
                "longstanding dispute", "longstanding enmity", 
                "previous enmity", "prior dispute", "had a dispute",
                "property dispute", "land dispute", "known to",
                "sharp weapons", "deadly weapons", "came armed"
            ]
            data["premeditated"] = any(w in complaint_lower for w in premeditated_keywords)
            
            # Extract minor_involved
            minor_keywords = [
                "child", "minor", "year old", "years old",
                "school", "boy", "girl", "daughter", "son",
                "student", "juvenile", "underage", "teenager",
                "8th standard", "9th standard", "class",
                "13-year", "14-year", "15-year", "16-year",
                "17-year", "aged 13", "aged 14", "aged 15",
                "aged 16", "aged 17"
            ]
            data["minor_involved"] = data.get("minor_involved", False) or any(w in complaint_lower for w in minor_keywords)
            
            # Additional fact extraction for verifier
            data["force_used"] = any(
                w in complaint_lower
                for w in ["hit", "punch", "slap", "push", "stab",
                          "beat", "struck", "kicked", "attacked",
                          "grabbed", "throttled", "choked"]
            )
            
            data["injury_occurred"] = any(
                w in complaint_lower
                for w in ["injured", "hurt", "wound", "bleeding",
                          "fracture", "hospitalized", "medical",
                          "injury", "pain", "bruise", "cut"]
            ) or data.get("victim_status") in ["injured", "dead"]
            
            data["penetration_occurred"] = any(
                w in complaint_lower
                for w in ["rape", "raped", "penetrat", "sexual intercourse",
                          "forced intercourse", "inserted", "sodomize"]
            )
            
            data["property_taken"] = any(
                w in complaint_lower
                for w in ["stole", "stolen", "took", "snatched", "robbed",
                          "missing", "taken", "seized", "looted",
                          "transferred", "debited", "withdrawn"]
            )
            
            data["cyber_method"] = any(
                w in complaint_lower
                for w in ["otp", "online", "upi", "neft", "imps",
                          "internet banking", "anydesk", "teamviewer",
                          "remote", "phishing", "whatsapp message",
                          "link", "install app", "download app"]
            )
            
            data["document_forged"] = any(
                w in complaint_lower
                for w in ["fake document", "fake letterhead", "forged",
                          "fake id", "fabricated", "fake certificate",
                          "counterfeit", "fake letter", "fake notice"]
            )
            
            data["govt_impersonation"] = any(
                w in complaint_lower
                for w in ["rbi officer", "police officer", "cbi",
                          "income tax", "customs", "government officer",
                          "bank manager", "claiming to be", "posing as",
                          "pretending to be", "impersonating"]
            )
            
            data["marital_relationship"] = any(
                w in complaint_lower
                for w in ["husband", "wife", "in-laws", "mother-in-law",
                          "father-in-law", "spouse", "matrimonial",
                          "marital", "domestic violence"]
            )
            
            data["female_victim"] = data.get("female_victim", False) or any(
                w in complaint_lower
                for w in ["she", "her", "woman", "lady", "girl",
                          "wife", "daughter", "mother", "sister"]
            )
            
            data["animal_involved"] = data.get("animal_involved", False) or any(
                w in complaint_lower
                for w in ["dog", "cat", "cow", "cattle", "animal", "pet", "puppy", "street dog"]
            )
            
            data["sexual_offence"] = data.get("sexual_offence", False) or any(
                w in complaint_lower
                for w in ["rape", "molest", "sexual", "inappropriate", "private parts", "groped", "assaulted sexually"]
            )
            
            print(f"[Orchestrator] Flags: animal={data.get('animal_involved')}, cyber={data.get('cyber_method')}, hurt={data.get('human_hurt')}, force={data.get('force_used')}")
        except Exception as e:
            print(f"[Orchestrator] Error parsing facts: {e}")
            pass
            
        print(f"[Orchestrator] Intake Agent output (first 300 chars): {facts_raw[:300]}")
        yield {"agent": "Intake Agent", "type": "thought", "message": facts_raw}
        
        # 2. Legal Mapping
        yield {"agent": "Legal Agent", "type": "header", "message": "Mapping facts to IPC & BNS sections..."}
        sections = self.legal.run(facts_raw, data)
        
        # ADD THIS — second LLM verification pass:
        import json
        try:
            sections_list = json.loads(sections)
            
            # Ensure sections_list is a list
            if isinstance(sections_list, dict):
                if "selected_sections" in sections_list:
                    sections_list = sections_list["selected_sections"]
                elif "sections" in sections_list:
                    sections_list = sections_list["sections"]
                else:
                    sections_list = []
                    
            if not isinstance(sections_list, list):
                sections_list = []

            verified_sections_list = verify_sections(sections_list, data)
            
            if not isinstance(verified_sections_list, list):
                verified_sections_list = []
                
            verified_sections = json.dumps(verified_sections_list, indent=2)
            kept_count = len(verified_sections_list)
            total_count = len(sections_list)
        except Exception as e:
            print(f"[Orchestrator] Error parsing sections: {e}")
            verified_sections = "[]"
            verified_sections_list = []
            kept_count = 0
            total_count = 0
            
        yield {"agent": "Verifier", "type": "status", "stage": "verifier", "kept": kept_count, "total": total_count}
        
        print(f"[Orchestrator] Legal Agent output (full):\n{sections}")
        yield {"agent": "Legal Agent", "type": "thought", "message": verified_sections}
        
        # 3. Drafting
        yield {"agent": "Drafting Agent", "type": "header", "message": "Drafting formal FIR document..."}
        draft = self.drafting.run(facts, verified_sections, data)
        print(f"[Orchestrator] Drafting Agent output (first 300 chars): {draft[:300]}")
        yield {"agent": "Drafting Agent", "type": "thought", "message": draft}
        
        # 4. Save to Database
        yield {"agent": "System", "type": "status", "message": "Saving FIR to database..."}
        
        # Separate IPC and BNS sections
        ipc_sections = []
        bns_sections = []
        other_sections = []
        if isinstance(verified_sections_list, list):
            for s in verified_sections_list:
                act = s.get("act", "").upper()
                if act == "IPC":
                    ipc_sections.append(s)
                elif act == "BNS":
                    bns_sections.append(s)
                else:
                    other_sections.append(s)
        
        fir_record = {
            "fir_number": f"FIR/{datetime.now().strftime('%Y/%m%d%H%M%S')}",
            "facts": facts,
            "sections": verified_sections_list,
            "ipc_sections": ipc_sections,
            "bns_sections": bns_sections,
            "other_sections": other_sections,
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
