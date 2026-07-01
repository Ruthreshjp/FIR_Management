import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from app.tools.rag_tool import search_legal_sections

class LegalAgent:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama3-8b-8192",
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1
        )
        self.prompt = PromptTemplate.from_template(
            "Based on the following extracted facts, determine the most applicable Indian Penal Code (IPC) and Bharatiya Nyaya Sanhita (BNS 2023) sections.\n"
            "Use the provided database matches to guide your decision.\n\n"
            "Extracted Facts:\n{facts}\n\n"
            "Relevant Law Database Matches:\n{law_matches}\n\n"
            "Provide a clear, bulleted list of the applied sections and a brief justification for each."
        )

    def run(self, extracted_facts: str) -> str:
        """Maps facts to IPC + BNS 2023 sections."""
        # Simple extraction of keywords from facts to query chroma
        # (In a real app, you might use an LLM to generate the search query)
        query = " ".join(extracted_facts.split()[:50]) # Use first 50 words as a basic query
        law_matches = search_legal_sections(query, top_k=3)
        law_matches_str = json.dumps(law_matches, indent=2) if law_matches else "No direct matches found."
        
        chain = self.prompt | self.llm
        result = chain.invoke({
            "facts": extracted_facts,
            "law_matches": law_matches_str
        })
        return result.content
