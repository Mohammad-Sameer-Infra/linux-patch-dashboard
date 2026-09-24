"""Public documentation: renders the Markdown files in docs/.

The same files read correctly on GitHub, so links between pages are written
as `page.md` and rewritten to dashboard URLs here.
"""

import re

import markdown
from flask import Blueprint, abort, redirect, render_template, url_for

from app.store import ROOT

DOCS_DIR = ROOT / "docs"

# (section, [(slug, title, description)]) -- each page is docs/<slug>.md
SECTIONS = [
    ("Getting started", [
        ("introduction", "Introduction", "What Patchli is, how it works and the key concepts."),
        ("requirements", "Requirements", "What the dashboard server and managed nodes need."),
        ("installation", "Installation", "Install the dashboard step by step."),
        ("adding-nodes", "Adding nodes", "Register the servers you want to monitor."),
    ]),
    ("Using Patchli", [
        ("dashboard", "Dashboard guide", "Every page, status and number explained."),
        ("update-classification", "Update classification", "How security, kernel and critical updates are detected."),
    ]),
    ("Administration", [
        ("administration", "Day-to-day administration", "Service, password, nodes and backups."),
        ("configuration", "Configuration reference", "Every setting in settings.json."),
        ("security", "Security", "Login, HTTPS, SSH trust and hardening."),
        ("upgrading", "Upgrading and uninstalling", "Move to a new version or remove Patchli."),
    ]),
    ("Reference", [
        ("architecture", "Architecture", "Components, data flow, files and database."),
        ("api", "API reference", "The endpoints managed nodes use."),
        ("troubleshooting", "Troubleshooting", "Symptoms, causes and fixes."),
        ("faq", "FAQ", "Answers to common questions."),
        ("release-notes", "Release notes", "What changed in each version."),
        ("roadmap", "Roadmap", "What is planned next."),
    ]),
]

PAGES = [page for _, pages in SECTIONS for page in pages]
SLUGS = [slug for slug, _, _ in PAGES]

# URLs from earlier versions of the documentation center.
ALIASES = {
    "getting-started": "introduction",
    "architecture-overview": "architecture",
}

# href="installation.md#step-3" -> href="/documentation/installation#step-3"
MD_LINK = re.compile(r'href="(?:\./)?([a-z0-9-]+)\.md(#[^"]*)?"')

documentation_bp = Blueprint("documentation", __name__, url_prefix="/documentation")


def render(slug):
    md = markdown.Markdown(extensions=["fenced_code", "tables", "toc"],
                           extension_configs={"toc": {"toc_depth": "2-3"}})
    html = md.convert((DOCS_DIR / f"{slug}.md").read_text(encoding="utf-8"))
    html = MD_LINK.sub(
        lambda m: f'href="{url_for("documentation.page", slug=m[1])}{m[2] or ""}"'
        if m[1] in SLUGS else m[0],
        html,
    )
    # "On this page": the h2 headings.
    toc = [(t["id"], t["name"]) for top in md.toc_tokens for t in [top] + top["children"]
           if t["level"] == 2]
    return html, toc


@documentation_bp.route("/")
def index():
    return render_template("documentation/index.html", sections=SECTIONS)


@documentation_bp.route("/<slug>")
def page(slug):
    if slug in ALIASES:
        return redirect(url_for("documentation.page", slug=ALIASES[slug]), 301)
    if slug not in SLUGS:
        abort(404)
    i = SLUGS.index(slug)
    html, toc = render(slug)
    return render_template(
        "documentation/page.html",
        sections=SECTIONS,
        slug=slug,
        title=PAGES[i][1],
        content=html,
        toc=toc,
        prev=PAGES[i - 1] if i > 0 else None,
        next=PAGES[i + 1] if i + 1 < len(PAGES) else None,
    )
