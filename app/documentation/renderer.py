"""
Patchli Documentation Renderer

Converts Markdown documents into HTML.

This module is responsible only for rendering
Markdown content.
"""

import markdown


def render_markdown(markdown_text: str) -> str:
    """
    Convert Markdown into HTML.

    Args:
        markdown_text:
            Markdown document.

    Returns:
        HTML string.
    """

    return markdown.markdown(
        markdown_text,
        extensions=[
            "fenced_code",
            "tables",
            "toc",
            "admonition",
        ],
    )
