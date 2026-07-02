import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

class DraftingAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.2
        )
        self.prompt = PromptTemplate.from_template(
            "You are a professional police officer drafting a formal First Information Report (FIR).\n"
            "Using the facts, legal sections, and structured details provided below, draft a comprehensive, official, and legally sound FIR narrative.\n\n"
            "Complainant Details:\n"
            "Name: {complainant_name}\n"
            "ID Proof: {id_proof}\n"
            "Home Address: {complainant_address}, {district}\n"
            "Phone: {phone_number}\n\n"
            "Incident Details:\n"
            "Date: {incident_date}\n"
            "Time: {incident_time}\n"
            "Location: {incident_location}\n\n"
            "Officer Details:\n"
            "Name: {officer_name}\n"
            "Rank: {officer_rank}\n"
            "Station: {officer_station}\n\n"
            "Facts:\n{facts}\n\n"
            "Legal Sections:\n{sections}\n\n"
            "Draft the FIR narrative clearly, in a professional tone. Ensure you sign off the FIR using the exact provided Officer Name, Rank, and Station, and reference the Complainant details accurately. DO NOT use [Name] or [Rank] placeholders."
        )

    def run(self, facts: str, sections: str, data: dict) -> str:
        """Synthesizes facts + legal mapping + full context into FIR draft."""
        
        id_proof_str = f"{data.get('id_proof_type', '')} - {data.get('id_proof_number', '')}".strip(" -")
        if not id_proof_str:
            id_proof_str = "None provided"
            
        chain = self.prompt | self.llm
        result = chain.invoke({
            "complainant_name": data.get("complainant_name", "Unknown"),
            "id_proof": id_proof_str,
            "complainant_address": data.get("address", "Unknown"),
            "district": data.get("district", "Unknown"),
            "phone_number": data.get("phone_number", "Unknown"),
            "incident_date": data.get("incident_date", "Unknown"),
            "incident_time": data.get("incident_time", "Unknown"),
            "incident_location": data.get("incident_location", "Unknown"),
            "officer_name": data.get("officer_name", "Unknown"),
            "officer_rank": data.get("officer_rank", "Unknown"),
            "officer_station": data.get("officer_station", "Unknown"),
            "facts": facts,
            "sections": sections
        })
        return result.content
