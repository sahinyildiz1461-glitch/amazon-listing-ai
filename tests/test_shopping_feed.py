import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from shopping_feed.cli import main
from shopping_feed.gtin import is_valid_gtin
from shopping_feed.jsonld import product_jsonld
from shopping_feed.product import clean_title, normalize_product, parse_price, validate_product
from shopping_feed.ring_size import parse_ring_size
from shopping_feed.xml_feed import G_NS, build_feed

ROOT = Path(__file__).resolve().parent.parent

BASE = {
    "id": "SKU-1",
    "title": "Örnek Takı 925 Ayar Gümüş Tek Taş Yüzük",
    "description": "925 ayar gümüş yüzük. " * 10,
    "link": "https://example.com/p/1",
    "image_link": "https://example.com/1.jpg",
    "additional_image_link": "https://example.com/2.jpg",
    "price": "1.250,00 TL",
    "availability": "stokta",
    "brand": "Örnek Takı",
    "gtin": "4006381333931",
    "google_product_category": "200",
    "color": "Gümüş",
    "gender": "kadın",
    "age_group": "yetişkin",
    "size": "TR 20",
    "item_group_id": "G1",
}


class RingSizeTest(unittest.TestCase):
    def test_eu_60_equivalents(self):
        size = parse_ring_size("60")
        self.assertEqual((size.tr, size.eu, size.us), (20, 60, 9))
        self.assertEqual(size.diameter_mm, 19.1)

    def test_explicit_systems(self):
        self.assertEqual(parse_ring_size("TR 14").eu, 54)
        self.assertEqual(parse_ring_size("US 7").tr, 14.5)
        self.assertEqual(parse_ring_size("16").eu, 56)  # sistemsiz 14-29 arası TR sayılır

    def test_rejects_garbage(self):
        for bad in ("abc", "EU 200", ""):
            with self.assertRaises(ValueError):
                parse_ring_size(bad)


class PriceAndTitleTest(unittest.TestCase):
    def test_turkish_price_formats(self):
        self.assertEqual(parse_price("1.250,90 TL"), "1250.90 TRY")
        self.assertEqual(parse_price("₺99,9"), "99.90 TRY")
        self.assertEqual(parse_price("1.250"), "1250.00 TRY")
        self.assertEqual(parse_price("19.99 USD"), "19.99 USD")
        self.assertEqual(parse_price("1,299.50 $"), "1299.50 USD")

    def test_title_cleanup(self):
        title = clean_title("GÜMÜŞ YÜZÜK %50 İNDİRİM ÜCRETSİZ KARGO!!", "Örnek Takı")
        self.assertEqual(title, "Örnek Takı Gümüş Yüzük")
        self.assertLessEqual(len(clean_title("kelime " * 50)), 150)

    def test_gtin(self):
        self.assertTrue(is_valid_gtin("4006381333931"))
        self.assertTrue(is_valid_gtin("036000291452"))
        self.assertFalse(is_valid_gtin("4006381333932"))
        self.assertFalse(is_valid_gtin("00000000"))


class ProductTest(unittest.TestCase):
    def test_clean_product_has_no_issues(self):
        product, issues = normalize_product(BASE)
        self.assertEqual(issues + validate_product(product), [])
        self.assertEqual(product["price"], "1250.00 TRY")
        self.assertEqual(product["availability"], "in_stock")
        self.assertEqual(product["gender"], "female")
        self.assertEqual(product["size"], "TR 20 / EU 60 / US 9")

    def test_errors_detected(self):
        row = dict(BASE, link="example.com", sale_price="2000 TL", gtin="123", availability="belki")
        product, issues = normalize_product(row)
        fields = {i.field for i in issues + validate_product(product) if i.level == "error"}
        self.assertEqual(fields, {"link", "sale_price", "gtin", "availability"})

    def test_identifier_exists_and_html(self):
        row = dict(BASE, gtin="", description="<p>Güzel &amp; şık</p>", image_link="http://example.com/1.jpg")
        product, _ = normalize_product(row)
        self.assertEqual(product["identifier_exists"], "no")
        self.assertEqual(product["description"], "Güzel & şık")
        self.assertTrue(product["image_link"].startswith("https://"))

    def test_earring_is_not_ring(self):
        product, _ = normalize_product(dict(BASE, google_product_category="Earrings", title="Küpe", size="60"))
        self.assertEqual(product["size"], "60")


class OutputTest(unittest.TestCase):
    def test_feed_and_jsonld(self):
        product, _ = normalize_product(dict(BASE, sale_price="999,90 TL"))
        root = ET.fromstring(build_feed([product], "Mağaza", "https://example.com"))
        item = root.find("channel/item")
        self.assertEqual(item.find(f"{{{G_NS}}}price").text, "1250.00 TRY")
        self.assertEqual(item.find(f"{{{G_NS}}}sale_price").text, "999.90 TRY")
        data = product_jsonld(product)
        self.assertEqual(data["offers"]["price"], "999.90")
        self.assertEqual(data["offers"]["availability"], "https://schema.org/InStock")

    def test_cli_on_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            out, report = Path(tmp, "feed.xml"), Path(tmp, "report.txt")
            code = main(["feed", str(ROOT / "examples/products.csv"), "-o", str(out),
                         "--report", str(report), "--jsonld-dir", str(Path(tmp, "jsonld")), "--strict"])
            self.assertEqual(code, 1)  # KLY-001 hatalı
            ids = [e.text for e in ET.parse(out).getroot().iter(f"{{{G_NS}}}id")]
            self.assertEqual(ids, ["YZK-925-TR20", "YZK-925-TR16"])
            self.assertIn("KLY-001", report.read_text(encoding="utf-8"))
            self.assertTrue(Path(tmp, "jsonld", "YZK-925-TR20.html").exists())


if __name__ == "__main__":
    unittest.main()
