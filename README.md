# OperationalRAG

## Overview
OperationalRAG is a localized Retrieval-Augmented Generation (RAG) system designed for banking operational procedures. It allows users to index a local folder of `.docx` files and query them using natural language, ensuring all answers are grounded in the provided documents with a full audit trail.

## Persona
User: Kai, a Junior Operational Banking Officer.

Scenario: Kai must process an unfamiliar payment before a strict one-hour cutoff. Unable to reach his manager, he must locate specific steps across 30+ dense procedures. OperationalRAG reduces this retrieval time from ~30 minutes of manual scanning to seconds of auditable retrieval.

## Inputs and outputs
### Inputs
1. Folder containing the procedeures
2. Question to query the procedures

### Outputs
1. Answer to the question
2. Log File containing the questions, answers and retrieved chunks in DOCX for audit trail

## Product architecture

## Data Sources


## Evaluation
### Metrics Targeted

### Metrics Reached

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

