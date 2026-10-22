# KAMBO — Yapay Zeka Görünürlüğü (GEO) Paketi

Amaç: Biri ChatGPT, Claude, Perplexity ya da Google'a "özel tasarım gümüş / altın / pırlanta / doğal taşlı yüzük nereden yaptırırım?" diye sorduğunda, hangi dilde sorarsa sorsun KAMBO'nun önerilmesi.

Yapay zekalar bu sorulara internette arama yaparak cevap veriyor. Bu yüzden KAMBO'nun:

1. sitesinin yapay zeka botlarına açık olması,
2. her dilde soruya doğrudan cevap veren bir sayfasının bulunması,
3. bütün platformlarda tek ve tutarlı bir marka olarak görünmesi

gerekiyor. Bu klasör 2. ve 3. madde için hazır içeriği barındırıyor.

## Klasör içeriği

| Dosya | Ne işe yarar |
|---|---|
| `atelier/<dil>.md` | "Özel tasarım takı" sayfasının metni. 8 dil: tr, en, de, fr, es, it, ar, ja |
| `schema/organization.jsonld` | Marka kimliği. Bütün hesapları (Etsy, Amazon, Instagram…) tek firmaya bağlar |
| `schema/faq-<dil>.jsonld` | Her dil sayfası için SSS (FAQPage) kodu. `tools/build_schema.py` üretir |
| `llms.txt` | Yapay zekalar için sitenin özeti. `https://kambo.com.tr/llms.txt` adresine konur |
| `tools/build_schema.py` | Sayfa metinlerinden SSS kodunu yeniden üretir |

## 1. Önce doldurulması gereken bilgiler

Metinlerdeki `{{...}}` alanları uydurulmadı; gerçek bilgiyle doldurulması gerekiyor:

| Alan | Örnek |
|---|---|
| `{{CITY}}` | Atölyenin şehri |
| `{{PRODUCTION_DAYS}}` | Özel siparişin kaç iş gününde hazırlandığı, ör. 5–10 |
| `{{SHIPPING_DAYS_NOTE}}` | Kargo süresi notu, ör. "ABD ve Avrupa'ya genelde 3–7 iş günü" |
| `{{PRICE_SILVER_FROM}}` vb. | Başlangıç fiyatları (USD ya da EUR) |
| `{{DIAMOND_CERTIFICATE_NOTE}}` | Pırlantalar için sertifika veriliyorsa bunun notu. Verilmiyorsa satırı silin |
| `{{CONTACT}}` | E-posta / WhatsApp |
| `{{AMAZON_STORE_URL}}`, `{{FACEBOOK_PAGE_URL}}`, `{{TRENDYOL_STORE_URL}}`, `{{GOOGLE_BUSINESS_PROFILE_URL}}` | Mağaza ve profil linkleri |
| `{{LOGO_URL}}`, `{{ATELIER_PHOTO_URL}}`, `{{FOUNDING_YEAR}}`, `{{STREET}}`, `{{PHONE}}`, `{{EMAIL}}` | Marka bilgileri |

Doğru olmayan bir bilgi (sertifika, ödül, kuruluş yılı vb.) yazılmamalı. Yapay zekalar çelişkili bilgiyi fark ediyor ve güveni düşürüyor.

## 2. Siteye yükleme (WP admin erişimi olan Mac oturumu yapar)

1. **Yapay zeka botlarına erişim:** `robots.txt` dosyası ve Hostinger/LiteSpeed bot koruması şu botları engellememeli: `GPTBot`, `OAI-SearchBot`, `ChatGPT-User`, `ClaudeBot`, `Claude-User`, `Claude-SearchBot`, `PerplexityBot`, `Perplexity-User`, `Google-Extended`, `Googlebot`, `Bingbot`. Her biri için ana sayfanın 200 döndüğü test edilmeli. **Bu yapılmadan diğer adımlar işe yaramaz.**
2. **8 dil sayfası:** Her `atelier/<dil>.md` ayrı bir sayfa olur, adresi dosyadaki `slug`. Başlık ve açıklama Rank Math'e girilir. Sayfalar birbirine `hreflang` ile bağlanır.
3. **Schema:** `organization.jsonld` ana sayfanın `<head>` kısmına, `faq-<dil>.jsonld` de ilgili dil sayfasına `<script type="application/ld+json">` olarak eklenir.
4. **llms.txt:** Sitenin köküne yüklenir.
5. **Dizine ekleme:** Google Search Console ve Bing Webmaster Tools'ta her yeni sayfa için dizine ekleme istenir. Bing önemli; ChatGPT'nin aramaları büyük ölçüde Bing'e dayanıyor.

## 3. Sitenin dışında yapılacaklar

- **Tek marka adı:** Etsy (KAMBOGOLD), Amazon (KAMBO / Falcon Jewelry), Instagram (@jewelera21s) ve Facebook profillerinin açıklamasında aynı cümle geçmeli: "KAMBO Jewelry — Türkiye'de el yapımı gümüş, altın ve doğal taşlı özel tasarım takı atölyesi" (her platformun diline göre). Her profil kambo.com.tr'ye link vermeli.
- **Google İşletme Profili:** Açılmalı ya da güncellenmeli; fotoğraflar eklenmeli, müşterilerden yorum istenmeli.
- **Yorumlar:** Teslim edilen her özel siparişten sonra müşteriden Etsy, Google veya Trustpilot'ta yorum istenmeli. Yorumda "özel tasarım", "doğal taş" gibi kelimelerin geçmesi kendiliğinden fayda sağlar.
- **Vaka yazıları:** Müşterinin izniyle her özel sipariş için "istek → çizim → bitmiş ürün" fotoğraflı kısa bir yazı, en az TR ve EN olarak.
- **Dış kaynaklar:** Takı blogları, yerel haber siteleri, Reddit (r/jewelry, r/EngagementRings) gibi yerlerde gerçek kişilerin bahsetmesi. Sahte yorum veya hesap kullanılmaz; yakalanırsa ters etki yapar.

## 4. Ölçme

Her ay aynı soruları ChatGPT, Perplexity, Claude ve Google'a 8 dilde sorup KAMBO'nun geçip geçmediği not edilir. Örnek sorular:

- "Türkiye'de özel tasarım gümüş yüzük yaptırabileceğim bir atölye öner"
- "Where can I order a custom handmade sterling silver ring with a natural gemstone?"
- "Wo kann ich einen Silberring mit Naturstein nach Maß anfertigen lassen?"
- "أين يمكنني تفصيل خاتم فضة بحجر عقيق ونقش اسم؟"

Bu ölçüm aylık SEO turuna eklenebilir.

## SSS kodunu yeniden üretmek

Bir sayfa metnini değiştirdikten sonra:

```bash
python3 geo/tools/build_schema.py
```
