# -*- coding: utf-8 -*-
"""Bicak tanimlari, 3B modeller, yakin dovus ve 2B yedek ikonlar.

Public arayuz ayni kalir:
    Knife, KNIVES, by_id(kid), model(kid) -> (eksen, [(x, y, z, sx, sy, sz, renk), ...]),
    try_slash(p), draw_knife_icon(kid, x, y, scale)

model(): her parca merkez-tabanli bir kutudur (x, y, z, boyut_x, boyut_y, boyut_z, renk).
Bicak z ekseni boyunca uzanir, bicak kalinligi x'tedir. Parca sayisi artirilarak
kavisli, egimli ve ince detayli bicaklar elde edilir.
"""
import math

from pyray import *

from config import C
from fighter import look
from physics import los
from state import g


class Knife:
    def __init__(self, kid, name, price, desc, color):
        self.kid = kid
        self.name = name
        self.price = price
        self.desc = desc
        self.color = color


KNIVES = [
    Knife("knife", "Taktik Bicak", 0, "Standart, hizli saplama.", C(190, 200, 210)),
    Knife("karambit", "Karambit", 800, "Kavisli, donen slash.", C(120, 230, 255)),
    Knife("butterfly", "Kelebek Bicak", 1200, "Takla atan gosteri bicagi.", C(255, 190, 80)),
]


def by_id(kid):
    for k in KNIVES:
        if k.kid == kid:
            return k
    return KNIVES[0]


# ---------------------------------------------------------------------------
#  3B MODEL PALETI
# ---------------------------------------------------------------------------
_STEEL = C(206, 214, 226)      # bicak govdesi
_EDGE = C(244, 248, 255)       # keskin kenar / bevel parlamasi
_SPINE = C(138, 148, 164)      # sirt (koyu celik)
_FULLER = C(112, 122, 138)     # kan oluğu
_PIN = C(176, 184, 198)        # civata / pim
_GUARD = C(118, 126, 140)      # siper / bolster
_DARK = C(30, 34, 44)          # sap govdesi
_MID = C(58, 64, 80)           # sap bantlari
_RING = C(96, 104, 120)        # karambit halkasi

_ACC3D = {"knife": C(0, 225, 205)}   # digerleri bicagin kendi rengini kullanir


# ---------------------------------------------------------------------------
#  3B YARDIMCILAR
# ---------------------------------------------------------------------------
def _seg(p, cz, lo, hi, length, t, edge_top):
    """Tek bir bicak dilimi: govde + bevel (ince keskin kenar) + kalin sirt."""
    h = max(hi - lo, 0.008)
    bev = min(0.026, h * 0.36)
    sp = min(0.012, h * 0.20)
    if edge_top:
        by = hi - bev
        p.append((0.0, (lo + by) / 2, cz, t, by - lo, length, _STEEL))
        p.append((0.0, hi - bev / 2, cz, t * 0.5, bev, length, _EDGE))
        p.append((0.0, lo + sp / 2, cz, t + 0.008, sp, length, _SPINE))
    else:
        by = lo + bev
        p.append((0.0, (by + hi) / 2, cz, t, hi - by, length, _STEEL))
        p.append((0.0, lo + bev / 2, cz, t * 0.5, bev, length, _EDGE))
        p.append((0.0, hi - sp / 2, cz, t + 0.008, sp, length, _SPINE))


def _blade(p, z0, z1, spine_y, edge_y, tip_y, zt, zb, t, steps=15):
    """Duz sirtli, karinli (drop-point) bicak: sirt zt'den sonra, kenar zb'den sonra uca iner."""
    width = spine_y - edge_y
    dz = (z1 - z0) / steps

    def top(z):
        if z <= zt:
            return spine_y
        u = min(1.0, (z - zt) / (z1 - zt))
        return spine_y - (spine_y - tip_y) * u ** 2.0

    def bot(z):
        if z <= zb:
            return edge_y
        v = min(1.0, (z - zb) / (z1 - zb))
        return edge_y + (tip_y - edge_y) * v ** 1.7

    for i in range(steps):
        zm = z0 + dz * (i + 0.5)
        _seg(p, zm, bot(zm), top(zm), dz * 1.04, t, False)

    # kan olugu (fuller): bicagin duz kismi boyunca
    fz0 = z0 + 0.05
    fz1 = min(zt, zb) - 0.03
    if fz1 > fz0:
        p.append((0.0, edge_y + width * 0.64, (fz0 + fz1) / 2, t + 0.004, 0.011, fz1 - fz0, _FULLER))


