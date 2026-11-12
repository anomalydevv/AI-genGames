# -*- coding: utf-8 -*-
"""Bicak tanimlari, 3B modeller, yakin dovus ve 2B yedek ikonlar.

Public arayuz ayni kalir:
    Knife, KNIVES, by_id(kid), model(kid) -> (eksen, [(x, y, z, sx, sy, sz, renk[, etiket]), ...]),
    try_slash(p), draw_knife_icon(kid, x, y, scale)

Yeni (geriye uyumlu) eklemeler:
    stats(kid) -> {"dmg", "cd", "dur", "range", "back"}   (bicaga ozel dovus degerleri)
    try_slash(p) artik vurulan kisi sayisini dondurur (eskiden None).

model(): her parca merkez-tabanli bir kutudur. Bicak z ekseni boyunca uzanir,
kalinlik x'tedir. Bicaklar artik: renk gecisli (kökten uca parlayan) celik,
neon kenar seridi, ucta parlama noktasi, disli sirt ve detayli saplar icerir.
"""
import math

from pyray import *

from config import C
from fighter import look
from physics import los
from state import g


class Knife:
    def __init__(self, kid, name, price, desc, color,
                 dmg=70, cd=0.45, dur=0.30, rng=2.6, back=1.8):
        self.kid = kid
        self.name = name
        self.price = price
        self.desc = desc
        self.color = color
        self.dmg = dmg        # temel hasar
        self.cd = cd          # vurus arasi bekleme (sn)
        self.dur = dur        # vurus animasyon suresi (sn)
        self.rng = rng        # menzil
        self.back = back      # arkadan vurus carpani


KNIVES = [
    Knife("knife", "Taktik Bicak", 0,
          "Dengeli, olumcul saplama.", C(190, 200, 210),
          dmg=70, cd=0.45, dur=0.30, rng=2.6, back=1.8),
    Knife("karambit", "Karambit", 800,
          "Cok hizli, kavisli kesikler.", C(120, 230, 255),
          dmg=58, cd=0.32, dur=0.24, rng=2.4, back=2.0),
    Knife("butterfly", "Kelebek Bicak", 1200,
          "Takla atan, genis menzilli bicak.", C(255, 190, 80),
          dmg=64, cd=0.38, dur=0.28, rng=2.8, back=1.9),
]


def by_id(kid):
    for k in KNIVES:
        if k.kid == kid:
            return k
    return KNIVES[0]


def stats(kid):
    k = by_id(kid)
    return {"dmg": k.dmg, "cd": k.cd, "dur": k.dur, "range": k.rng, "back": k.back}


# ---------------------------------------------------------------------------
#  3B MODEL PALETI
# ---------------------------------------------------------------------------
_STEEL = C(206, 214, 226)      # bicak govdesi
_EDGE = C(244, 248, 255)       # keskin kenar / bevel parlamasi
_SPINE = C(138, 148, 164)      # sirt (koyu celik)
_FULLER = C(112, 122, 138)     # kan olugu
_PIN = C(176, 184, 198)        # civata / pim
_GUARD = C(118, 126, 140)      # siper / bolster
_DARK = C(30, 34, 44)          # sap govdesi
_MID = C(58, 64, 80)           # sap bantlari
_RING = C(96, 104, 120)        # karambit halkasi
_GLINT = C(255, 255, 255)      # uc parlamasi

_ACC3D = {"knife": C(0, 225, 205)}   # digerleri bicagin kendi rengini kullanir

_SH = {}


def _shade(c, f):
    """Rengi f oraninda karart/aydinlat (onbellekli)."""
    key = (id(c), round(f, 3))
    if key not in _SH:
        try:
            _SH[key] = C(min(255, int(c.r * f)), min(255, int(c.g * f)),
                         min(255, int(c.b * f)), c.a)
        except Exception:
            _SH[key] = c
    return _SH[key]


