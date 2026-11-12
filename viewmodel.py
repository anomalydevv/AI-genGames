# -*- coding: utf-8 -*-
"""Birinci sahis silah modeli (viewmodel) geometrisi ve renkleri. (v2 - detayli)

Arayuz ayni kalir:
    VM[silah_id] = ([parcalar...], (muzzle_x, muzzle_y, muzzle_z))
    parca = (x, y, z, sx, sy, sz, renk)  veya  (x, y, z, sx, sy, sz, renk, "etiket")
    etiketler: "slide", "hammer", "pump" (animasyon icin)

Her parca merkez-tabanli bir kutudur. Bu surumde:
  * Havada kalan / birbirine degmeyen parcalar baglandi (govde-kundak, sarjor-govde,
    ammo kutusu-besleme yolu, gaz borusu-namlu vb.)
  * Kundaklar ve kavisli sarjorler dilimlerle egimli/kavisli yapildi.
  * Namlu, silindir, durbun gibi yuvarlak parcalar "_round" ile sekiz kenarli yapildi.
  * Tetik koruyuculari kapali halka seklinde, nisangahlar ayri taban + arpacik olarak yapildi.
Eller, kollar ve namlu agzi noktalari orijinaldekiyle birebir aynidir.
"""
import math
from config import C

# --- orijinal renkler (diger moduller kullaniyor olabilir) -------------------
METAL, LMETAL, WOOD = C(44, 47, 54), C(112, 118, 130), C(105, 68, 38)
GLOVE, SLEEVE, ACC = C(24, 24, 28), C(30, 95, 125), C(0, 230, 200)

# --- detay renkleri -----------------------------------------------------------
DARK = C(18, 19, 24)          # girintiler, pencereler, kabartma arasi
STEEL = C(150, 156, 168)      # civata, pim, parlak metal
WOOD_D = C(72, 45, 25)        # koyu agac damari
WOOD_L = C(132, 88, 50)       # acik agac panel
BRASS = C(205, 160, 62)       # mermi / kemer baglantisi
LENS = C(60, 120, 255)        # durbun camlari

ARM_R = (0.05, -0.15, -0.22, 0.075, 0.075, 0.5, SLEEVE)
ARM_L = (-0.09, -0.16, -0.08, 0.07, 0.07, 0.45, SLEEVE)


# =============================================================================
#  Yardimcilar
# =============================================================================
def _b(x, y, z, sx, sy, sz, c, tag=None):
    """Tek kutu (etiket varsa 8'li tuple)."""
    return (x, y, z, sx, sy, sz, c) if tag is None else (x, y, z, sx, sy, sz, c, tag)


def _m(x, y, z, sx, sy, sz, c, tag=None):
    """X ekseninde simetrik iki kutu (+x ve -x)."""
    return [_b(x, y, z, sx, sy, sz, c, tag), _b(-x, y, z, sx, sy, sz, c, tag)]


def _round(x, y, z, d, l, c, tag=None):
    """Yuvarlak govde (z ekseninde uzanan): 3 kutuyla sekiz kenarli kesit."""
    return [
        _b(x, y, z, d, d * 0.70, l, c, tag),
        _b(x, y, z, d * 0.70, d, l, c, tag),
        _b(x, y, z, d * 0.88, d * 0.88, l, c, tag),
    ]


def _guard(y_bot, z_back, z_front, y_top, c=METAL):
    """Kapali tetik koruyucu: alt cubuk + on ve arka dikme."""
    zc = (z_back + z_front) / 2.0
    h = y_top - y_bot
    return [
        _b(0, y_bot, zc, 0.010, 0.008, z_front - z_back + 0.008, c),
        _b(0, y_bot + h / 2.0, z_front, 0.010, h, 0.008, c),
        _b(0, y_bot + h / 2.0, z_back, 0.010, h, 0.008, c),
    ]