# ---------------------------------------------------------------------------
#  3B MODELLER
# ---------------------------------------------------------------------------
def _tactical(acc):
    p = []
    # sap: govde + yivli bantlar + bantlar arasinda aksan pencereleri
    p.append((0.0, -0.010, -0.1225, 0.044, 0.075, 0.275, _DARK))
    for i in range(5):
        p.append((0.0, -0.010, -0.235 + i * 0.045, 0.050, 0.080, 0.016, _MID))
    for i in range(4):
        p.append((0.0, -0.010, -0.2125 + i * 0.045, 0.047, 0.034, 0.020, acc))
    # kuyruk (pommel) + ip deligi
    p.append((0.0, -0.010, -0.272, 0.050, 0.086, 0.030, _GUARD))
    p.append((0.0, -0.016, -0.274, 0.053, 0.022, 0.012, _DARK))
    # siper
    p.append((0.0, 0.010, 0.030, 0.050, 0.125, 0.030, _GUARD))
    p.append((0.0, 0.010, 0.030, 0.054, 0.020, 0.018, _PIN))
    # bas parmak tirtiklari (jimping)
    for i in range(5):
        p.append((0.0, 0.081, 0.075 + i * 0.013, 0.020, 0.008, 0.006, _SPINE))
    # bicak
    _blade(p, 0.045, 0.585, 0.075, -0.025, 0.048, 0.40, 0.30, 0.018, steps=15)
    return p


def _karambit(acc):
    p = []
    # sap
    p.append((0.0, -0.030, -0.170, 0.046, 0.078, 0.260, _DARK))
    for z in (-0.270, -0.222, -0.126, -0.078):
        p.append((0.0, -0.030, z, 0.052, 0.082, 0.014, _MID))
    p.append((0.0, -0.030, -0.170, 0.0545, 0.030, 0.080, acc))
    # bolster (sap-bicak gecisi)
    p.append((0.0, -0.025, -0.030, 0.050, 0.092, 0.030, _GUARD))
    p.append((0.0, -0.025, -0.030, 0.054, 0.018, 0.016, _PIN))
    # parmak halkasi (sekizgen)
    cy, cz, r = -0.030, -0.370, 0.058
    d = r * 0.72
    p.append((0.0, cy + r, cz, 0.016, 0.016, 0.040, _RING))
    p.append((0.0, cy - r, cz, 0.016, 0.016, 0.040, _RING))
    p.append((0.0, cy, cz + r, 0.016, 0.040, 0.016, _RING))
    p.append((0.0, cy, cz - r, 0.016, 0.040, 0.016, _RING))
    for sy in (-1, 1):
        for sz in (-1, 1):
            p.append((0.0, cy + sy * d, cz + sz * d, 0.016, 0.022, 0.022, _RING))
    p.append((0.0, cy, -0.305, 0.040, 0.060, 0.020, _MID))      # halka-sap baglantisi
    p.append((0.0, cy, cz - r, 0.019, 0.010, 0.020, acc))        # halka ucundaki aksan
    # kavisli bicak (y ekseninde yukari kivrilir)
    n = 14
    t_bl = 0.016
    z0, z1 = -0.010, 0.460
    dz = (z1 - z0) / n

    def cy_(t):
        return 0.015 + 0.285 * t ** 1.9

    def wd(t):
        return 0.012 + 0.098 * (1.0 - t) ** 0.8

    for i in range(n):
        ta, tb = i / n, (i + 1) / n
        tm = (ta + tb) / 2
        zm = z0 + (z1 - z0) * tm
        h = wd(tm) + (cy_(tb) - cy_(ta)) * 0.9
        c = cy_(tm)
        lo, hi = c - h / 2, c + h / 2
        _seg(p, zm, lo, hi, dz * 1.08, t_bl, True)
        if 1 <= i <= 8:
            p.append((0.0, lo + h * 0.42, zm, t_bl + 0.004, 0.010, dz * 1.08, _FULLER))
    return p


def _butterfly(acc):
    p = []
    # iki sap yarimi: "hA"/"hB" etiketleri menteşe animasyonunda kullanilir
    for yc, tag in ((0.045, "hA"), (-0.055, "hB")):
        p.append((0.0, yc, -0.100, 0.045, 0.052, 0.240, _DARK, tag))
        p.append((0.0, yc, -0.115, 0.047, 0.024, 0.170, _MID, tag))
        for z in (-0.200, -0.120, -0.040):
            p.append((0.0, yc, z, 0.051, 0.014, 0.014, _PIN, tag))
        p.append((0.0, yc, -0.240, 0.046, 0.052, 0.040, acc, tag))     # kuyruk kapagi
        p.append((0.0, yc, 0.035, 0.050, 0.056, 0.030, _GUARD, tag))   # pivot koruyucu / kicker
    # iki sap arasindaki tang
    p.append((0.0, -0.005, -0.100, 0.030, 0.046, 0.240, _GUARD))
    # pivot civatasi ve mandal
    p.append((0.0, -0.005, 0.030, 0.056, 0.020, 0.020, _PIN))
    p.append((0.0, 0.040, 0.010, 0.054, 0.012, 0.050, _PIN, "hA"))
    # bicak (clip-point stili)
    _blade(p, 0.050, 0.550, 0.070, -0.030, 0.050, 0.36, 0.38, 0.016, steps=15)
    return p


