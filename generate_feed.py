#!/usr/bin/env python3
import csv
import html
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://shiftdose.com/wp-json/wc/store/v1/products"
OUTPUT = "feed.csv"
PER_PAGE = 100
BRAND = "SHIFT│DOSE™"

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")

FIELDS = [
    "id",
    "title",
    "description",
    "availability",
    "condition",
    "price",
    "link",
    "image_link",
    "brand",
    "product_type",
    "google_product_category",
    "custom_label_0",
]

def clean_text(value):
    value = value or ""
    value = html.unescape(TAG_RE.sub(" ", value))
    return SPACE_RE.sub(" ", value).strip()

def format_price(prices):
    prices = prices or {}
    raw = str(prices.get("price") or "0")
    currency = prices.get("currency_code") or "RSD"
    try:
        minor = int(prices.get("currency_minor_unit") or 0)
        amount = Decimal(raw) / (Decimal(10) ** minor)
    except (InvalidOperation, ValueError, TypeError):
        amount = Decimal("0")
        minor = 0

    if minor > 0:
        formatted = f"{amount:.{minor}f}"
    else:
        formatted = f"{amount:.0f}"
    return f"{formatted} {currency}"

def fetch_page(page):
    params = urlencode({
        "per_page": PER_PAGE,
        "page": page,
        "orderby": "id",
        "order": "asc",
    })
    req = Request(
        f"{API_URL}?{params}",
        headers={
            "User-Agent": "SHIFT-DOSE-Meta-Feed/1.0 (+https://shiftdose.com)",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 400 and "rest_post_invalid_page_number" in body:
            return []
        raise

def fetch_all_products():
    products = []
    page = 1
    while True:
        batch = fetch_page(page)
        if not batch:
            break
        products.extend(batch)
        if len(batch) < PER_PAGE:
            break
        page += 1
    return products

def row_for(product):
    categories = product.get("categories") or []
    category = categories[0].get("name", "Medical Streetwear") if categories else "Medical Streetwear"

    description = clean_text(product.get("short_description"))
    if not description:
        description = clean_text(product.get("description"))
    if not description:
        description = clean_text(product.get("name"))

    images = product.get("images") or []
    image_link = images[0].get("src", "") if images else ""

    return {
        # IMPORTANT: exact WooCommerce product ID to match PixelYourSite content_ids.
        "id": str(product.get("id", "")),
        "title": clean_text(product.get("name")),
        "description": description,
        "availability": "in stock" if product.get("is_in_stock") else "out of stock",
        "condition": "new",
        "price": format_price(product.get("prices")),
        "link": product.get("permalink", ""),
        "image_link": image_link,
        "brand": BRAND,
        "product_type": category,
        "google_product_category": "Apparel & Accessories > Clothing > Shirts & Tops",
        "custom_label_0": "SHIFT DOSE",
    }

def validate(rows):
    required = ["id", "title", "availability", "condition", "price", "link", "image_link", "brand"]
    problems = []
    seen = set()

    for index, row in enumerate(rows, start=2):
        for field in required:
            if not row.get(field):
                problems.append(f"row {index}: missing {field}")
        if row["id"] in seen:
            problems.append(f"row {index}: duplicate id {row['id']}")
        seen.add(row["id"])

    if problems:
        raise ValueError("Feed validation failed:\n" + "\n".join(problems[:30]))

def main():
    try:
        products = fetch_all_products()
    except (HTTPError, URLError, json.JSONDecodeError) as exc:
        print(f"Failed to fetch WooCommerce products: {exc}", file=sys.stderr)
        return 1

    rows = [row_for(p) for p in products]
    rows = [r for r in rows if r["id"] and r["link"]]
    validate(rows)

    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} products to {OUTPUT}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
