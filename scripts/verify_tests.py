import sys
import os
import json

# Add parent directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.act_selector import select_relevant_acts
from app.agents.legal_agent import LegalAgent

test_cases = [
    {
        "name": "TEST 1 — Drugs + weapons",
        "complaint": "Gangsters are selling cocaine near our school. They have country-made pistols and sickles.",
        "facts": {"minor_involved": True, "weapon_used": "pistols and sickles", "accused_count": 3}
    },
    {
        "name": "TEST 2 — Cheque bounce",
        "complaint": "My partner gave me a cheque for 5 lakhs but the bank returned it saying insufficient funds.",
        "facts": {"accused_count": 1}
    },
    {
        "name": "TEST 3 — Caste atrocity",
        "complaint": "A group of men abused me repeatedly using my caste name and beat me in public.",
        "facts": {"accused_count": 3}
    },
    {
        "name": "TEST 4 — Hit and run",
        "complaint": "A speeding car hit my father on the road and the driver fled without stopping.",
        "facts": {"accused_count": 1, "accused_fled": "true", "victim_status": "injured"}
    },
    {
        "name": "TEST 5 — Bribery",
        "complaint": "A government officer demanded Rs 10,000 bribe to process my building permit application.",
        "facts": {"accused_count": 1}
    }
]

def run_tests():
    agent = LegalAgent()
    for t in test_cases:
        print(f"\n======================================")
        print(f"{t['name']}")
        print(f"======================================")
        
        facts = t['facts'].copy()
        facts["complaint_text"] = t["complaint"]
        
        # Test 1: Act Selector independently
        acts = select_relevant_acts(t['complaint'], facts)
        print(f"[ActSelector] Selected acts: {acts}")
        
        # Test 2: Full LegalAgent run
        res = agent.run(facts=json.dumps(facts), data=facts)
        try:
            sections = json.loads(res)
            print("Legal Provisions Invoked:")
            for s in sections:
                print(f" - {s.get('act')} {s.get('section_number')}: {s.get('offense')}")
        except Exception as e:
            print(f"Failed to parse agent output: {e}\nRaw output: {res}")

if __name__ == "__main__":
    run_tests()
