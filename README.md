<<<<<<< HEAD
# AI-Based Source Code Plagiarism Detection Tool

Compiler Construction practical project using:
- Flask
- C/C++ lexical token normalization
- Weighted Tree-sitter AST fingerprints
- IDF-weighted lexical similarity
- Boilerplate-aware token n-gram similarity
- PDF report generation
- Batch similarity matrix

## 1. Install

Windows:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Run

```bash
python app.py
```

Open:

http://127.0.0.1:5000

## 3. Similarity processing

Analysis runs locally with Tree-sitter and hand-engineered similarity features. No CodeBERT model download or external AI service is used.

## 4. Supported files

The current AST pipeline is designed for:
- `.c`
- `.cpp`
- `.h`
- `.hpp`
- `.txt` containing C/C++ source

## 5. How the score works

Overall score:

20% Token Similarity
+ 40% Structural Similarity
+ 40% Semantic-Style Similarity

Token features down-weight boilerplate and generic identifiers while retaining operators, algorithm calls, and data-structure names. Structural features include AST constructs, operators, array/pointer use, and nested control-flow relationships. Semantic-style similarity compares informative local token n-grams; it does not use a trained language model.

The displayed LOW/MEDIUM/HIGH labels are project heuristics. A similarity score is a review signal, not proof of plagiarism.