# ---------------------------------------------------------------------------
#  3B YARDIMCILAR
# ---------------------------------------------------------------------------
def _seg(p, cz, lo, hi, length, t, edge_top, f=1.0, acc=None):
    """Tek bicak dilimi: govde + bevel + kalin sirt + (istege bagli) neon kenar seridi."""
    h = max(hi - lo, 0.008)
    bev = min(0.026, h * 0.36)
    sp = min(0.012, h * 0.20)
    steel = _shade(_STEEL, f)
    if edge_top:
        by = hi - bev
        p.append((0.0, (lo + by) / 2, cz, t, by - lo, length, steel))
        p.append((0.0, hi - bev / 2, cz, t * 0.5, bev, length, _EDGE))
        p.append((0.0, lo + sp / 2, cz, t + 0.008, sp, length, _SPINE))
        if acc is not None and h > 0.03:
            p.append((0.0, by - 0.005, cz, t + 0.005, 0.006, length, acc))
    else:
        by = lo + bev
        p.append((0.0, (by + hi) / 2, cz, t, hi - by, length, steel))
        p.append((0.0, lo + bev / 2, cz, t * 0.5, bev, length, _EDGE))
        p.append((0.0, hi - sp / 2, cz, t + 0.008, sp, length, _SPINE))
        if acc is not None and h > 0.03:
            p.append((0.0, by + 0.005, cz, t + 0.005, 0.006, length, acc))


def _blade(p, z0, z1, spine_y, edge_y, tip_y, zt, zb, t, steps=15, acc=None, teeth=None):
    """Karinli (drop-point) bicak. Renk gecisli govde, neon kenar, disli sirt ve uc parlamasi."""
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
        f = 0.82 + 0.30 * i / max(1, steps - 1)      # koku koyu, uca dogru parlak
        _seg(p, zm, bot(zm), top(zm), dz * 1.04, t, False, f, acc)

    # kan olugu
    fz0 = z0 + 0.05
    fz1 = min(zt, zb) - 0.03
    if fz1 > fz0:
        p.append((0.0, edge_y + width * 0.64, (fz0 + fz1) / 2, t + 0.004, 0.011, fz1 - fz0, _FULLER))

    # disli sirt (agresif gorunum)
    if teeth:
        a, b = teeth
        n = int((b - a) / 0.028)
        for i in range(n):
            p.append((0.0, spine_y + 0.006, a + i * 0.028 + 0.010, t + 0.010, 0.012, 0.014, _SPINE))

    # uc parlamasi
    p.append((0.0, tip_y, z1 - 0.012, t * 0.7, 0.014, 0.034, _GLINT))


# ---------------------------------------------------------------------------
#  3B MODELLER
# ---------------------------------------------------------------------------
def _tactical(acc):
    p = []
    # sap govdesi + yivli bantlar + aksan pencereleri
    p.append((0.0, -0.010, -0.1225, 0.044, 0.075, 0.275, _DARK))
    for i in range(5):
        p.append((0.0, -0.010, -0.235 + i * 0.045, 0.050, 0.080, 0.016, _MID))
    for i in range(4):
        p.append((0.0, -0.010, -0.2125 + i * 0.045, 0.047, 0.034, 0.020, acc))
    # elmas desenli sap yuzeyi (ust ve alt sira)
    for i in range(8):
        p.append((0.0, 0.020, -0.225 + i * 0.030, 0.047, 0.006, 0.010, _SPINE))
        p.append((0.0, -0.040, -0.225 + i * 0.030, 0.047, 0.006, 0.010, _SPINE))
    # kuyruk (pommel) + cam kirici sivri uclar + ip deligi
    p.append((0.0, -0.010, -0.272, 0.050, 0.086, 0.030, _GUARD))
    p.append((0.0, -0.016, -0.274, 0.053, 0.022, 0.012, _DARK))
    p.append((0.0, 0.040, -0.285, 0.030, 0.020, 0.018, _PIN))
    p.append((0.0, -0.060, -0.285, 0.030, 0.020, 0.018, _PIN))
    # siper + parmak kancasi
    p.append((0.0, 0.010, 0.030, 0.050, 0.125, 0.030, _GUARD))
    p.append((0.0, 0.010, 0.030, 0.054, 0.020, 0.018, _PIN))
    p.append((0.0, -0.058, 0.040, 0.046, 0.030, 0.026, _GUARD))
    p.append((0.0, -0.058, 0.040, 0.050, 0.010, 0.014, acc))
    # bas parmak tirtiklari
    for i in range(5):
        p.append((0.0, 0.081, 0.075 + i * 0.013, 0.020, 0.008, 0.006, _SPINE))
    # bicak (disli sirt + neon kenar)
    _blade(p, 0.045, 0.585, 0.075, -0.025, 0.048, 0.40, 0.30, 0.018,
           steps=15, acc=acc, teeth=(0.10, 0.34))
    return p


