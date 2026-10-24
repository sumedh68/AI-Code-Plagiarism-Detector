
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

import tempfile
import os


def generate_pdf_report(data):
    """
    Generate plagiarism analysis PDF report.
    """

    # Create temporary PDF file
    fd, pdf_path = tempfile.mkstemp(
        suffix=".pdf"
    )

    os.close(fd)

    # Create document
    document = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,

        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()

    content = []


    # ========================================================
    # TITLE
    # ========================================================

    content.append(
        Paragraph(
            "AI-Based Source Code Plagiarism Detection Report",
            styles["Title"]
        )
    )

    content.append(
        Spacer(1, 10)
    )


    # ========================================================
    # STUDENT INFORMATION
    # ========================================================

    student1 = data.get(
        "student1",
        "Student 1"
    )

    student2 = data.get(
        "student2",
        "Student 2"
    )

    content.append(
        Paragraph(
            f"<b>Student 1:</b> {student1}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Student 2:</b> {student2}",
            styles["Normal"]
        )
    )

    content.append(
        Spacer(1, 12)
    )


    # ========================================================
    # SCORE TABLE
    # ========================================================

    overall = data.get(
        "overall",
        0
    )

    token = data.get(
        "token_similarity",
        0
    )

    ast = data.get(
        "ast_similarity",
        0
    )

    semantic = data.get(
        "ai_similarity",
        0
    )

    risk = data.get(
        "risk",
        "Unknown"
    )


    score_data = [

        [
            "Metric",
            "Similarity"
        ],

        [
            "Overall Similarity",
            f"{overall}%"
        ],

        [
            "Token / Lexical Similarity",
            f"{token}%"
        ],

        [
            "AST / Structural Similarity",
            f"{ast}%"
        ],

        [
            "Semantic-Style Similarity",
            f"{semantic}%"
        ],

        [
            "Risk Level",
            risk
        ]

    ]


    score_table = Table(
        score_data,
        colWidths=[
            90 * mm,
            70 * mm
        ]
    )


    score_table.setStyle(
        TableStyle([

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "PADDING",
                (0, 0),
                (-1, -1),
                7
            )

        ])
    )


    content.append(
        score_table
    )

    content.append(
        Spacer(1, 15)
    )


    # ========================================================
    # MATCHING LINES
    # ========================================================

    matches = data.get(
        "matches",
        []
    )


    content.append(
        Paragraph(
            f"<b>Matching Lines Found:</b> {len(matches)}",
            styles["Heading2"]
        )
    )

    content.append(
        Spacer(1, 8)
    )


    if matches:

        match_data = [

            [
                "Code 1 Line",
                "Code 2 Line",
                "Similarity"
            ]

        ]


        for match in matches[:50]:

            match_data.append(

                [
                    str(
                        match.get(
                            "line1",
                            ""
                        )
                    ),

                    str(
                        match.get(
                            "line2",
                            ""
                        )
                    ),

                    f'{match.get("similarity", 0)}%'
                ]

            )


        match_table = Table(
            match_data,
            colWidths=[
                45 * mm,
                45 * mm,
                55 * mm
            ]
        )


        match_table.setStyle(
            TableStyle([

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )

            ])
        )


        content.append(
            match_table
        )

    else:

        content.append(
            Paragraph(
                "No strong matching lines detected.",
                styles["Normal"]
            )
        )


    # ========================================================
    # METHOD NOTE
    # ========================================================

    content.append(
        Spacer(1, 15)
    )

    content.append(
        Paragraph(
            "<b>Method:</b> The system combines lexical/token "
            "similarity, AST structural similarity and a "
            "lightweight semantic-style token comparison.",
            styles["Normal"]
        )
    )

    content.append(
        Spacer(1, 6)
    )

    content.append(
        Paragraph(
            "The similarity score is a review signal and "
            "should not by itself be treated as proof of "
            "plagiarism.",
            styles["Normal"]
        )
    )


    # ========================================================
    # BUILD PDF
    # ========================================================

    document.build(
        content
    )


    return pdf_path

