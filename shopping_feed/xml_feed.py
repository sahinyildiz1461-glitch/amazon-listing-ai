"""Google Merchant Center RSS 2.0 XML feed üretimi."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterable

G_NS = "http://base.google.com/ns/1.0"
ET.register_namespace("g", G_NS)

# Feed'e yazılacak alanlar ve sıraları; listede olmayan sütunlar atlanır.
FIELDS = [
    "id", "title", "description", "link", "mobile_link", "image_link", "additional_image_link",
    "availability", "availability_date", "price", "sale_price", "sale_price_effective_date",
    "condition", "brand", "gtin", "mpn", "identifier_exists", "google_product_category",
    "product_type", "item_group_id", "color", "size", "size_system", "material", "pattern",
    "gender", "age_group", "shipping_weight", "shipping_label", "custom_label_0", "custom_label_1",
    "custom_label_2", "custom_label_3", "custom_label_4", "product_highlight", "product_detail",
]
MULTI_VALUE = {"additional_image_link", "product_highlight"}


def build_feed(products: Iterable[dict[str, str]], title: str, link: str, description: str = "") -> bytes:
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = title
    ET.SubElement(channel, "link").text = link
    ET.SubElement(channel, "description").text = description or title

    for product in products:
        item = ET.SubElement(channel, "item")
        for field in FIELDS:
            value = product.get(field)
            if not value:
                continue
            values = [v.strip() for v in value.split("|" if field == "product_highlight" else ",")] \
                if field in MULTI_VALUE else [value]
            for v in filter(None, values):
                ET.SubElement(item, f"{{{G_NS}}}{field}").text = v

    ET.indent(rss)
    return ET.tostring(rss, encoding="utf-8", xml_declaration=True)