def _karambit(acc):
    p = []
    # sap
    p.append((0.0, -0.030, -0.170, 0.046, 0.078, 0.260, _DARK))
    for z in (-0.270, -0.222, -0.126, -0.078):
        p.append((0.0, -0.030, z, 0.052, 0.082, 0.014, _MID))
    p.append((0.0, -0.030, -0.170, 0.0545, 0.030, 0.080, acc))
    for i in range(5):                                            # yan tirtiklar
        p.append((0.0, 0.012, -0.250 + i * 0.040, 0.050, 0.006, 0.010, _SPINE))
    # bolster
    p.append((0.0, -0.025, -0.030, 0.050, 0.092, 0.030, _GUARD))
    p.append((0.0, -0.025, -0.030, 0.054, 0.018, 0.016, _PIN))
    # parmak halkasi (sekizgen) - daha kalin
    cy, cz, r = -0.030, -0.370, 0.058
    d = r * 0.72
    p.append((0.0, cy + r, cz, 0.020, 0.018, 0.044, _RING))
    p.append((0.0, cy - r, cz, 0.020, 0.018, 0.044, _RING))
    p.append((0.0, cy, cz + r, 0.020, 0.044, 0.018, _RING))
    p.append((0.0, cy, cz - r, 0.020, 0.044, 0.018, _RING))
    for sy in (-1, 1):
        for sz in (-1, 1):
            p.append((0.0, cy + sy * d, cz + sz * d, 0.020, 0.024, 0.024, _RING))
    p.append((0.0, cy, -0.305, 0.040, 0.060, 0.020, _MID))
    p.append((0.0, cy, cz - r, 0.023, 0.012, 0.022, acc))         # halka aksani
    p.append((0.0, cy + r, cz, 0.022, 0.008, 0.030, acc))
    # kavisli bicak
    n = 16
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
        f = 0.82 + 0.30 * tm
        _seg(p, zm, lo, hi, dz * 1.10, t_bl, True, f, acc)
        if 1 <= i <= 9:
            p.append((0.0, lo + h * 0.42, zm, t_bl + 0.004, 0.010, dz * 1.10, _FULLER))
    # uc parlamasi
    p.append((0.0, cy_(1.0), z1 - 0.010, 0.012, 0.016, 0.034, _GLINT))
    return p


