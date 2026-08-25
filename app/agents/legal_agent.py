import os
import json
import re
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.tools.rag_tool import search_legal_sections
from app.agents.act_selector import select_relevant_acts
from app.agents.crime_classifier import CrimeClassifierAgent
from app.config.section_mapping import ALLOWED_SECTIONS

PRIMARY_MODEL = os.getenv("GROQ_MODEL_PRIMARY", "openai/gpt-oss-120b")
VERIFIER_MODEL = os.getenv("GROQ_MODEL_VERIFIER", "openai/gpt-oss-20b")

SYSTEM_PROMPT = """You are a strict, senior Indian police legal officer 
with expertise in IPC, BNS 2023, and POCSO. Your task is to 
identify the most applicable legal sections for a given complaint.

QUALITY OVER QUANTITY:
Your primary directive is absolute accuracy. It is much better to return ONLY 2-4 highly accurate sections than a long list of weakly related ones.
Do not add extra sections unless the facts explicitly support every legal element. PREFER EXACT MATCHING SECTIONS ONLY.

CRITICAL RULE:
You CANNOT invent or pick sections that are not explicitly provided in the "Candidate sections from semantic search". You MUST only select from the provided candidates. If a section is not in the candidate list, DO NOT use it.

STRICT FILTERING RULES:
1. Animal Cruelty Case -> ONLY animal-related sections (e.g. IPC 428/429, BNS 325). NO human hurt sections (IPC 323, 302, BNS 115) should ever be added.
2. Robbery vs Extortion -> 
   - Robbery (force/threat of immediate force + theft) -> MUST use IPC 392. DO NOT use Extortion (IPC 384). Property MUST actually be taken. If no property is taken, DO NOT add Robbery.
   - Extortion (threat without immediate force to deliver property) -> IPC 384.
3. Pure Cyber Cases -> NO physical assault or physical theft sections.
4. Murder (IPC 302/BNS 103) -> ONLY if victim is dead.
5. Rash Driving / Accidents -> If the incident involves a vehicle causing injury (but no theft/robbery intent), use IPC 279, 337, 338. Do not use Robbery just because the accused fled in a vehicle.
6. Criminal Conspiracy (IPC 120B / BNS 61) -> ONLY add if there is clear evidence of pre-planning or prior agreement. DO NOT add conspiracy just because there are multiple accused, they acted together, or they used a weapon. (Use IPC 34 / BNS 3(5) for common intention instead).

CRITICAL BNS MAPPING RULES (Use these to supply BNS equivalents if missing):
- IPC 302 (Murder) -> BNS 103
- IPC 307 (Attempt to Murder) -> BNS 109
- IPC 323 (Voluntarily causing hurt) -> BNS 115
- IPC 324 (Hurt by dangerous weapons) -> BNS 115(2)
- IPC 326 (Grievous hurt by weapons) -> BNS 118
- IPC 354 (Assault to outrage modesty) -> BNS 74
- IPC 376 (Rape) -> BNS 64
- IPC 379 (Theft) -> BNS 303
- IPC 380 (Theft in dwelling) -> BNS 305
- IPC 384 (Extortion) -> BNS 308
- IPC 392 (Robbery) -> BNS 309
- IPC 395 (Dacoity) -> BNS 310
- IPC 406 (Criminal Breach of Trust) -> BNS 316
- IPC 411 (Dishonestly receiving stolen property) -> BNS 317
- IPC 420 (Cheating/Fraud) -> MUST INCLUDE BNS 318
- IPC 428/429 (Animal Mischief) -> BNS 325
- IPC 498A (Domestic Violence) -> BNS 85
- IPC 504 (Intentional insult) -> BNS 352
- IPC 506 (Criminal intimidation) -> BNS 351

EVALUATION PROCESS:
You must first evaluate the candidate sections in an "evaluations" array, explicitly stating whether each candidate applies or not and why. 
Then, populate the "selected_sections" array with ONLY the exact, truly applicable sections (IPC, BNS, or POCSO) chosen strictly from the candidates.
Do not link BNS and IPC in the same object; output them as separate, independent entries in "selected_sections".
"""

USER_PROMPT = """
Complaint: {complaint_text}

Extracted Facts:
- Who: {who}
- What: {what}  
- When: {when}
- Where: {where}
- Accused: {accused}
- Weapon used: {weapon}
- Number of accused: {accused_count}
- Victim status: {victim_status} (alive/injured/dead)
- Minor involved: {minor_involved}
- Accused fled: {accused_fled}

Candidate sections from semantic search (analyze each carefully):
{candidate_sections}

Return a JSON object strictly matching this schema:
{{
  "evaluations": [
    {{
      "section": "IPC 323",
      "applicable": false,
      "reason": "This is an animal cruelty case; human hurt section does not apply."
    }}
  ],
  "selected_sections": [
    {{
      "act": "IPC",
      "section_number": "428",
      "offense": "Mischief by killing or maiming animal",
      "justification": "The accused intentionally poisoned the pet dog.",
      "confidence": 0.95
    }},
    {{
      "act": "BNS",
      "section_number": "325",
      "offense": "Mischief by killing or maiming animal",
      "justification": "BNS equivalent for poisoning the pet dog.",
      "confidence": 0.95
    }}
  ]
}}

Return ONLY the JSON object. No explanation text outside the JSON."""

class LegalAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model=PRIMARY_MODEL,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1,
            timeout=120
        )
        self.crime_classifier = CrimeClassifierAgent()
        
        self.prompt = PromptTemplate.from_template(SYSTEM_PROMPT + "\n\n" + USER_PROMPT)

    def _boost_queries(self, complaint: str, facts_dict: dict) -> list:
        """Analyze complaint text to add mandatory keyword queries based on categories."""
        c = complaint.lower()
        queries = []
        
        # RULE A — Multiple accused acting together
        accused_count_str = str(facts_dict.get("accused_count", ""))
        try:
            count = int(accused_count_str) if accused_count_str and accused_count_str.isdigit() else 1
            if count >= 2 or any(w in c for w in [
                "planned", "came with", "brought", "waiting for",
                "along with", "accompanied by", "group of",
                "approached on", "came on motorcycle", "came prepared",
                "came together", "assembled", "gathered", "coordinated",
                "two motorcycles", "came in a vehicle", "came in a car",
                "came in an auto", "pre-planned", "conspired",
                "stopped me", "blocked my path", "surrounded",
                "demanded", "pointed", "gang", "armed with"
            ]):
                queries.append("common intention several persons joint act")
                queries.append("conspiracy pre-planned criminal agreement")
            
            if count >= 3 or any(w in c for w in ["group", "gang", "mob", "crowd", "they all", "five or more persons"]):
                queries.append("unlawful assembly five or more persons")
        except:
            pass

        # RULE B — Dangerous weapon used causing injury
        weapon = facts_dict.get("weapon", "")
        victim_status = str(facts_dict.get("victim_status", "")).lower()
        has_weapon = weapon and weapon.lower() not in ["none", "unknown", "n/a", ""]
        has_injury = "injured" in victim_status or "dead" in victim_status or "death" in victim_status
        if has_weapon and has_injury:
            queries.append("grievous hurt dangerous weapon knife")
        elif any(w in c for w in ["knife", "sword", "gun", "rod", "acid", "sharp object", "dangerous weapon"]):
            queries.append("grievous hurt dangerous weapon knife")
            
        # RULE C — Accused fled after offence
        accused_fled = str(facts_dict.get("accused_fled", "")).lower()
        if accused_fled in ["yes", "true"] or any(w in c for w in ["fled", "ran away", "escaped", "drove away", "left the scene", "absconded", "disappeared after"]):
            queries.append("causing disappearance of evidence absconding")
            
        # Death/killing
        if any(w in c for w in ["dead", "died", "killed", "murder", "stabbed", "shot", "body found"]):
            queries.append("murder homicide death")
            queries.append("attempt to murder")
            
        # Minor/child
        if facts_dict.get("minor_involved", False) or any(w in c for w in ["child", "minor", "year old", "school", "boy", "girl"]):
            queries.append("child POCSO minor")
            
        # Animal cruelty
        if facts_dict.get("animal_involved", False):
            queries.append("mischief killing maiming animal cattle IPC 428 IPC 429 BNS 325")
            
        # Cyber / IT Act
        if facts_dict.get("cyber_method", False):
            queries.append("IT Act 66C 66D cheating online fraud computer resource phishing")
            
        # Property taken
        if facts_dict.get("property_taken", False):
            if facts_dict.get("force_used", False):
                queries.append("robbery theft with force extortion")
            else:
                queries.append("theft stolen property cheating breach of trust")
            
        return queries

    def run(self, facts: str, data: dict = None) -> str:
        """Maps facts to IPC + BNS 2023 sections using RAG and LLM."""
        
        # We assume the Intake Agent returned a JSON string. Parse it to get raw complaint.
        try:
            facts_dict = json.loads(facts)
        except Exception:
            facts_dict = {"complaint_text": facts} # fallback if not valid JSON
            
        if data and "complaint_text" in data:
            complaint_text = data["complaint_text"]
        else:
            complaint_text = facts_dict.get("complaint_text", facts)
        
        # Step A: LLM selects relevant acts
        relevant_acts = select_relevant_acts(complaint_text, facts_dict)

        from app.tools.rag_tool import rag_instance
        self.collection = getattr(rag_instance, 'collection', None)
        
        candidates = {}
        if self.collection:
            # Step B: General semantic search
            query_vector = rag_instance.model.encode([complaint_text]).tolist()
            results = self.collection.query(
                query_embeddings=query_vector,
                n_results=10
            )
            for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                key = (meta.get('act'), meta.get('section_number'))
                candidates[key] = meta

            # Step C: Targeted search for each selected act
            act_query_map = {
                "NDPS_ACT": "narcotic drug cocaine heroin ganja possession sale trafficking dealer peddler",
                "ARMS_ACT": "illegal arms weapon firearm pistol rifle unlicensed ammunition country made gun",
                "POCSO": "child minor sexual assault harassment inappropriate touching private parts",
                "IT_ACT": "cyber online fraud OTP phishing identity theft anydesk remote access hacking",
                "SC_ST_ACT": "caste discrimination atrocity scheduled caste tribe abuse humiliation caste name",
                "MOTOR_VEHICLES_ACT": "accident rash driving death injury hit run drunk driving vehicle",
                "NI_ACT": "cheque bounce dishonour insufficient funds payment returned bank",
                "PREVENTION_OF_CORRUPTION": "bribe corruption public servant gratification misuse of office",
                "JUVENILE_JUSTICE_ACT": "child cruelty neglect abuse abandonment minor welfare",
                "EXPLOSIVES_ACT": "bomb blast explosion explosive IED explosive substance",
                "HUMAN_TRAFFICKING": "trafficking kidnap forced labour sexual exploitation bonded labour",
                "DOWRY_ACT": "dowry demand harassment dowry death matrimonial cruelty",
                "PMLA": "money laundering hawala proceeds of crime financial fraud large amount",
            }

            for act in relevant_acts:
                if act in act_query_map:
                    try:
                        act_query_vector = rag_instance.model.encode([act_query_map[act]]).tolist()
                        act_results = self.collection.query(
                            query_embeddings=act_query_vector,
                            n_results=5
                        )
                        for doc, meta in zip(act_results['documents'][0], act_results['metadatas'][0]):
                            key = (meta.get('act'), meta.get('section_number'))
                            if key not in candidates:
                                candidates[key] = meta
                    except Exception as e:
                        print(f"[LegalAgent] Act search error {act}: {e}")
        else:
            # Fallback if no collection
            candidate_sections = search_legal_sections(complaint_text, top_k=10)
            for sec in candidate_sections:
                key = (sec.get('act'), sec.get('section_number'))
                candidates[key] = sec

        # Step D: Filter candidates using Crime Classifier
        categories = self.crime_classifier.run(complaint_text, facts_dict)
        print(f"[LegalAgent] Detected Crime Categories: {categories}")
        
        allowed_sections = {}
        restrict_sections = True
        
        if "Others" in categories and len(categories) == 1:
            restrict_sections = False
        else:
            for cat in categories:
                mapping = ALLOWED_SECTIONS.get(cat, {})
                for act, secs in mapping.items():
                    if act not in allowed_sections:
                        allowed_sections[act] = set()
                    allowed_sections[act].update(secs)
        
        all_candidates = []
        for key, meta in candidates.items():
            act, sec = key
            if restrict_sections:
                if act in allowed_sections and str(sec) in allowed_sections[act]:
                    all_candidates.append(meta)
            else:
                all_candidates.append(meta)

        print(f"[LegalAgent] Filtered candidates to {len(all_candidates)} sections based on {categories}")

        candidates_str = json.dumps(all_candidates, indent=2)
        
        # Extract variables for the prompt safely
        chain = self.prompt | self.llm
        result = chain.invoke({
            "complaint_text": complaint_text,
            "who": facts_dict.get("who", "Unknown"),
            "what": facts_dict.get("what", "Unknown"),
            "when": facts_dict.get("when", "Unknown"),
            "where": facts_dict.get("where", "Unknown"),
            "accused": facts_dict.get("accused", "Unknown"),
            "weapon": facts_dict.get("weapon", "Unknown"),
            "accused_count": facts_dict.get("accused_count", "Unknown"),
            "victim_status": facts_dict.get("victim_status", "Unknown"),
            "minor_involved": facts_dict.get("minor_involved", "Unknown"),
            "accused_fled": facts_dict.get("accused_fled", "Unknown"),
            "candidate_sections": candidates_str
        })
        
        # Try to parse the response to ensure it's a valid JSON array, otherwise return raw text.
        # Sometimes the LLM includes markdown backticks (e.g., ```json ... ```). We must strip them.
        raw_output = result.content.strip()
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]
        raw_output = raw_output.strip()
        
        # === POST-PROCESSING RULES ===
        try:
            from app.agents.section_corrector import correct_sections
            parsed_json = json.loads(raw_output)
            
            # The new schema returns an object with "selected_sections"
            if isinstance(parsed_json, dict) and "selected_sections" in parsed_json:
                sections = parsed_json["selected_sections"]
            else:
                # Fallback in case LLM returned the array directly
                sections = parsed_json if isinstance(parsed_json, list) else []

            merged_facts = data.copy() if data else facts_dict.copy()
            if "complaint_text" not in merged_facts:
                merged_facts["complaint_text"] = complaint_text
            final_sections = correct_sections(sections, merged_facts)
            
            # ALWAYS override raw_output with final_sections so it's a JSON array
            raw_output = json.dumps(final_sections if final_sections else [], indent=2)

        except Exception as e:
            print(f"[LegalAgent] JSON Parse / Corrector Error: {e}")
            pass
            
        return raw_output