# =============================================================================
#  0 - TABANCA (kizak animasyonlu)
# =============================================================================
def _pistol():
    S = "slide"
    p = [
        # kizak ana govde + ust duz + atis penceresi
        _b(0, 0.0, 0.16, 0.05, 0.055, 0.30, METAL, S),
        _b(0, 0.0305, 0.16, 0.016, 0.006, 0.26, LMETAL, S),
        _b(0, 0.010, 0.12, 0.052, 0.020, 0.05, DARK, S),
        # on yuz plakasi
        _b(0, 0.0, 0.3085, 0.046, 0.050, 0.004, LMETAL, S),
    ]
    p += _m(0.0255, -0.017, 0.16, 0.002, 0.006, 0.28, LMETAL, S)          # alt kenar cizgisi
    p += _m(0.0255, 0.022, 0.16, 0.002, 0.004, 0.28, DARK, S)             # ust kenar cizgisi
    p += [_b(0, 0.0, 0.040 + i * 0.011, 0.053, 0.046, 0.004, DARK, S) for i in range(4)]   # arka tirtik
    p += [_b(0, 0.0, 0.235 + i * 0.011, 0.053, 0.046, 0.004, DARK, S) for i in range(3)]   # on tirtik
    # arka nisangah: taban + iki direk (noktali)
    p += [_b(0, 0.0345, 0.03, 0.026, 0.008, 0.022, METAL, S)]
    p += _m(0.0095, 0.0425, 0.03, 0.008, 0.008, 0.018, ACC, S)
    # on nisangah
    p += [_b(0, 0.0335, 0.30, 0.012, 0.008, 0.022, METAL, S),
          _b(0, 0.0405, 0.30, 0.006, 0.008, 0.008, ACC, S)]

    p += [
        # namlu agzi + burc
        _b(0, 0.0, 0.322, 0.014, 0.014, 0.026, DARK),
        _b(0, 0.0, 0.314, 0.024, 0.024, 0.012, LMETAL),
        # horoz ve kuyruk (kizagin arkasinda)
        _b(0, 0.016, 0.006, 0.010, 0.018, 0.016, LMETAL),
        # govde (frame) + kuyruk kisaltmasi
        _b(0, -0.030, 0.17, 0.040, 0.026, 0.30, LMETAL),
        _b(0, -0.012, 0.022, 0.032, 0.018, 0.040, METAL),
        # fener / lazer modulu
        _b(0, -0.050, 0.265, 0.036, 0.018, 0.07, DARK),
        _b(0, -0.050, 0.302, 0.020, 0.010, 0.004, ACC),
        _b(0, -0.050, 0.240, 0.038, 0.004, 0.010, LMETAL),
        # tetik
        _b(0, -0.054, 0.112, 0.008, 0.026, 0.008, LMETAL),
    ]
    p += [_b(0.0202, -0.032, 0.21 + i * 0.022, 0.002, 0.012, 0.008, DARK) for i in range(3)]
    p += [_b(-0.0202, -0.032, 0.21 + i * 0.022, 0.002, 0.012, 0.008, DARK) for i in range(3)]
    # tetik koruyucu (kapali halka)
    p += _guard(-0.0715, 0.078, 0.148, -0.036)
    # kabza: hafif egimli dilimler
    for i in range(5):
        p.append(_b(0, -0.050 - i * 0.020, 0.050 - i * 0.004, 0.045, 0.026, 0.06,
                    METAL if i % 2 == 0 else LMETAL))
    p += [
        _b(0, -0.148, 0.034, 0.048, 0.012, 0.07, LMETAL),                 # sarjor tabani
        _b(0, -0.122, 0.0795, 0.010, 0.07, 0.004, DARK),                  # sarjor on cizgisi
        _b(0.0, -0.07, 0.045, 0.07, 0.10, 0.085, GLOVE),
        _b(-0.04, -0.075, 0.07, 0.06, 0.06, 0.07, GLOVE),
        ARM_R, ARM_L,
    ]
    return p


# =============================================================================
#  1 - REVOLVER (horoz animasyonlu)
# =============================================================================
def _revolver():
    H = "hammer"
    p = [
        # govde
        _b(0, 0.0, 0.05, 0.05, 0.075, 0.14, METAL),
        # ust kayis (silindirin ustunden namluya uzanir) + arka nisangah
        _b(0, 0.0415, 0.085, 0.034, 0.010, 0.17, METAL),
        _b(0, 0.0495, 0.002, 0.030, 0.008, 0.016, DARK),
    ]
    p += _m(0.0115, 0.0525, 0.002, 0.008, 0.012, 0.016, METAL)
    # silindir (sekiz kenarli) + olukler + on/arka halka
    p += _round(0, 0.0, 0.095, 0.066, 0.075, LMETAL)
    p += [_b(0, 0.0, z, 0.0705, 0.044, 0.004, DARK) for z in (0.078, 0.095, 0.112)]
    p += _m(0.0375, 0.0, 0.095, 0.002, 0.02, 0.016, DARK)
    p += [_b(0, 0.0, 0.1335, 0.050, 0.050, 0.004, METAL),
          _b(0, 0.0, 0.0555, 0.050, 0.050, 0.004, METAL)]
    p += [
        # namlu alt kutugu (govdeye baglanir) + namlu + ejektor + ust ray
        _b(0, 0.006, 0.17, 0.034, 0.032, 0.10, METAL),
        _b(0, 0.028, 0.235, 0.032, 0.034, 0.31, LMETAL),
        _b(0, 0.0, 0.22, 0.026, 0.03, 0.20, METAL),
        _b(0, 0.0505, 0.215, 0.014, 0.008, 0.28, METAL),
        # aksan seridi
        _b(0, 0.028, 0.20, 0.036, 0.006, 0.18, ACC),
        # on nisangah ve namlu agzi tacı
        _b(0, 0.056, 0.375, 0.008, 0.016, 0.014, ACC),
        _b(0, 0.028, 0.392, 0.040, 0.040, 0.016, DARK),
        # horoz: govde + mahmuz (hepsi "hammer")
        _b(0, 0.045, 0.01, 0.02, 0.035, 0.06, METAL, H),
        _b(0, 0.058, -0.028, 0.016, 0.012, 0.022, LMETAL, H),
        _b(0, 0.050, -0.026, 0.018, 0.004, 0.018, DARK, H),
        # tetik koruyucu (halka) + tetik
        _b(0, -0.066, 0.055, 0.012, 0.008, 0.075, METAL),
        _b(0, -0.050, 0.0875, 0.012, 0.032, 0.010, METAL),
        _b(0, -0.050, 0.025, 0.012, 0.030, 0.010, METAL),
        _b(0, -0.050, 0.050, 0.008, 0.022, 0.008, LMETAL),
        # agac kabza + yan paneller + arka siper + civata + taban
        _b(0, -0.07, 0.0, 0.045, 0.12, 0.06, WOOD),
        _b(0, -0.07, 0.003, 0.050, 0.10, 0.045, WOOD_L),
        _b(0, -0.07, -0.036, 0.030, 0.12, 0.012, METAL),
        _b(0, -0.055, 0.003, 0.054, 0.008, 0.008, STEEL),
        _b(0, -0.1345, -0.010, 0.052, 0.012, 0.070, METAL),
        _b(0.0, -0.07, 0.0, 0.07, 0.10, 0.085, GLOVE),
        _b(-0.04, -0.07, 0.04, 0.06, 0.06, 0.07, GLOVE),
        ARM_R, ARM_L,
    ]
    return p