_CACHE = {}


def model(kid):
    k = by_id(kid)
    if k.kid not in _CACHE:
        acc = _ACC3D.get(k.kid, k.color)
        if k.kid == "karambit":
            _CACHE[k.kid] = ("Z", _karambit(acc))
        elif k.kid == "butterfly":
            _CACHE[k.kid] = ("X", _butterfly(acc))
        else:
            _CACHE[k.kid] = ("X", _tactical(acc))
    axis, parts = _CACHE[k.kid]
    return axis, list(parts)


# ---------------------------------------------------------------------------
#  YAKIN DOVUS
# ---------------------------------------------------------------------------
def try_slash(p):
    if p.slash_cd > 0 or not p.alive:
        return
    p.slash_cd = 0.45
    p.slash_t = 0.30
    p.slash_n += 1
    fx, fy, fz = look(p)
    for o in g.FS:
        if o is p or not o.alive or o.team == p.team:
            continue
        dx, dz = o.x - p.x, o.z - p.z
        d = math.hypot(dx, dz)
        if d > 2.6:
            continue
        if (dx * fx + dz * fz) / (d + 1e-9) < 0.55:
            continue
        if not los(p.x, p.y + 1.4, p.z, o.x, o.y + 1.2, o.z):
            continue
        from combat import apply_damage
        apply_damage(o, 70, p, False, by_id(p.knife).name)


# ---------------------------------------------------------------------------
#  2B YEDEK IKONLAR
# ---------------------------------------------------------------------------
_I_METAL = C(204, 212, 224)
_I_EDGE = C(238, 243, 250)
_I_SPINE = C(124, 134, 150)
_I_FULLER = C(150, 160, 176)
_I_DARK = C(46, 50, 62)
_I_MID = C(88, 96, 112)
_I_GRIP = C(70, 77, 94)
_I_SHADOW = C(0, 0, 0, 120)

_I_ACC = {
    "knife": C(0, 230, 200),
    "karambit": C(0, 230, 200),
    "butterfly": C(255, 205, 70),
}


def _pt(x, y, s, a):
    return x + a[0] * s, y + a[1] * s


def _tri(x, y, s, a, b, c, col):
    ax, ay = _pt(x, y, s, a)
    bx, by = _pt(x, y, s, b)
    cx, cy = _pt(x, y, s, c)
    # raylib: ucgen saat yonunun tersi (ekran) sirasi ister; yonu otomatik duzelt
    if (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) > 0:
        bx, by, cx, cy = cx, cy, bx, by
    draw_triangle(Vector2(ax, ay), Vector2(bx, by), Vector2(cx, cy), col)


def _poly(x, y, s, pts, col):
    """Konveks cokgen (fan)."""
    for i in range(1, len(pts) - 1):
        _tri(x, y, s, pts[0], pts[i], pts[i + 1], col)


def _strip(x, y, s, top, bot, col):
    """Iki egri arasini doldurur (kavisli bicak govdeleri icin)."""
    for i in range(len(top) - 1):
        _tri(x, y, s, top[i], top[i + 1], bot[i], col)
        _tri(x, y, s, top[i + 1], bot[i + 1], bot[i], col)


def _line(x, y, s, a, b, th, col):
    ax, ay = _pt(x, y, s, a)
    bx, by = _pt(x, y, s, b)
    draw_line_ex(Vector2(ax, ay), Vector2(bx, by), max(1.0, th * s), col)


def _polyline(x, y, s, pts, th, col):
    for i in range(len(pts) - 1):
        _line(x, y, s, pts[i], pts[i + 1], th, col)


def _dot(x, y, s, c, r, col):
    cx, cy = _pt(x, y, s, c)
    draw_circle(int(cx), int(cy), max(1, int(r * s)), col)


def _lerp(a, b, f):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def _mix(top, bot, f):
    """bot'tan top'a f oraninda ara nokta listesi (bevel seridi icin)."""
    return [_lerp(b, t, f) for t, b in zip(top, bot)]


def _karambit_curve(n=14):
    top, bot = [], []
    for i in range(n + 1):
        t = i / n
        sx = 40 + 40 * t + 4 * t * t
        sy = 8 + 6 * t + 21 * t ** 2.3
        w = 17 * (1 - t) ** 0.85
        top.append((sx, sy))
        bot.append((sx - 14 * t * (1 - t), sy + w))
    return top, bot


_K_TOP, _K_BOT = _karambit_curve()

