"""
Patchli Documentation Service

Coordinates documentation loading and rendering.
"""

from app.documentation.loader import read_markdown
from app.documentation.renderer import render_markdown


def render_document(relative_path: str) -> str:
    """
    Load a Markdown document and render it as HTML.

    Args:
        relative_path:
            Path relative to the docs directory.

    Returns:
        Rendered HTML.
    """

    markdown_text = read_markdown(relative_path)

    return render_markdown(markdown_text)