# =============================================================================
#  2 - POMPALI (pump animasyonlu)
# =============================================================================
def _shotgun():
    P = "pump"
    p = []
    # namlu (sekiz kenarli) + ust ray + boncuk + choke
    p += _round(0, 0.02, 0.32, 0.042, 0.65, METAL)
    p += [
        _b(0, 0.0435, 0.32, 0.014, 0.006, 0.60, LMETAL),
        _b(0, 0.051, 0.635, 0.008, 0.012, 0.008, ACC),
        _b(0, 0.02, 0.64, 0.048, 0.048, 0.02, LMETAL),
        _b(0, 0.02, 0.649, 0.030, 0.030, 0.004, DARK),
    ]
    # sarjor tupu (sekiz kenarli) + uc kapagi + iki kelepce
    p += _round(0, -0.015, 0.30, 0.036, 0.55, LMETAL)
    p += [
        _b(0, -0.015, 0.58, 0.042, 0.036, 0.012, METAL),
        _b(0, 0.003, 0.50, 0.046, 0.074, 0.015, METAL),
        _b(0, 0.003, 0.36, 0.046, 0.074, 0.012, METAL),
    ]
    p += [
        # govde: ana kutu, arka tang, atis penceresi, yukleme agzi, aksan seridi
        _b(0, 0.0, 0.0, 0.06, 0.075, 0.22, METAL),
        _b(0, 0.0, -0.125, 0.05, 0.07, 0.03, METAL),
        _b(0, 0.012, 0.05, 0.062, 0.028, 0.08, DARK),
        _b(0, -0.0375, 0.0, 0.03, 0.004, 0.06, DARK),
        _b(0.036, 0.010, 0.03, 0.014, 0.014, 0.04, LMETAL),
        _b(0, 0.0385, 0.0, 0.02, 0.004, 0.12, ACC),
        _b(0, 0.0395, -0.08, 0.016, 0.006, 0.03, DARK),
    ]
    # kundak: dilimlerle egimli (govdeden topuga dogru kalinlasir)
    n = 7
    last = None
    for i in range(n):
        z = -0.145 - i * 0.0345
        top = 0.022 - i * 0.004
        bot = -0.062 - i * 0.012
        yc, h = (top + bot) / 2.0, top - bot
        p.append(_b(0, yc, z, 0.044 + i * 0.001, h, 0.036, WOOD))
        last = (z, yc, h)
    p += _m(0.0255, -0.02, -0.25, 0.002, 0.006, 0.20, WOOD_D)
    p += _m(0.0255, -0.05, -0.27, 0.002, 0.006, 0.16, WOOD_D)
    p.append(_b(0, last[1], last[0] - 0.026, 0.052, last[2] + 0.004, 0.014, DARK))   # lastik tampon
    p += [_b(0, -0.063, -0.18, 0.040, 0.004, 0.12, WOOD_D)]
    # tetik koruyucu + tetik
    p += _guard(-0.0565, -0.012, 0.072, -0.036)
    p += [_b(0, -0.044, 0.022, 0.008, 0.016, 0.008, LMETAL)]
    # pompa (hepsi "pump"): ana govde, oluklar, uc kapaklari, aksiyon kollari
    p += [
        _b(0, -0.04, 0.28, 0.07, 0.05, 0.16, WOOD, P),
        _b(0, -0.04, 0.195, 0.066, 0.046, 0.012, METAL, P),
        _b(0, -0.04, 0.365, 0.066, 0.046, 0.012, METAL, P),
    ]
    p += [_b(0, -0.04, 0.225 + i * 0.036, 0.072, 0.052, 0.006, WOOD_D, P) for i in range(4)]
    p += _m(0.026, -0.032, 0.15, 0.008, 0.010, 0.12, LMETAL, P)
    p += [
        _b(0.0, -0.075, -0.04, 0.07, 0.10, 0.09, GLOVE),
        _b(-0.0, -0.06, 0.28, 0.075, 0.07, 0.10, GLOVE),
        ARM_R, ARM_L,
    ]
    return p


