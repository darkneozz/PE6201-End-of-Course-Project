"""
FILE: RunRag.py
PURPOSE: To generate RAG results with LLM-as-a-Judge (claude-haiku-4.5) in /results
INPUTS: ./procedures/{30 x Procedures.docx}, ./results/eval_50_cases.json, OPENROUTER_API_KEY set in system environment variables
OUTPUTS: eval_detailed_results.CSV, eval_detailed_results.JSON
DEPENDENCIES: numpy, python-docx, sentence-transformers, openai
"""

import os
import glob
import json
import csv 
import re 
import numpy as np
import getpass
from docx import Document
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# ==========================================
# 1. LOAD & CHUNK DOCUMENTS WITH METADATA
# ==========================================
def load_docs_from_folder(folder_path):
    """Read all .docx files and return a list of (text, filename) tuples."""
    docs = []
    for filepath in glob.glob(os.path.join(folder_path, "*.docx")):
        filename = os.path.basename(filepath).replace(".docx", "")
        doc = Document(filepath)
        text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        if text.strip():
            docs.append((text, filename)) 
    return docs

def chunk_with_metadata(docs, size=250, overlap=50):
    """Sliding window chunking that preserves the source filename."""
    all_chunks = []
    for text, source in docs:
        words = text.split()
        i = 0
        while i < len(words):
            chunk_text = ' '.join(words[i:i+size])
            all_chunks.append({"text": chunk_text, "source": source})
            if i + size >= len(words):
                break
            i += max(1, size - overlap)
    return all_chunks

# Initialize Data
RAW_DOCS = load_docs_from_folder("./Procedures")
CHUNKS_DATA = chunk_with_metadata(RAW_DOCS) 
CHUNKS_TEXT = [c["text"] for c in CHUNKS_DATA]

print(f"Loaded {len(RAW_DOCS)} documents -> {len(CHUNKS_TEXT)} chunks")

# ==========================================
# 2. EMBEDDING & RETRIEVAL
# ==========================================
EMBEDDER_MODEL = 'all-mpnet-base-v2'
embedder = SentenceTransformer(EMBEDDER_MODEL)
VECTOR_MATRIX = embedder.encode(CHUNKS_TEXT, normalize_embeddings=True)

def retrieve(question, k=15): 
    """Cosine similarity retrieval returning text and source."""
    q_vec = embedder.encode([question], normalize_embeddings=True)[0]
    scores = VECTOR_MATRIX @ q_vec
    top_k_idx = np.argsort(-scores)[:k]
    return [(CHUNKS_DATA[i]["text"], CHUNKS_DATA[i]["source"], scores[i]) for i in top_k_idx]

# ==========================================
# 3. GENERATION & JUDGING (OpenRouter)
# ==========================================
def get_client():
    key = os.environ.get('OPENROUTER_API_KEY') or getpass.getpass('Paste your OpenRouter API key: ')
    return OpenAI(base_url='https://openrouter.ai/api/v1', api_key=key)

client = get_client()

GROUNDED_SYSTEM = (
    "Answer using ONLY the notes provided. "
    "You MUST explicitly state BOTH the Document Name and the Procedure Reference (e.g., PAY-OPS-XXX) you used for your answer. "
    "Answer based on the provided notes. If the information is partially available, provide what is there and cite the source. Only if the information is completely absent should you say 'The notes do not say."
    "Do not use any other knowledge."
)

def generate_answer(question, context):
    context_text = "\n\n".join(f"[{i+1}] Source {src}: {txt}" for i, (txt, src, _) in enumerate(context))
    prompt = f"NOTES:\n{context_text}\n\nQUESTION: {question}"
    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[
            {"role": "system", "content": GROUNDED_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=300
    )
    answer = response.choices[0].message.content.strip()
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    return answer, input_tokens, output_tokens

def judge_answer(expected_ans, generated_ans):
    """Uses Poolside: Laguna XS 2.1 to grade factual equivalence."""
    judge_prompt = (
        f"You are an expert grader. Compare the Generated Answer against the Expected Answer.\n\n"
        f"Expected Answer: {expected_ans}\n"
        f"Generated Answer: {generated_ans}\n\n"
        f"Do they convey the same factual meaning? If yes, reply exactly with 'YES'. "
        f"If no, or if the generated answer is missing key facts, reply exactly with 'NO'."
    )
    try:
        response = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=[{"role": "user", "content": judge_prompt}],
            temperature=0.0,
        )
        result = response.choices[0].message.content.strip().upper()
        return 1.0 if "YES" in result else 0.0
    except Exception as e:
        print(f"Judging error: {e}")
        return 0.0

