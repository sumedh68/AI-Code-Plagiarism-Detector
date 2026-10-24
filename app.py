from flask import Flask, render_template, request, jsonify, send_file
from plagiarism.tokenizer import tokenize_code
from plagiarism.similarity import (
    token_similarity,
    ast_similarity,
    semantic_similarity,
    compare_normalized_lines
)
from plagiarism.ast_analyzer import analyze_ast
from plagiarism.report_generator import generate_pdf_report

import os

app = Flask(__name__)

# Allowed source-code files
ALLOWED_EXTENSIONS = {
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".txt"
}


def get_code(uploaded_file, pasted_code):
    """
    Get source code either from uploaded file
    or from the text area.
    """

    if pasted_code and pasted_code.strip():
        return pasted_code

    if uploaded_file and uploaded_file.filename:
        extension = os.path.splitext(
            uploaded_file.filename
        )[1].lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError(
                "Only C/C++ files are allowed."
            )

        return uploaded_file.read().decode(
            "utf-8",
            errors="ignore"
        )

    return ""


def analyze_pair(
    code1,
    code2,
    name1="Student 1",
    name2="Student 2"
):
    """
    Complete plagiarism analysis.

    Weight:
    Token      = 20%
    AST        = 40%
    Semantic   = 40%
    """

    # -----------------------------
    # 1. TOKEN ANALYSIS
    # -----------------------------

    tokens1 = tokenize_code(code1)
    tokens2 = tokenize_code(code2)

    token_score = token_similarity(
        tokens1,
        tokens2
    )

    # -----------------------------
    # 2. AST ANALYSIS
    # -----------------------------

    ast1 = analyze_ast(code1)
    ast2 = analyze_ast(code2)

    ast_score = ast_similarity(
        ast1,
        ast2
    )

    # -----------------------------
    # 3. LIGHTWEIGHT SEMANTIC
    # -----------------------------

    semantic_score = semantic_similarity(
        tokens1,
        tokens2
    )

    # -----------------------------
    # 4. FINAL SCORE
    # -----------------------------

    overall_score = (
        0.20 * token_score +
        0.40 * ast_score +
        0.40 * semantic_score
    )

    overall_score = round(
        overall_score,
        2
    )

    # -----------------------------
    # 5. RISK CLASSIFICATION
    # -----------------------------

    if overall_score >= 70:
        risk = "High"

    elif overall_score >= 30:
        risk = "Medium"

    else:
        risk = "Low"

    # -----------------------------
    # 6. MATCHING LINES
    # -----------------------------

    matching_lines = compare_normalized_lines(
        code1,
        code2
    )

    # -----------------------------
    # FINAL RESULT
    # -----------------------------

    return {
        "student1": name1,
        "student2": name2,

        "overall": overall_score,
        "dissimilarity": round(
            100 - overall_score,
            2
        ),

        "token_similarity": round(
            token_score,
            2
        ),

        "ast_similarity": round(
            ast_score,
            2
        ),

        "ai_similarity": round(
            semantic_score,
            2
        ),

        "risk": risk,

        "matches": matching_lines
    }


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():
    return render_template(
        "index.html"
    )


# ============================================================
# SINGLE COMPARISON
# ============================================================

@app.route(
    "/analyze",
    methods=["POST"]
)
def analyze():

    try:

        # Get uploaded files
        file1 = request.files.get(
            "file1"
        )

        file2 = request.files.get(
            "file2"
        )

        # Get pasted code
        pasted_code1 = request.form.get(
            "code1",
            ""
        )

        pasted_code2 = request.form.get(
            "code2",
            ""
        )

        # Extract code
        code1 = get_code(
            file1,
            pasted_code1
        )

        code2 = get_code(
            file2,
            pasted_code2
        )

        # Check code
        if not code1.strip():
            return jsonify({
                "error": "Student 1 code is empty."
            }), 400

        if not code2.strip():
            return jsonify({
                "error": "Student 2 code is empty."
            }), 400

        # Analyze
        result = analyze_pair(
            code1,
            code2,
            file1.filename
            if file1 and file1.filename
            else "Student 1",

            file2.filename
            if file2 and file2.filename
            else "Student 2"
        )

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# MULTIPLE STUDENT COMPARISON
# ============================================================

@app.route(
    "/compare_multiple",
    methods=["POST"]
)
def compare_multiple():

    try:

        uploaded_files = request.files.getlist(
            "files"
        )

        codes = []
        unsupported_files = []

        # Read files
        for uploaded_file in uploaded_files:

            if not uploaded_file.filename:
                continue

            extension = os.path.splitext(
                uploaded_file.filename
            )[1].lower()

            if extension not in ALLOWED_EXTENSIONS:
                unsupported_files.append(
                    uploaded_file.filename
                )
                continue

            code = uploaded_file.read().decode(
                "utf-8",
                errors="ignore"
            )

            codes.append(
                (
                    uploaded_file.filename,
                    code
                )
            )

        if unsupported_files:
            return jsonify({
                "error": (
                    "Unsupported file type: " +
                    ", ".join(unsupported_files) +
                    ". Use .c, .cpp, .h, .hpp, or .txt files."
                )
            }), 400

        # Need at least two files
        if len(codes) < 2:

            return jsonify({
                "error": "Select at least two supported code files."
            }), 400

        file_count = len(codes)
        matrix = [
            [100.0 if row == column else 0.0 for column in range(file_count)]
            for row in range(file_count)
        ]
        comparisons = []

        # Analyze each unique pair once, then mirror its score in the matrix.
        for i in range(file_count):
            for j in range(i + 1, file_count):
                result = analyze_pair(
                    codes[i][1],
                    codes[j][1],
                    codes[i][0],
                    codes[j][0]
                )

                matrix[i][j] = result["overall"]
                matrix[j][i] = result["overall"]
                comparisons.append({
                    "file1": codes[i][0],
                    "file2": codes[j][0],
                    "overall": result["overall"],
                    "dissimilarity": result["dissimilarity"],
                    "token_similarity": result["token_similarity"],
                    "ast_similarity": result["ast_similarity"],
                    "ai_similarity": result["ai_similarity"],
                    "risk": result["risk"],
                    "matching_lines": len(result["matches"])
                })

        return jsonify({
            "files": [
                item[0]
                for item in codes
            ],
            "matrix": matrix,
            "comparisons": comparisons
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# PDF REPORT
# ============================================================

@app.route(
    "/generate_report",
    methods=["POST"]
)
def generate_report():

    try:

        data = request.get_json(
            force=True
        )

        pdf_path = generate_pdf_report(
            data
        )

        return send_file(
            pdf_path,
            as_attachment=True,
            download_name="plagiarism_report.pdf"
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print(
        "\n======================================"
    )

    print(
        " AI Code Plagiarism Detector"
    )

    print(
        " FAST VERSION"
    )

    print(
        "======================================"
    )

    print(
        "Server: http://127.0.0.1:5000"
    )

    print(
        "CodeBERT: Disabled"
    )

    print(
        "Torch: Disabled"
    )

    print(
        "Transformers: Disabled"
    )

    print(
        "======================================\n"
    )

    app.run(
        debug=True
    )

