import re


# ============================================================
# C/C++ KEYWORDS
# ============================================================

KEYWORDS = {
    "alignas",
    "alignof",
    "and",
    "and_eq",
    "asm",
    "auto",
    "bitand",
    "bitor",
    "bool",
    "break",
    "case",
    "catch",
    "char",
    "char8_t",
    "char16_t",
    "char32_t",
    "class",
    "compl",
    "concept",
    "const",
    "consteval",
    "constexpr",
    "constinit",
    "const_cast",
    "continue",
    "co_await",
    "co_return",
    "co_yield",
    "decltype",
    "default",
    "delete",
    "do",
    "double",
    "dynamic_cast",
    "else",
    "enum",
    "explicit",
    "export",
    "extern",
    "false",
    "float",
    "for",
    "friend",
    "goto",
    "if",
    "inline",
    "int",
    "long",
    "mutable",
    "namespace",
    "new",
    "noexcept",
    "not",
    "not_eq",
    "nullptr",
    "operator",
    "or",
    "or_eq",
    "private",
    "protected",
    "public",
    "register",
    "reinterpret_cast",
    "requires",
    "return",
    "short",
    "signed",
    "sizeof",
    "static",
    "static_assert",
    "static_cast",
    "struct",
    "switch",
    "template",
    "this",
    "thread_local",
    "throw",
    "true",
    "try",
    "typedef",
    "typeid",
    "typename",
    "union",
    "unsigned",
    "using",
    "virtual",
    "void",
    "volatile",
    "wchar_t",
    "while",
    "xor",
    "xor_eq"
}


# ============================================================
# COMMON C/C++ BOILERPLATE
# ============================================================
# These tokens occur in many unrelated C/C++ programs.
# We mark them as COMMON so they don't dominate similarity.

COMMON_TOKENS = {
    "include",
    "iostream",
    "using",
    "namespace",
    "std",
    "int",
    "main",
    "return",
    "void",
    "char",
    "float",
    "double",
    "bool",
    "const"
}

CONTROL_KEYWORDS = {
    "break",
    "case",
    "catch",
    "continue",
    "do",
    "else",
    "for",
    "if",
    "return",
    "switch",
    "throw",
    "try",
    "while"
}

DATA_STRUCTURE_TOKENS = {
    "array",
    "deque",
    "forward_list",
    "list",
    "map",
    "multimap",
    "multiset",
    "pair",
    "priority_queue",
    "queue",
    "set",
    "stack",
    "tuple",
    "unordered_map",
    "unordered_set",
    "vector"
}

PRIMITIVE_TYPES = {
    "auto",
    "bool",
    "char",
    "double",
    "float",
    "int",
    "long",
    "short",
    "signed",
    "unsigned",
    "void"
}

ALGORITHM_CALLS = {
    "binary_search",
    "find",
    "find_if",
    "lower_bound",
    "max_element",
    "min_element",
    "reverse",
    "sort",
    "stable_sort",
    "swap",
    "upper_bound"
}

IMPORTANT_OPERATORS = {
    "!",
    "%",
    "&",
    "&&",
    "*",
    "+",
    "++",
    "+=",
    "-",
    "--",
    "-=",
    "/",
    "<",
    "<<",
    "<=",
    "=",
    "==",
    ">",
    ">=",
    ">>",
    "!=",
    "||",
    "^",
    "|"
}


# ============================================================
# REMOVE COMMENTS
# ============================================================

def strip_comments(code):
    """
    Remove single-line and multi-line comments.
    """

    # Remove // comments
    code = re.sub(
        r"//.*",
        " ",
        code
    )

    # Remove /* ... */ comments
    code = re.sub(
        r"/\*.*?\*/",
        " ",
        code,
        flags=re.DOTALL
    )

    return code


# ============================================================
# TOKENIZER
# ============================================================

