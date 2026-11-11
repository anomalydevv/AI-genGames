# RULE.md

Bu projenin degismez kurallari. Her katkida bu kurallara uyulur.

## 1. God dosya yasak

- Projede **asla god dosyasi olmayacak**. Tek bir dosyada tum oyun kodu toplanamaz.
- Bir dosya ~500 satiri gectiyse veya birden fazla sorumluluk tasiyorsa bolunmelidir.
- `main.py` sadece giris noktasidir; oyun mantigi, cizim, UI veya veri iceremez.

## 2. Her sey moduler

- Her modul tek bir is yapar (harita, fizik, combat, bot, UI, render, mac akisi...).
- Yeni ozellik once dogru modul belirlenerek eklenir; mevcut modullere gelisiguzel kod yigilmaz.
- Moduller arasi bagimlilik tek yonludur. Dongusel import yasaktir.
- Paylasilan durum sadece `state.py` icindeki `g` uzerinden tutulur.
- Sabitler ve ayarlar `config.py` icinde kalir.

## 3. opencode.md guncel kalacak

- Her yeni dosya eklendiginde, silindiginde veya bir dosyanin gorevi degistiginde
  `opencode.md` **guncellenecek**.
- `opencode.md`; dosya haritasini, gorevleri ve bagimlilik yonunu dogru anlatmak zorundadir.
- Guncellenmemis `opencode.md` kabul edilmez.

## 4. Veri ve icerik

- Oyuncu verisi `playerdata.json` icinde tutulur; souls, MVP, karakter ve bicak
  secimleri mac sonunda guncellenir ve kaybolmaz.
- Karakter, bicak, mod ve silah tanimlari kendi veri modullerinde tutulur
  (`characters.py`, `knives.py`, `modes.py`, `weapons.py`).
- Projeyle gelen font `assets/fonts/` icindedir; sistem fontlarina bagimlilik kurulmaz.
- Silah/bicak ikonlari `icons.py` tarafindan 3B sahneden uretilir ve
  `assets/icons/` altina kaydedilir; PNG'ler elle duzenlenmez.

## 5. Kod kalitesi

- Testsiz ve kontrolsuz buyuk degisiklik yapilmaz.
- Calisan davranis bozulmadan modulerlestirme yapilir.
- Yeni bagimlilik eklemeden once mevcut kutuphaneler (pyray/raylib) tercih edilir.

## 6. Baslatma

- Oyun her zaman `python main.py` ile baslatilir.
- `main.py` disinda bir giris noktasi olusturulmaz.
