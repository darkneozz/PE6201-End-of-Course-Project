# OperationalRAG

## Overview
OperationalRAG is a localized Retrieval-Augmented Generation (RAG) system designed for banking operational procedures. It allows users to index a local folder of `.docx` files and query them using natural language, ensuring all answers are grounded in the provided documents with a full audit trail.

## 1. Persona
User: Kai, a Junior Operational Banking Officer.

Scenario: Kai must process an unfamiliar payment before a strict one-hour cutoff. Unable to reach his manager, he must locate specific steps across 30+ dense procedures. OperationalRAG reduces this retrieval time from ~30 minutes of manual scanning to seconds of auditable retrieval.

## 2. Inputs and outputs
| Component | Description |
| :--- | :--- |
| **Input (Data)** | A local directory containing `.docx` procedural documents. |
| **Input (User)** | Natural language queries regarding banking operations. |
| **Output (AI)** | A grounded answer citing specific Procedure IDs (e.g., PAY-OPS-001). |
| **Output (Audit)** | A generated `.docx` log containing the query, AI response, and raw retrieved chunks. |
| **Output (UX)** | Direct system trigger to open source files for human-in-the-loop verification. |

## 3. Product architecture

## 4.Evaluation Methodology
To validate the system, I implemented a rigorous testing pipeline:

*   **Synthetic Data Generation:** Used GenerateProcedures.py to create a domain-specific banking corpus of 30 SOPs.
*   **Ground Truth Definition:** Created a curated set of 50 test cases across 10 complexity categories (e.g., Multi-Hop, Adversarial) using CreateCaseJSON.py.
*   **Lexical Baseline:** Ran NonAI_Baseline_BM25.py to establish a performance floor using BM25 keyword search.
*   **RAG Validation:** Executed 150 trials via RunRag.py, utilizing an LLM-as-a-Judge (claude-haiku-4.5) to ensure factual equivalence between generated answers and the ground truth.

## 5. Metrics Performance
*   **Target Metric:** Improve upon Lexical Search (BM25) Top-1 Accuracy and reduce "Hallucinations" in a banking context.
*   **Baseline (BM25):** 40% Accuracy.
*   **Reached (OperationalRAG):** 66% Accuracy.
*   **Key Win:** Vocabulary Mismatch performance rose from 20% (BM25) to 60% (RAG).


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

