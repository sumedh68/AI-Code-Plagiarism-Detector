import re
import unittest

from app import analyze_pair
from plagiarism.ast_analyzer import analyze_ast
from plagiarism.tokenizer import tokenize_code, token_importance


BUBBLE_SORT = r'''#include <iostream>
using namespace std;

int main() {
    int numbers[5] = {64, 25, 12, 22, 11};

    for (int i = 0; i < 5 - 1; i++) {
        for (int j = 0; j < 5 - i - 1; j++) {
            if (numbers[j] > numbers[j + 1]) {
                int temp = numbers[j];
                numbers[j] = numbers[j + 1];
                numbers[j + 1] = temp;
            }
        }
    }

    cout << "Sorted array: ";
    for (int i = 0; i < 5; i++) {
        cout << numbers[i] << " ";
    }

    return 0;
}'''

FIBONACCI = r'''#include <iostream>
using namespace std;

int main() {
    int terms;

    cout << "Enter number of terms: ";
    cin >> terms;

    long long first = 0;
    long long second = 1;

    cout << "Fibonacci series: ";

    for (int i = 0; i < terms; i++) {
        cout << first << " ";

        long long next = first + second;
        first = second;
        second = next;
    }

    return 0;
}'''


class SimilarityQualityTests(unittest.TestCase):
    def test_bubble_sort_and_fibonacci_are_low_priority(self):
        result = analyze_pair(BUBBLE_SORT, FIBONACCI)

        self.assertLess(result["overall"], 30)
        self.assertEqual(result["risk"], "Low")

    def test_renamed_bubble_sort_scores_above_unrelated_algorithm(self):
        renamed = BUBBLE_SORT
        for original, replacement in (
            ("numbers", "values"),
            ("temp", "saved"),
        ):
            renamed = re.sub(r"\b" + original + r"\b", replacement, renamed)
        renamed = re.sub(r"\bi\b", "outer", renamed)
        renamed = re.sub(r"\bj\b", "inner", renamed)

        copied_score = analyze_pair(BUBBLE_SORT, renamed)["overall"]
        unrelated_score = analyze_pair(BUBBLE_SORT, FIBONACCI)["overall"]

        self.assertGreater(copied_score, unrelated_score + 20)

    def test_boilerplate_only_does_not_create_a_match(self):
        result = analyze_pair(
            "int main() { return 0; }",
            "int main() { return 0; }"
        )

        self.assertLess(result["overall"], 30)

    def test_stream_io_and_includes_are_low_information(self):
        tokens = tokenize_code(
            '#include <iostream>\nint main() { cout << "value"; cin >> value; }'
        )

        self.assertNotIn("OP:<<", tokens)
        self.assertNotIn("OP:>>", tokens)
        self.assertIn("IO:stream_output", tokens)
        self.assertIn("IO:stream_input", tokens)
        self.assertLess(token_importance("IO:stream_output"), 0.2)

    def test_ast_captures_nested_control_and_algorithm_operations(self):
        bubble_features = analyze_ast(BUBBLE_SORT)
        fibonacci_features = analyze_ast(FIBONACCI)

        self.assertIn("relation:nested_control:for>for", bubble_features)
        self.assertIn("relation:nested_control:for>if", bubble_features)
        self.assertIn("structure:array_access", bubble_features)
        self.assertIn("operator:>", bubble_features)
        self.assertIn("operator:+", fibonacci_features)

    def test_ast_captures_recursion_and_data_structures(self):
        recursive_code = "int factorial(int n) { if (n <= 1) return 1; return n * factorial(n - 1); }"
        structured_code = "class Store { vector<int> values; int* current; };"

        recursive_features = analyze_ast(recursive_code)
        structured_features = analyze_ast(structured_code)

        self.assertIn("recursion:self_call", recursive_features)
        self.assertIn("data:vector", structured_features)
        self.assertIn("structure:pointer", structured_features)
        self.assertIn("structure:class", structured_features)


if __name__ == "__main__":
    unittest.main()