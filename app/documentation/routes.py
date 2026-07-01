"""
Patchli Documentation Routes
"""

from flask import Blueprint, render_template

from app.documentation.service import render_document

documentation_bp = Blueprint(
    "documentation",
    __name__,
    url_prefix="/documentation",
)


@documentation_bp.route("/")
def documentation_home():

    return render_template(
        "documentation/index.html"
    )


def render_doc(title, path):

    html = render_document(path)

    return render_template(
        "documentation/page.html",
        title=title,
        content=html,
    )


@documentation_bp.route("/getting-started")
def getting_started():

    return render_doc(
        "Getting Started",
        "getting-started/01-introduction.md",
    )


@documentation_bp.route("/administration")
def administration():

    return render_doc(
        "Administration",
        "administration/01-dashboard.md",
    )


@documentation_bp.route("/architecture")
def architecture():

    return render_doc(
        "Architecture",
        "architecture/01-overview.md",
    )


@documentation_bp.route("/troubleshooting")
def troubleshooting():

    return render_doc(
        "Troubleshooting",
        "troubleshooting/01-common-issues.md",
    )


@documentation_bp.route("/faq")
def faq():

    return render_doc(
        "FAQ",
        "faq/faq.md",
    )


@documentation_bp.route("/roadmap")
def roadmap():

    return render_doc(
        "Roadmap",
        "roadmap/roadmap.md",
    )


@documentation_bp.route("/release-notes")
def release_notes():

    return render_doc(
        "Release Notes",
        "release-notes/v1.0.0-foundation.md",
    )
