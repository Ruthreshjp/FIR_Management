import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

class IntakeAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama3-8b-8192",
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1
        )
        self.prompt = PromptTemplate.from_template(
            "Extract structured facts (Who, What, When, Where, Why/How) from the following crime complaint.\n\n"
            "Complaint: {complaint}\n\n"
            "Return the facts clearly formatted as a markdown list."
        )
        
    def run(self, complaint_text: str) -> str:
        """Extracts structured facts from the raw complaint text."""
        chain = self.prompt | self.llm
        result = chain.invoke({"complaint": complaint_text})
        return result.content
