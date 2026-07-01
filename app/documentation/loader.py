"""
Patchli Documentation Loader

Loads Markdown documentation from the docs/
directory.
"""

from pathlib import Path

DOCS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "docs"
)


def read_markdown(relative_path: str) -> str:
    """
    Read a Markdown document from the docs directory.

    Args:
        relative_path:
            Relative path inside docs/.

    Returns:
        Markdown document as a string.

    Raises:
        FileNotFoundError
            If the document does not exist.
    """

    document = DOCS_DIR / relative_path

    if not document.is_file():
        raise FileNotFoundError(
            f"Documentation file not found: {relative_path}"
        )

    return document.read_text(
        encoding="utf-8"
    )
