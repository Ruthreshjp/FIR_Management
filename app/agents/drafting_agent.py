import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

class DraftingAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama3-8b-8192",
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.2
        )
        self.prompt = PromptTemplate.from_template(
            "You are a professional police officer drafting a formal First Information Report (FIR).\n"
            "Using the facts and the legal sections provided below, draft a comprehensive, official, and legally sound FIR narrative.\n\n"
            "Facts:\n{facts}\n\n"
            "Legal Sections:\n{sections}\n\n"
            "Draft the FIR narrative clearly, in a professional tone, without adding any introductory or concluding pleasantries. Just the formal report text."
        )

    def run(self, facts: str, sections: str) -> str:
        """Synthesizes facts + legal mapping into FIR draft."""
        chain = self.prompt | self.llm
        result = chain.invoke({
            "facts": facts,
            "sections": sections
        })
        return result.content
