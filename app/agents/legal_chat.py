import os
import json
import re
from collections import Counter
from groq import Groq
from app.retrieval.chroma_store import search_legal_sections
from app.database.connection import Database

PRIMARY_MODEL = os.getenv("GROQ_MODEL_PRIMARY", "openai/gpt-oss-120b")

# Off-topic keywords for fast pre-filtering
OFF_TOPIC_KEYWORDS = [
    "recipe", "cook", "pizza", "burger", "weather", "temperature", "forecast",
    "movie", "actor", "actress", "song", "sports", "cricket", "football", "match",
    "game", "joke", "funny", "story", "code in python", "write a code", "debug",
    "math problem", "solve equation", "who is the president", "capital of",
    "tallest mountain", "distance to moon", "tell me about yourself outside"
]

GREETING_WORDS = {
    "hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening",
    "who are you", "what can you do", "help", "start", "welcome"
}

def clean_corresponding_section(corr) -> str:
    """Formats corresponding section cleanly instead of printing raw dict string."""
    if not corr or corr == "None" or corr == "null":
        return "None"
    if isinstance(corr, dict):
        parts = [f"{k} {v}" for k, v in corr.items() if v and v != "None"]
        return ", ".join(parts) if parts else "None"
    corr_str = str(corr).strip()
    if corr_str in ("", "None", "null", "{}"):
        return "None"
    return corr_str

def rank_citations_for_query(query: str, items: list) -> list:
    """Ranks citations so items directly matching the query keywords appear first. Returns [] if query has no legal keywords."""
    if not items:
        return []
    
    stop_words = {
        "what", "is", "the", "for", "under", "in", "and", "or", "to", "a", "of", "an", "are", 
        "most", "invoked", "sections", "how", "do", "you", "can", "i", "help", "me", "tell", 
        "about", "this", "that", "there", "here", "who", "where", "why", "when", "please",
        "give", "show", "get", "hi", "hello", "hey", "thanks", "thank"
    }
    words = [w.lower() for w in re.findall(r'\b\w+\b', query) if w.lower() not in stop_words and len(w) > 1]

    if not words:
        return []

    scored_items = []
    for item in items:
        title = str(item.get("section_name", item.get("offense", item.get("title", "")))).lower()
        sec = str(item.get("section_number", item.get("Section", ""))).lower()
        desc = str(item.get("description", "")).lower()
        act = str(item.get("act", "")).lower()
        
        s = 0
        for w in words:
            if w == sec:
                s += 20
            elif w in sec:
                s += 10
            if w in title:
                s += 8
            if w in desc:
                s += 2
            if w in act:
                s += 1

        if s > 0:
            scored_items.append((s, item))

    # Sort descending by score
    scored_items.sort(key=lambda x: x[0], reverse=True)
    return [item for sc, item in scored_items]

def get_project_database_analytics() -> str:
    """Retrieves real-time analytics and invoked section statistics from AutoFIR MongoDB database."""
    try:
        db = Database()
        firs = db.get_all_firs()
        if not firs:
            return "AUTOFIR PROJECT DATABASE RECORDS:\n- Total Registered FIRs: 0 (Database is currently empty)."

        total_firs = len(firs)
        status_counts = Counter()
        section_counts = Counter()
        section_titles = {}

        for f in firs:
            status = f.get('status', 'Draft')
            status_counts[status] += 1

            sections = f.get('sections', [])
            if isinstance(sections, list):
                for s in sections:
                    if isinstance(s, dict):
                        act = s.get('act', '')
                        sec = s.get('section_number', s.get('section', ''))
                        title = s.get('title', s.get('offense', 'Offense'))
                        if sec:
                            full_sec = f"{act} Section {sec}".strip()
                            section_counts[full_sec] += 1
                            section_titles[full_sec] = title

        summary = f"AUTOFIR PROJECT DATABASE REAL-TIME RECORDS:\n"
        summary += f"- Total Registered FIRs in System: {total_firs}\n"
        summary += f"- Status Breakdown: " + ", ".join([f"{k}: {v}" for k, v in status_counts.items()]) + "\n\n"

        summary += "MOST INVOKED LEGAL SECTIONS IN AUTOFIR DATABASE:\n"
        if section_counts:
            for sec_key, count in section_counts.most_common(8):
                title = section_titles.get(sec_key, 'Offense')
                summary += f"- {sec_key} ({title}): Invoked {count} time(s)\n"
        else:
            summary += "- No specific legal sections recorded in FIRs yet.\n"

        summary += "\nRECENT REGISTERED FIR CASES IN AUTOFIR:\n"
        for f in firs[:5]:
            fir_num = f.get('fir_number', 'N/A')
            comp = f.get('complainant', {}).get('name', 'N/A')
            stat = f.get('status', 'Draft')
            summary += f"- FIR #{fir_num} | Complainant: {comp} | Status: {stat}\n"

        return summary
    except Exception as e:
        print(f"[LegalChat] Error building database analytics: {e}")
        return "AUTOFIR PROJECT DATABASE RECORDS:\n- Error loading database records."

class LegalChatAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.client = Groq(api_key=api_key)
        else:
            self.client = None

    def _is_off_topic(self, query: str) -> bool:
        """Fast check for obvious off-topic queries."""
        q_lower = query.lower().strip()
        for word in OFF_TOPIC_KEYWORDS:
            if word in q_lower:
                return True
        return False

    def process_message(self, user_message: str, history: list = None, case_context: dict = None) -> dict:
        """
        Processes user chat message, enforces strict domain scope guardrails,
        retrieves legal context from ChromaDB & MongoDB, and generates response using Groq GPT model.
        """
        if not user_message or not user_message.strip():
            return {
                "reply": "Please enter a valid legal or project-related question.",
                "citations": [],
                "suggested_questions": ["What is BNS 103?", "Is theft bailable?", "How to draft e-FIR?"]
            }

        q_clean = user_message.strip().lower().rstrip("!.,?")
        # 0. Check Greetings
        if q_clean in GREETING_WORDS or any(q_clean.startswith(w + " ") for w in GREETING_WORDS):
            return {
                "reply": "Hello! I am your **AutoFIR Legal AI Assistant**.\n\nI am dedicated to assisting with Indian Criminal Law (**BNS 2023**, **IPC**, **IT Act**, **POCSO**), e-FIR drafting, police station procedures, and AutoFIR case records.\n\nHow can I help you today?",
                "citations": [],
                "suggested_questions": [
                    "What are the most invoked sections in AutoFIR?",
                    "What is BNS 103 for murder?",
                    "Is theft bailable under IPC 379?"
                ]
            }

        # 0b. Check pre-filter off-topic guardrail
        if self._is_off_topic(user_message):
            return {
                "reply": "I am specialized **exclusively as the AutoFIR Legal Assistant**.\n\nI can only answer questions related to Indian criminal laws (**BNS 2023**, **IPC**, **IT Act**, **POCSO**), e-FIR registration, legal sections, police procedures, and AutoFIR case records.\n\nPlease ask a legal or project-related question.",
                "citations": [],
                "suggested_questions": [
                    "What is BNS 103 for murder?",
                    "Is theft bailable under IPC 379?",
                    "How to draft an e-FIR for cyber fraud?"
                ]
            }

        # 1. RAG Retrieval for legal sections
        legal_results = []
        try:
            raw_results = search_legal_sections(user_message, top_k=10)
            legal_results = rank_citations_for_query(user_message, raw_results)
        except Exception as e:
            print(f"[LegalChat] Error searching legal sections: {e}")

        # Format retrieved legal sections for context
        legal_context_str = ""
        citations = []
        if legal_results:
            legal_context_str += "RETRIEVED LEGAL SECTIONS (IPC / BNS):\n"
            for item in legal_results:
                act = item.get("act", "")
                sec = item.get("section_number", item.get("Section", ""))
                title = item.get("section_name", item.get("offense", item.get("title", "")))
                desc = item.get("description", "")
                cog = item.get("cognizable", "Not Specified")
                bail = item.get("bailable", "Not Specified")
                corr_raw = item.get("corresponding_section", "")
                corr = clean_corresponding_section(corr_raw)

                citations.append({
                    "act": act,
                    "section_number": sec,
                    "title": title,
                    "cognizable": cog,
                    "bailable": bail,
                    "corresponding_section": corr
                })

                legal_context_str += f"- {act} Sec {sec}: {title} | Cognizable: {cog} | Bailable: {bail} | Equiv: {corr} | Desc: {desc[:250]}\n"

        # 2. Always inject real-time AutoFIR database project analytics
        db_analytics_str = get_project_database_analytics()

        # 3. Assemble prompt with strict project-only knowledge instructions
        system_prompt = (
            "You are AutoFIR Legal AI Assistant, an expert Indian legal advisor strictly embedded within the AutoFIR e-FIR Drafting & Case Management project.\n\n"
            "STRICT PROJECT-ONLY KNOWLEDGE BOUNDARY & RULES:\n"
            "1. IF THE USER ASKS ABOUT 'most invoked sections', 'most common offenses', 'statistics', 'registered cases', or 'project data':\n"
            "   - You MUST ONLY report the exact real-time statistics from the AutoFIR MongoDB database provided below.\n"
            "   - DO NOT make up generic real-world stats, estimations, or external examples.\n"
            "2. DOMAIN BOUNDARY: Only answer questions related to Indian criminal statutes (BNS 2023, IPC, IT Act, POCSO, CrPC/BNSS), e-FIR drafting, police procedures, or AutoFIR case records.\n"
            "3. FOR GREETINGS OR OFF-TOPIC QUESTIONS: State clearly that you are the AutoFIR Legal Assistant dedicated to Indian criminal laws and AutoFIR case records.\n"
            "4. FORMATTING: Use clean prose, bold section titles, and bullet points. Never output repeating character loops.\n\n"
            f"{db_analytics_str}\n\n"
            f"{legal_context_str}"
        )

        messages = [{"role": "system", "content": system_prompt}]

        if history and isinstance(history, list):
            for h in history[-6:]:
                role = "user" if h.get("sender") == "user" else "assistant"
                content = h.get("text", "")
                if content:
                    messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": user_message})

        # 4. Invoke LLM
        reply_text = ""
        try:
            if not self.client:
                raise ValueError("Groq API key not configured")

            response = self.client.chat.completions.create(
                model=PRIMARY_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=1024
            )
            reply_text = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[LegalChat] LLM call failed: {e}")
            if citations:
                c0 = citations[0]
                reply_text = f"**{c0['act']} Section {c0['section_number']} - {c0['title']}**\n\n" \
                             f"• **Cognizable**: {c0['cognizable']}\n" \
                             f"• **Bailable**: {c0['bailable']}\n\n" \
                             f"For complete guidance, please verify section details in the Law Browser."
            else:
                reply_text = db_analytics_str

        # Sanitize reply text against token repetition loops (e.g. repeated ₹ or -)
        reply_text = re.sub(r'(₹\s*){2,}', '₹', reply_text)
        reply_text = re.sub(r'(\-\s*){10,}', '---', reply_text)

        # STRICT CITATION FILTERING: Remove citations if response is a greeting/refusal/disclaimer or if no direct legal keyword matched
        final_citations = citations[:3]
        normalized_reply = reply_text.lower().replace("’", "'").replace("`", "'")

        refusal_triggers = [
            "exclusively as the autofir legal assistant",
            "autofir legal ai assistant",
            "autofir legal assistant",
            "i'm here to help",
            "here to help!",
            "here to help",
            "feel free to ask",
            "dedicated solely",
            "expert system dedicated",
            "i can only answer",
            "please ask a legal or project-related question",
            "outside the scope",
            "how can i help",
            "how can i assist"
        ]

        if any(trigger in normalized_reply for trigger in refusal_triggers) or not legal_results:
            final_citations = []

        # 5. Generate smart suggested follow-up questions
        suggested_questions = self._generate_suggested_questions(user_message, final_citations)

        return {
            "reply": reply_text,
            "citations": [],
            "suggested_questions": suggested_questions
        }

    def _generate_suggested_questions(self, query: str, citations: list) -> list:
        q_lower = query.lower()
        if "invoked" in q_lower or "stat" in q_lower or "common" in q_lower or "case" in q_lower:
            return [
                "What are the most invoked sections in AutoFIR?",
                "How many FIRs are currently filed or pending?",
                "What is the section for theft under BNS 303?"
            ]
        elif citations:
            c = citations[0]
            sec = c.get("section_number", "")
            act = c.get("act", "BNS")
            title = c.get("title", "")
            return [
                f"What is the punishment under {act} Section {sec}?",
                f"Is {act} Section {sec} ({title}) bailable?",
                "What is the corresponding IPC section?"
            ]
        elif "bns" in q_lower or "ipc" in q_lower or "theft" in q_lower:
            return [
                "What is the BNS section for theft (BNS 303 / IPC 379)?",
                "Is theft a bailable or cognizable offense?",
                "What are the major changes from IPC to BNS?"
            ]
        else:
            return [
                "What are the most invoked sections in AutoFIR database?",
                "What is the difference between BNS and IPC?",
                "Is Section 308 BNS (Extortion) bailable?"
            ]
