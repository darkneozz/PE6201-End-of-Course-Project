# OperationalRAG - Technical Setup Guide

## Overview
OperationalRAG is a localized Retrieval-Augmented Generation (RAG) system designed for banking operational procedures. It allows users to index a local folder of `.docx` files and query them using natural language, ensuring all answers are grounded in the provided documents with a full audit trail.

## 🛠 Installation & Prerequisites
### 1. Environment
- **Python Version:** 3.9+
- **OS:** Windows (Optimized for `os.startfile`), macOS, or Linux.

### 2. Dependencies
Install the required libraries via pip:
```bash
pip install numpy sentence-transformers openai python-docx
