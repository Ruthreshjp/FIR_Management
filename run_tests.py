import json
import time
from app.agents.orchestrator import Orchestrator

complaints = [
    {
        "id": 1,
        "name": "Theft",
        "text": "Yesterday evening at 6 PM, while I was waiting at the T Nagar bus stop, an unknown person snatched my mobile phone from my hand and ran away on foot. The phone is a Samsung Galaxy worth Rs. 25,000. No violence was used.",
        "location": "T Nagar, Chennai",
        "accused": "Unknown person",
        "accused_count": 1
    },
    {
        "id": 2,
        "name": "Robbery",
        "text": "At 9 PM near Guindy industrial estate, two persons on a motorcycle stopped me. One of them pointed a knife at me and demanded my wallet and watch. Out of fear I handed over my wallet containing Rs. 8,000 and my Titan watch worth Rs. 15,000. They rode away immediately after.",
        "location": "Guindy, Chennai",
        "accused": "2 unknown persons on motorcycle",
        "accused_count": 2
    },
    {
        "id": 3,
        "name": "Domestic violence",
        "text": "My husband Suresh has been beating me regularly for the past six months over dowry demands. Last night he hit me with a wooden rod on my back and arms causing severe injuries. He also threatened to kill me and my parents if I approach the police. I have medical reports from Apollo Hospital confirming the injuries.",
        "location": "Adyar, Chennai",
        "accused": "Husband — Suresh",
        "accused_count": 1
    },
    {
        "id": 4,
        "name": "Murder",
        "text": "My brother Selvam was attacked by our neighbour Karthik yesterday night at 11 PM outside our house. Karthik stabbed Selvam three times in the stomach with a kitchen knife during an argument over a parking dispute. Selvam was taken to Government Hospital but died at 2 AM. Karthik fled immediately after the stabbing.",
        "location": "Velachery, Chennai",
        "accused": "Karthik",
        "accused_count": 1
    },
    {
        "id": 5,
        "name": "Gang murder with conspiracy",
        "text": "My father Murugan was killed by Ravi and his gang of four persons last evening. Ravi had a longstanding property dispute with my father. They came prepared with sharp weapons — sickles and iron rods. They surrounded my father near the Ambattur market and attacked him together. My father died on the spot from multiple head injuries. All five fled in a white van immediately after. Two shopkeepers witnessed the attack.",
        "location": "Ambattur, Chennai",
        "accused": "Ravi + 4 others",
        "accused_count": 5
    },
    {
        "id": 6,
        "name": "Cybercrime fraud",
        "text": "I received a call from someone claiming to be an SBI bank manager. He said my account will be blocked due to KYC expiry. He sent a fake SBI letterhead document on WhatsApp and asked me to install an app called AnyDesk on my phone for remote verification. After I installed it he accessed my phone remotely and transferred Rs. 2,80,000 from my account in multiple transactions to unknown UPI IDs.",
        "location": "Online (Anna Nagar, Chennai)",
        "accused": "Unknown caller posing as bank officer",
        "accused_count": 1
    },
    {
        "id": 7,
        "name": "POCSO case",
        "text": "I am filing this complaint on behalf of my 13-year-old daughter Meena who studies in 8th standard. Her class teacher Pandian has been touching her inappropriately during private tuition classes for the past two months. He touched her private parts and threatened her not to tell anyone. My daughter finally told me yesterday. I took her to the doctor who confirmed the physical examination findings.",
        "location": "Tambaram, Chennai",
        "accused": "School teacher Pandian",
        "accused_count": 1
    },
    {
        "id": 8,
        "name": "Property dispute + trespass",
        "text": "My neighbour Balan has been illegally occupying a portion of my land for the past three months despite repeated requests to vacate. Yesterday he broke the compound wall between our properties and extended his construction into my land. When I objected he abused me with filthy language in front of other neighbours and threatened to break my legs if I complained to authorities.",
        "location": "Sholinganallur, Chennai",
        "accused": "Neighbour Balan",
        "accused_count": 1
    }
]

base_data = {
    "complainant_name": "TEST USER",
    "complainant_phone": "9000000000",
    "complainant_address": "123 Test Street, Chennai",
    "complainant_id_type": "Aadhar",
    "complainant_id_number": "123456789012",
    "complainant_gender": "Male",
    "incident_date": "2026-07-04",
    "incident_time": "10:00",
    "officer_name": "Inspector Raj",
    "officer_rank": "Sub-Inspector",
    "officer_station": "Central Police Station Chennai"
}

def run_all():
    orc = Orchestrator()
    results = {}
    print("Starting all 8 complaints through the pipeline...\n")
    
    for c in complaints:
        print(f"=== COMPLAINT {c['id']}: {c['name']} ===")
        data = base_data.copy()
        data["complaint_text"] = c["text"]
        data["incident_location"] = c["location"]
        data["accused_name"] = c["accused"]
        
        legal_sections = None
        for step in orc.generate_fir(data):
            if step["agent"] == "Legal Agent" and step["type"] == "thought":
                legal_sections = step["message"]
                print("Legal Sections output received!")
                break # We can break early since we only need the Legal Agent output!
                
        results[c["id"]] = {
            "name": c["name"],
            "sections": legal_sections
        }
        
        try:
            parsed = json.loads(legal_sections)
            for s in parsed:
                print(f"  [{s.get('act')}] {s.get('section_number')} - {s.get('offense')}")
        except:
            print(f"Failed to parse JSON: {legal_sections}")
            
        print("\n")
        time.sleep(1.5) # Prevent rate limiting
        
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("All done! Wrote full output to test_results.json.")

if __name__ == "__main__":
    run_all()
