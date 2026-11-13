# opencode.md

HEX ARENA: pyray (raylib) ile yazilmis, moduler yapida ozel macli bomba modu FPS oyunu.
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
| `state.py` | Tum calisma zamani durumunu tutan tek global `g` nesnesi (takim skorlari, bomba, efektler, yere dusen silahlar, asist gostergesi, harita havuzu secimi: `map_pick`/`map_name`, yari/taraf: `half`/`side_t`, magaza sekmesi: `shop_tab`, ozel mac ayarlari: `ally_bots`/`enemy_bots`/`target`, `rt`/`vmrt` render texture'lari). |
| `weapons.py` | 8 silahin tanimi, isimleri, slot eslemesi ve 5 bot zorluk parametresi (Kolay..Imkansiz). |
| `modes.py` | Mac turu on ayarlari: Dereceli (12) ve Tam Gaz (5); tur hedefi ayrica 1-30 arasi ayarlanabilir. |
| `characters.py` | `Character`/`Skill` siniflari ve 4 karakter (HEX, ZEPHYR, NYX, TITAN). |
| `world.py` | 84x84'luk, 180 derece simetrik 3 haritalik havuz (HEX Bolgesi, Sarnic, Kule): odali duvar izgarasi, spawnlar, A/B bolgeleri, callout bolgeleri, harita basina duvar/zemin/kapak renkleri ve vurgu paleti (`THEME`), bot yol agi. `select_map` secili haritayi ve temayi yerinde yukler. |
| `physics.py` | Ray-cast, gorunurluk, carpisma itmesi ve yer cekimi fizigi. |
| `fighter.py` | `F` savasci sinifi (takim, bot ekonomisi, bomba tasiyici, bicak alanlari dahil). |
| `combat.py` | Ates, hasar, oldurme, killfeed ve alt kill gostergesi; asist takibi (hasar veren yardimcilar); dost atesi yok; bomba dusurme; olumde silah dusurme ve envanter sifirlama; bot oldurme odulu. |
| `AI.py` | Takim bilincli bot AI: bot basina zorluk (`f.diff`) ile ekonomi ve tur basi silah satin alma, A/B site push, yerdeki spike'i alma, bomba kurma, defuse, hedef onceliklendirme (bomba tasiyici/defuser/dusuk HP), nisan, strafe, burst ates, yere dusen silahi (daha iyiyse veya bot isterse) alma; hedefsiz kalan botlar kisa yan hareketler/tarama ile AFK kalmaz, takilinca guclu kurtarma uygular. |
| `bomb.py` | Spike yerde baslar; botlar yakinda otomatik alir, oyuncu `F` ile alir; kurma/defuse, 30 saniyelik timer ve patlama durumu. |
| `knives.py` | Karambit/kelebek/bicak 3B modelleri, menteşe etiketleri (`hA`/`hB`), yakin dovus ve yedek 2B ikonlar. |
| `icons.py` | Silah/bicak modellerini ayri sahnede yandan cekip PNG kaydeder ve markete/kill gostergesine verir; PNG'leri Python ile okuyup bellekten yukler (Turkce karakterli yol sorunu) ve yedek 2B ikona dusebilir. |
| `weapon_icons.py` | Ikon uretilemezse kullanilan yedek 2B silah cizimleri. |
| `shaders.py` | Aydinlatma ve post-process GLSL kaynaklari. |
| `viewmodel.py` | Birinci sahis silah modeli geometrisi (8 silah) ve ates edince oynayan parca etiketleri (`slide`/`bolt`/`pump`/`hammer`). |
| `skins.py` | Silah/bicak kaplama tanimlari ve fiyatlari, parca renk paletleri, shader modu, muzzle/tracer/impact renkleri, Python ile uretilen prosedurel magaza dokulari (`init_textures`/`draw_swatch`). |
| `render.py` | Fontu bellekten yukleme (Turkce yol sorunu), kameralar, harita temasi (`THEME`) ile sinir/site renkleri, harita/site/bomba cizimi, parlayan yere dusen silah isaretleri, sert govdeli silah/bicak viewmodel'i, kaplama shader'i, Void silahlarda yogun partikullu inceleme firtinasi, dinamik iki kemikli kollar, ayri `vmrt` kompoziti, bicaga ozel slash yayi/iz ve zengin inceleme VFX'i, spectate viewmodel'i ve post-process. |
| `ui.py` | 2B arayuz yardimcilari: font, metin, buton, slider, toggle, panel. |
| `match.py` | Ozel mac akisi: ayarlanabilir ally/enemy bot sayisi ve tur hedefi, 3 haritalik havuzdan harita secimi, bot becerilerinin takimlara dengeli/rastgele dagitimi, her 11 tamamlanan roundda taraf degisimi (`swap_sides`), roundlar, bomba kosullari, spike'in yerde baslamasi, karakter skilleri, magaza ekonomisi, botlarin tur basi satin almasi, oyuncunun `F` ile spike/yere dusen silahi almasi, kelebek cift mente�Ye yay fizi�Yi; inceleme kapanisinda hizli donus (`inspect_off`/`inspect_out`); olumde once takim arkadasini, yoksa dusmani izletir. |
| `hud.py` | HUD, bomba/spike uyarisi ve yerden alma ipucu, kill gostergesi, crosshair stilleri, asist gostergesi ve skor tablosu, yere dusen silah alma ipucu, taraf/yari gostergesi, 3 slotlu ikonlu market, sekmeli magaza (bicak/silah kaplamasi/bicak kaplamasi), spectate edilen oyuncunun crosshair/scope'u ve menuler; ozel mac kurulum ekrani (bot sayilari, tur slider'i, 5 zorluk, 3 haritalik havuz secimi). |
| `playerdata.py` | `playerdata.json` kalici verisi: souls, MVP, karakter, bicak, silah/bicak kaplama sahipligi ve secimi, crosshair. |
| `playerdata.json` | Oyuncunun kayitli verisi (souls, matches, mvps, secimler). |
| `assets/fonts/` | Projeyle gelen font (Rajdhani); her bilgisayarda calisir. |
| `assets/icons/` | `icons.py` tarafindan uretilen 3B silah/bicak fotograflari (PNG). |

