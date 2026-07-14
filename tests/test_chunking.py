from pathlib import Path
import tempfile
import unittest

from obsidian_rag.chunking import chunk_markdown


class ChunkMarkdownTests(unittest.TestCase):
    def test_splits_by_heading_and_ignores_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            note = vault / "Customer.md"
            note.write_text(
                """---
type: customer
---
# Acme Motors
Initial context.
## Contact
Bea prefers email.
## Request
Looking for a 2022 vehicle.
""",
                encoding="utf-8",
            )
            chunks = chunk_markdown(note, vault)

        self.assertEqual([chunk.heading for chunk in chunks], [
            "Acme Motors",
            "Acme Motors > Contact",
            "Acme Motors > Request",
        ])
        self.assertEqual(chunks[0].title, "Acme Motors")
        self.assertNotIn("type: customer", chunks[0].content)


if __name__ == "__main__":
    unittest.main()
