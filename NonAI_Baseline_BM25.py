import os
import json
from docx import Document
import bm25s
import pandas as pd

# ================= CONFIGURATION =================
JSON_PATH = "./results/eval_50_cases.json"
CORPUS_FOLDER = "./Procedures"
SCORE_THRESHOLD = 1.5  
TOP_K = 1
output_folder = "results"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
# =================================================

# 1. Load evaluation cases from JSON
if not os.path.exists(JSON_PATH):
    raise FileNotFoundError(f"Evaluation JSON not found at '{JSON_PATH}'.")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    eval_cases = json.load(f)

# 2. Load corpus from .docx files
corpus_texts = []
corpus_filenames = []

if os.path.exists(CORPUS_FOLDER):
    for filename in os.listdir(CORPUS_FOLDER):
        if filename.endswith(".docx") and not filename.startswith("~$"):
            file_path = os.path.join(CORPUS_FOLDER, filename)
            try:
                doc = Document(file_path)
                full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                corpus_texts.append(full_text)
                corpus_filenames.append(filename)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
else:
    print(f"Directory '{CORPUS_FOLDER}' not found.")
    exit()

if not corpus_texts:
    print("No documents loaded. Exiting.")
    exit()

# 3. Tokenize and Index BM25
print("Tokenizing corpus and indexing BM25...")
corpus_tokens = bm25s.tokenize(corpus_texts, lower=True)
retriever = bm25s.BM25()
retriever.index(corpus_tokens)

PROCEDURE_TO_FILENAME = {
}

# 4. Run Evaluation
results = []
correct_count = 0

print(f"Running BM25 baseline evaluation on {len(eval_cases)} cases...\n")

for i, case in enumerate(eval_cases):
    question = case["Question"]
    expected_ref = case["Procedure Reference"]

    # Retrieve top document
    query_tokens = bm25s.tokenize(question, lower=True)
    retrieved_docs, scores = retriever.retrieve(query_tokens, corpus=corpus_filenames, k=TOP_K)

    top_doc = retrieved_docs[0][0]
    top_score = float(scores[0][0])

    expected_filename = PROCEDURE_TO_FILENAME.get(expected_ref, expected_ref)

    is_correct = False
    
    if expected_ref == "N/A":
        if top_score < SCORE_THRESHOLD:
            is_correct = True
            display_doc = "N/A"
        else:
            is_correct = False
            display_doc = top_doc
    else:
        if top_score < SCORE_THRESHOLD:
            display_doc = "N/A"
            is_correct = False
        else:
            display_doc = top_doc
            is_correct = (top_doc == expected_filename) or (expected_filename in top_doc)

    if is_correct:
        correct_count += 1

    results.append({
        "Case #": i + 1,
        "Category": case["Category"],
        "Question": question[:65] + "..." if len(question) > 65 else question,
        "Expected Reference": expected_ref,
        "Retrieved Document": display_doc,
        "BM25 Score": f"{top_score:.2f}",
        "Result": "Correct" if is_correct else "Incorrect"
    })

# 5. Output Results Table
df = pd.DataFrame(results)

# Create a binary column for easy averaging (1 for Correct, 0 for Incorrect)
df['Is_Correct_Binary'] = df['Result'].apply(lambda x: 1 if x == 'Correct' else 0)

# Group by Category and calculate stats
category_analysis = df.groupby('Category')['Is_Correct_Binary'].agg(['count', 'sum']).reset_index()
category_analysis.columns = ['Category', 'Total_Cases', 'Correct_Cases']
category_analysis['Pass_Rate_%'] = (category_analysis['Correct_Cases'] / category_analysis['Total_Cases']) * 100

# Print the Category Pass Rate table to console
print("\n" + "="*60)
print("PASS RATE BY CATEGORY")
print("="*60)
print(category_analysis.to_string(index=False))
print("="*60)

# Save category pass rates to CSV
category_analysis.to_csv(f"{output_folder}/category_pass_rates.csv", index=False)
# --------------------------------------------------

print("\n" + "="*90)
print("BM25 BASELINE EVALUATION RESULTS (FIXED)")
print("="*90)
print(df.drop(columns=['Is_Correct_Binary']).to_string(index=False)) # Drop helper col for print
print("="*90)
print(f"Total Cases:           {len(eval_cases)}")
print(f"Correctly Answered:    {correct_count}")
print(f"Accuracy:              {correct_count / len(eval_cases) * 100:.1f}%")
print("="*90)

# Save to CSV & JSON
df.drop(columns=['Is_Correct_Binary']).to_csv(f"{output_folder}/bm25_baseline_results.csv", index=False)
df.drop(columns=['Is_Correct_Binary']).to_json(f"{output_folder}/bm25_baseline_results.json", orient="records", indent=2)
print("Results saved to 'bm25_baseline_results.csv' and 'category_pass_rates.csv'")
