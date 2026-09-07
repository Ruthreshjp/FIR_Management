# Mapping BNS (Bharatiya Nyaya Sanhita) sections back to IPC (Indian Penal Code)
# for backward compatibility and reference.

BNS_TO_IPC_MAP = {
    "103": "302",      # Murder
    "109": "307",      # Attempt to Murder
    "115": "323",      # Voluntarily causing hurt
    "115(2)": "324",   # Hurt by dangerous weapons
    "118": "326",      # Grievous hurt by weapons
    "74": "354",       # Assault to outrage modesty
    "64": "376",       # Rape
    "303": "379",      # Theft
    "305": "380",      # Theft in dwelling
    "308": "384",      # Extortion
    "309": "392",      # Robbery
    "310": "395",      # Dacoity
    "316": "406",      # Criminal Breach of Trust
    "317": "411",      # Dishonestly receiving stolen property
    "318": "420",      # Cheating/Fraud
    "325": "428, 429", # Animal Mischief
    "85": "498A",      # Domestic Violence
    "352": "504",      # Intentional insult
    "351": "506",      # Criminal intimidation
    "3(5)": "34",      # Common intention
    "61(2)": "120B",   # Criminal Conspiracy
    "190": "149",      # Unlawful Assembly
    "238": "201",      # Causing disappearance of evidence
    "281": "279",      # Rash driving
    "125": "337, 338", # Act endangering life (Hurt / Grievous Hurt)
    "288": "338",      # Causing grievous hurt by act endangering life
    "117": "325",      # Grievous hurt
    "329": "447",      # Criminal trespass
    "324": "427",      # Mischief
    "296": "294",      # Obscene acts
    "126": "341",      # Wrongful restraint
    "189": "147",      # Rioting
    "191(2)": "148",   # Rioting armed
    "79": "509",       # Word/gesture to insult modesty
    "106": "304A",     # Death by negligence
}

def get_ipc_for_bns(bns_section: str) -> str:
    """Returns the equivalent IPC section(s) for a given BNS section, or None."""
    bns_str = str(bns_section).strip()
    if bns_str in BNS_TO_IPC_MAP:
        return BNS_TO_IPC_MAP[bns_str]
        
    import re
    match = re.match(r'^(\d+)', bns_str)
    if match:
        base_section = match.group(1)
        if base_section in BNS_TO_IPC_MAP:
            return BNS_TO_IPC_MAP[base_section]
            
    return None