# =============================================================================
#  3 - ASSAULT RIFLE (AR tarzi, kirmizi nokta nisangah)
# =============================================================================
def _ar():
    p = [
        # ust / alt govde
        _b(0, 0.015, 0.05, 0.058, 0.05, 0.45, METAL),
        _b(0, -0.0275, 0.04, 0.06, 0.035, 0.38, LMETAL),
        # atis penceresi + toz kapagi + ileri itme dugmesi
        _b(0.031, 0.02, 0.07, 0.004, 0.022, 0.06, DARK),
        _b(0.0305, 0.022, 0.01, 0.004, 0.020, 0.05, METAL),
        _b(0.034, 0.005, -0.02, 0.012, 0.012, 0.012, LMETAL),
        # sarj kolu
        _b(0, 0.045, -0.16, 0.03, 0.014, 0.03, LMETAL),
        _b(0, 0.040, -0.145, 0.040, 0.008, 0.012, DARK),
        # ust ray
        _b(0, 0.043, 0.10, 0.026, 0.008, 0.46, LMETAL),
    ]
    p += [_b(0, 0.0485, -0.10 + i * 0.04, 0.028, 0.004, 0.012, DARK) for i in range(13)]  # ray disleri
    # kirmizi nokta nisangah: taban + acik cerceve + cam
    p += [_b(0, 0.0545, 0.05, 0.036, 0.008, 0.12, DARK)]
    p += _m(0.016, 0.068, 0.05, 0.004, 0.026, 0.12, DARK)
    p += [
        _b(0, 0.0825, 0.05, 0.036, 0.004, 0.12, DARK),
        _b(0, 0.068, -0.005, 0.036, 0.026, 0.010, DARK),
        _b(0, 0.068, 0.102, 0.028, 0.024, 0.004, ACC),
        _b(0, 0.0685, 0.03, 0.004, 0.004, 0.004, ACC),
    ]
    # el koruma + havalandirma + ust/alt ray + uc kapagi
    p += [
        _b(0, -0.005, 0.33, 0.065, 0.07, 0.28, LMETAL),
        _b(0, 0.026, 0.33, 0.067, 0.005, 0.26, ACC),
        _b(0, -0.042, 0.33, 0.030, 0.008, 0.26, METAL),
        _b(0, -0.005, 0.472, 0.070, 0.075, 0.012, DARK),
    ]
    p += [_b(0, -0.005, 0.23 + i * 0.045, 0.067, 0.02, 0.02, DARK) for i in range(5)]
    # namlu, gaz blogu, on nisan, alev kesici
    p += _round(0, 0.01, 0.45, 0.032, 0.35, METAL)
    p += [
        _b(0, 0.01, 0.49, 0.04, 0.04, 0.025, LMETAL),
        _b(0, 0.04, 0.49, 0.008, 0.022, 0.008, DARK),
        _b(0, 0.01, 0.61, 0.042, 0.042, 0.06, LMETAL),
        _b(0, 0.01, 0.595, 0.045, 0.02, 0.01, DARK),
        _b(0, 0.01, 0.615, 0.045, 0.02, 0.01, DARK),
        _b(0, 0.01, 0.635, 0.045, 0.02, 0.01, DARK),
    ]
    # tetik koruyucu + tetik + kabza (egimli dilimler)
    p += _guard(-0.062, -0.005, 0.062, -0.040)
    p += [_b(0, -0.050, 0.030, 0.008, 0.020, 0.006, LMETAL)]
    for i in range(3):
        p.append(_b(0, -0.07 - i * 0.03, -0.045 - i * 0.012, 0.04, 0.034, 0.05, METAL))
    p += [_b(0, -0.153, -0.081, 0.042, 0.010, 0.054, DARK)]
    # kavisli sarjor (dilimli) + tabani + aksan bandi
    p += [_b(0, -0.052, 0.098, 0.046, 0.030, 0.082, METAL)]
    for i in range(5):
        p.append(_b(0, -0.080 - i * 0.032, 0.098 + i * i * 0.0035, 0.04, 0.036, 0.07, METAL))
    p += [_b(0, -0.226, 0.154, 0.044, 0.012, 0.074, LMETAL)]
    p += _m(0.0205, -0.14, 0.108, 0.002, 0.018, 0.05, ACC)
    # kundak: tampon borusu + ayarli kundak + yanak yastigi + tampon
    p += [
        _b(0, 0.008, -0.23, 0.030, 0.030, 0.12, METAL),
        _b(0, -0.015, -0.315, 0.046, 0.075, 0.15, METAL),
        _b(0, 0.031, -0.30, 0.034, 0.012, 0.12, DARK),
        _b(0, -0.022, -0.395, 0.048, 0.092, 0.012, DARK),
        _b(0, -0.0525, -0.28, 0.030, 0.008, 0.08, LMETAL),
    ]
    p += [
        _b(0.0, -0.095, -0.05, 0.07, 0.10, 0.09, GLOVE),
        _b(0.0, -0.06, 0.33, 0.08, 0.075, 0.10, GLOVE),
        ARM_R, ARM_L,
    ]
    return p


