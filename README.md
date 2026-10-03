# OperationalRAG

## Overview
OperationalRAG is a localized Retrieval-Augmented Generation (RAG) system designed for banking operational procedures. It allows users to index a local folder of `.docx` files and query them using natural language, ensuring all answers are grounded in the provided documents with a full audit trail.

## Technical Instruction
### 1. Environment
- **Python Version:** 3.9+
- **OS:** Windows (Optimized for `os.startfile`), macOS, or Linux.

### 2. Dependencies
Install the required libraries via pip:

pip install numpy sentence-transformers openai python-docx

### 3. API Configuration
OperationalRAG uses OpenRouter to access gpt-4o-mini.
Edit in the Environment Variable and set OPENROUTER_API_KEY='your_key_here'

### 4. How to Run - OperationalRAG_Prototype.py
1. Ensure you have a folder containing the .docx procedural documents (e.g., the /procedures folder provided in the repo).
2. Run OperationalRAG_Prototype.py
3. Index Folder: When prompted, enter the full path to your procedures folder.
4. Query: Enter a natural language question (e.g., "How do I handle an urgent payment cutoff?").
5. Verify: The system will provide an answer and ask if you wish to open the cited .docx files immediately for manual verification.
6. Audit: Every query is automatically saved as a timestamped document in the /Log folder.

### 5. How to Run - Evals
1. Run GenerateProcedures.py to generate 30 SOP in /procedures
2. Run CreateCaseJSON.py to generate 50 test cases in /results (Output: eval_50_cases.JSON, eval_50_cases.CSV )
3. Run NonAI_Baseline_BM25.py to get NonAI Baseline results in /results (Output: bm25_baseline_results.JSON, bm25_baseline_results.CSV and category_pass_rates.csv)
4. Run RunRag.py to get the RAG results with LLM-as-a-Judge (claude-haiku-4.5) in /results (Output: eval_detailed_results.CSV, eval_detailed_results.JSON)
