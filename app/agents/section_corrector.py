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

    # Use LLM boolean flags primarily, fallback to keyword matching
    is_cyber_fraud = str(facts.get("cyber_method", "")).lower() == "true" or any(w in complaint_lower for w in [
        "otp", "online fraud", "cyber", "phishing",
        "upi fraud", "bank fraud", "internet banking",
        "app download", "screen sharing", "remote access",
        "password shared", "pin shared", "anydesk",
        "teamviewer", "remote verification", "kyc expiry",
        "account blocked", "account frozen", "verify account",
        "install app", "download app", "link sent", "claiming to be"
    ])
    
    has_physical_force = str(facts.get("force_used", "")).lower() == "true" or any(w in complaint_lower for w in [
        "hit", "punch", "slap", "push", "knife", "gun", "weapon",
        "physically attacked", "beat", "assault", "grabbed",
        "snatched physically", "held at gunpoint"
    ])
    
    no_violence_phrases = [
        "no violence", "without violence", "no force used",
        "did not use force", "ran away without", "just ran",
        "no physical", "peacefully", "without touching"
    ]
    
    if str(facts.get("force_used", "")).lower() == "false":
        has_physical_force = False
    
    if is_cyber_fraud:
        # FIX 3: Remove theft and criminal breach of trust in cyber cases
        original_count = len(sections)
        sections = [s for s in sections if str(s.get("section_number")) not in ["378","379","380","303","304", "405", "406", "316", "179", "180", "181", "182", "489A", "489B", "489C", "489D", "489E"]]
        if len(sections) < original_count:
            print("[Corrector] REMOVED theft+breach_of_trust+fake_currency — cyber fraud case")
            
    if is_cyber_fraud and not has_physical_force:
        original_count = len(sections)
        sections = [
            s for s in sections
            if not (str(s.get("section_number")) in ["392", "309", "390", "391", "394", "395", "396"])
        ]
        if len(sections) < original_count:
            print("[Corrector] REMOVED robbery — cyber fraud detected, no physical force")
            
    if any(p in complaint_lower for p in no_violence_phrases):
        original_count = len(sections)
        sections = [
            s for s in sections
            if str(s.get("section_number")) not in ["309", "392", "390", "391", "394", "395", "396"]
        ]
        if len(sections) < original_count:
            print("[Corrector] REMOVED robbery — no violence explicitly stated")

    # Wrong BNS sections (BNS 4, BNS 12)
    sections = [s for s in sections if not (s.get("act") == "BNS" and str(s.get("section_number")) in ["4", "5", "6", "7", "8", "9", "10", "11", "12"])]
    
    # Replace IPC 503 with 506
    for s in sections:
        if s.get("act") == "IPC" and str(s.get("section_number")) == "503":
            s["section_number"] = "506"
            s["offense"] = "Criminal Intimidation"
            
    # Add strict removals
    if str(facts.get("animal_involved", "")).lower() != "true":
        original_count = len(sections)
        sections = [s for s in sections if not (s.get("act") == "IPC" and str(s.get("section_number")) in ["428", "429"])]
        sections = [s for s in sections if not (s.get("act") == "BNS" and str(s.get("section_number")) == "325")]
        if len(sections) < original_count:
            print("[Corrector] REMOVED animal mischief — no animal involved")

    if str(facts.get("minor_involved", "")).lower() != "true":
        original_count = len(sections)
        sections = [s for s in sections if s.get("act") != "POCSO"]
        if len(sections) < original_count:
            print("[Corrector] REMOVED POCSO — no minor involved")
            
    victim_status = str(facts.get("victim_status", "")).lower()
    if "dead" not in victim_status and "death" not in victim_status:
        original_count = len(sections)
        sections = [s for s in sections if not (s.get("act") == "IPC" and str(s.get("section_number")) == "302")]
        sections = [s for s in sections if not (s.get("act") == "BNS" and str(s.get("section_number")) == "103")]
        if len(sections) < original_count:
            print("[Corrector] REMOVED Murder — victim is not dead")

    # ------------------ PASS 2: STRUCTURAL RULES ------------------
    try:
        accused_count = int(facts.get("accused_count", 1))
    except (ValueError, TypeError):
        accused_count = 1

    # 1. Common Intention — accused_count >= 2
    if accused_count >= 2:
        sections.extend([
            {"act": "IPC", "section_number": "34", "offense": "Acts done by several persons in furtherance of common intention", "justification": "Multiple accused acting together", "confidence": 0.90, "primary": False},
            {"act": "BNS", "section_number": "3(5)", "offense": "Acts done by several persons in furtherance of common intention", "justification": "BNS equivalent of IPC 34", "confidence": 0.90, "primary": False}
        ])

    # 2. Criminal Conspiracy — accused_count >= 2 AND premeditated
    is_premeditated = str(facts.get("premeditated", "")).lower() == "true"
    planning_keywords = ["planned", "conspired", "agreed beforehand", "plotted", "trap", "pre-planned", "ambush"]
    has_planning_evidence = any(kw in complaint_lower for kw in planning_keywords)
    
    if accused_count >= 2 and (is_premeditated or has_planning_evidence):
        sections.extend([
            {"act": "IPC", "section_number": "120B", "offense": "Criminal Conspiracy", "justification": "Clear evidence of prior agreement or pre-planning", "confidence": 0.90, "primary": False},
            {"act": "BNS", "section_number": "61(2)", "offense": "Criminal Conspiracy", "justification": "BNS equivalent of IPC 120B", "confidence": 0.90, "primary": False}
        ])
    else:
        # STRICT RULE: Remove conspiracy if no clear planning
        original_count = len(sections)
        sections = [s for s in sections if not str(s.get("section_number")) in ["120B", "61", "61(2)"]]
        if len(sections) < original_count:
            print("[Corrector] STRICT RULE: REMOVED Conspiracy because no clear pre-planning was found.")

    # 3. Unlawful Assembly — accused_count >= 3
    if accused_count >= 3:
        sections.extend([
            {"act": "IPC", "section_number": "149", "offense": "Every member of unlawful assembly guilty of offence", "justification": "Group of persons acting unlawfully", "confidence": 0.85, "primary": False},
            {"act": "BNS", "section_number": "190", "offense": "Every member of unlawful assembly guilty", "justification": "BNS equivalent of IPC 149", "confidence": 0.85, "primary": False}
        ])

    # 4. Absconding — accused_fled = True
    if str(facts.get("accused_fled", "")).lower() in ["true", "yes"]:
        sections.extend([
            {"act": "IPC", "section_number": "201", "offense": "Causing disappearance of evidence of offence", "justification": "Accused fled the scene to avoid apprehension", "confidence": 0.80, "primary": False},
            {"act": "BNS", "section_number": "238", "offense": "Causing disappearance of evidence", "justification": "BNS equivalent of IPC 201", "confidence": 0.80, "primary": False}
        ])

    # 5. Domestic Violence (IPC 498A) — marital_relationship = True
    if str(facts.get("marital_relationship", "")).lower() in ["true", "yes"]:
        sections.extend([
            {"act": "IPC", "section_number": "498A", "offense": "Cruelty by husband or relatives of husband", "justification": "Domestic violence in marital relationship", "confidence": 0.92, "primary": True},
            {"act": "BNS", "section_number": "85", "offense": "Cruelty by husband or his relatives", "justification": "BNS equivalent of IPC 498A", "confidence": 0.92, "primary": True}
        ])

    # 6. Grievous Hurt — weapon_used AND injury_occurred
    weapon = facts.get("weapon_used", "")
    has_weapon = weapon and str(weapon).lower() not in ["none", "unknown", "n/a", ""]
    injury_occurred = "injured" in victim_status or "dead" in victim_status
    if has_weapon and injury_occurred:
        sections.extend([
            {"act": "IPC", "section_number": "326", "offense": "Voluntarily causing grievous hurt by dangerous weapons", "justification": "Use of weapon resulting in injury", "confidence": 0.90, "primary": True},
            {"act": "BNS", "section_number": "118", "offense": "Voluntarily causing grievous hurt by dangerous weapons", "justification": "BNS equivalent of IPC 326", "confidence": 0.90, "primary": True}
        ])

    # 7. Murder — victim_status = dead
    if "dead" in victim_status or "death" in victim_status:
        sections.extend([
            {"act": "IPC", "section_number": "302", "offense": "Murder", "justification": "Death of the victim", "confidence": 0.95, "primary": True},
            {"act": "BNS", "section_number": "103", "offense": "Murder", "justification": "BNS equivalent of IPC 302", "confidence": 0.95, "primary": True}
        ])
        
    # 8. Robbery — force_used AND property_taken
    force_used = str(facts.get("force_used", "")).lower() == "true"
    property_taken = str(facts.get("property_taken", "")).lower() == "true"
    if force_used and property_taken and not is_cyber_fraud:
        sections.extend([
            {"act": "IPC", "section_number": "392", "offense": "Robbery", "justification": "Property taken with use of force or threat", "confidence": 0.95, "primary": True},
            {"act": "BNS", "section_number": "309", "offense": "Robbery", "justification": "BNS equivalent of IPC 392", "confidence": 0.95, "primary": True}
        ])
    else:
        # STRICT RULE: Remove all robbery if property was not taken or force was not used
        original_count = len(sections)
        sections = [s for s in sections if not str(s.get("section_number")) in ["392", "390", "393", "394", "395", "397", "309", "310", "311"]]
        if len(sections) < original_count:
            print("[Corrector] STRICT RULE: REMOVED robbery because force_used AND property_taken were not BOTH true.")

    # 9. Rash Driving / Vehicle Injury
    vehicle_keywords = ["vehicle", "car", "bike", "motorcycle", "scooter", "truck", "bus", "driving", "rode", "hit and run"]
    has_vehicle = any(kw in complaint_lower for kw in vehicle_keywords)
    if has_vehicle and injury_occurred and not property_taken:
        sections.extend([
            {"act": "IPC", "section_number": "279", "offense": "Rash driving or riding on a public way", "justification": "Vehicle involved in rash manner", "confidence": 0.90, "primary": True},
            {"act": "BNS", "section_number": "281", "offense": "Rash driving or riding on a public way", "justification": "BNS equivalent of IPC 279", "confidence": 0.90, "primary": True},
            {"act": "IPC", "section_number": "337", "offense": "Causing hurt by act endangering life", "justification": "Injury caused by vehicle", "confidence": 0.90, "primary": True},
            {"act": "BNS", "section_number": "125", "offense": "Act endangering life or personal safety of others", "justification": "BNS equivalent of IPC 337", "confidence": 0.90, "primary": True}
        ])

    # 10. Cheating (IPC 420 -> BNS 318)
    has_ipc_420 = any(s.get("act") == "IPC" and str(s.get("section_number")) == "420" for s in sections)
    has_bns_318 = any(s.get("act") == "BNS" and str(s.get("section_number")) == "318" for s in sections)
    if has_ipc_420 and not has_bns_318:
        # Find justification from IPC 420 if possible
        ipc_420_section = next((s for s in sections if s.get("act") == "IPC" and str(s.get("section_number")) == "420"), None)
        justification = ipc_420_section.get("justification", "BNS equivalent of IPC 420") if ipc_420_section else "BNS equivalent of IPC 420"
        confidence = ipc_420_section.get("confidence", 0.90) if ipc_420_section else 0.90
        
        sections.append({
            "act": "BNS", 
            "section_number": "318", 
            "offense": "Cheating and dishonestly inducing delivery of property", 
            "justification": justification, 
            "confidence": confidence, 
            "primary": True
        })
        print("[Corrector] FORCE ADDED BNS 318 for IPC 420")

    # Deduplicate
    final_sections = []
    seen_keys = set()
    for s in sections:
        k = f"{s.get('act')}_{s.get('section_number')}"
        if k not in seen_keys:
            seen_keys.add(k)
            final_sections.append(s)

    return final_sections

