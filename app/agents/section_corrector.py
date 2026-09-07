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
    
    # Reverse mapping to fix LLM BNS hallucinations (LLM assigning IPC numbers to BNS)
    try:
        from app.config.bns_ipc_mapping import BNS_TO_IPC_MAP
        IPC_TO_BNS_MAP = {}
        for bns, ipc_str in BNS_TO_IPC_MAP.items():
            for ipc in ipc_str.split(','):
                IPC_TO_BNS_MAP[ipc.strip()] = bns
                
        for s in sections:
            if s.get("act") == "BNS":
                sec = str(s.get("section_number")).strip()
                if sec in IPC_TO_BNS_MAP:
                    print(f"[Corrector] FIXED Hallucinated BNS {sec} -> BNS {IPC_TO_BNS_MAP[sec]}")
                    s["section_number"] = IPC_TO_BNS_MAP[sec]
    except Exception as e:
        print(f"[Corrector] Error applying hallucination map: {e}")
        
    for s in sections:
        if s.get("act") == "BNS" and str(s.get("section_number")) in ["288", "338"]:
            s["section_number"] = "125"
            s["offense"] = "Act endangering life or personal safety of others (Grievous Hurt)"
    
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
    }
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