# =============================================================================
#  4 - KESKIN NISANCI (durbunlu, civatali)
# =============================================================================
def _sniper():
    p = [
        # govde + ust ray + atis penceresi
        _b(0, 0.0, 0.0, 0.055, 0.075, 0.70, METAL),
        _b(0, 0.042, 0.0, 0.026, 0.008, 0.35, LMETAL),
        _b(0.0285, 0.015, 0.0, 0.004, 0.03, 0.09, DARK),
        # civata arkasi (shroud) + civa kolu (sap + kabarcik)
        _b(0, 0.015, -0.355, 0.034, 0.04, 0.022, DARK),
        _b(0.041, 0.014, -0.10, 0.026, 0.010, 0.010, LMETAL),
        _b(0.060, 0.016, -0.10, 0.016, 0.018, 0.016, DARK),
        # serbest yuzen el koruma
        _b(0, 0.005, 0.55, 0.05, 0.06, 0.40, METAL),
    ]
    p += [_b(0, 0.005, 0.42 + i * 0.06, 0.052, 0.02, 0.03, DARK) for i in range(5)]   # havalandirma
    # namlu + agiz freni
    p += _round(0, 0.012, 0.70, 0.030, 0.55, LMETAL)
    p += [
        _b(0, 0.012, 0.965, 0.04, 0.04, 0.07, DARK),
        _b(0, 0.012, 0.95, 0.044, 0.012, 0.012, METAL),
        _b(0, 0.012, 0.975, 0.044, 0.012, 0.012, METAL),
    ]
    # katlanmis bipod
    p += [_b(0, -0.030, 0.58, 0.040, 0.012, 0.03, METAL)]
    p += _m(0.02, -0.040, 0.65, 0.008, 0.012, 0.14, METAL)
    # durbun: tup + objektif/okuler govdesi + camlar + kulplar + halkalar + gunes siperligi
    p += _round(0, 0.085, 0.05, 0.036, 0.30, METAL)
    p += _round(0, 0.085, 0.17, 0.054, 0.07, DARK)
    p += _round(0, 0.085, -0.085, 0.046, 0.05, DARK)
    p += [
        _b(0, 0.085, 0.208, 0.042, 0.042, 0.004, LENS),
        _b(0, 0.085, -0.112, 0.030, 0.030, 0.003, LENS),
        _b(0, 0.085, 0.222, 0.056, 0.056, 0.020, DARK),            # gunes siperligi
        _b(0, 0.085, 0.0, 0.042, 0.042, 0.012, STEEL),            # yakinlastirma halkasi
        _b(0, 0.113, 0.05, 0.02, 0.02, 0.02, LMETAL),
        _b(0.03, 0.085, 0.05, 0.02, 0.02, 0.02, LMETAL),
        _b(0, 0.0525, -0.02, 0.04, 0.03, 0.02, LMETAL),
        _b(0, 0.0525, 0.12, 0.04, 0.03, 0.02, LMETAL),
    ]
    # kundak: dilimler + yanak yastigi + tampon + govde baglanti parcasi
    p += [_b(0, -0.045, -0.17, 0.048, 0.030, 0.14, WOOD)]
    n = 12
    last = None
    for i in range(n):
        z = -0.26 - i * 0.0225
        top = 0.022
        bot = -0.055 - i * 0.004
        yc, h = (top + bot) / 2.0, top - bot
        p.append(_b(0, yc, z, 0.05, h, 0.026, WOOD))
        last = (z, yc, h)
    p += [
        _b(0, 0.03, -0.42, 0.046, 0.02, 0.16, WOOD_L),
        _b(0, last[1], last[0] - 0.020, 0.052, last[2] + 0.006, 0.014, DARK),
        _b(0, last[1], last[0] - 0.008, 0.044, last[2] - 0.01, 0.010, STEEL),
    ]
    p += _m(0.0255, -0.02, -0.38, 0.002, 0.006, 0.26, WOOD_D)
    # kabza paneli + tetik koruyucu + tetik
    p += [_b(0, -0.085, -0.05, 0.042, 0.09, 0.05, WOOD)]
    p += _guard(-0.062, -0.022, 0.016, -0.036)
    p += [_b(0, -0.050, -0.005, 0.008, 0.020, 0.006, LMETAL)]
    # sarjor + govdeye baglanti + taban
    p += [
        _b(0, -0.045, 0.05, 0.046, 0.016, 0.08, METAL),
        _b(0, -0.09, 0.05, 0.04, 0.10, 0.07, METAL),
        _b(0, -0.145, 0.05, 0.044, 0.01, 0.074, LMETAL),
        _b(0.0, -0.08, -0.05, 0.07, 0.10, 0.09, GLOVE),
        _b(0.0, -0.05, 0.30, 0.08, 0.07, 0.10, GLOVE),
        ARM_R, ARM_L,
    ]
    return p


