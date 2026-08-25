import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

PRIMARY_MODEL = os.getenv("GROQ_MODEL_PRIMARY", "openai/gpt-oss-120b")
VERIFIER_MODEL = os.getenv("GROQ_MODEL_VERIFIER", "openai/gpt-oss-20b")

class DraftingAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model=PRIMARY_MODEL,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.2,
            timeout=120
        )
        self.prompt = PromptTemplate.from_template(
            "You are a highly experienced Indian Police Officer drafting an official First Information Report (FIR).\n"
            "Your tone must be strictly professional, objective, and legally precise. Do not use informal language.\n\n"
            "COMPLAINANT DETAILS:\n"
            "Name: {complainant_name}\n"
            "ID Proof: {id_proof}\n"
            "Home Address: {complainant_address}, {district}\n"
            "Phone: {phone_number}\n\n"
            "INCIDENT DETAILS:\n"
            "Date: {incident_date}\n"
            "Time: {incident_time}\n"
            "Location: {incident_location}\n\n"
            "ACCUSED: {accused_info}\n\n"
            "WITNESSES: {witnesses_info}\n\n"
            "EXTRACTED FACTS:\n{facts}\n\n"
            "VERIFIED LEGAL SECTIONS (You MUST include ALL of these in the FIR "
            "under 'Legal Provisions Invoked' — do not drop any, and do not add any unverified sections):\n"
            "{sections}\n\n"
            "OFFICER DETAILS:\n"
            "Name: {officer_name}\n"
            "Rank: {officer_rank}\n"
            "Station: {officer_station}\n\n"
            "You must return ONLY a JSON object strictly matching this schema:\n"
            "{{\n"
            "  \"narrative\": \"A formal, chronological prose paragraph describing the events clearly and objectively. Do not use dramatic language.\",\n"
            "  \"prayer\": \"Briefly state the legal action requested by the complainant.\",\n"
            "  \"witnesses\": \"Summary of witness details or 'None provided'.\"\n"
            "}}\n"
            "Return ONLY the JSON object. No other text."
        )

    def run(self, facts: str, sections: str, data: dict) -> str:
        """Synthesizes facts + legal mapping + full context into FIR draft."""

        id_proof_str = f"{data.get('complainant_id_type', '')} - {data.get('complainant_id_number', '')}".strip(" -")
        if not id_proof_str:
            id_proof_str = "None provided"

        # Build accused info
        accused_name = data.get('accused_name', 'Unknown')
        accused_desc = data.get('accused_description', '')
        accused_vehicle = data.get('accused_vehicle', '')
        accused_parts = [accused_name or 'Unknown']
        if accused_desc:
            accused_parts.append(accused_desc)
        if accused_vehicle:
            accused_parts.append(f"Vehicle: {accused_vehicle}")
        accused_info = ", ".join(accused_parts)

        # Build witnesses info
        witnesses = data.get('witnesses', [])
        if witnesses:
            witnesses_info = "; ".join([
                f"{w.get('name', 'Unknown')} (Phone: {w.get('phone', 'N/A')})"
                for w in witnesses
            ])
        else:
            witnesses_info = "None provided"

        # Fallback: if sections string is empty or empty array/object, note it
        if not sections or sections.strip() in ["", "[]", "{}", "null"]:
            sections = "No legal sections were matched. The drafting officer should determine applicable sections."
            print("[DraftingAgent] WARNING: Received empty sections from Legal Agent!")

        print(f"[DraftingAgent] Sections received (first 200 chars): {sections[:200]}")

        chain = self.prompt | self.llm
        result = chain.invoke({
            "complainant_name": data.get("complainant_name", "Unknown"),
            "id_proof": id_proof_str,
            "complainant_address": data.get("complainant_address", "Unknown"),
            "district": data.get("complainant_city", "Unknown"),
            "phone_number": data.get("complainant_phone", "Unknown"),
            "incident_date": data.get("incident_date", "Unknown"),
            "incident_time": data.get("incident_time", "Unknown"),
            "incident_location": data.get("incident_location", "Unknown"),
            "accused_info": accused_info,
            "witnesses_info": witnesses_info,
            "officer_name": data.get("officer_name", "Unknown"),
            "officer_rank": data.get("officer_rank", "Unknown"),
            "officer_station": data.get("officer_station", "Unknown"),
            "facts": facts,
            "sections": sections
        })
        
        raw_output = result.content.strip()
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]
        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]
        return raw_output.strip()
