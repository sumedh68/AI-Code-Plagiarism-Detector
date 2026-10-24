from difflib import SequenceMatcher
from collections import Counter


def semantic_similarity(tokens1, tokens2):
    if not tokens1 or not tokens2:
        return 0.0

    sequence_score = SequenceMatcher(
        None,
        tokens1,
        tokens2,
        autojunk=False
    ).ratio()

    def ngrams(tokens, n=3):
        if len(tokens) < n:
            return Counter(tokens)
        return Counter(
            tuple(tokens[i:i+n])
            for i in range(len(tokens)-n+1)
        )

    a = ngrams(tokens1)
    b = ngrams(tokens2)

    keys = set(a) | set(b)

    intersection = sum(min(a[k], b[k]) for k in keys)
    union = sum(max(a[k], b[k]) for k in keys)

    ngram_score = intersection / union if union else 0

    return (0.55 * sequence_score + 0.45 * ngram_score) * 100