def tokenize_code(code):
    """
    Convert C/C++ source code into normalized tokens.

    Identifiers -> IDENTIFIER
    Numbers    -> NUMBER
    Strings    -> LITERAL
    Common code -> COMMON
    """

    code = re.sub(
        r"(?m)^\s*#\s*include\b[^\n]*",
        " ",
        code
    )
    code = strip_comments(code)

    pattern = (
        r'"(?:\\.|[^"\\])*"'
        r"|\'(?:\\.|[^\'\\])*\'"
        r"|[A-Za-z_][A-Za-z0-9_]*"
        r"|\d+(?:\.\d+)?"
        r"|==|!=|<=|>="
        r"|\+\+|--"
        r"|&&|\|\|"
        r"|->"
        r"|<<|>>"
        r"|[^\s]"
    )

    raw_tokens = re.findall(
        pattern,
        code
    )

    tokens = []
    statement_context = set()

    for index, token in enumerate(raw_tokens):
        if token in {";", "{", "}"}:
            statement_context.clear()

        # ----------------------------------------
        # String / character literal
        # ----------------------------------------

        if (
            token.startswith('"')
            or token.startswith("'")
        ):
            tokens.append("LITERAL:string")


        # ----------------------------------------
        # Number
        # ----------------------------------------

        elif re.fullmatch(
            r"\d+(?:\.\d+)?",
            token
        ):
            tokens.append(
                "NUMBER:" + token
                if token in {"0", "1"}
                else "NUMBER:value"
            )


        # ----------------------------------------
        # Identifier / keyword
        # ----------------------------------------

        elif re.fullmatch(
            r"[A-Za-z_][A-Za-z0-9_]*",
            token
        ):

            lowered = token.lower()
            next_token = raw_tokens[index + 1] if index + 1 < len(raw_tokens) else ""

            if lowered in DATA_STRUCTURE_TOKENS:
                tokens.append("DATA:" + lowered)
            elif lowered in ALGORITHM_CALLS:
                tokens.append("ALGORITHM:" + lowered)
            elif lowered in {"cin", "cout", "cerr", "clog", "endl", "printf", "scanf", "getchar", "putchar"}:
                tokens.append("IO:" + lowered)
            elif lowered in PRIMITIVE_TYPES:
                tokens.append("TYPE:" + lowered)
            elif lowered in CONTROL_KEYWORDS:
                tokens.append("CONTROL:" + lowered)
            elif lowered in COMMON_TOKENS:
                tokens.append("COMMON:" + lowered)
            elif lowered in KEYWORDS:
                if lowered in {"true", "false", "nullptr"}:
                    tokens.append("LITERAL:" + lowered)
                elif lowered in {"int", "long", "short", "signed", "unsigned", "float", "double", "char", "bool", "void", "auto"}:
                    tokens.append("TYPE:" + lowered)
                else:
                    tokens.append("KEYWORD:" + lowered)
            elif next_token == "(":
                tokens.append("CALL:" + lowered)
            else:
                tokens.append("IDENTIFIER")


        # ----------------------------------------
        # Operators / symbols
        # ----------------------------------------

        else:
            if token == "<<" and statement_context.intersection({"cout", "cerr", "clog"}):
                tokens.append("IO:stream_output")
            elif token == ">>" and "cin" in statement_context:
                tokens.append("IO:stream_input")
            elif token in IMPORTANT_OPERATORS:
                tokens.append("OP:" + token)
            else:
                tokens.append("PUNCT:" + token)

        if token not in {";", "{", "}"}:
            statement_context.add(token.lower())


    return tokens


def token_importance(token):
    """Return a base weight that reduces boilerplate influence."""

    if token.startswith(("ALGORITHM:", "CALL:", "DATA:", "OP:")):
        return 1.0
    if token.startswith("CONTROL:"):
        return 0.48
    if token.startswith("KEYWORD:"):
        return 0.35
    if token.startswith("TYPE:"):
        return 0.22
    if token.startswith("NUMBER:"):
        return 0.35
    if token.startswith("LITERAL:"):
        return 0.25
    if token.startswith("IO:"):
        return 0.12
    if token.startswith("COMMON:"):
        return 0.08
    if token == "IDENTIFIER":
        return 0.12
    if token.startswith("PUNCT:"):
        return 0.08
    return 0.2


# ============================================================
# NORMALIZED LINES
# ============================================================

def normalized_lines(code):
    """
    Convert each source-code line into normalized tokens.
    Used to find matching lines.
    """

    cleaned_code = strip_comments(
        code
    )

    result = []

    for line in cleaned_code.splitlines():

        tokens = tokenize_code(
            line
        )

        if tokens:

            result.append(
                " ".join(tokens)
            )

    return result

