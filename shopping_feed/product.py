"""Ürün satırlarını Merchant Center formatına çevirme ve doğrulama."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from .gtin import is_valid_gtin
from .ring_size import parse_ring_size

TITLE_MAX = 150
DESCRIPTION_MAX = 5000
ID_MAX = 50

AVAILABILITY = {
    "in_stock": "in_stock", "in stock": "in_stock", "stokta": "in_stock", "var": "in_stock", "mevcut": "in_stock",
    "out_of_stock": "out_of_stock", "out of stock": "out_of_stock", "yok": "out_of_stock",
    "tükendi": "out_of_stock", "stokta yok": "out_of_stock",
    "preorder": "preorder", "ön sipariş": "preorder", "on siparis": "preorder",
    "backorder": "backorder", "tedarik ediliyor": "backorder",
}
CONDITION = {
    "new": "new", "yeni": "new", "sıfır": "new",
    "used": "used", "ikinci el": "used", "kullanılmış": "used",
    "refurbished": "refurbished", "yenilenmiş": "refurbished",
}
GENDER = {"female": "female", "kadın": "female", "male": "male", "erkek": "male", "unisex": "unisex"}
AGE_GROUP = {
    "adult": "adult", "yetişkin": "adult", "kids": "kids", "çocuk": "kids", "toddler": "toddler",
    "infant": "infant", "bebek": "infant", "newborn": "newborn", "yenidoğan": "newborn",
}

# Google başlıkta promosyon metnine izin vermiyor; bunlar başlıktan temizlenir.
PROMO_PATTERNS = [
    r"ücretsiz\s+kargo", r"bedava\s+kargo", r"kargo\s+bedava", r"free\s+shipping",
    r"\bindirim(li)?\b", r"\bkampanya(lı)?\b", r"\bfırsat\b", r"\ben\s+ucuz\b", r"\bsale\b",
    r"%\s*\d+", r"\d+\s*%",
]
_PROMO_RE = re.compile("|".join(PROMO_PATTERNS), re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_CURRENCY_RE = re.compile(r"(TRY|TL|USD|EUR|GBP|₺|\$|€|£)", re.I)
_CURRENCY_MAP = {"TL": "TRY", "₺": "TRY", "$": "USD", "€": "EUR", "£": "GBP"}

_RING_RE = re.compile(r"yüzük|\brings?\b", re.I)
APPAREL_CATEGORY_HINTS = ("apparel", "giyim", "aksesuar", "jewelry", "takı", "mücevher")


@dataclass(frozen=True)
class Issue:
    level: str  # "error" veya "warning"
    field: str
    message: str

    def __str__(self) -> str:
        return f"[{self.level.upper()}] {self.field}: {self.message}"


def _clean(text: str | None) -> str:
    return _WS_RE.sub(" ", html.unescape(text or "")).strip()


def _lookup(table: dict[str, str], value: str) -> str:
    return table.get(value.lower(), value.lower()) if value else ""


def parse_price(text: str, default_currency: str = "TRY") -> str:
    """'1.250,90 TL', '₺99,9', '19.99 USD' -> '1250.90 TRY' biçimi."""
    raw = _clean(text)
    if not raw:
        return ""
    match = _CURRENCY_RE.search(raw)
    currency = default_currency
    if match:
        token = match.group(1).upper() if match.group(1).isalpha() else match.group(1)
        currency = _CURRENCY_MAP.get(token, token)
    number = _CURRENCY_RE.sub("", raw).replace(" ", "")
    if "," in number and "." in number:
        if number.rfind(",") > number.rfind("."):
            number = number.replace(".", "").replace(",", ".")
        else:
            number = number.replace(",", "")
    elif "," in number:
        number = number.replace(",", ".")
    elif number.count(".") > 1 or re.fullmatch(r"\d{1,3}\.\d{3}", number):
        number = number.replace(".", "")
    try:
        amount = Decimal(number)
    except InvalidOperation:
        raise ValueError(f"Fiyat anlaşılamadı: {text!r}") from None
    return f"{amount.quantize(Decimal('0.01'))} {currency}"


def _amount(price: str) -> Decimal | None:
    try:
        return Decimal(price.split()[0])
    except (IndexError, InvalidOperation):
        return None


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit + 1].rsplit(" ", 1)[0]
    return (cut if len(cut) > limit * 0.6 else text[:limit]).rstrip(" ,-|/")


def clean_title(title: str, brand: str = "") -> str:
    title = _PROMO_RE.sub(" ", _clean(title))
    title = re.sub(r"[!*]{1,}", " ", title)
    title = _WS_RE.sub(" ", title).strip(" -|,/")
    if title.isupper() and len(title) > 10:
        title = title.title()
    if brand and brand.lower() not in title.lower():
        title = f"{brand} {title}"
    return _truncate(title, TITLE_MAX)


def is_ring(product: dict[str, str]) -> bool:
    text = " ".join(product.get(k, "") for k in ("google_product_category", "product_type", "title")).lower()
    return bool(_RING_RE.search(text)) or product.get("google_product_category", "").strip() == "200"


def is_apparel(product: dict[str, str]) -> bool:
    text = " ".join(product.get(k, "") for k in ("google_product_category", "product_type")).lower()
    return any(hint in text for hint in APPAREL_CATEGORY_HINTS) or is_ring(product)


def normalize_product(row: dict[str, str], default_currency: str = "TRY") -> tuple[dict[str, str], list[Issue]]:
    """Ham satırı Merchant Center alanlarına çevirir; düzeltilemeyenleri Issue olarak döner."""
    issues: list[Issue] = []
    p = {k.strip().lower(): _clean(v) for k, v in row.items() if k}

    p["brand"] = p.get("brand", "")
    original_title = p.get("title", "")
    p["title"] = clean_title(original_title, p["brand"])
    if original_title and _PROMO_RE.search(original_title):
        issues.append(Issue("warning", "title", "Promosyon ifadesi başlıktan çıkarıldı (Google buna izin vermiyor)."))

    desc = _clean(_TAG_RE.sub(" ", html.unescape(p.get("description", ""))))
    p["description"] = _truncate(desc, DESCRIPTION_MAX)

    for field in ("price", "sale_price"):
        if p.get(field):
            try:
                p[field] = parse_price(p[field], default_currency)
            except ValueError as exc:
                issues.append(Issue("error", field, str(exc)))
                p[field] = ""

    p["availability"] = _lookup(AVAILABILITY, p.get("availability", ""))
    p["condition"] = _lookup(CONDITION, p.get("condition", "")) or "new"
    if p.get("gender"):
        p["gender"] = _lookup(GENDER, p["gender"])
    if p.get("age_group"):
        p["age_group"] = _lookup(AGE_GROUP, p["age_group"])

    p["gtin"] = re.sub(r"\D", "", p.get("gtin", ""))
    if not p["gtin"] and not p.get("mpn") and not p.get("identifier_exists"):
        p["identifier_exists"] = "no"

    if p.get("size") and is_ring(p):
        try:
            p["size"] = parse_ring_size(p["size"]).label()
        except ValueError as exc:
            issues.append(Issue("warning", "size", str(exc)))

    if p.get("image_link", "").startswith("http://"):
        p["image_link"] = "https://" + p["image_link"][len("http://"):]

    return {k: v for k, v in p.items() if v}, issues


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def validate_product(p: dict[str, str]) -> list[Issue]:
    """Normalize edilmiş ürünü Merchant Center kurallarına göre denetler."""
    issues: list[Issue] = []

    def err(field: str, msg: str) -> None:
        issues.append(Issue("error", field, msg))

    def warn(field: str, msg: str) -> None:
        issues.append(Issue("warning", field, msg))

    for field in ("id", "title", "description", "link", "image_link", "price", "availability"):
        if not p.get(field):
            err(field, "Zorunlu alan boş.")

    if len(p.get("id", "")) > ID_MAX:
        err("id", f"En fazla {ID_MAX} karakter olabilir.")
    for field in ("link", "image_link", "mobile_link"):
        if p.get(field) and not _is_url(p[field]):
            err(field, "Geçerli bir http(s) adresi değil.")
    for url in filter(None, p.get("additional_image_link", "").split(",")):
        if not _is_url(url.strip()):
            err("additional_image_link", f"Geçersiz adres: {url.strip()}")

    if p.get("availability") and p["availability"] not in set(AVAILABILITY.values()):
        err("availability", f"Geçersiz değer: {p['availability']}")
    if p.get("condition") not in set(CONDITION.values()):
        err("condition", f"Geçersiz değer: {p.get('condition')}")

    price, sale = _amount(p.get("price", "")), _amount(p.get("sale_price", ""))
    if p.get("price") and (price is None or price <= 0):
        err("price", "Fiyat sıfırdan büyük olmalı.")
    if sale is not None and price is not None and sale >= price:
        err("sale_price", "İndirimli fiyat normal fiyattan düşük olmalı.")

    if p.get("gtin") and not is_valid_gtin(p["gtin"]):
        err("gtin", "GTIN kontrol hanesi hatalı (barkodu kontrol edin).")
    if not p.get("brand"):
        warn("brand", "Marka boş; kendi üretiminizse mağaza adınızı yazın.")
    if not p.get("gtin") and p.get("identifier_exists") != "no":
        warn("gtin", "GTIN yok; barkodlu ürünlerde eklemek gösterim oranını artırır.")
    if not p.get("google_product_category"):
        warn("google_product_category", "Google kategori ID'si eklenmesi önerilir (ör. yüzük için 200).")

    title = p.get("title", "")
    if title and len(title) < 25:
        warn("title", "Başlık çok kısa; marka + ürün tipi + malzeme + renk/ölçü ekleyin.")
    if p.get("description") and len(p["description"]) < 100:
        warn("description", "Açıklama çok kısa; en az birkaç cümle önerilir.")
    if not p.get("additional_image_link"):
        warn("additional_image_link", "Ek görsel yok; farklı açılardan görseller dönüşümü artırır.")

    if is_apparel(p):
        for field, hint in (("color", "renk"), ("gender", "cinsiyet"), ("age_group", "yaş grubu")):
            if not p.get(field):
                warn(field, f"Giyim/takı ürünlerinde {hint} alanı önerilir.")
        if is_ring(p) and not p.get("size"):
            warn("size", "Yüzükte ölçü belirtilmemiş; her ölçü ayrı varyant olmalı.")
        if p.get("size") and not p.get("item_group_id"):
            warn("item_group_id", "Ölçü/renk varyantları aynı item_group_id ile gruplanmalı.")

    return issues
