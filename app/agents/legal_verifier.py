import os
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
VERIFIER_MODEL = os.getenv("GROQ_MODEL_VERIFIER",
                           "openai/gpt-oss-20b")


def verify_sections(sections: list, facts: dict) -> list:
    """
    Second LLM pass — independently verifies each proposed
    section against the actual facts. Returns only sections
    that pass verification.
    
    Uses a fast small model (8B) for binary YES/NO decisions
    — no complex reasoning needed, just fact-checking.
    """
    if not sections or not isinstance(sections, list):
        return sections

    print(f"[Verifier] Hard Rule Pre-filter starting with {len(sections)} sections")
    pre_filtered = []
    hard_rejected = []
    
    # Boolean flags from intake
    animal_involved = str(facts.get("animal_involved", "")).lower() == "true"
    human_hurt = str(facts.get("human_hurt", "")).lower() == "true"
    cyber_method = str(facts.get("cyber_method", "")).lower() == "true"
    force_used = str(facts.get("force_used", "")).lower() == "true"
    property_taken = str(facts.get("property_taken", "")).lower() == "true"
    
    for s in sections:
        sec = str(s.get("section_number", ""))
        act = s.get("act", "").upper()
        
        # RULE 1: If animal involved but NO human hurt, reject all human physical assault sections
        if animal_involved and not human_hurt:
            if act == "IPC" and sec in ["323", "324", "325", "326", "302", "307", "354"]:
                hard_rejected.append(f"{act} {sec} (Human assault rejected in animal case)")
                continue
            if act == "BNS" and sec in ["115", "116", "117", "118", "103", "109", "74"]:
                hard_rejected.append(f"{act} {sec} (Human assault rejected in animal case)")
                continue
                
        # RULE 2: If cyber method and NO physical force, reject Robbery / Dacoity
        if cyber_method and not force_used:
            if act == "IPC" and sec in ["392", "390", "393", "394", "395", "397"]:
                hard_rejected.append(f"{act} {sec} (Robbery rejected in cyber fraud)")
                continue
            if act == "BNS" and sec in ["309", "310", "311"]:
                hard_rejected.append(f"{act} {sec} (Robbery rejected in cyber fraud)")
                continue
                
        # RULE 3: If no force was used, reject Robbery
        if not force_used:
            if act == "IPC" and sec in ["392", "393", "394", "397"]:
                hard_rejected.append(f"{act} {sec} (Robbery rejected as no force used)")
                continue
            if act == "BNS" and sec in ["309", "310", "311"]:
                hard_rejected.append(f"{act} {sec} (Robbery rejected as no force used)")
                continue

        # RULE 3B: If no property was actually taken, reject Robbery
        if not property_taken:
            if act == "IPC" and sec in ["392", "390", "393", "394", "395", "397"]:
                hard_rejected.append(f"{act} {sec} (Robbery rejected as no property was taken)")
                continue
            if act == "BNS" and sec in ["309", "310", "311"]:
                hard_rejected.append(f"{act} {sec} (Robbery rejected as no property was taken)")
                continue

        # RULE 4: If not dead, reject Murder
        victim_status = str(facts.get("victim_status", "")).lower()
        if "dead" not in victim_status and "death" not in victim_status:
            if act == "IPC" and sec in ["302"]:
                hard_rejected.append(f"{act} {sec} (Murder rejected as victim not dead)")
                continue
            if act == "BNS" and sec in ["103"]:
                hard_rejected.append(f"{act} {sec} (Murder rejected as victim not dead)")
                continue
                
        # RULE 5: If no minor involved, reject POCSO
        minor_involved = str(facts.get("minor_involved", "")).lower() == "true"
        if not minor_involved and act == "POCSO":
            hard_rejected.append(f"{act} {sec} (POCSO rejected as no minor involved)")
            continue
            
        # RULE 6: If force used AND property taken, reject Extortion (must be Robbery)
        if force_used and property_taken:
            if act == "IPC" and sec in ["384", "385", "386"]:
                hard_rejected.append(f"{act} {sec} (Extortion rejected as force + theft = Robbery)")
                continue
            if act == "BNS" and sec in ["308"]:
                hard_rejected.append(f"{act} {sec} (Extortion rejected as force + theft = Robbery)")
                continue

        # RULE 7: Conspiracy requires pre-planning
        premeditated = str(facts.get("premeditated", "")).lower() == "true"
        if not premeditated:
            # We strictly reject conspiracy unless there is explicit planning
            if act == "IPC" and sec in ["120B", "120A"]:
                hard_rejected.append(f"{act} {sec} (Conspiracy rejected as no explicit pre-planning)")
                continue
            if act == "BNS" and sec in ["61", "61(2)"]:
                hard_rejected.append(f"{act} {sec} (Conspiracy rejected as no explicit pre-planning)")
                continue
                
        pre_filtered.append(s)

    if hard_rejected:
        print(f"[Verifier] Hard Rejected {len(hard_rejected)} sections: {', '.join(hard_rejected)}")
        
    if not pre_filtered:
        return []
        
    sections = pre_filtered

    # Build facts summary for the verifier
    facts_summary = f"""
FACTS FROM COMPLAINT:
- Physical force actually applied to a person: {facts.get('force_used', False)}
- Actual physical injury occurred (not just threat): {facts.get('injury_occurred', False)}
- Death occurred: {facts.get('victim_status') == 'dead'}
- Penetration occurred (rape): {facts.get('penetration_occurred', False)}
- Property physically taken: {facts.get('property_taken', False)}
- Weapon used: {facts.get('weapon_used') or 'None'}
- Accused fled scene: {facts.get('accused_fled', False)}
- Number of accused: {facts.get('accused_count', 1)}
- Minor victim (under 18): {facts.get('minor_involved', False)}
- Female victim: {facts.get('female_victim', False)}
- Online/cyber method used: {facts.get('cyber_method', False)}
- Document forged: {facts.get('document_forged', False)}
- Government official impersonated: {facts.get('govt_impersonation', False)}
- Marital/domestic relationship: {facts.get('marital_relationship', False)}
- Complaint text: {facts.get('complaint_text', '')[:300]}
"""

    # Build section list for verification
    section_lines = []
    for i, s in enumerate(sections):
        section_lines.append(
            f"{i+1}. [{s.get('act')} {s.get('section_number')}] "
            f"{s.get('offense', '')} — {s.get('justification', '')}"
        )
    sections_text = "\n".join(section_lines)

    verification_prompt = f"""You are a strict Indian legal reviewer.
Check each proposed FIR section below against the facts.
Answer ONLY with the section number and YES or NO.

STRICT LEGAL RULES YOU MUST APPLY:
- IPC 326 / BNS 118 (Grievous Hurt by weapon): 
  YES only if weapon caused ACTUAL injury. 
  Weapon threat alone = NO.
  
- IPC 392 / BNS 309 (Robbery): 
  YES only if force was used AND property was actually taken 
  at the same time. No property taken = NO. Fleeing in vehicle = NO.
  
- POCSO 4/5/6 (Penetrative Sexual Assault): 
  YES only if penetration EXPLICITLY mentioned. 
  Touching without penetration = NO.
  
- POCSO 8 (Sexual Assault): 
  YES only if non-penetrative sexual touching of minor.
  Physical assault during robbery (no sexual element) = NO.
  
- BNS 64 / IPC 376 (Rape): 
  YES only if penetration EXPLICITLY mentioned. 
  Touching = NO.
  
- IPC 302 / BNS 103 (Murder): 
  YES only if death explicitly confirmed. 
  Stabbing where victim survived = NO.
  
- BNS 74 / IPC 354 (Outraging Modesty): 
  YES only if act was sexually motivated toward woman.
  Domestic beating = NO. Robbery assault = NO.
  
- IT Act 66C / 66D: 
  YES only if crime used electronic/digital method.
  Physical crime = NO.
  
- IPC 406 / BNS 316 (Breach of Trust): 
  YES only if accused was entrusted with property first.
  Fraud where victim was deceived = NO.
  
- IPC 120B / BNS 61 (Conspiracy): 
  YES only if 2+ accused AND clear evidence of pre-planning/agreement.
  Simply acting together or using weapons = NO.
  
- IPC 34 / BNS 3(5) (Common Intention): 
  YES only if 2+ accused acted together.
  Single accused = NO.
  
- IPC 149 / BNS 190 (Unlawful Assembly): 
  YES only if 3+ accused (courts apply even below 5).
  Single or 2 accused = NO.

{facts_summary}

PROPOSED SECTIONS TO VERIFY:
{sections_text}

RESPOND IN THIS EXACT FORMAT — one line per section:
1: YES
2: NO - weapon threatened only, no actual injury
3: YES
(and so on for every section)

ONLY output the numbered verdicts. Nothing else."""

    try:
        response = client.chat.completions.create(
            model=VERIFIER_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict legal verifier. "
                               "Output ONLY numbered YES/NO verdicts. "
                               "No explanations except after NO."
                },
                {
                    "role": "user", 
                    "content": verification_prompt
                }
            ],
            max_tokens=500,
            temperature=0.0  # zero temperature — deterministic
        )

        verdict_text = response.choices[0].message.content.strip()
        logger.info(f"[Verifier] Raw verdicts:\n{verdict_text}")

        # Parse verdicts
        verdicts = {}
        for line in verdict_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Match "1: YES" or "2: NO - reason"
            parts = line.split(":", 1)
            if len(parts) == 2:
                try:
                    idx = int(parts[0].strip()) - 1
                    verdict = parts[1].strip().upper()
                    verdicts[idx] = verdict.startswith("YES")
                    if not verdict.startswith("YES"):
                        reason = parts[1].strip()
                        logger.info(
                            f"[Verifier] REJECTED section "
                            f"{idx+1}: {reason}"
                        )
                except ValueError:
                    continue

        # Filter sections — keep only verified ones
        verified = []
        rejected = []
        for i, section in enumerate(sections):
            if verdicts.get(i, True):  # default True if not parsed
                verified.append(section)
            else:
                rejected.append(
                    f"{section.get('act')} "
                    f"{section.get('section_number')}"
                )

        if rejected:
            logger.info(
                f"[Verifier] Removed {len(rejected)} sections: "
                f"{', '.join(rejected)}"
            )
        logger.info(
            f"[Verifier] Kept {len(verified)}/{len(sections)} sections"
        )

        return verified

    except Exception as e:
        logger.error(f"[Verifier] Error: {e}")
        # On failure, return original sections unchanged
        # Never let verifier failure break the pipeline
        return sections
        logger.error(f"[Verifier] Error: {e}")
        # On failure, return original sections unchanged
        # Never let verifier failure break the pipeline
        return sections
