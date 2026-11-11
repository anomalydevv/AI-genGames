# opencode.md

HEX ARENA: pyray (raylib) ile yazilmis, moduler yapida 5v5 bomba modu FPS oyunu.
Bu dosya projenin haritasidir. Her yeni dosya/modul eklendiginde veya bir
dosyanin gorevi degistiginde burasi **guncellenmek zorundadir**.

## Giris Noktasi

| Dosya | Gorev |
| --- | --- |
| `main.py` | Sadece giris noktasi. Hicbir oyun mantigi icermez; `app.main()` cagirir. |

## Cekirdek Moduller

| Dosya | Gorev |
| --- | --- |
| `app.py` | Pencereyi acar, font/playerdata yukler, ana oyun dongusunu calistirir ve ekranlari yonlendirir. |
| `config.py` | Ekran boyutu, renkler, `cl`/`lerpf`/`wrap` yardimcilari ve `cfg` ayar sozlugu (crosshair dahil). |
| `state.py` | Tum calisma zamani durumunu tutan tek global `g` nesnesi (takim skorlari, bomba, efektler). |
| `weapons.py` | 8 silahin tanimi, isimleri ve bot zorluk parametreleri. |
| `modes.py` | Mac turleri: Dereceli (12 round) ve Tam Gaz (5 round). |
| `characters.py` | `Character`/`Skill` siniflari ve 4 karakter (HEX, ZEPHYR, NYX, TITAN). |
| `world.py` | Duvarlar, koridorlar, acik/kapali odalar, heaven platformlari, A/B bolgeleri, spawnlar ve yol agi. |
| `physics.py` | Ray-cast, gorunurluk, carpisma itmesi ve yer cekimi fizigi. |
| `fighter.py` | `F` savasci sinifi (takim, bomba tasiyici, bicak alanlari dahil). |
| `combat.py` | Ates, hasar, oldurme, killfeed ve alt kill gostergesi; dost atesi yok; bomba dusurme. |
| `bot.py` | Takim bilincli bot AI: A/B site push, bomba kurma, defuse, nisan ve strafe. |
| `bomb.py` | Bomba kurma/defuse, 120 saniyelik timer ve patlama durumu. |
| `knives.py` | Karambit/kelebek/bicak 3B modelleri, yakin dovus ve yedek 2B ikonlar. |
| `icons.py` | Silah/bicak modellerini ayri sahnede yandan cekip PNG kaydeder ve markete/kill gostergesine verir. |
| `weapon_icons.py` | Ikon uretilemezse kullanilan yedek 2B silah cizimleri. |
| `shaders.py` | Aydinlatma ve post-process GLSL kaynaklari. |
| `viewmodel.py` | Birinci sahis silah modeli geometrisi (8 silah). |
| `render.py` | Font yukleme, kameralar, harita/site/bomba cizimi, bicak animasyonlari, post-process. |
| `ui.py` | 2B arayuz yardimcilari: font, metin, buton, slider, toggle, panel. |
| `match.py` | 5v5 mac akisi: takimlar, roundlar, bomba kosullari, karakter skilleri, magaza ekonomisi. |
| `hud.py` | HUD, bomba uyarisi, kill gostergesi, crosshair stilleri, skor tablosu, ikonlu market, magaza ve menuler. |
| `playerdata.py` | `playerdata.json` kalici verisi: souls, MVP, karakter, bicak, crosshair. |
| `playerdata.json` | Oyuncunun kayitli verisi (souls, matches, mvps, secimler). |
| `assets/fonts/` | Projeyle gelen font (Rajdhani); her bilgisayarda calisir. |
| `assets/icons/` | `icons.py` tarafindan uretilen 3B silah/bicak fotograflari (PNG). |

## Bagimlilik Yonu

`main.py -> app.py -> {render, hud, match, icons}`
`match.py -> {bot, bomb, combat, characters, knives, modes, playerdata, physics, world}`
`render.py -> {world, viewmodel, shaders, characters, bomb, knives, ui}`
`hud.py -> {characters, bomb, knives, icons, playerdata, modes, ui}`
`icons.py -> {weapons, viewmodel, knives, shaders, config}`

Not: Kontroller `WASD`, `1-8` silah, `0` bicak, `E` bomba, `B` market.

Dongusel import yasaktir. Yeni bir modul eklerken bu yonu koru.

## Kurallar

- `main.py` sadece baslatir; is mantigi burada tutulmaz.
- God dosya yasaktir; her modul tek bir sorumluluk tasir.
- Yeni ozellik, ait oldugu modulde gelistirilir; mevcut dosyalar sismez.
- Bu dosya (`opencode.md`) her yapisal degisiklikte guncellenir.
- Ayrintili kurallar icin `RULE.md` dosyasina bak.
