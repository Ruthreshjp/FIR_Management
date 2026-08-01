import os
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
VERIFIER_MODEL = os.getenv("GROQ_MODEL_VERIFIER",
                           "llama-3.1-8b-instant")


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
  YES only if force was used AND property was taken 
  at the same time. Online fraud = NO.
  
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
  
- IPC 120B (Conspiracy): 
  YES only if 2+ accused AND pre-planning evidence exists.
  Single accused = NO.
  
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