DETERMINISTIC_RULES = [
    # IF accused_count >= 2 → ALWAYS add IPC 34 + BNS 3(5)
    {
        "condition": lambda f: int(f.get("accused_count",1)) >= 2,
        "always_add": [
            {"act":"IPC","section_number":"34",
             "offense":"Common Intention",
             "justification":"Multiple accused acting together",
             "confidence":1.0,"primary":False},
            {"act":"BNS","section_number":"3(5)",
             "offense":"Common Intention",
             "justification":"BNS equivalent of IPC 34",
             "confidence":1.0,"primary":False},
        ]
    },
    # IF accused_count >= 2 AND premeditated → ALWAYS IPC 120B
    {
        "condition": lambda f: (
            int(f.get("accused_count",1)) >= 2 and
            f.get("premeditated", False)
        ),
        "always_add": [
            {"act":"IPC","section_number":"120B",
             "offense":"Criminal Conspiracy",
             "justification":"Pre-planned act with multiple accused",
             "confidence":1.0,"primary":False},
        ]
    },
    # IF accused_count >= 3 → ALWAYS add unlawful assembly
    {
        "condition": lambda f: int(f.get("accused_count",1)) >= 3,
        "always_add": [
            {"act":"IPC","section_number":"149",
             "offense":"Unlawful Assembly",
             "justification":"Three or more persons with common object",
             "confidence":1.0,"primary":False},
            {"act":"BNS","section_number":"190",
             "offense":"Unlawful Assembly",
             "justification":"BNS equivalent of IPC 149",
             "confidence":1.0,"primary":False},
        ]
    },
    # IF victim_status == dead → ALWAYS IPC 302 + BNS 103
    {
        "condition": lambda f: f.get("victim_status") == "dead" or f.get("death", False),
        "always_add": [
            {"act":"IPC","section_number":"302",
             "offense":"Murder",
             "justification":"Death of victim confirmed",
             "confidence":1.0,"primary":True},
            {"act":"BNS","section_number":"103",
             "offense":"Murder",
             "justification":"BNS equivalent of IPC 302",
             "confidence":1.0,"primary":True},
        ]
    },
    # IF accused_fled → ALWAYS BNS 238 + IPC 201
    {
        "condition": lambda f: str(f.get("accused_fled", "")).lower() in ["true", "yes"],
        "always_add": [
            {"act":"IPC","section_number":"201",
             "offense":"Causing disappearance of evidence",
             "justification":"Accused fled scene after offence",
             "confidence":0.95,"primary":False},
            {"act":"BNS","section_number":"238",
             "offense":"Causing disappearance of evidence",
             "justification":"BNS equivalent of IPC 201",
             "confidence":0.95,"primary":False},
        ]
    },
    # IF marital_relationship → ALWAYS IPC 498A + BNS 85
    {
        "condition": lambda f: str(f.get("marital_relationship","")).lower() in ["true", "yes"],
        "always_add": [
            {"act":"IPC","section_number":"498A",
             "offense":"Cruelty by husband",
             "justification":"Domestic violence by spouse",
             "confidence":0.95,"primary":True},
            {"act":"BNS","section_number":"85",
             "offense":"Cruelty by husband",
             "justification":"BNS equivalent of IPC 498A",
             "confidence":0.95,"primary":True},
        ]
    },
    # IF minor + sexual touching → ALWAYS POCSO 8 + POCSO 12
    {
        "condition": lambda f: (
            str(f.get("minor_involved", "")).lower() in ["true", "yes"] and
            f.get("sexual_element", False) and
            not f.get("penetration_occurred", False)
        ),
        "always_add": [
            {"act":"POCSO","section_number":"8",
             "offense":"Sexual Assault on child",
             "justification":"Non-penetrative sexual assault on minor",
             "confidence":0.95,"primary":True},
            {"act":"POCSO","section_number":"12",
             "offense":"Sexual Harassment of child",
             "justification":"Sexual harassment of minor",
             "confidence":0.90,"primary":False},
        ]
    },
    # IF drugs mentioned → ALWAYS NDPS 8 + NDPS 21
    {
        "condition": lambda f: f.get("drug_involved", False),
        "always_add": [
            {"act":"NDPS_ACT","section_number":"8",
             "offense":"Prohibition on narcotic drugs",
             "justification":"Narcotic substance involved",
             "confidence":0.95,"primary":True},
            {"act":"NDPS_ACT","section_number":"21",
             "offense":"Punishment for drug offence",
             "justification":"Sale/possession of narcotic drug",
             "confidence":0.95,"primary":True},
        ]
    },
    # IF weapon used AND injury → ALWAYS IPC 326 + BNS 118
    {
        "condition": lambda f: (
            f.get("weapon_used") not in [None,"","none","unknown"]
            and (f.get("injury_occurred", False) or "injured" in str(f.get("victim_status", "")).lower())
        ),
        "always_add": [
            {"act":"IPC","section_number":"326",
             "offense":"Grievous Hurt by dangerous weapon",
             "justification":"Weapon caused actual injury",
             "confidence":0.92,"primary":False},
            {"act":"BNS","section_number":"118",
             "offense":"Grievous Hurt by dangerous weapon",
             "justification":"BNS equivalent of IPC 326",
             "confidence":0.92,"primary":False},
        ]
    },
]

def apply_deterministic_rules(sections, facts):
    seen = {(s.get("act"), str(s.get("section_number")))
            for s in sections}
    added = []
    
    for rule in DETERMINISTIC_RULES:
        try:
            if rule["condition"](facts):
                for s in rule["always_add"]:
                    key = (s["act"], str(s["section_number"]))
                    if key not in seen:
                        seen.add(key)
                        added.append(s)
                        print(f"[Rules] AUTO-ADDED: "
                              f"{s['act']} {s['section_number']}"
                              f" — {s['offense']}")
        except Exception as e:
            print(f"[Rules] Rule error: {e}")
    
    return sections + added
