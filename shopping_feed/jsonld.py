"""Ürün sayfaları için schema.org Product JSON-LD üretimi.

Sayfadaki structured data feed ile birebir aynı fiyat/stok bilgisini taşımalı;
aksi halde Merchant Center "fiyat uyuşmazlığı" nedeniyle ürünü reddeder.
"""

from __future__ import annotations

import json

AVAILABILITY_URLS = {
    "in_stock": "https://schema.org/InStock",
    "out_of_stock": "https://schema.org/OutOfStock",
    "preorder": "https://schema.org/PreOrder",
    "backorder": "https://schema.org/BackOrder",
}
CONDITION_URLS = {
    "new": "https://schema.org/NewCondition",
    "used": "https://schema.org/UsedCondition",
    "refurbished": "https://schema.org/RefurbishedCondition",
}


def product_jsonld(p: dict[str, str]) -> dict:
    images = [p["image_link"]] + [u.strip() for u in p.get("additional_image_link", "").split(",") if u.strip()]
    amount, currency = (p.get("sale_price") or p["price"]).split()
    data: dict = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": p["title"],
        "description": p.get("description", ""),
        "image": images,
        "sku": p["id"],
        "offers": {
            "@type": "Offer",
            "url": p["link"],
            "price": amount,
            "priceCurrency": currency,
            "availability": AVAILABILITY_URLS.get(p.get("availability", ""), AVAILABILITY_URLS["in_stock"]),
            "itemCondition": CONDITION_URLS.get(p.get("condition", "new")),
        },
    }
    if p.get("brand"):
        data["brand"] = {"@type": "Brand", "name": p["brand"]}
    if p.get("gtin"):
        data["gtin"] = p["gtin"]
    if p.get("mpn"):
        data["mpn"] = p["mpn"]
    for field, key in (("color", "color"), ("size", "size"), ("material", "material"), ("item_group_id", "inProductGroupWithID")):
        if p.get(field):
            data[key] = p[field]
    return data


def jsonld_script(p: dict[str, str]) -> str:
    body = json.dumps(product_jsonld(p), ensure_ascii=False, indent=2).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{body}\n</script>\n'
