# Architectural Improvements To-Do List

This document tracks the planned architectural changes to resolve the limitations of the current RAG-based legal classification pipeline. These changes aim to improve the system's accuracy, reduce cascading failures, and better handle edge cases (like colloquial complaint descriptions).

## 1. Fix the "Semantic Gap" in Vector Search (RAG)
- [ ] **Implement Hybrid Search**: Upgrade the ChromaDB/Retrieval logic to combine Vector Search (semantic meaning) with BM25 (exact keyword matching). This ensures that specific words like "cow", "stolen", or "knife" will reliably trigger the correct legal sections.
- [ ] **Enhance CSV Datasets with Synonym Tagging**: Add a `Keywords` column to `bns_sections.csv` and `FIR_Dataset.csv` containing everyday/colloquial synonyms (e.g., *stealing, snatching, bike theft* for Theft). Update the ingest script (`ingest_legal_data.py`) to embed these keywords.

## 2. Address Cascading Failures in the Pipeline
- [ ] **Implement Iterative Reflection for the Legal Agent**: Modify `orchestrator.py` and `legal_agent.py` to allow the LLM to request a secondary database search if the initial candidate sections do not match the extracted facts. Break the strictly linear dependency on the Intake Agent.

## 3. Reduce Over-Reliance on Hardcoded Rules
- [ ] **Adopt Few-Shot Prompting**: Refactor the `SYSTEM_PROMPT` in `legal_agent.py` to include 10-15 highly varied examples of real-world FIRs and edge cases. 
- [ ] **Prune `section_corrector.py`**: Gradually remove the aggressive deterministic `if/else` rules from the corrector as the Few-Shot Prompting improves the Legal Agent's natural accuracy.

## 4. Resolve the BNS vs. IPC Overlap Conflict
- [ ] **Standardize Internal Processing to BNS Only**: Update the pipeline to only search and evaluate the BNS database. This reduces the LLM's cognitive load and prevents it from splitting its confidence between identical IPC and BNS sections.
- [ ] **Implement a 1-to-1 Mapping Table**: Create a post-processing step that automatically appends the corresponding IPC equivalent purely for reference *after* the LLM has made its decision based on the BNS codes.
