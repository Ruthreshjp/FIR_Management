import json

def correct_sections(raw_sections, facts):
    """
    Applies post-processing rules to the LLM sections.
    raw_sections: list of dicts representing sections
    facts: facts dict containing complaint_text
    """
    if not isinstance(raw_sections, list):
        return raw_sections
        
    complaint_text = facts.get("complaint_text", "")
    complaint_lower = complaint_text.lower()
    sections = raw_sections.copy()
    
    print("[Corrector] Running post-processing rules...")
    print(f"[Corrector] complaint_text length: {len(complaint_text)}")
    print(f"[Corrector] complaint_text preview: {complaint_text[:100]}")

    # FIX 4: "No direct BNS equivalent" appearing as section_number
    sections = [
        s for s in sections
        if str(s.get("section_number","")).strip().lower() not in [
            "no direct bns equivalent",
            "none", "n/a", "na", "null", ""
        ]
    ]
    
    # FIX 1: POCSO sections appearing with wrong act field
    POCSO_SECTION_NUMBERS = [str(i) for i in range(1, 47)]
    POCSO_OFFENSE_KEYWORDS = [
        "penetrative sexual assault", "sexual assault", 
        "sexual harassment", "pornography", "pocso",
        "aggravated penetrative", "aggravated sexual"
    ]
    for s in sections:
        act = s.get("act","").upper()
        sec = str(s.get("section_number",""))
        offense = s.get("offense","").lower()
        if act == "BNS" and sec in POCSO_SECTION_NUMBERS:
            if any(kw in offense for kw in POCSO_OFFENSE_KEYWORDS):
                s["act"] = "POCSO"
                print(f"[Corrector] FIXED act field: BNS {sec} -> POCSO {sec} ({s.get('offense')})")

    # RULE 1: Remove false positive robbery
    is_cyber_fraud = any(w in complaint_lower for w in [
        "otp", "online fraud", "cyber", "phishing",
        "upi fraud", "bank fraud", "internet banking",
        "app download", "screen sharing", "remote access",
        "password shared", "pin shared", "anydesk",
        "teamviewer", "remote verification", "kyc expiry",
        "account blocked", "account frozen", "verify account",
        "install app", "download app", "link sent", "claiming to be"
    ])
    has_physical_force = any(w in complaint_lower for w in [
        "hit", "punch", "slap", "push", "knife", "gun", "weapon",
        "physically attacked", "beat", "assault", "grabbed",
        "snatched physically", "held at gunpoint"
    ])
    no_violence_phrases = [
        "no violence", "without violence", "no force used",
        "did not use force", "ran away without", "just ran",
        "no physical", "peacefully", "without touching"
    ]
    
    if is_cyber_fraud:
        # FIX 3: Remove theft and criminal breach of trust in cyber cases
        original_count = len(sections)
        sections = [s for s in sections if str(s.get("section_number")) not in ["378","379","380","303","304"]]
        sections = [s for s in sections if str(s.get("section_number")) not in ["405","406","316"]]
        if len(sections) < original_count:
            print("[Corrector] REMOVED theft+breach_of_trust — cyber fraud case")
            
    if is_cyber_fraud and not has_physical_force:
        original_count = len(sections)
        sections = [
            s for s in sections
            if not (str(s.get("section_number")) in ["392", "309", "390", "391", "394", "395", "396", "179", "489A", "489B", "489C", "489D", "489E", "178", "180", "181", "182"])
        ]
        if len(sections) < original_count:
            print("[Corrector] REMOVED robbery and fake currency sections — cyber fraud detected, no physical force")
            
    if any(p in complaint_lower for p in no_violence_phrases):
        original_count = len(sections)
        sections = [
            s for s in sections
            if str(s.get("section_number")) not in ["309", "392", "390", "391", "394", "395", "396"]
        ]
        if len(sections) < original_count:
            print("[Corrector] REMOVED robbery — no violence explicitly stated")

    # RULE 2: Cheating by Personation
    if any(w in complaint_lower for w in ["impersonat", "posing as", "pretended to be", "claimed to be", "claiming to be", "introduced himself as", "fake officer", "fake rbi", "fake police", "fake bank", "fake manager", "disguised as", "masquerading"]):
        sections.extend([
            {"act": "IPC", "section_number": "419", "offense": "Cheating by personation", "justification": "Accused impersonated another person or government official to commit fraud", "bns_equivalent": "319", "confidence": 0.88, "primary": False},
            {"act": "BNS", "section_number": "319", "offense": "Cheating by personation", "justification": "BNS equivalent of IPC 419", "confidence": 0.88, "primary": False}
        ])

    # RULE 3: Forgery
    if any(w in complaint_lower for w in ["fake", "forged", "fake id", "fabricated", "counterfeit", "false document"]):
        sections.extend([
            {"act": "IPC", "section_number": "468", "offense": "Forgery for purpose of cheating", "justification": "Fake document created and used to deceive the complainant", "bns_equivalent": "336", "confidence": 0.87, "primary": False},
            {"act": "IPC", "section_number": "471", "offense": "Using forged document as genuine", "justification": "Forged document was presented as genuine to the complainant", "bns_equivalent": "336", "confidence": 0.87, "primary": False},
            {"act": "BNS", "section_number": "336", "offense": "Forgery", "justification": "BNS equivalent of IPC 468/471", "confidence": 0.87, "primary": False}
        ])

    # RULE 4: Cybercrime / IT Act
    if is_cyber_fraud:
        sections.extend([
            {"act": "IT Act", "section_number": "66C", "offense": "Identity theft", "justification": "Accused fraudulently used complainant's banking credentials and OTP", "confidence": 0.90, "primary": False},
            {"act": "IT Act", "section_number": "66D", "offense": "Cheating by personation using computer resource", "justification": "Accused impersonated a government official using phone/app/WhatsApp to commit fraud", "confidence": 0.90, "primary": False}
        ])

    # RULE 5: Criminal Intimidation
    if any(w in complaint_lower for w in ["threatened", "threat", "warned", "demanded", "pointed knife", "pointed gun", "at gunpoint", "at knifepoint", "will kill", "will harm", "if you report", "do not tell", "keep quiet or", "break your", "taught a lesson"]):
        sections.extend([
            {"act": "IPC", "section_number": "506", "offense": "Criminal Intimidation", "justification": "Accused made threats to cause fear of injury to person or property", "bns_equivalent": "351", "confidence": 0.85, "primary": False},
            {"act": "BNS", "section_number": "351", "offense": "Criminal Intimidation", "justification": "BNS equivalent of IPC 506", "confidence": 0.85, "primary": False}
        ])

    # RULE 6: Domestic Violence
    is_domestic = any(w in complaint_lower for w in ["husband", "wife", "spouse", "in-laws", "mother-in-law", "father-in-law", "sister-in-law", "brother-in-law", "dowry", "marital", "matrimonial", "domestic violence", "domestic abuse"])
    if is_domestic:
        sections.extend([
            {"act": "IPC", "section_number": "498A", "offense": "Cruelty by husband or relatives of husband", "justification": "Accused is spouse or relative subjecting victim to cruelty, harassment or dowry demands", "bns_equivalent": "85", "confidence": 0.92, "primary": True},
            {"act": "BNS", "section_number": "85", "offense": "Cruelty by husband or his relatives", "justification": "BNS equivalent of IPC 498A", "confidence": 0.92, "primary": True}
        ])
        
    # Dowry Death Attempt - FIX 5
    has_dowry = any(w in complaint_lower for w in ["dowry", "dowry demand", "harassing for dowry", "dowry harassment", "demands for dowry"])
    victim_status = str(facts.get("victim_status", "")).lower()
    if has_dowry and victim_status in ["dead", "critical"]:
        sections.extend([
            {"act": "IPC", "section_number": "304B", "offense": "Dowry death", "justification": "Dowry-related harassment that may lead to unnatural death", "bns_equivalent": "80", "confidence": 0.80, "primary": False},
            {"act": "BNS", "section_number": "80", "offense": "Dowry death", "justification": "BNS equivalent of IPC 304B", "confidence": 0.80, "primary": False}
        ])

    is_weapon_assault = any(w in complaint_lower for w in ["rod", "stick", "belt", "wire", "beat", "thrash"])
    if is_domestic and is_weapon_assault:
        sections = [s for s in sections if str(s.get("section_number")) not in ["74", "354"]]
        
    # RULE 7: POCSO
    has_penetration = any(w in complaint_lower for w in ["rape", "penetrat", "sexual intercourse", "inserted", "forced intercourse", "raped"])
    if not has_penetration:
        sections = [s for s in sections if str(s.get("section_number")) not in ["376", "376A", "376D", "64", "65", "66", "63"] or s.get("act") not in ["IPC", "BNS"]]
        sections = [s for s in sections if not (s.get("act") == "POCSO" and str(s.get("section_number")) in ["4", "5", "6"])]

    is_minor = facts.get("minor_involved", False) or any(w in complaint_lower for w in ["year-old", "minor", "child", "daughter", "son", "student", "kid"])
    if is_minor and any(w in complaint_lower for w in ["touched", "private parts", "fondled", "molested", "inappropriate", "harass"]):
        sections.extend([
            {"act": "POCSO", "section_number": "8", "offense": "Punishment for sexual assault on child", "justification": "Accused committed sexual assault (non-penetrative) on a minor", "confidence": 0.92, "primary": True},
            {"act": "POCSO", "section_number": "12", "offense": "Punishment for sexual harassment of child", "justification": "Accused sexually harassed a minor", "confidence": 0.88, "primary": False}
        ])

    # RULE 8: Intentional Insult
    if any(w in complaint_lower for w in ["abused", "insulted", "filthy language", "obscene language", "abusive language", "vulgar language", "publicly humiliated", "called names", "verbal abuse", "slurred", "shouted abuses", "abused in public"]):
        sections.extend([
            {"act": "IPC", "section_number": "504", "offense": "Intentional insult with intent to provoke breach of peace", "justification": "Accused used abusive/filthy language intentionally to provoke and insult", "bns_equivalent": "352", "confidence": 0.83, "primary": False},
            {"act": "BNS", "section_number": "352", "offense": "Intentional insult with intent to provoke breach of peace", "justification": "BNS equivalent of IPC 504", "confidence": 0.83, "primary": False}
        ])
        
    # RULE 9: Mischief
    if any(w in complaint_lower for w in ["broke", "broken", "damaged", "destroyed", "smashed"]):
        sections.extend([
            {"act": "IPC", "section_number": "427", "offense": "Mischief causing damage", "justification": "Accused caused damage to property", "bns_equivalent": "324", "confidence": 0.85, "primary": False},
            {"act": "BNS", "section_number": "324", "offense": "Mischief causing damage", "justification": "BNS equivalent of IPC 427", "confidence": 0.85, "primary": False}
        ])
        
    # RULE 10: Criminal Conspiracy
    premeditated_keywords = [
        "planned", "came with", "brought", "waiting for",
        "along with", "accompanied by", "group of",
        "approached on", "came on motorcycle", "came prepared",
        "came together", "assembled", "gathered", "coordinated",
        "two motorcycles", "came in a vehicle", "came in a car",
        "came in an auto", "pre-planned", "conspired",
        "stopped me", "blocked my path", "surrounded",
        "demanded", "pointed", "gang", "armed with"
    ]
    if facts.get("accused_count", 1) >= 2 and any(w in complaint_lower for w in premeditated_keywords):
        sections.extend([
            {"act": "IPC", "section_number": "120B", "offense": "Criminal Conspiracy", "justification": "Multiple accused acted with pre-planning", "bns_equivalent": "61(2)", "confidence": 0.90, "primary": False},
            {"act": "BNS", "section_number": "61(2)", "offense": "Criminal Conspiracy", "justification": "BNS equivalent of IPC 120B", "confidence": 0.90, "primary": False}
        ])

    # Replace IPC 503 with 506
    for s in sections:
        if s.get("act") == "IPC" and str(s.get("section_number")) == "503":
            s["section_number"] = "506"
            s["offense"] = "Criminal Intimidation"
            
    # FIX 4: IPC 427 -> BNS 324 mapping update in place
    for s in sections:
        if s.get("act") == "IPC" and str(s.get("section_number")) == "427":
            s["bns_equivalent"] = "324"

    # Deduplicate
    final_sections = []
    seen_keys = set()
    for s in sections:
        k = f"{s.get('act')}_{s.get('section_number')}"
        if k not in seen_keys:
            seen_keys.add(k)
            final_sections.append(s)

    return final_sections
