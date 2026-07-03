import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

class DraftingAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.2,
            request_timeout=120
        )
        self.prompt = PromptTemplate.from_template(
            "You are drafting an official First Information Report (FIR) for the Indian Police.\n\n"
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
            "LEGAL SECTIONS MATCHED (you MUST include ALL of these in the FIR "
            "under 'Legal Provisions Invoked' — do not drop any):\n"
            "{sections}\n\n"
            "OFFICER DETAILS:\n"
            "Name: {officer_name}\n"
            "Rank: {officer_rank}\n"
            "Station: {officer_station}\n\n"
            "Draft a complete FIR with these numbered sections in clean Markdown:\n"
            "### 1. Complainant Details\n"
            "### 2. Incident Details\n"
            "Use a Markdown table with Who/What/When/Where/How rows.\n"
            "### 3. Narrative\n"
            "A formal prose paragraph describing the events.\n"
            "### 4. Legal Provisions Invoked\n"
            "List ALL the legal sections from above. For each one, include:\n"
            "- Act name (IPC or BNS 2023)\n"
            "- Section number\n"
            "- Offense name\n"
            "- One-line justification\n"
            "The Legal Provisions section is MANDATORY — never omit it.\n"
            "### 5. Witness Details\n"
            "### 6. Action Requested\n"
            "### 7. Prepared By\n"
            "Use the exact Officer Name, Rank, and Station provided above.\n"
            "DO NOT use [Name] or [Rank] or any placeholders.\n\n"
            "Format the output in clean Markdown. Use ### for section headers, "
            "**bold** for labels, and | tables | for structured data."
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

        # Fallback: if sections string is empty, note it
        if not sections or sections.strip() == "":
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
        return result.content
