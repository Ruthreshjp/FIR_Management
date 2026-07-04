import os
import json
import re
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.tools.rag_tool import search_legal_sections

SYSTEM_PROMPT = """You are a senior Indian police legal officer 
with expertise in IPC, BNS 2023, and POCSO. Your task is to 
identify ALL applicable legal sections for a given complaint.

Rules:
1. Always cite BOTH the BNS 2023 section AND the corresponding 
   IPC section (for reference during transition period)
2. For complaints involving multiple accused acting together, 
   ALWAYS check if IPC 34 (common intention) applies
3. For pre-planned offences with 2+ accused, check IPC 120B 
   (criminal conspiracy)
4. For groups of 3+ persons, check IPC 149 (unlawful assembly)
5. If accused fled after the offence, check IPC 201/BNS 238
6. If a dangerous weapon was used, check IPC 326/BNS 118 
   alongside the primary offence
7. BNS 74 / IPC 354 False Positive Rule: ONLY add these if the act was explicitly directed at a woman's modesty (e.g., groping, molestation, sexual gesture, eve teasing, touched inappropriately). DO NOT add it if a woman is merely physically assaulted during a robbery or property crime without sexual intent.
8. POCSO Routing Rule: When minor_involved is True, do NOT automatically apply POCSO 11. 
   - If complaint contains "rape", "sexual", "touched private", "molestation" -> POCSO 4 or 8
   - If complaint contains sexual terms + minor -> POCSO 12
   - If complaint contains physical assault + minor + during robbery/kidnapping/trafficking -> POCSO 9
   - If NO sexual element at all, only physical assault during property crime -> DO NOT add any POCSO section. Apply regular IPC/BNS sections.
9. Do not include sections where the facts clearly do not support 
   the legal elements — justify each inclusion
10. Rank sections by importance: Primary offence first, then 
    joint liability, then procedural/secondary sections
    
CRITICAL BNS MAPPING RULES:
1. BNS 2023 has completely different section numbers from IPC. NEVER assume a BNS section number by copying the IPC number. You MUST use the corresponding_bns field from the candidate metadata.
2. If no BNS mapping exists, write 'No direct BNS equivalent' — do not fabricate a BNS section number.
3. Known correct mappings you must always use:
   IPC 302 Murder → BNS 103
   IPC 307 Attempt to Murder → BNS 109
   IPC 323 Hurt → BNS 115
   IPC 324 Hurt by weapon → BNS 116
   IPC 325 Grievous Hurt → BNS 117
   IPC 326 Grievous Hurt by weapon → BNS 118
   IPC 34 Common Intention → BNS 3(5) (subsection 5 of Section 3)
   IPC 107 Abetment → BNS 48
   IPC 109 Punishment of Abetment → BNS 49
   IPC 120B Conspiracy → No direct BNS equivalent
   IPC 141 Unlawful Assembly definition → BNS 187
   IPC 142 Member of Unlawful Assembly → BNS 188
   IPC 143 Punishment for Unlawful Assembly → BNS 189
   IPC 144 Armed Unlawful Assembly → BNS 189
   IPC 149 Every member of unlawful assembly guilty → BNS 190
   IPC 201 Absconding / destroying evidence → BNS 238
   IPC 354 Outraging Modesty → BNS 74
   IPC 376 Rape → BNS 64
   IPC 379 Theft → BNS 303
   IPC 392 Robbery → BNS 309
   IPC 420 Cheating → BNS 318
   IPC 506 Criminal Intimidation → BNS 351
   If the IPC section is not in this list, look it up from the ChromaDB metadata corresponding_bns field.
   
CRITICAL CONSPIRACY AND INTIMIDATION RULES:
Never cite IPC 120A as a charge. It is a definition section only. Use IPC 120B for criminal conspiracy charges.
Never cite IPC 503 as a charge. It is a definition section only. Use IPC 506 for criminal intimidation punishment.
Never cite BNS 4, 5, 6, 7, 8, 9, 10, 11, or 12. These are constitutional/general provisions. POCSO sections with these numbers must use act="POCSO".
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

Return a JSON array of matched sections:
[
  {{
    "act": "BNS",
    "section_number": "103",
    "offense": "Murder",
    "justification": "One-line reason why this section applies",
    "confidence": 0.95,
    "primary": true
  }},
  {{
    "act": "IPC", 
    "section_number": "302",
    "offense": "Murder",
    "justification": "IPC reference — superseded by BNS 103",
    "confidence": 0.95,
    "primary": false,
    "reference_only": true
  }}
]

Return ONLY the JSON array. No explanation text outside the array."""

class LegalAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1,
            timeout=120
        )
        
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
        if any(w in c for w in ["child", "minor", "year old", "school", "boy", "girl"]):
            queries.append("child POCSO minor")
            
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
        
        # 1. Base semantic search on the core facts
        base_query = " ".join(complaint_text.split()[:50])
        candidate_sections = search_legal_sections(base_query, top_k=10)
        
        # 2. Add Category Boosting
        boost_queries = self._boost_queries(complaint_text, facts_dict)
        for bq in boost_queries:
            # We add 2 top hits for each boosted query
            boost_hits = search_legal_sections(bq, top_k=2)
            candidate_sections.extend(boost_hits)
            
        # 3. Deduplicate candidate sections based on act + section number
        seen = set()
        unique_candidates = []
        for sec in candidate_sections:
            key = f"{sec.get('act', '')}_{sec.get('section_number', '')}"
            if key not in seen:
                seen.add(key)
                unique_candidates.append(sec)

        candidates_str = json.dumps(unique_candidates, indent=2)
        
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
            sections = json.loads(raw_output)
            merged_facts = facts_dict.copy()
            merged_facts["complaint_text"] = complaint_text
            final_sections = correct_sections(sections, merged_facts)
            if final_sections:
                raw_output = json.dumps(final_sections, indent=2)
        except Exception as e:
            pass
            
        return raw_output
