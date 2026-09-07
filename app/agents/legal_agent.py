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
with expertise in BNS 2023, POCSO, and IT Act. Your task is to 
identify the most applicable legal sections for a given complaint.

QUALITY OVER QUANTITY:
Return 3-8 highly accurate, directly applicable sections.
Do not add extra sections unless the facts explicitly support every legal element.

CRITICAL RULE:
You MUST only select from the candidate list provided. Do not invent sections.
You MUST ONLY select BNS, POCSO, or IT Act sections. DO NOT select bare IPC sections.
*EXCEPTION*: If an applicable IPC section appears in the candidate list, translate it to its BNS equivalent instead.

STRICT FILTERING RULES:
1. Animal Cruelty -> ONLY BNS 325. NO human hurt sections.
2. Robbery (BNS 309) -> ONLY if force was used AND property was actually taken.
3. Extortion (BNS 308) -> Use when threats were made demanding property but no immediate physical force.
4. Pure Cyber Cases -> NO physical assault sections.
5. Murder (BNS 103) -> ONLY if victim is confirmed dead.
6. Conspiracy (BNS 61) -> ONLY if clear prior planning/agreement is described.
7. Common Intention BNS 3(5) -> Use when 2+ accused acted together even without prior planning.

FEW-SHOT EXAMPLES:
Example (Cyber Extortion with impersonation):
Facts: Person posed as customs officer, demanded Rs 50,000, also hacked victim social media and demanded Rs 2 lakhs threatening to circulate obscene morphed images.
Candidates: IT Act 66D, BNS 308, BNS 351, BNS 204, BNS 79
Output selected_sections: [IT Act 66D, BNS 308, BNS 351, BNS 204, BNS 79]

IMPORTANT FINAL RULES:
- Do not return empty sections. You MUST select at least 3 sections.
- Prefer 4-8 highly relevant sections.
- Output ONLY the JSON. No markdown. No explanation outside JSON.
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

{reflection_prompt}

Return ONLY a JSON object with this exact structure — no evaluations, no extra text, no markdown:
{{
  "selected_sections": [
    {{
      "act": "BNS",
      "section_number": "308",
      "offense": "Extortion",
      "justification": "Accused demanded money under threat.",
      "confidence": 0.95,
      "primary": true
    }},
    {{
      "act": "IT Act",
      "section_number": "66D",
      "offense": "Cheating by personation using computer resource",
      "justification": "Accused used WhatsApp to impersonate a government official.",
      "confidence": 0.90,
      "primary": true
    }}
  ]
}}

