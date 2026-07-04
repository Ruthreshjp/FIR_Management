import os
import csv
import json
import re

# Setup paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw_ipc_csv = os.path.join(base_dir, "data", "raw", "FIR_DATASET.csv")
raw_bns_csv = os.path.join(base_dir, "data", "raw", "bns_sections.csv")
output_json = os.path.join(base_dir, "data", "ipc_bns_dataset.json")

# Ensure output directory exists
os.makedirs(os.path.dirname(output_json), exist_ok=True)

# The user-provided hardcoded IPC-to-BNS mapping
IPC_TO_BNS = {
  "302": "103", "303": "104", "304": "105", "304A": "106",
  "305": "107", "306": "108", "307": "109", "308": "110",
  "309": "111", "310": "112", "311": "113", "312": "88",
  "313": "89", "314": "90", "315": "91", "316": "92",
  "317": "93", "318": "94", "319": "114", "320": "114",
  "321": "115", "322": "115", "323": "115", "324": "116",
  "325": "117", "326": "118", "326A": "119", "326B": "120",
  "327": "121", "328": "122", "329": "123", "330": "124",
  "331": "125", "332": "121", "333": "121", "334": "115",
  "335": "115", "336": "125", "337": "125", "338": "125",
  "339": "126", "340": "127", "341": "126", "342": "127",
  "343": "127", "344": "127", "345": "127", "346": "127",
  "347": "128", "348": "129", "349": "130", "350": "131",
  "351": "131", "352": "115", "353": "132", "354": "74",
  "354A": "75", "354B": "76", "354C": "77", "354D": "78",
  "355": "74", "356": "74", "357": "74", "358": "74",
  "359": "133", "360": "134", "361": "134", "362": "134",
  "363": "135", "363A": "136", "364": "137", "364A": "138",
  "365": "139", "366": "140", "366A": "141", "366B": "142",
  "367": "143", "368": "144", "369": "145", "370": "143",
  "370A": "143", "371": "143", "372": "98", "373": "99",
  "374": "143", "375": "63", "376": "64", "376A": "66",
  "376B": "67", "376C": "68", "376D": "70", "376E": "66",
  "377": "100", "378": "303", "379": "303", "380": "303",
  "381": "303", "382": "304", "383": "308", "384": "308",
  "385": "308", "386": "308", "387": "308", "388": "308",
  "389": "308", "390": "309", "391": "310", "392": "309",
  "393": "309", "394": "309", "395": "310", "396": "310",
  "397": "309", "398": "309", "399": "310", "400": "310",
  "401": "310", "402": "310", "403": "314", "404": "314",
  "405": "316", "406": "316", "407": "316", "408": "316",
  "409": "316", "410": "317", "411": "317", "412": "317",
  "413": "317", "414": "317", "415": "318", "416": "318",
  "417": "318", "418": "318", "419": "319", "420": "318",
  "421": "320", "422": "321", "423": "321", "424": "321",
  "425": "324", "426": "324", "427": "324", "428": "325",
  "429": "325", "430": "324", "431": "324", "432": "324",
  "433": "324", "434": "324", "435": "326", "436": "326",
  "437": "326", "438": "326", "439": "326", "440": "326",
  "441": "329", "442": "329", "443": "330", "444": "331",
  "445": "330", "446": "332", "447": "329", "448": "329",
  "449": "333", "450": "333", "451": "333", "452": "333",
  "453": "334", "454": "334", "455": "334", "456": "335",
  "457": "305", "458": "305", "459": "305", "460": "305",
  "461": "336", "462": "336", "463": "336", "464": "336",
  "465": "336", "466": "336", "467": "336", "468": "336",
  "469": "336", "470": "336", "471": "336", "472": "336",
  "473": "336", "474": "336", "475": "336", "476": "336",
  "477": "336", "477A": "336", "489A": "178", "489B": "179",
  "489C": "180", "489D": "181", "489E": "182",
  "499": "356", "500": "356", "501": "357", "502": "357",
  "503": "351", "504": "352", "505": "353", "506": "351",
  "507": "351", "508": "354", "509": "79",
  "34": "3(5)", "107": "48", "109": "49",
  "120A": None, "120B": None,
  "141": "187", "142": "188", "143": "189", "144": "189",
  "149": None, "201": "238"
}

