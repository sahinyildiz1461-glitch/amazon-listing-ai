# amazon-listing-ai

## Google Shopping feed aracı (`shopping_feed`)

Ürün listesini (CSV) Google Merchant Center'ın kabul ettiği XML feed'e çevirir.
Bunu yaparken veriyi düzeltir ve reddedilmeye yol açacak hataları raporlar.
Python 3.10+ yeterli, ek paket gerekmez.

### Kullanım

```bash
python -m shopping_feed feed urunler.csv -o feed.xml \
    --title "Mağaza Adı" --link https://magazam.com \
    --report rapor.txt --jsonld-dir jsonld/
```

- `feed.xml` dosyası Merchant Center'a feed olarak yüklenir (planlı getirme ya da dosya yükleme ile).
- `rapor.txt` her ürün için hataları (`ERROR`) ve uyarıları (`WARNING`) listeler. Hatalı ürünler feed'e yazılmaz; yine de yazılmasını istiyorsanız `--include-invalid` ekleyin.
- `jsonld/<id>.html` her ürün sayfasına eklenecek `<script type="application/ld+json">` parçasını içerir. Sayfadaki fiyat ve stok bilgisi feed'dekiyle aynı olmalıdır, yoksa Merchant Center "fiyat uyuşmazlığı" hatası verir.
- `--strict` verilirse hata olduğunda çıkış kodu 1 olur; CI'da ya da zamanlanmış görevlerde işe yarar.

Yüzük ölçüsü çevirmek için:

```bash
python -m shopping_feed ring-size 60      # TR 20 / EU 60 / US 9  (iç çap ≈ 19.1 mm)
python -m shopping_feed ring-size "TR 16"
```

### CSV biçimi

Sütun adları Google'ın alan adlarıyla aynıdır (`id`, `title`, `description`, `link`, `image_link`, `price`, `availability`, `brand`, `gtin`, `google_product_category`, `color`, `size`, `item_group_id` vb.).
Ayraç olarak virgül, noktalı virgül veya tab kullanılabilir. Örnek dosya: [`examples/products.csv`](examples/products.csv).

### Otomatik yapılan düzeltmeler

| Alan | Düzeltme |
|---|---|
| Başlık | "Ücretsiz kargo", "%50 indirim", "!!" gibi promosyon ifadeleri silinir (Google başlıkta promosyon metnine izin vermez). Tamamı büyük harfli başlıklar normal yazıma çevrilir, başlıkta yoksa marka başa eklenir ve 150 karakterde kesilir. |
| Fiyat | `1.250,00 TL` ve `₺99,9` gibi yazımlar `1250.00 TRY` biçimine çevrilir. |
| Stok / durum / cinsiyet / yaş grubu | Türkçe değerler (`stokta`, `tükendi`, `yeni`, `kadın`, `yetişkin`…) Google değerlerine çevrilir. |
| Açıklama | HTML etiketleri temizlenir ve 5000 karakterde kesilir. |
| Görsel | `http://` adresleri `https://` yapılır. |
| GTIN/MPN yok | `identifier_exists=no` eklenir. |
| Yüzük ölçüsü | `60`, `TR 20`, `US 9` gibi değerler `TR 20 / EU 60 / US 9` biçimine çevrilir. |

### Denetlenen kurallar

- **Hata (ürün feed'e girmez):** zorunlu alanların boş olması, geçersiz URL, indirimli fiyatın normal fiyattan düşük olmaması, GTIN kontrol hanesinin hatalı olması, geçersiz stok değeri.
- **Uyarı:** marka, Google kategorisi ya da ek görsel eksikliği, çok kısa başlık veya açıklama, giyim/takı ürünlerinde renk, cinsiyet ya da yaş grubu eksikliği, varyantlarda `item_group_id` eksikliği.

### Testler

```bash
python -m unittest discover -s tests
```
