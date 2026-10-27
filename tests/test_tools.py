import unittest

from tools import execute_tool, lookup_booking, search_knowledge_base


class ToolTests(unittest.TestCase):
    def test_lookup_booking_found(self):
        result = lookup_booking("bk-1001")
        self.assertTrue(result["ok"])
        self.assertEqual(result["booking"]["status"], "confirmed")

    def test_lookup_booking_missing(self):
        result = lookup_booking("BK-9999")
        self.assertFalse(result["ok"])
        self.assertIn("not found", result["error"])

    def test_search_knowledge_base(self):
        result = search_knowledge_base("wheelchair accessibility")
        self.assertTrue(result["ok"])
        self.assertEqual(result["articles"][0]["article_id"], "KB-001")

    def test_unknown_tool_is_safe(self):
        result = execute_tool("delete_everything", {})
        self.assertFalse(result["ok"])


if __name__ == "__main__":
    unittest.main()

