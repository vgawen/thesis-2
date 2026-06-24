import unittest

from heal_baseline import build_testid_selector, is_supported_selector_expr


class TestTestIdPostFilter(unittest.TestCase):
    def test_quoted_js_expression_testid_becomes_valid_get_by_testid(self):
        selector = build_testid_selector("{'signup-card-content'}")
        self.assertEqual(selector, "page.getByTestId('signup-card-content')")
        self.assertTrue(is_supported_selector_expr(selector))

    def test_unresolved_js_expression_testid_is_not_rewritten(self):
        self.assertIsNone(build_testid_selector("{props.testId}"))

    def test_invalid_nested_quotes_are_rejected_by_syntax_check(self):
        self.assertFalse(is_supported_selector_expr("page.getByTestId('{'signup-card-content'}')"))


if __name__ == "__main__":
    unittest.main()
