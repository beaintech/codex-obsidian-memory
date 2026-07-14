from pathlib import Path
import tempfile
import unittest

from obsidian_rag.index import index_status, index_vault, read_note, search_index


class IndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp.name)
        (self.vault / ".obsidian").mkdir()
        (self.vault / ".obsidian" / "private.md").write_text(
            "This must not be indexed", encoding="utf-8"
        )
        (self.vault / "Customers").mkdir()
        (self.vault / "Customers" / "Acme.md").write_text(
            """# Acme Motors
## Vehicle request
The customer wants a blue electric vehicle for city driving.
## Follow-up
Contact by email next Tuesday.
""",
            encoding="utf-8",
        )
        self.database = self.vault / ".rag" / "index.sqlite3"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_indexes_searches_and_cites_notes(self) -> None:
        summary = index_vault(self.vault, self.database)
        results = search_index(self.database, "electric vehicle", limit=3)

        self.assertEqual(summary["files"], 1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["path"], "Customers/Acme.md")
        self.assertIn("Vehicle request", results[0]["citation"])
        self.assertEqual(index_status(self.database)["status"], "ready")

    def test_read_note_blocks_path_traversal(self) -> None:
        with self.assertRaisesRegex(ValueError, "escapes the vault"):
            read_note(self.vault, "../outside.md")

    def test_read_note_returns_relative_source(self) -> None:
        result = read_note(self.vault, "Customers/Acme.md")
        self.assertEqual(result["path"], "Customers/Acme.md")
        self.assertIn("city driving", result["content"])

    def test_read_note_blocks_excluded_directories(self) -> None:
        with self.assertRaisesRegex(ValueError, "excluded vault directory"):
            read_note(self.vault, ".obsidian/private.md")


if __name__ == "__main__":
    unittest.main()