def _butterfly(acc):
    p = []
    # iki sap yarimi: "hA"/"hB" etiketleri mentese animasyonunda kullanilir
    for yc, tag in ((0.045, "hA"), (-0.055, "hB")):
        p.append((0.0, yc, -0.100, 0.045, 0.052, 0.240, _DARK, tag))
        p.append((0.0, yc, -0.115, 0.047, 0.024, 0.170, _MID, tag))
        for z in (-0.200, -0.120, -0.040):
            p.append((0.0, yc, z, 0.051, 0.014, 0.014, _PIN, tag))
        # neon aksan seridi (sapin iceri gomulu isik seridi)
        p.append((0.0, yc, -0.120, 0.049, 0.008, 0.150, acc, tag))
        p.append((0.0, yc, -0.240, 0.046, 0.052, 0.040, acc, tag))     # kuyruk kapagi
        p.append((0.0, yc, 0.035, 0.050, 0.056, 0.030, _GUARD, tag))   # pivot koruyucu
    # sap arasi tang
    p.append((0.0, -0.005, -0.100, 0.030, 0.046, 0.240, _GUARD))
    # pivot civatasi ve mandal
    p.append((0.0, -0.005, 0.030, 0.058, 0.022, 0.022, _PIN))
    p.append((0.0, -0.005, 0.030, 0.062, 0.010, 0.010, acc))
    p.append((0.0, 0.040, 0.010, 0.054, 0.012, 0.050, _PIN, "hA"))
    # bicak (clip-point, neon kenar)
    _blade(p, 0.050, 0.550, 0.070, -0.030, 0.050, 0.36, 0.38, 0.016, steps=15, acc=acc)
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
    """Bicak vurusu. Onunde, menzildeki dusmanlara hasar verir.
    Arkadan vurus: hedef sirtini donmusse hasar carpani uygulanir.
    Vurulan kisi sayisini dondurur."""
    if p.slash_cd > 0 or not p.alive:
        return 0
    k = by_id(p.knife)
    p.slash_cd = k.cd
    p.slash_t = k.dur
    p.slash_n += 1
    fx, fy, fz = look(p)
    fh = math.hypot(fx, fz) or 1.0
    fx, fz = fx / fh, fz / fh                      # yatay yon (yukari bakinca da calisir)
    hits = 0
    for o in g.FS:
        if o is p or not o.alive or o.team == p.team:
            continue
        dx, dz = o.x - p.x, o.z - p.z
        d = math.hypot(dx, dz)
        if d > k.rng or abs(o.y - p.y) > 2.2:
            continue
        if (dx * fx + dz * fz) / (d + 1e-9) < 0.55:
            continue
        if not los(p.x, p.y + 1.4, p.z, o.x, o.y + 1.2, o.z):
            continue
        dmg = k.dmg
        label = k.name
        try:
            ox, oy, oz = look(o)
            oh = math.hypot(ox, oz) or 1.0
            if (ox * fx + oz * fz) / oh > 0.6:      # ayni yone bakiyorlar = sirtindan
                dmg = int(round(dmg * k.back))
                label = k.name + " (Arkadan)"
        except Exception:
            pass
        from combat import apply_damage
        apply_damage(o, dmg, p, False, label)
        hits += 1
    return hits


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
_I_GLINT = C(255, 255, 255, 230)
_I_GLINT2 = C(255, 255, 255, 110)

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
    # raylib: ucgen saat yonunun tersi sirasi ister; yonu otomatik duzelt
    if (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) > 0:
        bx, by, cx, cy = cx, cy, bx, by
    draw_triangle(Vector2(ax, ay), Vector2(bx, by), Vector2(cx, cy), col)


def _poly(x, y, s, pts, col):
    """Konveks cokgen (fan)."""
    for i in range(1, len(pts) - 1):
        _tri(x, y, s, pts[0], pts[i], pts[i + 1], col)


def _strip(x, y, s, top, bot, col):
    """Iki egri arasini doldurur."""
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
    """bot'tan top'a f oraninda ara nokta listesi."""
    return [_lerp(b, t, f) for t, b in zip(top, bot)]