Return ONLY the JSON object. No explanation, no markdown, no extra text."""

class LegalAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model=PRIMARY_MODEL,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.0,
            timeout=120,
            max_tokens=4000
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
        
        max_attempts = 2
        restrict_sections = True
        raw_output = "[]"
        
        for attempt in range(max_attempts):
            candidates = {}
            if self.collection:
                # Step B1: General semantic search
                query_vector = rag_instance.model.encode([complaint_text]).tolist()
                
                # Fetch more results if first attempt failed
                n_results = 25 if attempt == 0 else 50
                results = self.collection.query(
                    query_embeddings=query_vector,
                    n_results=n_results
                )
                for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                    key = (meta.get('act'), meta.get('section_number'))
                    candidates[key] = meta
                    
                # Step B2: Execute Targeted Boost Queries
                boost_queries = self._boost_queries(complaint_text, facts_dict)
                for bq in boost_queries:
                    try:
                        bq_vector = rag_instance.model.encode([bq]).tolist()
                        bq_results = self.collection.query(
                            query_embeddings=bq_vector,
                            n_results=10
                        )
                        for doc, meta in zip(bq_results['documents'][0], bq_results['metadatas'][0]):
                            key = (meta.get('act'), meta.get('section_number'))
                            candidates[key] = meta
                    except Exception as e:
                        pass

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
                                n_results=10 if attempt == 0 else 20
                            )
                            for doc, meta in zip(act_results['documents'][0], act_results['metadatas'][0]):
                                key = (meta.get('act'), meta.get('section_number'))
                                if key not in candidates:
                                    candidates[key] = meta
                        except Exception as e:
                            print(f"[LegalAgent] Act search error {act}: {e}")
            else:
                # Fallback if no collection
                candidate_sections = search_legal_sections(complaint_text, top_k=25 if attempt == 0 else 50)
                for sec in candidate_sections:
                    key = (sec.get('act'), sec.get('section_number'))
                    candidates[key] = sec

            # Step D: Filter candidates using Crime Classifier
            categories = self.crime_classifier.run(complaint_text, facts_dict)
            print(f"[LegalAgent] Attempt {attempt+1} Detected Crime Categories: {categories}")
            
            allowed_sections = {}
            if attempt == 1:
                # Relax restrictions on second attempt
                restrict_sections = False
            
            if "Others" in categories and len(categories) == 1:
                restrict_sections = False
            else:
                for cat in categories:
                    mapping = ALLOWED_SECTIONS.get(cat, {})
                    for act, secs in mapping.items():
                        if act not in allowed_sections:
                            allowed_sections[act] = set()
                        allowed_sections[act].update(secs)
            
            # Instead of just filtering ChromaDB results, we should ALSO inject the 
            # explicitly allowed sections from the Classifier into the candidates list!
            all_candidates = []
            
            # 1. Add all candidates found by ChromaDB (NEVER filter them out)
            for key, meta in candidates.items():
                all_candidates.append(meta)
                    
            # 2. Force inject the allowed sections from the Classifier so they are NEVER missed
            if allowed_sections:
                try:
                    import json
                    ipc_path = "data/processed/ipc_sections.json"
                    bns_path = "data/processed/bns_sections.json"
                    ipc_data = json.load(open(ipc_path, 'r', encoding='utf-8'))
                    bns_data = json.load(open(bns_path, 'r', encoding='utf-8'))
                    
                    # Create quick lookups
                    ipc_lookup = {str(item.get('section_number', '')): item for item in ipc_data}
                    bns_lookup = {str(item.get('section_number', '')): item for item in bns_data}
                    
                    # Track what we already have
                    existing_keys = {(meta.get('act'), str(meta.get('section_number'))) for meta in all_candidates}
                    
                    for act, secs in allowed_sections.items():
                        for sec in secs:
                            if (act, sec) not in existing_keys:
                                if act == 'IPC' and sec in ipc_lookup:
                                    all_candidates.append(ipc_lookup[sec])
                                    existing_keys.add((act, sec))
                                elif act == 'BNS' and sec in bns_lookup:
                                    all_candidates.append(bns_lookup[sec])
                                    existing_keys.add((act, sec))
                except Exception as e:
                    print(f"[LegalAgent] Failed to inject allowed sections: {e}")

            print(f"[LegalAgent] Filtered candidates to {len(all_candidates)} sections")

            # Minimize payload size to prevent '413 Payload Too Large' errors
            # Also fix RAG act:None bug by inferring act from section_number
            minimal_candidates = []
            for c in all_candidates:
                act = c.get("act") or c.get("Act") or ""
                sec = str(c.get("section_number", c.get("Section", "")) or "").strip()
                
                # Infer act if missing — ChromaDB sometimes drops the act field for IPC
                if not act and sec:
                    if any(sec == str(s) for s in ["66C", "66D", "66E", "67", "67A", "43", "72"]):
                        act = "IT Act"
                    elif any(kw in str(c.get("description", "")).lower() for kw in ["bharatiya nyaya"]):
                        act = "BNS"
                    else:
                        act = "IPC"  # Default: IPC sections stored without act label
                
                if not act or not sec:
                    continue  # Skip truly invalid entries
                    
                desc = str(c.get("description", c.get("Description", "")))
                minimal_candidates.append({
                    "act": act,
                    "section_number": sec,
                    "offense": c.get("offense", c.get("Offense", c.get("title", ""))),
                    "description": desc[:150] + "..." if len(desc) > 150 else desc
                })

            candidates_str = json.dumps(minimal_candidates, indent=2)
            
            reflection_prompt = ""
            if attempt > 0:
                reflection_prompt = "REFLECTION: In your previous attempt, you failed to select any valid sections or the output was malformed. Please try again with these broader candidates and ensure you follow the JSON structure perfectly."
            
            # Extract variables for the prompt safely
            chain = self.prompt | self.llm
            try:
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
                    "candidate_sections": candidates_str,
                    "reflection_prompt": reflection_prompt
                })
            except Exception as e:
                print(f"[LegalAgent] API Error on attempt {attempt+1}: {e}")
                import time
                time.sleep(3) # Wait before retrying
                if attempt == max_attempts - 1:
                    print("[LegalAgent] Max attempts reached, failing gracefully.")
                    return "[]" # Return empty array if all attempts fail
                continue
            
            # Try to parse the response
            raw_output = result.content.strip()
            
            # Strip markdown fences
            if raw_output.startswith("```json"):
                raw_output = raw_output[7:]
            if raw_output.startswith("```"):
                raw_output = raw_output[3:]
            if raw_output.endswith("```"):
                raw_output = raw_output[:-3]
            raw_output = raw_output.strip()
            
            # === RESILIENT PARSING: Try 3 strategies ===
            sections = []
            try:
                # Strategy 1: Full clean JSON parse
                parsed_json = json.loads(raw_output)
                if isinstance(parsed_json, dict) and "selected_sections" in parsed_json:
                    sections = parsed_json["selected_sections"]
                elif isinstance(parsed_json, list):
                    sections = parsed_json
            except Exception:
                # Strategy 2: Extract selected_sections block via regex (handles truncation)
                try:
                    sel_match = re.search(
                        r'"selected_sections"\s*:\s*(\[.*?\])(?:\s*[,}]|\s*$)',
                        raw_output, re.DOTALL
                    )
                    if sel_match:
                        sections = json.loads(sel_match.group(1))
                        print(f"[LegalAgent] Attempt {attempt+1}: Parsed via selected_sections regex.")
                    else:
                        # Strategy 3: Extract any JSON array of objects
                        arr_match = re.search(r'(\[\s*\{.*?\}\s*\])', raw_output, re.DOTALL)
                        if arr_match:
                            sections = json.loads(arr_match.group(1))
                            print(f"[LegalAgent] Attempt {attempt+1}: Parsed via array regex.")
                except Exception as e2:
                    print(f"[LegalAgent] Attempt {attempt+1} all parse strategies failed: {e2}")
            
            # === POST-PROCESSING: correct + validate sections ===
            if sections:
                try:
                    from app.agents.section_corrector import correct_sections
                    merged_facts = data.copy() if data else facts_dict.copy()
                    if "complaint_text" not in merged_facts:
                        merged_facts["complaint_text"] = complaint_text
                    final_sections = correct_sections(sections, merged_facts)
                    
                    if final_sections and len(final_sections) > 0:
                        raw_output = json.dumps(final_sections, indent=2)
                        print(f"[LegalAgent] Attempt {attempt+1} SUCCESS: {len(final_sections)} sections.")
                        break
                    else:
                        print(f"[LegalAgent] Attempt {attempt+1} resulted in 0 sections after correction. Reflecting...")
                except Exception as e:
                    print(f"[LegalAgent] Attempt {attempt+1} correction error: {e}")
            else:
                print(f"[LegalAgent] Attempt {attempt+1} produced 0 parseable sections. Reflecting...")
                
        return raw_output
