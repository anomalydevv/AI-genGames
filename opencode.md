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
| `state.py` | Tum calisma zamani durumunu tutan tek global `g` nesnesi (takim skorlari, bomba, efektler, yere dusen silahlar, `rt`/`vmrt` render texture'lari). |
| `weapons.py` | 8 silahin tanimi, isimleri, slot eslemesi ve bot zorluk parametreleri. |
| `modes.py` | Mac turleri: Dereceli (12 round) ve Tam Gaz (5 round). |
| `characters.py` | `Character`/`Skill` siniflari ve 4 karakter (HEX, ZEPHYR, NYX, TITAN). |
| `world.py` | Duvarlar, koridorlar, acik/kapali odalar, heaven platformlari, A/B bolgeleri, spawnlar ve yol agi. |
| `physics.py` | Ray-cast, gorunurluk, carpisma itmesi ve yer cekimi fizigi. |
| `fighter.py` | `F` savasci sinifi (takim, bot ekonomisi, bomba tasiyici, bicak alanlari dahil). |
| `combat.py` | Ates, hasar, oldurme, killfeed ve alt kill gostergesi; dost atesi yok; bomba dusurme; olumde silah dusurme ve envanter sifirlama; bot oldurme odulu. |
| `AI.py` | Takim bilincli bot AI: ekonomi ve tur basi silah satin alma, A/B site push, bomba kurma, defuse, nisan, strafe, burst ates ve yere dusen silahi alma. |
| `bomb.py` | Bomba kurma/defuse, 120 saniyelik timer ve patlama durumu. |
| `knives.py` | Karambit/kelebek/bicak 3B modelleri, menteşe etiketleri (`hA`/`hB`), yakin dovus ve yedek 2B ikonlar. |
| `icons.py` | Silah/bicak modellerini ayri sahnede yandan cekip PNG kaydeder ve markete/kill gostergesine verir. |
| `weapon_icons.py` | Ikon uretilemezse kullanilan yedek 2B silah cizimleri. |
| `shaders.py` | Aydinlatma ve post-process GLSL kaynaklari. |
| `viewmodel.py` | Birinci sahis silah modeli geometrisi (8 silah) ve ates edince oynayan parca etiketleri (`slide`/`bolt`/`pump`/`hammer`). |
| `render.py` | Font yukleme, kameralar, harita/site/bomba/yere dusen silah cizimi, sert govdeli silah/bicak viewmodel'i, ayri `vmrt` kompoziti, bicaga ozel slash yayi/iz ve asimetrik kelebek kanat animasyonu, post-process. |
| `ui.py` | 2B arayuz yardimcilari: font, metin, buton, slider, toggle, panel. |
| `match.py` | 5v5 mac akisi: takimlar, roundlar, bomba kosullari, karakter skilleri, magaza ekonomisi, botlarin tur basi satin almasi, kelebek cift menteşe yay fiziği. |
| `hud.py` | HUD, bomba uyarisi, kill gostergesi, crosshair stilleri, skor tablosu, 3 slotlu ikonlu market, magaza ve menuler. |
| `playerdata.py` | `playerdata.json` kalici verisi: souls, MVP, karakter, bicak, crosshair. |
| `playerdata.json` | Oyuncunun kayitli verisi (souls, matches, mvps, secimler). |
| `assets/fonts/` | Projeyle gelen font (Rajdhani); her bilgisayarda calisir. |
| `assets/icons/` | `icons.py` tarafindan uretilen 3B silah/bicak fotograflari (PNG). |

## Bagimlilik Yonu

`main.py -> app.py -> {render, hud, match, icons}`
`match.py -> {AI, bomb, combat, characters, knives, modes, playerdata, physics, world}`
`render.py -> {world, viewmodel, shaders, characters, bomb, knives, ui}`
`hud.py -> {characters, bomb, knives, icons, playerdata, modes, ui}`
`icons.py -> {weapons, viewmodel, knives, shaders, config}`

Not: Kontroller `WASD`, `1` ana silah, `2` tabanca, `3` bicak, `Y` incele, `E` bomba, `B` market (sadece tur basi 5 sn); scroll slot degistirir.

Dongusel import yasaktir. Yeni bir modul eklerken bu yonu koru.

## Viewmodel Sabitleri (test edilmis)

Silah/bicak viewmodel'i sert govde olarak doner; asagidaki degerler ekran
goruntusu testleriyle sabitlendi. Degistirirken tekrar test edin.

- Silah inspect `_GUN_INSPECT` = (spd, yaw, pitch, roll, dist, scale):
  - 0 Tabanca `(1.55, 1.10, 0.22, 0.26, 0.62, 1.00)`
  - 1 Revolver `(1.15, 1.05, 0.20, 0.30, 0.66, 1.00)`
  - 2 Pompali `(1.00, 0.95, 0.18, 0.22, 0.88, 0.92)`
  - 3 Tufek `(0.95, 0.90, 0.20, 0.25, 0.92, 0.92)`
  - 4 Nisanci `(0.65, 0.80, 0.16, 0.20, 1.12, 0.88)`
  - 5 Piyade `(0.90, 0.90, 0.18, 0.24, 0.92, 0.92)`
  - 6 .50 Tabanca `(1.65, 1.15, 0.24, 0.28, 0.72, 1.00)`
  - 7 LMG `(0.60, 0.75, 0.15, 0.18, 1.02, 0.90)`
- Bicak rig (hold pos/scale/roll/pivot/hand; inspect pos/iscale):
  - knife `(-0.30,-0.22,0.72) 0.62 0.52 (0,-0.010,-0.130) 0.00` / `(-0.14,-0.03,0.88) 0.62`
  - karambit `(-0.30,-0.23,0.72) 0.55 0.58 (0,-0.030,-0.370) 0.09` / `(-0.12,-0.02,0.92) 0.52`
  - butterfly `(-0.30,-0.22,0.72) 0.62 0.55 (0,-0.005,0.030) 0.01` / `(-0.14,-0.08,0.82) 0.70`
- Kelebek menteşe yayi: k=140, damping=16, clamp `-0.18..1.45`; iki kanat
  ayri yaylarla (`hinge_a`/`hinge_b`) sirayla acilip kapanir. Incelemede
  `inspect_t % 3.6` sirasiyla: 0-0.5 A ac, 0.5-1.0 A kapat, 1.0-1.5 B ac,
  1.5-2.0 B kapat, 2.0-2.4 A hizli ac, 2.4-2.8 A kapat; hedef `1.30`.
- Bicak slash: `_knife_slash_A` bicaga ozel 3B yay (knife chop, karambit genis
  kavis, butterfly flip); `_slash_offset` govdeyi ekranda kaydirir, 3 ornekli
  hayalet iz cizilir.
- Viewmodel isigi (LIT `vm=1`): L `(0.32,0.58,-0.75)`, ambient x1.25,
  diff x0.68, spec x0.55, fog x0.15.

## Kurallar

- `main.py` sadece baslatir; is mantigi burada tutulmaz.
- God dosya yasaktir; her modul tek bir sorumluluk tasir.
- Yeni ozellik, ait oldugu modulde gelistirilir; mevcut dosyalar sismez.
- Bu dosya (`opencode.md`) her yapisal degisiklikte guncellenir.
- Ayrintili kurallar icin `RULE.md` dosyasina bak.
