import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

class IntakeAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1
        )
        self.prompt = PromptTemplate.from_template(
            "Extract structured facts (Who, What, When, Where, Why/How) from the following crime complaint and structured fields.\n\n"
            "Complainant Name: {complainant_name}\n"
            "Complainant ID Proof: {id_proof}\n"
            "Complainant Home Address: {complainant_address}\n"
            "Incident Date & Time: {incident_date} at {incident_time}\n"
            "Incident Location: {incident_location}\n"
            "Witnesses: {witnesses}\n"
            "Complaint Narrative: {complaint}\n\n"
            "Return the facts clearly formatted as a markdown list."
        )
        
    def run(self, data: dict) -> str:
        """Extracts structured facts from the raw complaint text."""
        witnesses_str = ", ".join([f"{w['name']} ({w['contact']})" for w in data.get('witnesses', [])]) if data.get('witnesses') else "None provided"
        
        id_proof_str = f"{data.get('id_proof_type', '')} - {data.get('id_proof_number', '')}".strip(" -")
        if not id_proof_str:
            id_proof_str = "None provided"
            
        chain = self.prompt | self.llm
        result = chain.invoke({
            "complainant_name": data.get("complainant_name", "Unknown"),
            "id_proof": id_proof_str,
            "complainant_address": data.get("address", "Unknown"),
            "incident_date": data.get("incident_date", "Unknown"),
            "incident_time": data.get("incident_time", "Unknown"),
            "incident_location": data.get("incident_location", "Unknown"),
            "witnesses": witnesses_str,
            "complaint": data.get("complaint_text", "")
        })
        return result.content