# Helper to normalize Cognizable/Bailable
def normalize_status(val, expected_type):
    val = (val or "").strip()
    if expected_type == "cognizable":
        if val == "Cognizable": return "Cognizable"
        if val == "Non-Cognizable": return "Non-Cognizable"
        return "Conditional"
    if expected_type == "bailable":
        if val == "Bailable": return "Bailable"
        if val == "Non-Bailable": return "Non-Bailable"
        return "Conditional"
    return None

def extract_offense_from_description(desc: str, section_num: str) -> str:
    """For IPC rows missing an Offense field, extract a short title from the Description."""
    if not desc:
        return f"IPC Section {section_num}"
    # Clean the preamble first
    text = re.sub(
        rf"Description of IPC Section {re.escape(section_num)}\s*"
        rf"According to section {re.escape(section_num)} of [Ii]ndian penal code,?\s*",
        "", desc, flags=re.IGNORECASE
    )
    # Take first sentence as the offense title (up to 80 chars)
    first_sentence = text.split('.')[0].strip()
    if len(first_sentence) > 80:
        first_sentence = first_sentence[:77] + "..."
    return first_sentence or f"IPC Section {section_num}"

def main():
    dataset = []
    
    # 1. Process IPC CSV
    with open(raw_ipc_csv, "r", encoding="utf-8") as f:
        # Check first line to know headers
        reader = csv.DictReader(f)
        for row in reader:
            # url: https://lawrato.com/indian-kanoon/ipc/section-302
            url = row.get("URL") or row.get("url") or ""
            sec_num = url.split("section-")[-1].strip() if "section-" in url else ""
            if not sec_num:
                continue

            # Some rows might have slightly different header names, handle gracefully
            offense = row.get("Offense") or row.get("offense")
            desc = row.get("Description") or row.get("description", "")
            punish = row.get("Punishment") or row.get("punishment")
            cog = normalize_status(row.get("Cognizable") or row.get("cognizable"), "cognizable")
            bail = normalize_status(row.get("Bailable") or row.get("bailable"), "bailable")
            court = row.get("Court") or row.get("court")

            # If offense is null/empty, extract from description
            if not offense or str(offense).strip() in ('', 'nan'):
                offense = extract_offense_from_description(desc, sec_num)
            else:
                offense = offense.strip()

            item = {
                "act": "IPC",
                "section_number": sec_num,
                "offense": offense,
                "description": desc.strip(),
                "punishment": punish.strip() if punish else None,
                "cognizable": cog,
                "bailable": bail,
                "court": court.strip() if court else None,
                "corresponding_section": {"BNS": IPC_TO_BNS.get(sec_num, None)},
                "source": "FIR_DATASET.csv"
            }
            
            # Add specific note if it's one of the special general provisions with no BNS equivalent
            if sec_num in ["120A", "120B", "149"]:
                item["note"] = "No direct BNS equivalent — charged under general provisions"
                
            dataset.append(item)

    MISSING_IPC_SECTIONS = [
        {
            "act": "IPC",
            "section_number": "34",
            "offense": "Acts done by several persons in furtherance of common intention",
            "description": "When a criminal act is done by several persons in furtherance of the common intention of all, each of such persons is liable for that act in the same manner as if it were done by him alone. This section does not create a substantive offence but only makes each member of a group liable for acts done in furtherance of the common intention.",
            "punishment": "Same punishment as the principal offender for the substantive offence committed",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Same court as principal offence",
            "corresponding_section": {
                "BNS": "3(5)",
                "note": "BNS Section 3 subsection (5) covers common intention under General Explanations — no standalone BNS section exists"
            },
            "source": "manual"
        },
        {
            "act": "IPC",
            "section_number": "107",
            "offense": "Abetment of a thing",
            "description": "A person abets the doing of a thing who — First, instigates any person to do that thing; or Secondly, engages with one or more other person or persons in any conspiracy for the doing of that thing, if an act or illegal omission takes place in pursuance of that conspiracy; or Thirdly, intentionally aids, by any act or illegal omission, the doing of that thing.",
            "punishment": "Definition section — punishment under IPC 109, 110, 111 depending on outcome",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Same court as principal offence",
            "corresponding_section": {
                "BNS": "48",
                "note": "BNS Section 48 covers abetment"
            },
            "source": "manual"
        },
        {
            "act": "IPC",
            "section_number": "109",
            "offense": "Punishment of abetment if the act abetted is committed in consequence",
            "description": "Whoever abets any offence shall, if the act abetted is committed in consequence of the abetment, and no express provision is made by this Code for the punishment of such abetment, be punished with the punishment provided for the offence. Explanation: An act or offence is said to be committed in consequence of abetment, when it is committed in consequence of the instigation, or in pursuance of the conspiracy, or with the aid which constitutes the abetment.",
            "punishment": "Same punishment as the principal offence abetted",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Same court as principal offence",
            "corresponding_section": {
                "BNS": "49",
                "note": "BNS Section 49 covers punishment of abetment"
            },
            "source": "manual"
        },
        {
            "act": "IPC",
            "section_number": "120A",
            "offense": "Definition of Criminal Conspiracy",
            "description": "When two or more persons agree to do, or cause to be done, an illegal act, or an act which is not illegal by illegal means, such an agreement is designated a criminal conspiracy. Provided that no agreement except an agreement to commit an offence shall amount to a criminal conspiracy unless some act besides the agreement is done by one or more parties to such agreement in pursuance thereof.",
            "punishment": "Definition only — punishment under IPC 120B",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Court of Session",
            "corresponding_section": {
                "BNS": None,
                "note": "No direct BNS equivalent. Do not cite as a charge — cite IPC 120B for punishment."
            },
            "source": "manual",
            "is_definition_only": True
        },
        {
            "act": "IPC",
            "section_number": "120B",
            "offense": "Punishment of Criminal Conspiracy",
            "description": "Whoever is a party to a criminal conspiracy to commit an offence punishable with death, imprisonment for life or rigorous imprisonment for a term of two years or upwards, shall, where no express provision is made in this Code for the punishment of such a conspiracy, be punished in the same manner as if he had abetted such offence. Whoever is a party to a criminal conspiracy other than a criminal conspiracy to commit an offence punishable as aforesaid shall be punished with imprisonment of either description for a term not exceeding six months, or with fine or with both.",
            "punishment": "Same as abetment of principal offence / 6 months or fine for lesser conspiracies",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Court of Session",
            "corresponding_section": {
                "BNS": None,
                "note": "No direct BNS equivalent. BNS handles conspiracy under general provisions. Cite IPC 120B alongside BNS primary sections."
            },
            "source": "manual"
        },
        {
            "act": "IPC",
            "section_number": "141",
            "offense": "Unlawful Assembly — definition",
            "description": "An assembly of five or more persons is designated an unlawful assembly if the common object of the persons composing that assembly is to overawe by criminal force or show of criminal force, Central or any State Government or Parliament or the Legislature of any State, or any public servant in the exercise of the lawful power of such public servant; or to resist the execution of any law or of any legal process; or to commit any mischief or criminal trespass, or other offence; or by means of criminal force to any person, to take or obtain possession of any property, or to deprive any person of the enjoyment of a right of way or of the use of water or other incorporeal right of which he is in possession or enjoyment, or to enforce any right or supposed right; or by means of criminal force or show of criminal force to compel any person to do what he is not legally bound to do, or to omit to do what he is legally entitled to do.",
            "punishment": "Definition section — punishment under IPC 143, 144, 145, 149",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Any Magistrate",
            "corresponding_section": {
                "BNS": "187",
                "note": "BNS Section 187 defines unlawful assembly"
            },
            "source": "manual"
        },
        {
            "act": "IPC",
            "section_number": "142",
            "offense": "Being member of unlawful assembly",
            "description": "Whoever, being aware of facts which render any assembly an unlawful assembly, intentionally joins that assembly, or continues in it, is said to be a member of an unlawful assembly.",
            "punishment": "Punishable under IPC 143",
            "cognizable": "Cognizable",
            "bailable": "Bailable",
            "court": "Any Magistrate",
            "corresponding_section": {
                "BNS": "188",
                "note": "BNS Section 188"
            },
            "source": "manual"
        },
        {
            "act": "IPC",
            "section_number": "143",
            "offense": "Punishment for member of unlawful assembly",
            "description": "Whoever is a member of an unlawful assembly shall be punished with imprisonment of either description for a term which may extend to six months, or with fine, or with both.",
            "punishment": "6 months imprisonment or fine or both",
            "cognizable": "Cognizable",
            "bailable": "Bailable",
            "court": "Any Magistrate",
            "corresponding_section": {
                "BNS": "189",
                "note": "BNS Section 189"
            },
            "source": "manual"
        },
        {
            "act": "IPC",
            "section_number": "144",
            "offense": "Joining unlawful assembly armed with deadly weapon",
            "description": "Whoever, being armed with any deadly weapon, or with anything which, used as a weapon of offence, is likely to cause death, is a member of an unlawful assembly, shall be punished with imprisonment of either description for a term which may extend to two years, or with fine, or with both.",
            "punishment": "2 years imprisonment or fine or both",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Magistrate of the First Class",
            "corresponding_section": {
                "BNS": "189",
                "note": "BNS Section 189 covers armed unlawful assembly"
            },
            "source": "manual"
        }
    ]
    dataset.extend(MISSING_IPC_SECTIONS)
    print(f"Added {len(MISSING_IPC_SECTIONS)} manual IPC sections")

    IT_ACT_SECTIONS = [
        {
            "act": "IT Act",
            "section_number": "43",
            "offense": "Penalty for damage to computer or computer system",
            "description": "If any person without permission of the owner or any other person who is in charge of a computer, computer system or computer network accesses or secures access to such computer, downloads, copies or extracts any data, introduces or causes to be introduced any computer virus or contaminant, damages or causes to be damaged any computer or data, disrupts or causes disruption of any computer or denies or causes the denial of access to any authorised person.",
            "punishment": "Compensation up to Rs. 1 crore to affected person",
            "cognizable": "Non-Cognizable",
            "bailable": "Bailable",
            "court": "Adjudicating Officer / Civil Court",
            "corresponding_section": {"BNS": None},
            "source": "manual"
        },
        {
            "act": "IT Act",
            "section_number": "66",
            "offense": "Computer related offences",
            "description": "If any person, dishonestly or fraudulently, does any act referred to in section 43, he shall be punishable with imprisonment for a term which may extend to three years or with fine which may extend to five lakh rupees or with both.",
            "punishment": "3 years imprisonment or fine up to Rs. 5 lakh",
            "cognizable": "Cognizable",
            "bailable": "Bailable",
            "court": "Any Magistrate",
            "corresponding_section": {"BNS": None},
            "source": "manual"
        },
        {
            "act": "IT Act",
            "section_number": "66C",
            "offense": "Identity theft",
            "description": "Whoever, fraudulently or dishonestly makes use of the electronic signature, password or any other unique identification feature of any other person, shall be punished with imprisonment of either description for a term which may extend to three years and shall also be liable to fine which may extend to rupees one lakh. Includes fraudulent use of OTP, banking password, UPI PIN, Aadhar OTP, internet banking credentials.",
            "punishment": "3 years imprisonment and fine up to Rs. 1 lakh",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Court of Session",
            "corresponding_section": {"BNS": None},
            "source": "manual"
        },
        {
            "act": "IT Act",
            "section_number": "66D",
            "offense": "Cheating by personation using computer resource",
            "description": "Whoever, by means of any communication device or computer resource cheats by personation, shall be punished with imprisonment of either description for a term which may extend to three years and shall also be liable to fine which may extend to one lakh rupees. Includes impersonating bank officials, RBI officers, police officers, government servants via phone, WhatsApp, email, or fake apps to commit fraud.",
            "punishment": "3 years imprisonment and fine up to Rs. 1 lakh",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Court of Session",
            "corresponding_section": {"BNS": None},
            "source": "manual"
        },
        {
            "act": "IT Act",
            "section_number": "66F",
            "offense": "Cyber terrorism",
            "description": "Whoever with intent to threaten the unity, integrity, security or sovereignty of India or to strike terror in the people or any section of people by denying or cause the denial of access to any person authorised to access computer resource, or attempts to penetrate or access a computer resource without authorisation or exceeding authorised access.",
            "punishment": "Imprisonment for life",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Court of Session",
            "corresponding_section": {"BNS": None},
            "source": "manual"
        },
        {
            "act": "IT Act",
            "section_number": "67",
            "offense": "Publishing obscene material in electronic form",
            "description": "Whoever publishes or transmits or causes to be published or transmitted in the electronic form any material which is lascivious or appeals to the prurient interest or if its effect is such as to tend to deprave and corrupt persons who are likely to read, see or hear the matter contained or embodied in it.",
            "punishment": "First conviction: 3 years and fine up to Rs. 5 lakh. Second: 5 years and fine up to Rs. 10 lakh",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Court of Session",
            "corresponding_section": {"BNS": None},
            "source": "manual"
        },
        {
            "act": "IT Act",
            "section_number": "67A",
            "offense": "Publishing sexually explicit material electronically",
            "description": "Whoever publishes or transmits or causes to be published or transmitted in the electronic form any material which contains sexually explicit act or conduct.",
            "punishment": "First conviction: 5 years and fine up to Rs. 10 lakh. Second: 7 years and fine",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Court of Session",
            "corresponding_section": {"BNS": None},
            "source": "manual"
        },
        {
            "act": "IT Act",
            "section_number": "67B",
            "offense": "Publishing child sexually abusive material online",
            "description": "Whoever publishes or transmits material depicting children in sexually explicit act or conduct. Includes creating, collecting, seeking, browsing, downloading or exchanging material in any electronic form depicting children in obscene or sexually explicit manner.",
            "punishment": "First conviction: 5 years and fine up to Rs. 10 lakh. Second: 7 years and fine",
            "cognizable": "Cognizable",
            "bailable": "Non-Bailable",
            "court": "Court of Session",
            "corresponding_section": {"BNS": None},
            "source": "manual"
        }
    ]
    dataset.extend(IT_ACT_SECTIONS)
    print(f"Added {len(IT_ACT_SECTIONS)} manual IT Act sections")
            
    # 2. Process BNS CSV
    # Need to reverse mapping: BNS -> primary IPC
    BNS_TO_IPC = {}
    for ipc, bns in IPC_TO_BNS.items():
        if bns is not None:
            if bns not in BNS_TO_IPC: # Only take first/primary one
                BNS_TO_IPC[bns] = ipc
                
    with open(raw_bns_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sec_num = row.get("Section", "").strip()
            if not sec_num:
                continue
                
            desc = row.get("Description", "").replace("\\r\\n", "\n").replace("\r\n", "\n")
            
            item = {
                "act": "BNS",
                "section_number": sec_num,
                "section_name": row.get("Section _name", "").strip(),
                "chapter": row.get("Chapter", "").strip(),
                "chapter_name": row.get("Chapter_name", "").strip(),
                "description": desc.strip(),
                "cognizable": None,
                "bailable": None,
                "corresponding_section": {"IPC": BNS_TO_IPC.get(sec_num, None)},
                "source": "bns_sections.csv"
            }
            dataset.append(item)

    # Output to JSON
    with open(output_json, "w", encoding="utf-8") as out:
        json.dump(dataset, out, indent=2, ensure_ascii=False)
        
    ipc_count = sum(1 for x in dataset if x["act"] == "IPC")
    bns_count = sum(1 for x in dataset if x["act"] == "BNS")
    ipc_mapped = sum(1 for x in dataset if x["act"] == "IPC" and x.get("corresponding_section", {}).get("BNS"))
    bns_mapped = sum(1 for x in dataset if x["act"] == "BNS" and x.get("corresponding_section", {}).get("IPC"))
    ipc_unmapped = [x["section_number"] for x in dataset if x["act"] == "IPC" and not x.get("corresponding_section", {}).get("BNS")]
    
    csv_ipc = ipc_count - len(MISSING_IPC_SECTIONS)
    print(f"IPC sections written: {ipc_count} ({csv_ipc} from CSV + {len(MISSING_IPC_SECTIONS)} manual)")
    print(f"BNS sections written: {bns_count}")
    print(f"Total: {len(dataset)}")
    print(f"IPC sections with BNS mapping: {ipc_mapped}")
    print(f"BNS sections with IPC mapping: {bns_mapped}")
    print(f"IPC sections with null mapping: {len(ipc_unmapped)} ({ipc_unmapped[:10]})")

if __name__ == "__main__":
    main()
