#!/usr/bin/env python3
"""Build JSON-LD (FAQPage + WebPage) for each atelier page in geo/atelier/*.md.

Usage: python3 geo/tools/build_schema.py
Writes geo/schema/faq-<lang>.jsonld. Pages with unfilled {{PLACEHOLDER}}s
are still built, but the placeholders are reported so they get filled first.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://kambo.com.tr"


def parse(md):
    fm_match = re.match(r"^---\n(.*?)\n---\n", md, re.S)
    front = dict(
        line.split(": ", 1) for line in fm_match.group(1).splitlines() if ": " in line
    )
    body = md[fm_match.end():]
    faq_part = body.split("\n## ")[-1]  # last H2 is the FAQ
    faqs = []
    for block in re.split(r"\n### ", "\n" + faq_part)[1:]:
        question, _, answer = block.partition("\n")
        faqs.append((question.strip(), " ".join(answer.split())))
    return front, faqs


def build(front, faqs):
    url = SITE + front["slug"]
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": url,
                "url": url,
                "name": front["title"],
                "description": front["description"],
                "inLanguage": front["lang"],
                "about": {"@id": SITE + "/#organization"},
            },
            {
                "@type": "FAQPage",
                "@id": url + "#faq",
                "inLanguage": front["lang"],
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a},
                    }
                    for q, a in faqs
                ],
            },
        ],
    }


def main():
    out_dir = ROOT / "schema"
    out_dir.mkdir(exist_ok=True)
    for page in sorted((ROOT / "atelier").glob("*.md")):
        md = page.read_text(encoding="utf-8")
        front, faqs = parse(md)
        data = build(front, faqs)
        out = out_dir / f"faq-{front['lang']}.jsonld"
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        todo = sorted(set(re.findall(r"\{\{(\w+)\}\}", md)))
        print(f"{out.relative_to(ROOT)}: {len(faqs)} FAQ" + (f"  | doldurulacak: {', '.join(todo)}" if todo else ""))


if __name__ == "__main__":
    main()