## Bagimlilik Yonu

`main.py -> app.py -> {render, hud, match, icons}`
`match.py -> {AI, bomb, combat, characters, knives, playerdata, physics, world}`
`bomb.py -> world` (A/B site koordinatlari harita havuzundan gelir)
`render.py -> {world, viewmodel, shaders, characters, bomb, knives, ui}`
`hud.py -> {characters, bomb, knives, icons, playerdata, modes, ui}`
`icons.py -> {weapons, viewmodel, knives, shaders, config}`

Not: Kontroller `WASD`, `1` ana silah, `2` tabanca, `3` bicak, `Y` incele, `E` bomba, `F` spike veya yere dusen silahi al, `B` market (sadece tur basi 5 sn); scroll slot degistirir. Ozel macta ally/enemy bot sayisi 0-4/0-5, tur hedefi 1-30, zorluk ve 3 haritalik havuzdan harita (veya rastgele) secilebilir; her 11 tamamlanan roundda taraflar degisir, bot sayisi 0 olan takimda eleme roundu kapatilir.

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
  - knife `(-0.30,-0.22,0.66) 0.62 0.52 (0,-0.010,-0.130) 0.00` / `(-0.14,-0.03,0.84) 0.62`
  - karambit `(-0.30,-0.23,0.66) 0.55 0.58 (0,-0.030,-0.370) 0.09` / `(-0.12,-0.02,0.88) 0.52`
  - butterfly `(-0.30,-0.22,0.66) 0.62 0.55 (0,-0.005,0.030) 0.01` / `(-0.14,-0.08,0.78) 0.70`
- Kelebek menteşe yayi: k=140, damping=16, clamp `-0.18..1.45`; iki kanat
  ayri yaylarla (`hinge_a`/`hinge_b`) sirayla acilip kapanir. Incelemede
  `inspect_t % 3.6` sirasiyla: 0-0.5 A ac, 0.5-1.0 A kapat, 1.0-1.5 B ac,
  1.5-2.0 B kapat, 2.0-2.4 A hizli ac, 2.4-2.8 A kapat; hedef `1.30`.
- Bicak slash: `_knife_slash_A` bicaga ozel 3B yay (knife chop, karambit genis
  kavis, butterfly flip); `_slash_offset` govdeyi ekranda kaydirir, 3 ornekli
  hayalet iz cizilir.
- Viewmodel isigi (LIT `vm=1`): L `(0.32,0.58,-0.75)`, ambient x1.25,
  diff x0.68, spec x0.55, fog x0.15.

## Kaplamalar ve Inceleme VFX

- Kaplamalar `skins.py` icinde tanimlidir; silah secimi global `gun_skin`,
  bicak secimi global `knife_skin` alanlarinda tutulur. Void Seti tum silahlara
  uygulanir; hasar formulu degismez.
- Magazada `BICAKLAR`, `SILAH KAPLAMALARI`, `BICAK KAPLAMALARI` sekmeleri vardir;
  kaplama kartlari Python ile uretilen prosedurel dokuyu (`skins.draw_swatch`)
  gosterir. Doku uretimi `app.main` icinde `skins.init_textures()` ile yapilir.