# ==========================================
# 4. EVALUATION LOGIC
# ==========================================
def extract_generated_ref(text):
    """Helper to find the Procedure Reference (e.g., PAY-OPS-001) in the LLM response."""
    match = re.search(r'[A-Z]{3}-[A-Z]{3}-\d+', text)
    return match.group(0) if match else "No Ref Found"

def evaluate_case(expected_ans, expected_proc, generated, category):
    gen_lower = generated.lower().strip()
    exp_ans_lower = expected_ans.lower().strip()
    
    # 1. Handle Refusals (Out-of-Corpus/Discontinued)
    refusal_expected = any(kw in exp_ans_lower for kw in ["not in documents", "refusal", "out-of-corpus", "discontinued"])
    if refusal_expected:
        refusal_detected = any(kw in gen_lower for kw in ["the notes do not say", "refusal", "out of scope", "not covered"])
        return 1.0 if refusal_detected else 0.0
    
    # 2. Handle Factual Answers (Judge + Ref Check)
    fact_pass = judge_answer(expected_ans, generated)
    
    ref_pass = False
    if expected_proc and expected_proc != "N/A":
        refs_to_check = [r.strip() for r in expected_proc.split('&')]
        if any(ref.lower() in gen_lower for ref in refs_to_check):
            ref_pass = True
    else:
        ref_pass = True 
        
    return 1.0 if (fact_pass and ref_pass) else 0.0

# ==========================================
# 5. RUN EVALUATION & EXPORT
# ==========================================
def run_evaluation(eval_json_path, iterations=3):
    with open(eval_json_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    results = []
    category_stats = {} 
    
    for i, case in enumerate(cases):
        q = case['Question']
        expected_ans = case['Answer']
        expected_proc = case['Procedure Reference'] 
        category = case['Category']
        supporting_sentence = case['Supporting Sentence']
        
        if category not in category_stats:
            category_stats[category] = {"correct": 0, "total": 0}
        
        for run_idx in range(iterations):
            hits = retrieve(q, k=15)
            top_3_info = ", ".join([f"{src}({score:.4f})" for txt, src, score in hits[:3]])
            
            generated, in_tokens, out_tokens = generate_answer(q, hits)
            score = evaluate_case(expected_ans, expected_proc, generated, category)
            gen_ref = extract_generated_ref(generated)
            
            category_stats[category]["correct"] += score
            category_stats[category]["total"] += 1
            
            results.append({
                "question": q, 
                "expected_ref": expected_proc,
                "supporting_sentence": supporting_sentence,
                "generated_ref": gen_ref,
                "top_3_docs": top_3_info,
                "expected_answer": expected_ans,
                "generated": generated, 
                "score": score,
                "input_tokens": in_tokens,
                "output_tokens": out_tokens,
                "category": category,
                "run_number": run_idx + 1
            })

        if (i+1) % 5 == 0: print(f"Evaluated {i+1}/{len(cases)} cases... ({((i+1)*iterations)} total runs)")

    # Ensure results folder exists for output
    output_dir = "results"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # EXPORT 1: Detailed JSON (Updated path)
    with open(f"{output_dir}/eval_detailed_results.json", "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=4)

    # EXPORT 2: Full Audit CSV (Updated path)
    if results:
        keys = [
            "question", "expected_ref", "supporting_sentence", "generated_ref", "top_3_docs", 
            "expected_answer", "generated", "score", "input_tokens", 
            "output_tokens", "category", "run_number"
        ]
        with open(f"{output_dir}/eval_detailed_results.csv", "w", newline="", encoding="utf-8") as cf:
            dict_writer = csv.DictWriter(cf, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows([{k: v for k, v in row.items()} for row in results])

    print(f"\n{'='*65}")
    print(f"EVALUATION COMPLETE - {len(results)} total iterations processed")
    print(f"Files saved to /{output_dir} folder: eval_detailed_results.csv, .json")
    print(f"{'Category':<20} | {'Pass Rate':<15}")
    print("-" * 65)
    overall_correct, overall_total = 0, 0
    for cat, stats in category_stats.items():
        pass_rate = stats["correct"] / stats["total"]
        print(f"{cat:<20} | {pass_rate:.2%}")
        overall_correct += stats["correct"]
        overall_total += stats["total"]
    print("-" * 65)
    print(f"{'OVERALL':<20} | {overall_correct/overall_total:.2%}")
    print(f"{'='*65}")
    
    return category_stats

# Execute: 50 cases * 3 iterations = 150 total runs
eval_results = run_evaluation("./results/eval_50_cases.json", iterations=3)
