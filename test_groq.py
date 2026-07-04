import os
from dotenv import load_dotenv
load_dotenv()
import traceback
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

try:
    print(f"Model: {os.getenv('GROQ_MODEL')}")
    print(f"API Key: {os.getenv('GROQ_API_KEY')[:5]}...{os.getenv('GROQ_API_KEY')[-5:]}")
    
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama3-70b-8192"),
        groq_api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.1,
        request_timeout=120
    )
    result = llm.invoke("Hello, say this is a test.")
    print("Success:", result.content)
except Exception as e:
    print("Error invoking ChatGroq:")
    traceback.print_exc()
