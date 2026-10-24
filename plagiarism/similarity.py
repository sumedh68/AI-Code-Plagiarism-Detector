
from collections import Counter
from difflib import SequenceMatcher
from math import log, sqrt

from .tokenizer import (
    tokenize_code,
    normalized_lines,
    token_importance
)


# ============================================================
# TOKEN / LEXICAL SIMILARITY
# ============================================================

def token_similarity(tokens1, tokens2):
    """
    Calculate IDF-weighted cosine similarity over normalized code features.
    """

    if not tokens1 or not tokens2:
        return 0.0

    counts1 = Counter(tokens1)
    counts2 = Counter(tokens2)
    features = set(counts1) | set(counts2)
    weights1 = {}
    weights2 = {}

    for feature in features:
        document_frequency = int(feature in counts1) + int(feature in counts2)
        inverse_frequency = log(
            1 + (2 - document_frequency + 0.5) / (document_frequency + 0.5)
        )
        importance = token_importance(feature)

        if feature in counts1:
            weights1[feature] = (1 + log(counts1[feature])) * inverse_frequency * importance
        if feature in counts2:
            weights2[feature] = (1 + log(counts2[feature])) * inverse_frequency * importance

    dot_product = sum(
        weights1.get(feature, 0.0) * weights2.get(feature, 0.0)
        for feature in features
    )
    magnitude1 = sqrt(sum(value * value for value in weights1.values()))
    magnitude2 = sqrt(sum(value * value for value in weights2.values()))

    if not magnitude1 or not magnitude2:
        return 0.0

    information1 = _information_ratio(counts1)
    information2 = _information_ratio(counts2)
    support = sqrt(information1 * information2)
    return (dot_product / (magnitude1 * magnitude2)) * support * 100


# ============================================================
# AST / STRUCTURAL SIMILARITY
# ============================================================

def ast_similarity(ast1, ast2):
    """
    Compare weighted structural fingerprints from the AST.
    """

    if not ast1 or not ast2:
        return 0.0

    features = set(ast1) | set(ast2)
    intersection = 0.0
    union = 0.0

    for feature in features:
        importance = _ast_importance(feature)
        value1 = ast1.get(feature, 0) * importance
        value2 = ast2.get(feature, 0) * importance
        intersection += min(value1, value2)
        union += max(value1, value2)

    if not union:
        return 0.0

    support = sqrt(
        _ast_information_ratio(ast1) *
        _ast_information_ratio(ast2)
    )
    return intersection / union * support * 100


# ============================================================
# LIGHTWEIGHT SEMANTIC SIMILARITY
# ============================================================

def semantic_similarity(tokens1, tokens2):
    """
    Compare informative local token patterns with weighted n-gram overlap.
    """

    if not tokens1 or not tokens2:
        return 0.0


    grams1 = _weighted_ngrams(tokens1)
    grams2 = _weighted_ngrams(tokens2)
    features = set(grams1) | set(grams2)
    intersection = sum(min(grams1.get(key, 0.0), grams2.get(key, 0.0)) for key in features)
    union = sum(max(grams1.get(key, 0.0), grams2.get(key, 0.0)) for key in features)

    if not union:
        return 0.0

    support = sqrt(_information_ratio(tokens1) * _information_ratio(tokens2))
    return (intersection / union) * support * 100


def _information_ratio(tokens):
    total_weight = sum(token_importance(token) for token in tokens)
    informative_weight = sum(
        token_importance(token)
        for token in tokens
        if token_importance(token) >= 0.65
    )
    return informative_weight / total_weight if total_weight else 0.0


def _weighted_ngrams(tokens):
    weighted_grams = Counter()
    for size in (2, 3):
        for start in range(len(tokens) - size + 1):
            gram = tuple(tokens[start:start + size])
            average_importance = sum(token_importance(token) for token in gram) / size
            if average_importance >= 0.28:
                weighted_grams[(size, gram)] += average_importance
    return weighted_grams


def _ast_importance(feature):
    if feature.startswith(("operator:", "call:", "data:", "structure:")):
        return 1.0
    if feature.startswith(("relation:nested_control:", "relation:control_operator:")):
        return 0.9
    if feature.startswith("control:"):
        return 0.3
    if feature.startswith("declaration:function"):
        return 0.12
    if feature == "statement:return":
        return 0.08
    if feature == "declaration:variable":
        return 0.12
    return 0.25


def _ast_information_ratio(ast_features):
    total_weight = sum(
        count * _ast_importance(feature)
        for feature, count in ast_features.items()
    )
    informative_weight = sum(
        count * _ast_importance(feature)
        for feature, count in ast_features.items()
        if feature.startswith((
            "operator:",
            "call:",
            "data:",
            "structure:",
            "relation:nested_control:",
            "relation:control_operator:"
        ))
    )
    return informative_weight / total_weight if total_weight else 0.0


# ============================================================
# MATCHING CODE LINES
# ============================================================

def compare_normalized_lines(
    code1,
    code2,
    threshold=0.70
):
    """
    Find similar lines between two programs.
    """

    lines1 = normalized_lines(
        code1
    )

    lines2 = normalized_lines(
        code2
    )

    matches = []


    for line_number1, line1 in enumerate(
        lines1,
        start=1
    ):

        best_score = 0
        best_line_number = None


        for line_number2, line2 in enumerate(
            lines2,
            start=1
        ):

            # Ignore empty lines
            if not line1 or not line2:
                continue


            score = SequenceMatcher(
                None,
                line1,
                line2,
                autojunk=False
            ).ratio()


            if score > best_score:

                best_score = score

                best_line_number = (
                    line_number2
                )


        if (
            best_score >= threshold
            and
            best_line_number is not None
        ):

            matches.append({

                "line1":
                    line_number1,

                "line2":
                    best_line_number,

                "similarity":
                    round(
                        best_score * 100,
                        2
                    )

            })


    # Limit results
    return matches[:100]