# =============================================================================
#  5 - KALASH TARZI TUFEK (agac kundak, kavisli sarjor)
# =============================================================================
def _ak():
    p = [
        # govde + toz kapagi (nervurlu) + aksan seridi
        _b(0, 0.02, 0.04, 0.045, 0.05, 0.36, METAL),
        _b(0, 0.058, 0.06, 0.034, 0.022, 0.32, LMETAL),
        _b(0, 0.0715, 0.06, 0.012, 0.003, 0.28, DARK),
        _b(0, 0.0725, 0.06, 0.014, 0.004, 0.20, ACC),
        # atis penceresi + sarj kolu + emniyet kolu
        _b(0.0235, 0.03, 0.05, 0.004, 0.020, 0.07, DARK),
        _b(0.032, 0.035, 0.05, 0.016, 0.012, 0.03, LMETAL),
        _b(0.0235, 0.012, -0.01, 0.004, 0.034, 0.010, LMETAL),
        # on govde bloku (ironsight tabani) + arka nisangah
        _b(0, 0.020, 0.235, 0.05, 0.055, 0.04, METAL),
        _b(0, 0.050, 0.265, 0.026, 0.018, 0.07, METAL),
        _b(0, 0.062, 0.255, 0.020, 0.014, 0.04, LMETAL),
        _b(0, 0.0705, 0.255, 0.006, 0.004, 0.030, DARK),
    ]
    # namlu (sekiz kenarli), gaz boru, gaz blogu, temizleme cubugu
    p += _round(0, 0.02, 0.52, 0.028, 0.60, LMETAL)
    p += [
        _b(0, 0.041, 0.60, 0.020, 0.018, 0.16, LMETAL),
        _b(0, 0.030, 0.70, 0.034, 0.040, 0.04, METAL),
        _b(0, 0.004, 0.62, 0.008, 0.008, 0.24, STEEL),
        # on nisan tabani + arpacik
        _b(0, 0.040, 0.76, 0.030, 0.040, 0.030, METAL),
        _b(0, 0.066, 0.76, 0.008, 0.024, 0.008, ACC),
        # egimli agiz freni + yarik
        _b(0, 0.02, 0.82, 0.036, 0.036, 0.08, LMETAL),
        _b(0, 0.02, 0.805, 0.040, 0.012, 0.010, DARK),
        _b(0, 0.02, 0.83, 0.040, 0.012, 0.010, DARK),
        _b(0, 0.02, 0.855, 0.040, 0.012, 0.010, DARK),
    ]
    # agac el korumalar: ust + alt + demir halka
    p += [
        _b(0, 0.034, 0.41, 0.044, 0.026, 0.22, WOOD),
        _b(0, -0.006, 0.36, 0.05, 0.056, 0.28, WOOD),
        _b(0, -0.006, 0.505, 0.054, 0.060, 0.010, DARK),
        _b(0, -0.0345, 0.36, 0.052, 0.004, 0.28, WOOD_D),
        _b(0, 0.034, 0.41, 0.046, 0.004, 0.22, WOOD_D),
    ]
    p += _m(0.026, -0.006, 0.36, 0.002, 0.006, 0.22, WOOD_D)
    # tetik koruyucu + tetik
    p += _guard(-0.050, -0.040, 0.075, -0.003)
    p += [_b(0, -0.030, 0.035, 0.008, 0.026, 0.006, LMETAL)]
    # tabanca kabzasi (egimli dilimler) + alt govde
    for i in range(4):
        p.append(_b(0, -0.030 - i * 0.022, -0.035 - i * 0.012, 0.042, 0.030, 0.056, WOOD))
    p += [_b(0, -0.118, -0.071, 0.046, 0.008, 0.058, METAL)]
    # kundak: dilimli ve kalinlasan agac + metal tampon
    last = None
    for i in range(6):
        z = -0.17 - i * 0.05
        top = 0.030
        bot = -0.045 - i * 0.012
        yc, h = (top + bot) / 2.0, top - bot
        p.append(_b(0, yc, z, 0.046, h, 0.054, WOOD))
        last = (z, yc, h)
    p += _m(0.0245, -0.01, -0.30, 0.002, 0.006, 0.26, WOOD_D)
    p += [_b(0, last[1], last[0] - 0.030, 0.052, last[2] + 0.006, 0.012, DARK),
          _b(0, last[1], last[0] - 0.020, 0.040, last[2] - 0.010, 0.006, STEEL)]
    # kavisli sarjor: dilimler + kaburga + baglanti + taban
    p += [_b(0, -0.030, 0.12, 0.046, 0.024, 0.085, METAL)]
    for i in range(6):
        p.append(_b(0, -0.050 - i * 0.030, 0.12 + i * i * 0.004, 0.04, 0.034, 0.075, METAL))
        p += _m(0.0205, -0.050 - i * 0.030, 0.12 + i * i * 0.004, 0.002, 0.006, 0.06, LMETAL)
    p += [_b(0, -0.2175, 0.12 + 25 * 0.004, 0.044, 0.012, 0.079, LMETAL)]
    p += [
        _b(0.0, -0.075, -0.04, 0.07, 0.10, 0.09, GLOVE),
        _b(0.0, -0.06, 0.28, 0.08, 0.07, 0.10, GLOVE),
        ARM_R, ARM_L,
    ]
    return p