- `Y` incelemesi yumusak girer; kapatinca `inspect_out` ile 0.22 sn hizli
  geri doner. Ates, reload, silah degistirme ve spike islemleri incelemeyi kapatir.
- Firtina efekti **yalnizca Void Seti + silah viewmodel'i** icin calisir.
  Silah parcalari dagilmaz veya donmez; govde kaplama rengini korur. 92 helix
  partikulu, 28 namlu parcasi ve 18 isik izi additive olarak cizilir.
- Bicak incelemesinde parca firtinasi yoktur; bicak govdesi butun kalir. Karambit
  (ozellikle Void Tasi) 54 parcaya kadar orbit spark, kelebek 30, diger bicaklar
  22 parcaya kadar VFX kullanir; isik izleri ve merkez parlamasi eklenir.
- Silah kaplama shader'i (`skinMode`/`skinA`/`skinB`) govdeye palet deseni verir;
  firtina VFX'i bu renkleri ezmez. Void Seti namlu/tracer/impact efektlerini cyan
  yapar.

## Ozel Mac

- `hud.screen_setup`: ally bot `0-4`, enemy bot `0-5`, tur hedefi `1-30`
  slider'i, 5 zorluk (Kolay, Orta, Zor, Acimasiz, Imkansiz) ve 3 haritalik
  havuz secimi (Rastgele + HEX/Sarnic/Kule).
- `match.start_match` bu degerleri kullanir; `g.target` artik mode tarafindan
  ezilmez. Mode butonlari sadece hazir hedef degeri atar.
- Harita havuzu: secim yoksa mac basinda 3 haritadan biri rastgele yuklenir;
  `world.select_map` geometri, A/B siteleri, spawnlar, yol agi ve renk temasini
  yerinde gunceller (`BOX`/`SITES`/`WPS` referanslari korunur).
- Her 11 tamamlanan rounddan sonra `match.swap_sides` calisir: tum savascilarin
  takim/taraf etiketleri, saldiri/savunma skorlari ve bot/world renkleri
  yer degistirir. `g.round` kazanana bakmadan her round basinda artar; varsayilan
  Dereceli hedefi 12 oldugu icin taraf degisimi mac icinde garanti edilir.
- Spike her round saldiran spawn'inda yerde baslar. Botlar yakina gelince
  otomatik alir; oyuncu `F` ile alir. Bomba tasiyicisi olunce spike yine yere
  duser ve en yakin saldiran bot onu almaya gider.
- Harita temasi: her haritanin kendi zemin/duvar/kapak renkleri ve `THEME`
  vurgu rengi vardir; sinir cizgileri ve site isaretleri harita ile degisir.
- Bot becerileri secilen zorluga gore uretilip takimlara dengeli dagitilir;
  en iyi bot her mac rastgele bir takima dusebilir, boylece oyuncu takimi
  otomatik ustun olmaz.
- Asist: bir dusmani yaralayan ayni takim oyuncusu kill'i almazsa asist alir;
  skor tablosunda/bitis ekraninda gorunur, oyuncu asistinde +100 para gelir.
- Yere dusen silahlar fiyat sinifina gore parlar; oyuncu `F`, botlar yakinlik
  ve istek (`greed`) ile alabilir.
- Hedefsiz ve hareketsiz kalan botlar kisa yan hareket/etrafi tarama yapar;
  takilma algilanirsa yol sifirlanip daha uzun kurtarma manevrasi uygulanir.
- Bot sayisi `0` olan takimda eleme roundu kapatilir; boylece dusmansiz
  custom macta round aninda bitmez.
- Oyuncu olunce `spectate_targets` once canli takim arkadasini, yoksa canli
  dusmani izletir; `g.spec` asla bos kamerada kilitli kalmaz.
- `icons.py` PNG'leri Python ile okuyup `load_image_from_memory` ile yukler;
  `render.py` de Rajdhani fontunu ayni sekilde bellekten yukler; boylece
  Turkce karakterli proje yolu raylib'in `fopen` hatasina takilmaz.

## Kurallar

- `main.py` sadece baslatir; is mantigi burada tutulmaz.
- God dosya yasaktir; her modul tek bir sorumluluk tasir.
- Yeni ozellik, ait oldugu modulde gelistirilir; mevcut dosyalar sismez.
- Bu dosya (`opencode.md`) her yapisal degisiklikte guncellenir.
- Ayrintili kurallar icin `RULE.md` dosyasina bak.
