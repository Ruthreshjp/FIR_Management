# Mapping of Crime Types to their allowed legal sections
# This acts as a strict whitelist filter before sections are passed to the Legal Agent.

ALLOWED_SECTIONS = {
    "Murder": {
        "BNS": ["103", "3(5)", "190", "109", "61"],
        "IPC": ["302", "34", "149", "307", "120B"]
    },
    "Culpable Homicide": {
        "BNS": ["105", "104", "3(5)", "61"],
        "IPC": ["304", "304A", "34", "120B"]
    },
    "Robbery": {
        "BNS": ["309", "351", "3(5)", "311", "312", "115"],
        "IPC": ["392", "506", "34", "394", "397", "323"]
    },
    "Theft": {
        "BNS": ["303", "304", "305", "3(5)", "61"],
        "IPC": ["379", "380", "381", "34", "120B"]
    },
    "Hurt / Grievous Hurt": {
        "BNS": ["115", "117", "351", "118", "120", "126", "3(5)"],
        "IPC": ["323", "325", "506", "324", "326", "34"]
    },
    "Sexual Harassment / Outraging Modesty": {
        "BNS": ["74", "75", "79", "351", "64", "65", "66", "70", "76", "77", "3(5)"],
        "IPC": ["354A", "354", "509", "506", "376", "376D", "354B", "354C", "354D", "34"]
    },
    "Cyber Fraud / Online Cheating": {
        "BNS": ["318", "3(5)", "61"],
        "IPC": ["420", "34", "120B"],
        "IT Act": ["66C", "66D"]
    },
    "Extortion": {
        "BNS": ["308", "3(5)"],
        "IPC": ["384", "506", "34"]
    },
    "Criminal Intimidation": {
        "BNS": ["351", "352", "3(5)"],
        "IPC": ["506", "504", "34"]
    },
    "Animal Cruelty": {
        "BNS": ["325"],
        "IPC": ["428", "429"]
    },
    "Rash Driving / Hit and Run": {
        "BNS": ["281", "125", "106", "106(1)", "106(2)"],
        "IPC": ["279", "337", "338", "304A"],
        "MV Act": ["184", "185", "187", "134"]
    },
    "Cheating": {
        "BNS": ["316", "318", "336", "338", "3(5)", "61"],
        "IPC": ["406", "420", "467", "468", "471", "34", "120B"]
    },
    "Domestic Violence / Cruelty": {
        "BNS": ["85", "86", "3(5)"],
        "IPC": ["498A", "304B", "34"]
    },
    "Wrongful Confinement": {
        "BNS": ["127", "126", "3(5)"],
        "IPC": ["342", "340", "34"]
    },
    "IT Act Offences / Cyber Threat": {
        "BNS": ["351", "74", "318", "3(5)", "61"],
        "IPC": ["506", "503", "354C", "420", "34", "120B"],
        "IT Act": ["66C", "66D", "66E", "67", "67A"]
    },
    "Others": {
        # 'Others' acts as a fallback to allow any section if the classifier fails to find a specific category.
    }
}
