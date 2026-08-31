import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.config.section_mapping import ALLOWED_SECTIONS

PRIMARY_MODEL = os.getenv("GROQ_MODEL_PRIMARY", "openai/gpt-oss-120b")

SYSTEM_PROMPT = """You are an expert Indian Police intake officer.
Your task is to classify a given complaint into one or more primary Crime Types.

Allowed Crime Types:
{allowed_types}

RULES:
1. Analyze the core facts of the incident carefully.
2. If a victim is dead due to assault/attack, MUST include "Murder/Culpable Homicide".
3. If property was taken using force or threat of immediate force, MUST include "Robbery". If no property was actually taken, DO NOT include Robbery (use Hurt or Criminal Intimidation instead).
4. If property was taken without force/threat (e.g. pickpocketing, stealing from a house), use "Theft".
5. For online scams, OTP frauds, or digital money theft, use "Cyber Fraud / Online Cheating".
6. You can return multiple categories if the crime spans multiple types (e.g. ["Robbery", "Hurt / Grievous Hurt", "Criminal Intimidation"]).
7. If the crime does not fit any category, return ["Others"].

Return your answer strictly as a JSON array of strings containing the selected Crime Types. Do not include any other text.
"""

USER_PROMPT = """Complaint Text:
{complaint}

Extracted Facts:
{facts}

Classify the crime:"""

class CrimeClassifierAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model=PRIMARY_MODEL,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.0,
            timeout=30
        )
        self.allowed_types = "\n".join([f"- {k}" for k in ALLOWED_SECTIONS.keys()])
        self.prompt = PromptTemplate.from_template(SYSTEM_PROMPT + "\n\n" + USER_PROMPT)
        
    def run(self, complaint: str, facts: dict) -> list:
        chain = self.prompt | self.llm
        try:
            result = chain.invoke({
                "allowed_types": self.allowed_types,
                "complaint": complaint,
                "facts": json.dumps(facts, indent=2)
            })
            
            raw_output = result.content.strip()
            import re
            match = re.search(r'\[.*\]', raw_output, re.DOTALL)
            if match:
                raw_output = match.group(0)
            else:
                if raw_output.startswith("```json"):
                    raw_output = raw_output[7:]
                if raw_output.endswith("```"):
                    raw_output = raw_output[:-3]
                raw_output = raw_output.strip()
            
            try:
                categories = json.loads(raw_output)
            except json.JSONDecodeError:
                print(f"[CrimeClassifier] JSON Decode failed on text: {raw_output}")
                categories = ["Others"]

            if not isinstance(categories, list):
                categories = ["Others"]
                
            # Filter to only allowed categories
            valid_categories = [c for c in categories if c in ALLOWED_SECTIONS]
            if not valid_categories:
                return ["Others"]
            return valid_categories
            
        except Exception as e:
            print(f"[CrimeClassifier] Error: {e}")
            return ["Others"]