_T_TOP = [(32, 8), (48, 7.4), (62, 7), (74, 8.2), (84, 13)]
_T_BOT = [(32, 23.5), (48, 23.5), (60, 22.6), (73, 19.5), (84, 13)]

_B_TOP = [(32, 9), (50, 8), (66, 8.6), (80, 11.5), (84, 15)]
_B_BOT = [(32, 26), (50, 26), (64, 24), (78, 19.5), (84, 15)]


def _draw(kid, x, y, s, sh):
    def col(c):
        return _I_SHADOW if sh else c

    acc = _I_ACC.get(kid, _I_ACC["knife"])

    if kid == "karambit":
        # parmak halkasi
        draw_ring(Vector2(*_pt(x, y, s, (9, 19.5))), 4.0 * s, 7.4 * s, 0.0, 360.0, 28, col(_I_MID))
        # sap
        _poly(x, y, s, [(16, 12), (39, 9), (39, 26), (17, 27)], col(_I_DARK))
        # bolster
        _poly(x, y, s, [(37, 7), (43, 6), (43, 28), (37, 28)], col(_I_SPINE))
        # kavisli bicak
        _strip(x, y, s, _K_TOP, _K_BOT, col(_I_METAL))
        if not sh:
            _strip(x, y, s, _mix(_K_TOP, _K_BOT, 0.30), _K_BOT, _I_EDGE)       # keskin kenar
            _polyline(x, y, s, _K_TOP, 1.8, _I_SPINE)                          # sirt
            _polyline(x, y, s, _mix(_K_TOP, _K_BOT, 0.58)[1:10], 1.2, _I_FULLER)  # kan olugu
            for gx in (22, 28, 34):                                            # sap yivleri
                _line(x, y, s, (gx, 10.5 + (gx - 16) * 0.0), (gx + 0.6, 26.5), 1.4, _I_GRIP)
            _line(x, y, s, (18, 19), (37, 17.5), 2.2, acc)                     # aksan seridi
            _dot(x, y, s, (40, 17), 1.6, _I_EDGE)                              # civata

    elif kid == "butterfly":
        # tang (iki sap arasi)
        _poly(x, y, s, [(0, 13), (30, 16), (30, 20), (0, 21)], col(_I_SPINE))
        # iki sap yarimi
        _poly(x, y, s, [(0, 6), (30, 9), (30, 16), (0, 13)], col(_I_DARK))
        _poly(x, y, s, [(0, 21), (30, 20), (30, 27), (0, 29)], col(_I_DARK))
        # bicak
        _strip(x, y, s, _B_TOP, _B_BOT, col(_I_METAL))
        if not sh:
            _strip(x, y, s, _mix(_B_TOP, _B_BOT, 0.30), _B_BOT, _I_EDGE)
            _polyline(x, y, s, _B_TOP, 1.8, _I_SPINE)
            _line(x, y, s, (36, 14), (70, 14.2), 1.3, _I_FULLER)
            _line(x, y, s, (4, 10), (26, 12.3), 2.2, acc)                      # aksan seritleri
            _line(x, y, s, (4, 25), (26, 23.7), 2.2, acc)
            for px, py in ((10, 11.2), (19, 12.0), (10, 24.6), (19, 24.0)):    # pimler
                _dot(x, y, s, (px, py), 1.4, _I_EDGE)
            _dot(x, y, s, (30, 18), 2.8, _I_EDGE)                              # pivot
            _dot(x, y, s, (30, 18), 1.2, _I_DARK)

    else:
        # sap
        _poly(x, y, s, [(0, 11), (25, 8), (26, 23), (1, 26)], col(_I_DARK))
        # siper
        _poly(x, y, s, [(25, 5), (31, 4), (32, 27), (26, 28)], col(_I_SPINE))
        # bicak
        _strip(x, y, s, _T_TOP, _T_BOT, col(_I_METAL))
        if not sh:
            _strip(x, y, s, _mix(_T_TOP, _T_BOT, 0.30), _T_BOT, _I_EDGE)
            _polyline(x, y, s, _T_TOP, 1.8, _I_SPINE)
            _line(x, y, s, (36, 12.5), (70, 11.6), 1.3, _I_FULLER)
            for u in (0.18, 0.38, 0.58, 0.78):                                 # sap yivleri
                a = _lerp((0, 11), (25, 8), u)
                b = _lerp((1, 26), (26, 23), u)
                _line(x, y, s, a, b, 1.4, _I_GRIP)
            _line(x, y, s, (3, 18.5), (23, 15.5), 2.2, acc)                    # aksan seridi
            _dot(x, y, s, (4, 18.5), 1.5, _I_EDGE)


def draw_knife_icon(kid, x, y, scale=1.0):
    _draw(kid, x + 6 * scale, y + 7 * scale, scale, True)
    _draw(kid, x, y, scale, False)