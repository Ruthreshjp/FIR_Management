import os
import json
import logging
from groq import Groq

logger = logging.getLogger(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
PRIMARY_MODEL = os.getenv("GROQ_MODEL_PRIMARY",
                          "openai/gpt-oss-120b")

ALL_INDIAN_ACTS = {
    "IPC": "Indian Penal Code 1860 — murder, theft, robbery, "
           "fraud, assault, intimidation, trespass, cheating, "
           "forgery, kidnapping, rape, hurt, grievous hurt, "
           "criminal conspiracy, unlawful assembly, abetment.",

    "BNS": "Bharatiya Nyaya Sanhita 2023 — replaced IPC from "
           "July 2024. Same offences under new section numbers. "
           "Always include alongside IPC.",

    "NDPS_ACT": "Narcotic Drugs and Psychotropic Substances Act "
                "1985 — cocaine, heroin, ganja, marijuana, "
                "brown sugar, ecstasy, MDMA, opium, drug "
                "peddling, drug trafficking, drug possession, "
                "drug sale, psychotropic substances.",

    "IT_ACT": "Information Technology Act 2000 — cybercrime, "
              "online fraud, OTP theft, phishing, AnyDesk remote "
              "access fraud, hacking, fake websites, data theft, "
              "identity theft, social media harassment, "
              "morphed images, revenge porn.",

    "POCSO": "Protection of Children from Sexual Offences Act "
             "2012 — any sexual offence against a person under "
             "18 years: sexual assault, sexual harassment, "
             "penetrative assault, pornography involving minor.",

    "ARMS_ACT": "Arms Act 1959 — illegal firearms, unlicensed "
                "weapons, country-made guns, pistols, rifles, "
                "swords, knives carried as weapons, ammunition "
                "without licence, possessing prohibited arms.",

    "MOTOR_VEHICLES_ACT": "Motor Vehicles Act 1988 — rash "
                           "driving, drunk driving, hit and run, "
                           "driving without licence, road accident "
                           "causing death or injury, vehicle "
                           "documents offences.",

    "DOWRY_ACT": "Dowry Prohibition Act 1961 — giving, taking "
                 "or demanding dowry. Use alongside IPC 498A "
                 "and IPC 304B for dowry harassment cases.",

    "SC_ST_ACT": "Scheduled Castes and Scheduled Tribes "
                 "Prevention of Atrocities Act 1989 — "
                 "caste-based abuse, discrimination, violence, "
                 "humiliation using caste name, atrocity against "
                 "SC/ST community members.",

    "DOMESTIC_VIOLENCE_ACT": "Protection of Women from Domestic "
                              "Violence Act 2005 — physical, "
                              "sexual, verbal, emotional or "
                              "economic abuse by husband or "
                              "in-laws. Civil relief.",

    "PREVENTION_OF_CORRUPTION": "Prevention of Corruption Act "
                                 "1988 — bribery, demanding "
                                 "illegal gratification, "
                                 "corruption by public servants, "
                                 "misuse of official position.",

    "NI_ACT": "Negotiable Instruments Act 1881 Section 138 — "
              "cheque bounce, dishonoured cheque, insufficient "
              "funds, payment failure by cheque.",

    "JUVENILE_JUSTICE_ACT": "Juvenile Justice Act 2015 — "
                             "cruelty to child, child labour, "
                             "child trafficking, abandonment, "
                             "neglect of minor.",

    "EXPLOSIVES_ACT": "Explosives Act 1884 / Explosive Substances"
                      " Act 1908 — illegal bombs, IEDs, explosive "
                      "materials, blast, explosion.",

    "HUMAN_TRAFFICKING": "IPC 370/BNS 143 + related laws — "
                         "human trafficking, forced labour, "
                         "sexual exploitation, bonded labour, "
                         "selling or buying persons.",

    "PMLA": "Prevention of Money Laundering Act 2002 — "
            "money laundering, hawala, proceeds of crime, "
            "financial crimes involving large sums.",
}


def select_relevant_acts(complaint_text: str,
                         facts: dict) -> list:
    acts_list = "\n".join([
        f"- {key}: {desc}"
        for key, desc in ALL_INDIAN_ACTS.items()
    ])

    prompt = f"""You are a senior Indian police legal officer.
Read this complaint and identify ALL Indian criminal acts 
that are potentially relevant for filing an FIR.

COMPLAINT TEXT:
{complaint_text}

KEY FACTS:
- Minor victim (under 18): {facts.get('minor_involved', False)}
- Weapon mentioned: {facts.get('weapon_used', 'None')}
- Number of accused: {facts.get('accused_count', 1)}
- Online/cyber method: {facts.get('cyber_method', False)}
- Marital/domestic context: {facts.get('marital_relationship', False)}
- Death occurred: {facts.get('victim_status') == 'dead'}

AVAILABLE ACTS:
{acts_list}

INSTRUCTIONS:
- Select ALL acts that could reasonably apply.
- Be inclusive — if there is any chance an act applies, include it.
- Always include IPC and BNS as baseline.
- If drugs mentioned in ANY form → include NDPS_ACT.
- If weapons mentioned → include ARMS_ACT.
- If victim is a minor + sexual element → include POCSO.
- If online/digital method → include IT_ACT.
- If caste mentioned → include SC_ST_ACT.
- If cheque/payment failure → include NI_ACT.
- If public servant/bribe → include PREVENTION_OF_CORRUPTION.

Return ONLY a JSON array of act key strings.
Example: ["IPC", "BNS", "NDPS_ACT", "ARMS_ACT"]
No explanation. No other text."""

    try:
        response = client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal expert. "
                               "Return only a valid JSON array "
                               "of act key strings. "
                               "No markdown, no explanation."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.1
        )

        text = response.choices[0].message.content.strip()
        text = text.replace("```json","").replace("```","").strip()
        selected = json.loads(text)

        # Force baseline
        for required in ["IPC", "BNS"]:
            if required not in selected:
                selected.append(required)

        logger.info(f"[ActSelector] Selected: {selected}")
        print(f"[ActSelector] Selected acts: {selected}")
        return selected

    except Exception as e:
        logger.error(f"[ActSelector] Failed: {e}")
        print(f"[ActSelector] Error — defaulting IPC+BNS: {e}")
        return ["IPC", "BNS"]
