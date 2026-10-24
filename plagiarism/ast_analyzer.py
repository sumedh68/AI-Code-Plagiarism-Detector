from collections import Counter
import re

try:
    from tree_sitter import Language, Parser
    import tree_sitter_cpp

    TREE_SITTER_AVAILABLE = True

except Exception:

    TREE_SITTER_AVAILABLE = False


def analyze_ast(code):
    """
    Extract weighted structural fingerprints from a C++ syntax tree.
    """

    # If Tree-sitter is unavailable
    if not TREE_SITTER_AVAILABLE:
        return {}

    try:

        # Create parser
        parser = Parser()

        # Load C++ language
        cpp_language = Language(
            tree_sitter_cpp.language()
        )

        # Different Tree-sitter versions
        try:

            parser.language = cpp_language

        except Exception:

            parser.set_language(
                cpp_language
            )

        # Parse source code
        tree = parser.parse(
            code.encode("utf-8")
        )

        source = code.encode("utf-8")
        features = Counter()
        control_types = {
            "for_statement": "for",
            "while_statement": "while",
            "do_statement": "do_while",
            "if_statement": "if",
            "switch_statement": "switch",
            "conditional_expression": "ternary"
        }
        structure_types = {
            "array_declarator": "array",
            "subscript_expression": "array_access",
            "pointer_declarator": "pointer",
            "class_specifier": "class",
            "struct_specifier": "struct",
            "lambda_expression": "lambda"
        }
        operator_nodes = {
            "binary_expression",
            "assignment_expression"
        }
        data_structures = {
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

        def text_of(node):
            if node is None:
                return ""
            return source[node.start_byte:node.end_byte].decode(
                "utf-8",
                errors="ignore"
            )

        def function_name(declarator):
            if declarator is None:
                return ""
            if declarator.type in {"identifier", "field_identifier"}:
                return text_of(declarator)
            nested = declarator.child_by_field_name("declarator")
            if nested is not None:
                return function_name(nested)
            for child in declarator.named_children:
                name = function_name(child)
                if name:
                    return name
            return ""

        declared_functions = set()
        call_names = []

        def collect_names(node):
            if node.type == "function_definition":
                name = function_name(
                    node.child_by_field_name("declarator")
                )
                if name:
                    declared_functions.add(name.lower())
            elif node.type == "call_expression":
                function_node = node.child_by_field_name("function")
                called_name = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text_of(function_node))
                if called_name:
                    call_names.append(called_name[-1].lower())
            for child in node.named_children:
                collect_names(child)

        collect_names(tree.root_node)

        def add_operator_feature(node, active_controls):
            operator_node = node.child_by_field_name("operator")
            if operator_node is None:
                return
            operator = text_of(operator_node)
            left_node = node.child_by_field_name("left")
            left_text = text_of(left_node)

            if operator == "<<" and "cout" in left_text:
                feature = "io:stream_output"
            elif operator == ">>" and "cin" in left_text:
                feature = "io:stream_input"
            else:
                feature = "operator:" + operator

            features[feature] += 1
            if active_controls:
                features[
                    "relation:control_operator:" + active_controls[-1] + ">" + feature
                ] += 1

        def traverse(node, active_controls=()):
            node_type = node.type
            current_controls = active_controls

            if node_type in control_types:
                control = control_types[node_type]
                features["control:" + control] += 1
                if active_controls:
                    features[
                        "relation:nested_control:" + active_controls[-1] + ">" + control
                    ] += 1
                current_controls = active_controls + (control,)

            if node_type == "function_definition":
                features["declaration:function"] += 1
            elif node_type == "function_declarator":
                features["declaration:function_signature"] += 1
            elif node_type == "declaration":
                features["declaration:variable"] += 1
            elif node_type == "return_statement":
                features["statement:return"] += 1
            elif node_type in structure_types:
                features["structure:" + structure_types[node_type]] += 1

            if node_type in operator_nodes:
                add_operator_feature(node, current_controls)
            elif node_type == "update_expression":
                for child in node.children:
                    if child.type in {"++", "--"}:
                        features["operator:" + child.type] += 1
                        break

            if node_type == "call_expression":
                function_node = node.child_by_field_name("function")
                called_name = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text_of(function_node))
                if called_name:
                    name = called_name[-1].lower()
                    if name not in {"main", "cout", "cin", "cerr", "clog"}:
                        features["call:" + name] += 1

            if node_type in {"template_type", "type_identifier"}:
                type_text = text_of(node).lower()
                for data_structure in data_structures:
                    if re.search(r"\b" + re.escape(data_structure) + r"\b", type_text):
                        features["data:" + data_structure] += 1

            for child in node.named_children:
                traverse(child, current_controls)

        traverse(tree.root_node)

        for called_name in call_names:
            if called_name in declared_functions:
                features["recursion:self_call"] += 1

        return dict(features)

    except Exception as e:

        print(
            "AST analysis error:",
            e
        )

        return {}

