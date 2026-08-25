import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

PRIMARY_MODEL = os.getenv("GROQ_MODEL_PRIMARY", "openai/gpt-oss-120b")
VERIFIER_MODEL = os.getenv("GROQ_MODEL_VERIFIER", "openai/gpt-oss-20b")

class IntakeAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model=PRIMARY_MODEL,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1,
            timeout=120
        )
        self.prompt = PromptTemplate.from_template(
            "Extract structured facts and explicit boolean flags from the following crime complaint.\n\n"
            "Complainant Name: {complainant_name}\n"
            "Complainant ID Proof: {id_proof}\n"
            "Complainant Home Address: {complainant_address}\n"
            "Incident Date & Time: {incident_date} at {incident_time}\n"
            "Incident Location: {incident_location}\n"
            "Witnesses: {witnesses}\n"
            "Complaint Narrative: {complaint}\n\n"
            "Return a strictly valid JSON object with EXACTLY these keys:\n"
            "{{\n"
            "  \"facts\": \"A clear, bulleted summary of Who, What, When, Where, Why/How.\",\n"
            "  \"animal_involved\": true/false,\n"
            "  \"human_hurt\": true/false,\n"
            "  \"force_used\": true/false,\n"
            "  \"property_taken\": true/false,\n"
            "  \"cyber_method\": true/false,\n"
            "  \"sexual_offence\": true/false,\n"
            "  \"premeditated\": true/false,\n"
            "  \"minor_involved\": true/false,\n"
            "  \"accused_count\": 1 (integer),\n"
            "  \"weapon_used\": \"name of weapon or 'none'\"\n"
            "}}\n"
            "Only return the JSON. No markdown backticks."
        )
        
    def run(self, data: dict) -> str:
        """Extracts structured facts and boolean flags from the raw complaint text."""
        witnesses_str = ", ".join([f"{w.get('name', '')} ({w.get('phone', '')})" for w in data.get('witnesses', [])]) if data.get('witnesses') else "None provided"
        
        id_proof_str = f"{data.get('complainant_id_type', '')} - {data.get('complainant_id_number', '')}".strip(" -")
        if not id_proof_str:
            id_proof_str = "None provided"
            
        chain = self.prompt | self.llm
        result = chain.invoke({
            "complainant_name": data.get("complainant_name", "Unknown"),
            "id_proof": id_proof_str,
            "complainant_address": data.get("complainant_address", "Unknown"),
            "incident_date": data.get("incident_date", "Unknown"),
            "incident_time": data.get("incident_time", "Unknown"),
            "incident_location": data.get("incident_location", "Unknown"),
            "witnesses": witnesses_str,
            "complaint": data.get("complaint_text", "")
        })
        
        import json
        content = result.content.strip()
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        try:
            parsed = json.loads(content)
            # Merge original complaint text so downstream has it
            parsed["complaint_text"] = data.get("complaint_text", "")
            return json.dumps(parsed)
        except Exception:
            # Fallback
            fallback = {
                "facts": content,
                "complaint_text": data.get("complaint_text", "")
            }
            return json.dumps(fallback)
