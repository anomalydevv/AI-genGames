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
| `state.py` | Tum calisma zamani durumunu tutan tek global `g` nesnesi (takim skorlari, bomba, efektler, yere dusen silahlar, asist gostergesi, harita havuzu secimi: `map_pick`/`map_name`, yari/taraf: `half`/`side_t`, magaza sekmesi: `shop_tab`, magaza scroll: `shop_scroll`, ozel mac ayarlari: `ally_bots`/`enemy_bots`/`target`, `rt`/`vmrt` render texture'lari). |
| `weapons.py` | 9 silahin tanimi (yeni: Akrep-9 SMG, 1400$, slot 0), isimleri, slot eslemesi ve 5 bot zorluk parametresi (Kolay..Imkansiz). |
| `modes.py` | Mac turu on ayarlari: Dereceli (12) ve Tam Gaz (5); tur hedefi ayrica 1-30 arasi ayarlanabilir. |
| `characters.py` | `Character`/`Skill` siniflari ve 5 karakter (HEX, ZEPHYR, NYX, TITAN, VOLT). X dalgalari karaktere ozel (Kasirga itme / Golge Ok dar menzil / Sismik Yumruk yakin radial / Zincir Carpma sekme); V dash varyantli (zephyr uzun / nyx ghost'lu / titan hasarli omuz / volt izli); C'de VOLT `overload` (4sn ates hizi); G'de VOLT `ult_storm` (glitch + aura reveal). |
| `world.py` | 84x84'luk, 180 derece simetrik 3 haritalik havuz (HEX Bolgesi, Sarnic, Kule): simetrik CSG duvarlar (orta serit garantili), tutarli callout'lar (Orta/Kuzey/Guney Koridor, A/B Baglanti; `Oda X-Y` yok), simetrik cover, izole waypoint budama + spawn/site yakin nokta garantisi. `select_map` ayni. |
| `csg.py` | Eksen hizali CSG: AABB kutu cikarma (`subtract`, `subtract_all`) ve kapi/pencere kesicileri. Harita duvarlari bu sistemle oyulur; lintel otomatik kalir. |
| `props.py` | Harita esyalari: sandik, varil, kolon, kum torbasi, terminal, boru, isik ve tabela; collide kutular + dekor kutulari uretir. |
| `physics.py` | Ray-cast, gorunurluk, carpisma itmesi ve yer cekimi fizigi. |
| `human.py` | Insan modeli (govde, kask, eklemli kol/bacak, elde silah), yurume/nisan animasyonu ve ragdoll olum pozu; olumde govde devrilir, uzuvlar savrulur ve ~2.6 sn sonra donar. `render` model referanslarini `set_models` ile verir. |
| `fighter.py` | `F` savasci sinifi (takim, bot ekonomisi, bomba tasiyici, bicak alanlari dahil). |
| `combat.py` | Ates, hasar, oldurme, killfeed ve alt kill gostergesi; asist takibi (hasar veren yardimcilar); dost atesi yok; bomba dusurme; olumde silah dusurme ve envanter sifirlama; bot oldurme odulu. |
| `AI.py` | Takim bilincli bot AI: ekonomi/satin alma, A/B push, spike alma/kurma/defuse, hedef oncelik, nisan/strafe/burst, drop alma, AFK onleme; + eskort (tasiyiciya 5.5m geriden dagilma), retake disiplini (daginksa bekle, sure<8sn rush), savunma spike dusmusse kayma, yakin mesafe bicak bitirme (<2.4m `try_slash`). |
| `bomb.py` | Spike yerde baslar; botlar yakinda otomatik alir, oyuncu `F` ile alir; kurma/defuse, 30 saniyelik timer ve patlama durumu. |
| `knives.py` | Karambit/kelebek/bicak 3B modelleri, menteşe etiketleri (`hA`/`hB`), yakin dovus ve yedek 2B ikonlar. |
| `icons.py` | Silah/bicak modellerini ayri sahnede yandan cekip PNG kaydeder ve markete/kill gostergesine verir; PNG'leri Python ile okuyup bellekten yukler (Turkce karakterli yol sorunu) ve yedek 2B ikona dusebilir. |
| `weapon_icons.py` | Ikon uretilemezse kullanilan yedek 2B silah cizimleri. |
| `shaders.py` | Aydinlatma ve post-process GLSL kaynaklari. |
| `viewmodel.py` | Birinci sahis silah modeli geometrisi (9 silah; Akrep-9 susturuculu/tamburlu) ve ates/inceleme parca etiketleri (`slide`/`bolt`/`pump`/`hammer`/`cyl`; revolver topu `cyl`). |
| `skins.py` | Silah/bicak kaplama tanimlari ve fiyatlari, parca renk paletleri, shader modu (0-13: tiger, void, neon, crimson, glacier, ember, aurora, galaxy, hextech, obsidian, frostbite, bloodmoon, cyberwave), muzzle/tracer/impact renkleri, Python ile uretilen prosedurel magaza dokulari (`init_textures`/`draw_swatch`). |
| `render.py` | Fontu bellekten yukleme (Turkce yol sorunu), kameralar, harita temasi (`THEME`) ile sinir/site renkleri, harita/site/bomba cizimi, parlayan yere dusen silah isaretleri, sert govdeli silah/bicak viewmodel'i, kaplama shader'i, Void silahlarda yogun partikullu inceleme firtinasi, dinamik iki kemikli kollar, ayri `vmrt` kompoziti, bicaga ozel slash yayi/iz ve zengin inceleme VFX'i, Void Tasi bicakta gruplu atom yorungesi/parcalanma, skinsiz bicakta hizlanan donus + uc dumani, spectate viewmodel'i ve post-process. |
| `menu.py` | Ana menu: editoryal/askeri minimal duzen, sol ray, dev tipografi, tek beyaz secim cubugu, topografya cizgileri ve canli kelebek animasyonlari. |
| `killfx.py` | Kill hype arayuzu: sagdan kayarak giren "ELIMINATED" banner'i, seri gostergesi ve her kill'de kucuk ekran efekti (kenar isigi, halka, seri yazisi). |
| `ui.py` | 2B UI: duz/editoryal askeri stil; beyaz sac teli cerceveler, tek asit vurgu, fare altinda beyaz parlama (`cursor_glow`), acili kose detaylari. Buton/slider/toggle/panel tum ekranlarda bu dili kullanir. |
| `match.py` | Ozel mac akisi: ayarlanabilir ally/enemy bot sayisi ve tur hedefi, 3 haritalik havuzdan harita secimi, bot becerilerinin takimlara dengeli/rastgele dagitimi, her 11 tamamlanan roundda taraf degisimi (`swap_sides`), roundlar, bomba kosullari, spike'in yerde baslamasi, karakter skilleri, magaza ekonomisi, botlarin tur basi satin almasi, oyuncunun `F` ile spike/yere dusen silahi almasi, kelebek cift mente�Ye yay fizi�Yi; inceleme kapanisinda hizli donus (`inspect_off`/`inspect_out`); olumde once takim arkadasini, yoksa dusmani izletir. |
| `hud.py` | HUD, bomba/spike uyarisi ve yerden alma ipucu, kill gostergesi, crosshair stilleri, asist gostergesi ve skor tablosu, yere dusen silah alma ipucu, taraf/yari gostergesi, 3 slotlu ikonlu market, sekmeli magaza (bicak/silah kaplamasi/bicak kaplamasi), spectate edilen oyuncunun crosshair/scope'u ve menuler; ozel mac kurulum ekrani (bot sayilari, tur slider'i, 5 zorluk, 3 haritalik havuz secimi). |
| `playerdata.py` | `playerdata.json` kalici verisi: souls, MVP, karakter, bicak, silah/bicak kaplama sahipligi ve secimi, crosshair. |
| `playerdata.json` | Oyuncunun kayitli verisi (souls, matches, mvps, secimler). |
| `assets/fonts/` | Projeyle gelen font (Rajdhani); her bilgisayarda calisir. |
| `assets/icons/` | `icons.py` tarafindan uretilen 3B silah/bicak fotograflari (PNG). |
| `slenderman/main.py` | Bagimsiz PS1-tarzi Slenderman oyunu: 8 kagit, pil/kulube gunlugu/kamp-atesi/araba-bagaji etkilesimi, korkuyla cogalan dokunacli parlayan slender modeli, ateste guvenli alan. |
| `opencode-tasinabilir/` | Adminsiz portable opencode paketi: `run.bat` (indir+baslat), `kur.ps1`, `coz.bat`/`coz.ps1` (parolayla `apikey.enc` cozer, parola repoda yok), sade `opencode.json`, `AGENTS.md`, `skills/`. |

## Bagimlilik Yonu

`main.py -> app.py -> {render, hud, match, icons, menu}`
`match.py -> {AI, bomb, combat, characters, knives, playerdata, physics, world}`
`bomb.py -> world` (A/B site koordinatlari harita havuzundan gelir)
`world.py -> {csg, props}`
`render.py -> {human, world, viewmodel, shaders, characters, bomb, knives, KnivesAnim, skins, ui}`
`human.py -> {config, state}` (model referanslari `set_models` ile enjekte edilir)
`hud.py -> {characters, bomb, knives, icons, killfx, playerdata, modes, ui}`
`killfx.py -> {icons, ui}`
`menu.py -> {characters, knives, playerdata, skins, ui}`
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
  - knife `(-0.30,-0.22,0.66) 0.62 0.52 (0,-0.010,-0.130) 0.18` / `(-0.14,-0.03,0.84) 0.62`
  - karambit `(-0.20,-0.10,0.58) 0.54 -0.42 (0,-0.030,-0.370) 0.24` / `(-0.08,0.02,0.80) 0.55` (ters tutus rx0.62 + ry-0.08; slash bilek-flick, tam tur yok)
    (index finger ring icinden gecer; govde `_rx(0.55)` ile ters tutus, uc asagi)
  - butterfly `(-0.30,-0.22,0.66) 0.62 0.55 (0,-0.005,0.030) 0.16` / `(-0.14,-0.08,0.78) 0.70`
- Revolver inceleme: `cyl` etiketli top 2.6sn dongude disari acilir, ~20 rad
  hizli doner, kapanir (`render._revolver_cyl`); derinlik testi acik kalir.
- Kelebek menteşe yayi: k=220, damping=16, clamp `-0.18..1.45`; iki kanat
  ayri yaylarla (`hinge_a`/`hinge_b`) sirayla acilip kapanir. Incelemede
  `inspect_t % 3.6` icinde 14 adimli koreografi (tek kanat fiskeleri, cift
  kanat acilimi, hizli cirpinti, toparlanma) ve 26/31 Hz mikro cirpinti uygulanir.
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
- **Void Tasi bicak**: `group_shatter` once `_connected_groups` ile temas eden
  parcalari birlestirir (AABB komsuluk), sonra govde boyunca 4 kirilma hattinda
  4-6 buyuk gruba ayirir; tek tek toz olmaz, bagli parcalar birlikte hareket eder.
  Her grup elin ustunde atomik yorungede doner (`draw_atom_trails` elektron/proton
  izleri ve parlamalar cizer), `draw_void_shatter_fx` mor hacimsel sis, yukselen
  kor parcaciklari ve isik huzmeleri ekler; yuzey shader'inda `skinMode=2` icin
  nabiz atan fresnel emissive isik vardir.
- **Skinsiz bicaklar**: `Y` incelemesinde `spin_state` ile donus yavasca baslar
  ve ~2.4 sn'de tam hiza cikar; hiz %50'yi gecince `draw_tip_smoke` bicak ucundan
  bicagin renginde duman ve isik cekirdegi cikarir.
- Magaza gridlerinde tekerlek ile satir bazli scroll vardir (`g.shop_scroll`);
  sagda konum cubugu cizilir, sekmeler arasi geciste sifirlanir.
- Silah kaplama shader'i (`skinMode`/`skinA`/`skinB`/`time`) govdeye palet deseni
  verir; her kaplamanin kendi modu (0-13) ve paleti vardir. Void Seti
  namlu/tracer/impact efektlerini cyan yapar.
- Kill heyecani (sessiz, ses yok): `killfx.py` sagdan kayan `ELIMINATED` banner'i, kalin cift katman kenar, cift halka, zoomlu `xN`/KAFA VURUSU/BICAKLA ALDIN/DEVAM ET yazilari; ulti sirasinda dusmanlarda depth-testli simetrik kirmizi glow (`render._draw_enemy_aura`: 3 halka + cift ku re; duvar arkasi sizmaz, kutu/wire yok); fullscreen `update_view` tam piksel + `play_camera` gercek aspect + letterbox siyahlama ile kayma onlenir.

## Harita, Esyalar ve Karakter

- Duvarlar `wall_x`/`wall_z` icinde once dolu kutu olarak kurulur; kapi ve bazi
  pencereler `csg.subtract` ile oyulur. Boylece kapi ustlerinde gercek lintel
  kalir, duvar parcalari arasinda seam olusmaz.
- Odalarda `props.py` ile sandik kumesi, varil, kum torbasi, kolon, terminal,
  boru, isik ve tabela uretilir; collide olanlar `BOX`, dekor olanlar `DECOR`
  listesine gider ve `render.draw_env` ikisini de cizer.
- Zemin derz izgarasi ve vurgu seritleri render tarafinda cizilir; yuzeylerde
  `pattern` prosedurel malzeme shader'i calisir.
- Insan modeli `human.py`: pelvis/gogus/kask, eklemli kol-bacak, elde silah.
  Canliyken yurume, kosma, nisan ve sallanma animasyonu; olumde ragdoll: govde
  secilen eksende devrilir, uzuvlar sonumlu savrulur, 2.6 sn sonra donar.
- Bicak elde tutusu: palm hizada, dort parmak iki eklemli, bas parmak kavrar;
  karambitte index parmak ringin icinden gecer, kalan parmaklar sapi sarar.

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
- Bot silah zekasi: `bot_buy` rol (sniper/entry/rifle), takim sniper sayisi ve
  zirh butcesine gore satin alir; `_weapon_score`/`_switch_weapon` mesafeye,
  mermiye ve silah tipine gore sahip olunan en iyi silaha gecirir; `_pickup`
  sadece anlamli yukseltme veya mermi doldurma icin yerdeki silahi alir.
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