# =============================================================================
#  6 - SMG / PDW (tel kundak, havalandirmali gomlek, kirmizi nokta)
# =============================================================================
def _smg():
    p = [
        # govde + ust ray + yan kapak
        _b(0, 0.02, 0.18, 0.055, 0.065, 0.42, METAL),
        _b(0, 0.052, 0.18, 0.04, 0.03, 0.38, LMETAL),
        _b(0.0285, 0.03, 0.18, 0.004, 0.025, 0.07, DARK),
        _b(0.0282, 0.02, 0.0, 0.002, 0.040, 0.06, LMETAL),
        _b(0.034, 0.045, 0.02, 0.012, 0.012, 0.030, LMETAL),                 # sarj kolu
        # on alt tutamak govdesi (sol el icin)
        _b(0, -0.020, 0.26, 0.05, 0.03, 0.14, METAL),
        _b(0, -0.0365, 0.26, 0.030, 0.004, 0.12, DARK),
    ]
    p += [_b(0, 0.0705, 0.02 + i * 0.045, 0.03, 0.008, 0.02, LMETAL) for i in range(7)]   # ray disleri
    # kirmizi nokta: acik cerceve + cam + nokta
    p += _m(0.014, 0.087, 0.18, 0.004, 0.025, 0.07, DARK)
    p += [
        _b(0, 0.0745, 0.18, 0.032, 0.006, 0.07, DARK),
        _b(0, 0.1, 0.18, 0.032, 0.004, 0.07, DARK),
        _b(0, 0.087, 0.217, 0.024, 0.020, 0.004, ACC),
        _b(0, 0.087, 0.15, 0.004, 0.004, 0.004, ACC),
        _b(0, 0.068, 0.35, 0.02, 0.012, 0.035, ACC),
    ]
    # namlu + delikli isi kalkani + agiz cihazi + on nisan
    p += _round(0, 0.0, 0.46, 0.032, 0.18, METAL)
    p += _round(0, 0.0, 0.43, 0.046, 0.12, LMETAL)
    p += [_b(0, 0.0, 0.40 + i * 0.03, 0.049, 0.016, 0.010, DARK) for i in range(3)]
    p += [
        _b(0, 0.0, 0.555, 0.034, 0.034, 0.04, DARK),
        _b(0, 0.0, 0.545, 0.038, 0.012, 0.008, METAL),
        _b(0, 0.035, 0.53, 0.008, 0.035, 0.010, METAL),
    ]
    # tel kundak: ust + alt teller + uc dikmeleri + tampon plakasi
    p += _m(0.02, 0.02, -0.145, 0.01, 0.01, 0.23, LMETAL)
    p += _m(0.02, -0.015, -0.145, 0.01, 0.01, 0.23, LMETAL)
    p += _m(0.02, 0.0025, -0.255, 0.01, 0.045, 0.01, LMETAL)
    p += [
        _b(0, 0.02, -0.262, 0.05, 0.06, 0.012, DARK),
        _b(0, 0.02, -0.0, 0.05, 0.04, 0.03, METAL),
    ]
    # tetik koruyucu + tetik
    p += _guard(-0.052, 0.0, 0.10, -0.0125)
    p += [_b(0, -0.035, 0.05, 0.008, 0.024, 0.006, LMETAL)]
    # kabza (sarjor kabzada) + agac panel + taban
    p += [
        _b(0, -0.07, -0.04, 0.05, 0.14, 0.09, METAL),
        _b(0, -0.075, -0.02, 0.052, 0.10, 0.06, WOOD),
        _b(0, -0.075, -0.02, 0.054, 0.004, 0.06, WOOD_D),
        _b(0, -0.143, -0.04, 0.054, 0.012, 0.094, LMETAL),
        _b(0.0, -0.09, -0.05, 0.07, 0.10, 0.09, GLOVE),
        _b(0.0, -0.05, 0.26, 0.08, 0.07, 0.10, GLOVE),
        ARM_R, ARM_L,
    ]
    return p


