"""
Patchli Product Metadata

Loads product information from config/product.json.

This module provides a single source of truth for
Patchli branding and product metadata.
"""

import json
from pathlib import Path

PRODUCT_FILE = (
    Path(__file__).resolve().parent.parent
    / "config"
    / "product.json"
)

with open(PRODUCT_FILE, encoding="utf-8") as file:

    PRODUCT = json.load(file)
