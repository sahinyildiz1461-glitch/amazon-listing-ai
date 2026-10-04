"""Komut satırı: python -m shopping_feed feed ürünler.csv -o feed.xml"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from .jsonld import jsonld_script
from .product import normalize_product, validate_product
from .ring_size import parse_ring_size
from .xml_feed import build_feed


def _read_rows(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig")
    dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t")
    return list(csv.DictReader(text.splitlines(), dialect=dialect))


def cmd_feed(args: argparse.Namespace) -> int:
    rows = _read_rows(Path(args.input))
    accepted, report, error_count, warning_count = [], [], 0, 0

    for line_no, row in enumerate(rows, start=2):
        product, issues = normalize_product(row, args.currency)
        issues += validate_product(product)
        errors = [i for i in issues if i.level == "error"]
        error_count += len(errors)
        warning_count += len(issues) - len(errors)
        if issues:
            report.append(f"Satır {line_no} — {product.get('id', '?')}: {product.get('title', '')}")
            report.extend(f"  {issue}" for issue in issues)
        if not errors or args.include_invalid:
            accepted.append(product)

    Path(args.output).write_bytes(build_feed(accepted, args.title, args.link, args.description))

    if args.jsonld_dir:
        out = Path(args.jsonld_dir)
        out.mkdir(parents=True, exist_ok=True)
        for product in accepted:
            safe_id = re.sub(r"[^\w.-]", "_", product["id"])
            (out / f"{safe_id}.html").write_text(jsonld_script(product), encoding="utf-8")

    summary = (f"{len(rows)} ürün okundu, {len(accepted)} ürün feed'e yazıldı → {args.output}\n"
               f"{error_count} hata, {warning_count} uyarı")
    text = "\n".join(report + ["", summary]) if report else summary
    if args.report:
        Path(args.report).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1 if args.strict and error_count else 0


def cmd_ring_size(args: argparse.Namespace) -> int:
    try:
        size = parse_ring_size(args.size)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    print(f"{size.label()}  (çevre {size.circumference_mm:g} mm, iç çap ≈ {size.diameter_mm} mm)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shopping_feed", description="Google Shopping feed araçları")
    sub = parser.add_subparsers(dest="command", required=True)

    feed = sub.add_parser("feed", help="CSV'den Merchant Center XML feed'i üret")
    feed.add_argument("input", help="Ürün CSV dosyası (virgül, noktalı virgül veya tab ayraçlı)")
    feed.add_argument("-o", "--output", default="feed.xml")
    feed.add_argument("--report", help="Hata/uyarı raporunu bu dosyaya da yaz")
    feed.add_argument("--jsonld-dir", help="Her ürün için JSON-LD <script> parçası yazılacak klasör")
    feed.add_argument("--currency", default="TRY", help="Para birimi yazılmamış fiyatlar için (varsayılan TRY)")
    feed.add_argument("--title", default="Ürün Feed'i", help="Feed (kanal) başlığı")
    feed.add_argument("--link", default="https://example.com", help="Mağaza adresi")
    feed.add_argument("--description", default="")
    feed.add_argument("--include-invalid", action="store_true", help="Hatalı ürünleri de feed'e yaz")
    feed.add_argument("--strict", action="store_true", help="Hata varsa 1 çıkış koduyla bitir")
    feed.set_defaults(func=cmd_feed)

    ring = sub.add_parser("ring-size", help="Yüzük ölçüsü çevir (ör. 'TR 20', 'EU 60', 'US 9')")
    ring.add_argument("size")
    ring.set_defaults(func=cmd_ring_size)

    args = parser.parse_args(argv)
    return args.func(args)