# =============================================================================
#  7 - MAKINALI TUFEK (kemerli, mermi kutulu, bipodlu)
# =============================================================================
def _lmg():
    p = [
        # on govde + arka govde (kundakla baglanti) + atis penceresi + sarj kolu
        _b(0, 0.03, 0.28, 0.07, 0.095, 0.56, METAL),
        _b(0, 0.02, -0.09, 0.062, 0.08, 0.18, METAL),
        _b(0.0355, 0.04, 0.28, 0.004, 0.04, 0.12, DARK),
        _b(0.045, 0.06, 0.15, 0.03, 0.015, 0.03, LMETAL),
        _b(0, 0.0795, 0.42, 0.02, 0.004, 0.20, ACC),
        _b(0, 0.0675, -0.09, 0.040, 0.008, 0.14, LMETAL),
        # besleme kapagi mandali
        _b(0, 0.0795, 0.22, 0.05, 0.004, 0.06, DARK),
        # tasima sapi (iki ayak + ust cubuk)
        _b(0, 0.095, -0.01, 0.04, 0.036, 0.025, LMETAL),
        _b(0, 0.095, 0.20, 0.04, 0.036, 0.025, LMETAL),
        _b(0, 0.1175, 0.095, 0.05, 0.016, 0.24, LMETAL),
        # arka nisangah
        _b(0, 0.0875, 0.30, 0.020, 0.016, 0.030, METAL),
        _b(0, 0.098, 0.30, 0.006, 0.006, 0.030, DARK),
    ]
    # agir namlu + gaz silindiri + gaz blogu + soguma halkalari + alev kesici
    p += _round(0, 0.02, 0.63, 0.040, 0.34, LMETAL)
    p += [
        _b(0, 0.03, 0.68, 0.03, 0.03, 0.10, METAL),
        _b(0, 0.05, 0.66, 0.02, 0.02, 0.20, LMETAL),
        _b(0, 0.062, 0.745, 0.008, 0.030, 0.012, ACC),               # on nisan
    ]
    p += [_b(0, 0.02, 0.62 + i * 0.04, 0.044, 0.044, 0.012, DARK) for i in range(4)]
    p += _round(0, 0.02, 0.77, 0.052, 0.06, DARK)
    p += [_b(0, 0.02, 0.75, 0.056, 0.012, 0.010, METAL),
          _b(0, 0.02, 0.79, 0.056, 0.012, 0.010, METAL)]
    # el koruma (govdeye ve namluya baglanir) + katlanmis bipod
    p += [
        _b(0, -0.018, 0.48, 0.055, 0.07, 0.36, LMETAL),
        _b(0, -0.018, 0.48, 0.057, 0.008, 0.32, DARK),
        _b(0, -0.060, 0.62, 0.05, 0.02, 0.02, METAL),
    ]
    p += _m(0.02, -0.070, 0.66, 0.008, 0.012, 0.16, METAL)
    # besleme yolu + mermi kutusu + nervurlar + kapak + aksan kayisi
    p += [
        _b(0, -0.035, 0.22, 0.07, 0.04, 0.12, METAL),
        _b(0, -0.13, 0.22, 0.085, 0.17, 0.15, METAL),
        _b(0, -0.046, 0.22, 0.092, 0.010, 0.16, LMETAL),
        _b(0, -0.05, 0.22, 0.09, 0.01, 0.04, ACC),
        _b(0, -0.217, 0.22, 0.090, 0.008, 0.156, DARK),
    ]
    p += [_b(0, y, 0.22, 0.088, 0.008, 0.152, LMETAL) for y in (-0.09, -0.13, -0.17)]
    p += _m(0.0425, -0.13, 0.22, 0.002, 0.14, 0.008, DARK)
    # kemer: pirinc mermi + celik baglanti, kutudan besleme yoluna kavisli
    for i in range(8):
        t = i / 7.0
        x = -(0.040 + 0.035 * math.sin(math.pi * t * 0.9))
        y = -0.035 - 0.115 * t
        if i % 2 == 0:
            p.append(_b(x, y, 0.22, 0.030, 0.012, 0.014, BRASS))
        else:
            p.append(_b(x, y, 0.22, 0.014, 0.012, 0.020, STEEL))
    # tetik koruyucu + tetik + agac kabza (egimli)
    p += _guard(-0.060, -0.060, 0.020, -0.0175)
    p += [_b(0, -0.040, -0.01, 0.008, 0.04, 0.008, LMETAL)]
    for i in range(3):
        p.append(_b(0, -0.050 - i * 0.034, -0.095 - i * 0.010, 0.05, 0.040, 0.11, WOOD))
    p += [_b(0, -0.07, -0.10, 0.052, 0.004, 0.11, WOOD_D)]
    # kundak + yanak + tampon + metal bilezik
    p += [
        _b(0, 0.0, -0.30, 0.06, 0.10, 0.24, METAL),
        _b(0, 0.054, -0.30, 0.04, 0.012, 0.16, DARK),
        _b(0, 0.0, -0.425, 0.062, 0.105, 0.014, DARK),
        _b(0, 0.0, -0.18, 0.064, 0.104, 0.010, LMETAL),
    ]
    p += _m(0.0305, 0.0, -0.30, 0.002, 0.06, 0.18, DARK)
    p += [
        _b(0.0, -0.08, -0.04, 0.07, 0.10, 0.09, GLOVE),
        _b(0.0, -0.06, 0.30, 0.08, 0.07, 0.10, GLOVE),
        ARM_R, ARM_L,
    ]
    return p


# =============================================================================
#  VM SOZLUGU: id -> (parcalar, namlu_agzi)
# =============================================================================
VM = {
    0: (_pistol(), (0, 0.0, 0.33)),
    1: (_revolver(), (0, 0.02, 0.40)),
    2: (_shotgun(), (0, 0.02, 0.66)),
    3: (_ar(), (0, 0.01, 0.64)),
    4: (_sniper(), (0, 0.012, 1.0)),
    5: (_ak(), (0, 0.02, 0.86)),
    6: (_smg(), (0, 0.0, 0.57)),
    7: (_lmg(), (0, 0.02, 0.80)),
}