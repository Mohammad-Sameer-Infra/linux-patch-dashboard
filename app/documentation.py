"""In-app documentation: renders the Markdown files under docs/."""

import markdown
from flask import Blueprint, abort, render_template

from app.store import ROOT

DOCS_DIR = ROOT / "docs"

# slug: (icon, title, Markdown file, description)
DOCS = {
    "getting-started": ("📘", "Getting Started", "getting-started/01-introduction.md",
                        "Learn Patchli and complete your first deployment."),
    "administration": ("⚙️", "Administration", "administration/01-dashboard.md",
                       "Configure and manage your Patchli deployment."),
    "architecture": ("🏗️", "Architecture", "architecture/01-overview.md",
                     "Understand Patchli's internal architecture and design."),
    "troubleshooting": ("🩺", "Troubleshooting", "troubleshooting/01-common-issues.md",
                        "Resolve common deployment and operational issues."),
    "faq": ("❓", "Frequently Asked Questions", "faq/faq.md",
            "Answers to common Patchli questions."),
    "roadmap": ("🛣️", "Roadmap", "roadmap/roadmap.md",
                "Discover the future direction of Patchli."),
    "release-notes": ("📝", "Release Notes", "release-notes/v1.0.0-foundation.md",
                      "Learn what has changed in each release."),
}

documentation_bp = Blueprint("documentation", __name__, url_prefix="/documentation")


@documentation_bp.route("/")
def index():
    return render_template("documentation/index.html", docs=DOCS)


@documentation_bp.route("/<slug>")
def page(slug):
    if slug not in DOCS:
        abort(404)
    _, title, path, _ = DOCS[slug]
    text = (DOCS_DIR / path).read_text(encoding="utf-8")
    html = markdown.markdown(text, extensions=["fenced_code", "tables", "toc", "admonition"])
    return render_template("documentation/page.html", title=title, content=html)