def _glint(x, y, s, c, r):
    """Dort uclu parlama yildizi (uc parlamasi)."""
    _line(x, y, s, (c[0] - r, c[1]), (c[0] + r, c[1]), 1.1, _I_GLINT)
    _line(x, y, s, (c[0], c[1] - r), (c[0], c[1] + r), 1.1, _I_GLINT)
    _line(x, y, s, (c[0] - r * 0.55, c[1] - r * 0.55), (c[0] + r * 0.55, c[1] + r * 0.55), 0.8, _I_GLINT2)
    _line(x, y, s, (c[0] - r * 0.55, c[1] + r * 0.55), (c[0] + r * 0.55, c[1] - r * 0.55), 0.8, _I_GLINT2)
    _dot(x, y, s, c, 1.1, _I_GLINT)


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
            _strip(x, y, s, _mix(_K_TOP, _K_BOT, 0.30), _K_BOT, _I_EDGE)
            _polyline(x, y, s, _K_TOP, 1.8, _I_SPINE)
            _polyline(x, y, s, _mix(_K_TOP, _K_BOT, 0.58)[1:10], 1.2, _I_FULLER)
            _polyline(x, y, s, _K_BOT[1:], 1.2, acc)                           # neon kenar
            for gx in (22, 28, 34):
                _line(x, y, s, (gx, 10.5), (gx + 0.6, 26.5), 1.4, _I_GRIP)
            _line(x, y, s, (18, 19), (37, 17.5), 2.2, acc)
            _dot(x, y, s, (40, 17), 1.6, _I_EDGE)
            _dot(x, y, s, (9, 19.5), 1.2, acc)
            _glint(x, y, s, _K_BOT[-1], 4.5)

    elif kid == "butterfly":
        _poly(x, y, s, [(0, 13), (30, 16), (30, 20), (0, 21)], col(_I_SPINE))
        _poly(x, y, s, [(0, 6), (30, 9), (30, 16), (0, 13)], col(_I_DARK))
        _poly(x, y, s, [(0, 21), (30, 20), (30, 27), (0, 29)], col(_I_DARK))
        _strip(x, y, s, _B_TOP, _B_BOT, col(_I_METAL))
        if not sh:
            _strip(x, y, s, _mix(_B_TOP, _B_BOT, 0.30), _B_BOT, _I_EDGE)
            _polyline(x, y, s, _B_TOP, 1.8, _I_SPINE)
            _polyline(x, y, s, _B_BOT[:-1], 1.2, acc)                          # neon kenar
            _line(x, y, s, (36, 14), (70, 14.2), 1.3, _I_FULLER)
            _line(x, y, s, (4, 10), (26, 12.3), 2.2, acc)
            _line(x, y, s, (4, 25), (26, 23.7), 2.2, acc)
            for px, py in ((10, 11.2), (19, 12.0), (10, 24.6), (19, 24.0)):
                _dot(x, y, s, (px, py), 1.4, _I_EDGE)
            _dot(x, y, s, (30, 18), 2.8, _I_EDGE)
            _dot(x, y, s, (30, 18), 1.2, _I_DARK)
            _glint(x, y, s, _B_TOP[-1], 4.5)

    else:
        _poly(x, y, s, [(0, 11), (25, 8), (26, 23), (1, 26)], col(_I_DARK))
        _poly(x, y, s, [(25, 5), (31, 4), (32, 27), (26, 28)], col(_I_SPINE))
        _strip(x, y, s, _T_TOP, _T_BOT, col(_I_METAL))
        if not sh:
            _strip(x, y, s, _mix(_T_TOP, _T_BOT, 0.30), _T_BOT, _I_EDGE)
            _polyline(x, y, s, _T_TOP, 1.8, _I_SPINE)
            _polyline(x, y, s, _T_BOT[:-1], 1.2, acc)                          # neon kenar
            for i in range(6):                                                 # disli sirt
                tx = 38 + i * 6.2
                _tri(x, y, s, (tx, 7.3), (tx + 3.2, 7.0), (tx + 1.4, 4.8), _I_SPINE)
            _line(x, y, s, (36, 12.5), (70, 11.6), 1.3, _I_FULLER)
            for u in (0.18, 0.38, 0.58, 0.78):
                a = _lerp((0, 11), (25, 8), u)
                b = _lerp((1, 26), (26, 23), u)
                _line(x, y, s, a, b, 1.4, _I_GRIP)
            _line(x, y, s, (3, 18.5), (23, 15.5), 2.2, acc)
            _dot(x, y, s, (4, 18.5), 1.5, _I_EDGE)
            _glint(x, y, s, _T_TOP[-1], 4.5)


def draw_knife_icon(kid, x, y, scale=1.0):
    _draw(kid, x + 6 * scale, y + 7 * scale, scale, True)
    _draw(kid, x, y, scale, False)