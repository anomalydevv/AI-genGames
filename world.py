# -*- coding: utf-8 -*-
"""Harita geometrisi: Valorant tarzi A/B bomba bolgeleri, takim spawnlari,
bolge (callout) tanimlari ve bot yol agi.

Koordinat: x dogu(+)/bati(-), z guney(+)/kuzey(-). Harita -30..30.
Harita 180 derece donusle simetriktir: (x, z) -> (-x, -z).
Savunan (DFN) spawn: KUZEY-BATI kose  |  Saldiran (ATK) spawn: GUNEY-DOGU kose
A sitesi: kuzey-dogu                  |  B sitesi: guney-bati
Iki spawn haritanin zit koselerinde, duvarlarla kapali; birbirini goremez.
"""
import math
import random

from config import C

BOX = []

# ---------------------------------------------------------------- renkler
WALL, WALL2, DARK = C(108, 114, 128), C(82, 88, 102), C(64, 70, 84)
CR, CR2, PLANT = C(150, 108, 62), C(112, 96, 80), C(54, 92, 66)
F_ATK, F_DFN = C(122, 58, 58), C(52, 84, 128)
F_A, F_B = C(156, 112, 48), C(52, 132, 122)
F_MID, F_LANE = C(78, 82, 94), C(70, 74, 86)


def add_box(cx, cz, sx, sy, sz, col, y0=0.0):
    BOX.append((cx - sx / 2, y0, cz - sz / 2, cx + sx / 2, y0 + sy, cz + sz / 2, col))


def mbox(cx, cz, sx, sy, sz, col, y0=0.0, col2=None):
    """Kutuyu x ekseninde aynalayarak (hem +x hem -x) ekler."""
    add_box(cx, cz, sx, sy, sz, col, y0)
    if cx != 0:
        add_box(-cx, cz, sx, sy, sz, col2 or col, y0)


def floor(x0, z0, x1, z1, col):
    """Zemin renk yamasi (yurunebilir, sadece gorsel)."""
    add_box((x0 + x1) / 2, (z0 + z1) / 2, x1 - x0, 1.02, z1 - z0, col, y0=-1.0)


def _segments(a, b, gaps):
    segs, cur = [], a
    for g0, g1 in sorted(gaps):
        if g0 > cur:
            segs.append((cur, g0))
        cur = max(cur, g1)
    if cur < b:
        segs.append((cur, b))
    return segs


def wall_z(z, x0, x1, gaps=(), h=5, col=None, t=1.0):
    """Yatay duvar (z sabit, x0..x1). gaps = kapi bosluklari [(xa, xb), ...]."""
    for a, b in _segments(x0, x1, gaps):
        add_box((a + b) / 2, z, b - a, h, t, col or WALL)


def wall_x(x, z0, z1, gaps=(), h=5, col=None, t=1.0):
    """Dikey duvar (x sabit, z0..z1)."""
    for a, b in _segments(z0, z1, gaps):
        add_box(x, (a + b) / 2, t, h, b - a, col or WALL)


def mwall_x(x, z0, z1, gaps=(), **k):
    wall_x(x, z0, z1, gaps, **k)
    wall_x(-x, z0, z1, gaps, **k)


def mwall_z(z, x0, x1, gaps=(), **k):
    wall_z(z, x0, x1, gaps, **k)
    wall_z(z, -x1, -x0, [(-b, -a) for a, b in gaps], **k)


def rbox(cx, cz, sx, sy, sz, col, y0=0.0, col2=None):
    """Kutuyu 180 derece donusle (x,z)->(-x,-z) iki noktaya ekler."""
    add_box(cx, cz, sx, sy, sz, col, y0)
    add_box(-cx, -cz, sx, sy, sz, col2 or col, y0)


def rfloor(x0, z0, x1, z1, col):
    floor(x0, z0, x1, z1, col)
    floor(-x1, -z1, -x0, -z0, col)


def rwall_x(x, z0, z1, gaps=(), **k):
    wall_x(x, z0, z1, gaps, **k)
    wall_x(-x, -z1, -z0, [(-b, -a) for a, b in gaps], **k)


def rwall_z(z, x0, x1, gaps=(), **k):
    wall_z(z, x0, x1, gaps, **k)
    wall_z(-z, -x1, -x0, [(-b, -a) for a, b in gaps], **k)


# ------------------------------------------------------------ bolgeler
SITE_A = (19.5, -21.0, 6.0)    # (x, z, bomba yerlestirme yaricapi) kuzey-dogu
SITE_B = (-19.5, 21.0, 6.0)    # guney-bati

# (isim, x0, z0, x1, z1) -- bolge / callout listesi (ilk eslesen gecerli)
ZONES = [
    ("Saldiran Spawn", 13.5, 16.5, 30, 30),
    ("Savunan Spawn", -30, -30, -13.5, -16.5),
    ("A Sitesi", 7.5, -30, 30, -13.5),
    ("B Sitesi", -30, 13.5, -7.5, 30),
    ("Savunan Avlu", -13.5, -30, 7.5, -13.5),
    ("Saldiran Avlu", -7.5, 13.5, 13.5, 30),
    ("Orta Oda", -10.5, -7.5, 10.5, 7.5),
    ("Dogu Oda", 10.5, -7.5, 22.5, 7.5),
    ("Bati Oda", -22.5, -7.5, -10.5, 7.5),
    ("A Ana Koridor", 22.5, -13.5, 30, 16.5),
    ("B Ana Koridor", -30, -16.5, -22.5, 13.5),
    ("Kuzey Salon", -22.5, -16.5, 22.5, -7.5),
    ("Guney Salon", -22.5, 7.5, 22.5, 16.5),
]


def zone_at(x, z):
    for name, x0, z0, x1, z1 in ZONES:
        if x0 <= x <= x1 and z0 <= z <= z1:
            return name
    return "Harita"


def build_map():
    # ------------------------------------------------ dis sinirlar
    add_box(0, -30.5, 64, 8, 1, WALL)
    add_box(0, 30.5, 64, 8, 1, WALL)
    add_box(-30.5, 0, 1, 8, 62, WALL)
    add_box(30.5, 0, 1, 8, 62, WALL)

    # ------------------------------------------------ zemin bolgeleri
    floor(13.5, 16.5, 30, 30, F_ATK)            # saldiran spawn (GD kose)
    floor(-30, -30, -13.5, -16.5, F_DFN)        # savunan spawn (KB kose)
    rfloor(13.5, -25.5, 25.5, -16.5, F_A)       # A plant alani (KD) / B (GB)
    floor(-10.5, -7.5, 10.5, 7.5, F_MID)        # orta oda
    floor(23, -13.5, 30, 16.5, F_LANE)          # A ana koridor
    floor(-30, -16.5, -23, 13.5, F_LANE)        # B ana koridor
    # B plant alani rengi (A ile farkli olsun)
    BOX[:] = [b for b in BOX if b[6] != F_A or b[0] > 0]
    floor(-25.5, 16.5, -13.5, 25.5, F_B)

    # ------------------------------------------------ SPAWN ODALARI (zit koseler)
    # Savunan (KB): dogu kapisi avluya, guney kapisi B Ana koridoruna
    # Saldiran (GD): bati kapisi avluya, kuzey kapisi A Ana koridoruna
    rwall_x(-13.5, -30, -16.5, [(-27, -21)])
    rwall_z(-16.5, -30, -13.5, [(-28.5, -22.5)])
    rbox(-16.0, -19.2, 2.2, 1.1, 1.6, CR2)
    rbox(-27.5, -19.5, 1.8, 1.0, 1.8, CR)

    # ------------------------------------------------ A SITESI (kuzey-dogu) + B (guney-bati)
    rwall_z(-13.5, 7.5, 30, [(10.5, 16.5), (22.5, 28.5)])   # Kisa + Ana girisleri
    rwall_x(7.5, -30, -13.5, [(-27, -21)])                  # avlu kapisi
    # heaven (balkon)
    rbox(26.25, -27.75, 7.5, 1.1, 4.5, DARK)
    rbox(26.25, -25.5, 7.5, 1.2, 0.5, WALL, y0=1.1)
    rbox(22.5, -27.75, 0.5, 1.2, 4.5, WALL, y0=1.1)
    # kapaklar
    rbox(17.0, -22.5, 2.4, 1.2, 2.4, CR, col2=CR2)
    rbox(22.5, -19.5, 1.8, 1.0, 1.8, CR2, col2=CR)
    rbox(13.5, -17.5, 1.6, 0.9, 1.6, PLANT)
    rbox(25.5, -16.5, 2.2, 1.2, 2.2, CR, col2=CR2)
    rbox(12.0, -27.0, 4.0, 1.0, 1.0, CR2, col2=CR)

    # ------------------------------------------------ AVLULAR (spawn onleri)
    rbox(-4.5, -22.5, 2.4, 1.2, 2.4, CR2)
    rbox(1.5, -17.0, 2.4, 1.1, 2.4, CR)
    rbox(-9.0, -26.0, 1.6, 0.9, 1.6, PLANT)

    # ------------------------------------------------ KUZEY / GUNEY SALON
    mbox(14.0, -10.0, 2.0, 1.2, 2.0, CR2, col2=CR)
    mbox(14.0, 10.0, 2.0, 1.2, 2.0, CR, col2=CR2)
    mbox(19.0, -9.0, 1.6, 0.9, 1.6, PLANT)
    mbox(19.0, 9.0, 1.6, 0.9, 1.6, PLANT)
    mbox(9.0, -9.0, 1.0, 6.0, 1.0, DARK)                    # pilonlar
    mbox(9.0, 9.0, 1.0, 6.0, 1.0, DARK)

    # ------------------------------------------------ ORTA ODA (4 kapili)
    # kapilar sacilmis (hizasiz): iki spawn arasinda capraz goz hizasi olusmasin
    wall_z(-7.5, -10.5, 10.5, [(0.75, 5.25)])              # kuzey kapi (x=+3)
    wall_z(7.5, -10.5, 10.5, [(-5.25, -0.75)])             # guney kapi (x=-3)
    wall_x(10.5, -7.5, 7.5, [(0.75, 5.25)], col=WALL2)     # dogu kapi (z=+3)
    wall_x(-10.5, -7.5, 7.5, [(-5.25, -0.75)], col=WALL2)  # bati kapi (z=-3)
    add_box(0, 0, 2.2, 1.2, 2.2, CR)
    add_box(-6, 4.5, 1.6, 0.9, 1.6, CR2)
    add_box(6, -4.5, 1.6, 0.9, 1.6, CR2)

    # ------------------------------------------------ DOGU / BATI ODALARI
    mwall_z(-7.5, 10.5, 22.5, [(13.5, 19.5)])
    mwall_z(7.5, 10.5, 22.5, [(13.5, 19.5)])
    mbox(16.5, 0, 2.0, 1.2, 2.0, CR, col2=CR2)
    mbox(19.5, -4.5, 1.4, 0.9, 1.4, PLANT)

    # ------------------------------------------------ ANA KORIDORLAR (A Main / B Main)
    rwall_x(-22.5, -16.5, 13.5, [(-3, 3), (7.5, 13.5)])
    rbox(26.5, -3.0, 2.2, 1.2, 2.2, CR, col2=CR2)
    rbox(25.5, 8.0, 2.4, 1.1, 2.4, CR2, col2=CR)
    rbox(27.0, 13.0, 1.6, 0.9, 1.6, PLANT)

    # ------------------------------------------------ karakter sahnesi
    add_box(100, 100, 14, 1.02, 14, C(70, 74, 82), y0=-1.0)


build_map()

# Savunan: kuzey-bati kose odasi | Saldiran: guney-dogu kose odasi
SPAWNS_DFN = [(-27, -27), (-22, -27), (-17, -27), (-25, -22), (-20, -22)]
SPAWNS_ATK = [(27, 27), (22, 27), (17, 27), (25, 22), (20, 22)]
SPAWNS = SPAWNS_ATK + SPAWNS_DFN


def in_box(x, z, m):
    for b in BOX:
        if b[0] - m < x < b[3] + m and b[2] - m < z < b[5] + m and b[1] < 1.5 and b[4] > 0.3 and b[1] > -0.5:
            return True
    return False


WPS = []
ADJ = []
STEP = 3.0
BASE = -27.0


def build_waypoints():
    pts = []
    v = BASE
    while v <= 27.01:
        w = BASE
        while w <= 27.01:
            if not in_box(v, w, 1.0):
                pts.append((v, w))
            w += STEP
        v += STEP
    WPS.extend(pts)
    cells = {}
    for i, (x, z) in enumerate(pts):
        cells[(int(round((x - BASE) / STEP)), int(round((z - BASE) / STEP)))] = i
    for i, a in enumerate(pts):
        ci = int(round((a[0] - BASE) / STEP))
        cj = int(round((a[1] - BASE) / STEP))
        ns = []
        for ox in (-2, -1, 0, 1, 2):
            for oz in (-2, -1, 0, 1, 2):
                if ox == 0 and oz == 0:
                    continue
                j = cells.get((ci + ox, cj + oz))
                if j is None:
                    continue
                b = pts[j]
                d = math.hypot(a[0] - b[0], a[1] - b[1])
                if d > 7.0:
                    continue
                ok = True
                n = int(d / 0.6) + 1
                for k in range(1, n):
                    t = k / n
                    if in_box(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 0.55):
                        ok = False
                        break
                if ok:
                    ns.append(j)
        ADJ.append(ns)


build_waypoints()


def nearest_wp(x, z):
    bi, bd = 0, 1e9
    for i, p in enumerate(WPS):
        d = (p[0] - x) ** 2 + (p[1] - z) ** 2
        if d < bd:
            bd, bi = d, i
    return bi


def find_path(x, z, gx, gz):
    s, e = nearest_wp(x, z), nearest_wp(gx, gz)
    if s == e:
        return [(gx, gz)]
    prev = {s: None}
    q = [s]
    qi = 0
    while qi < len(q):
        c = q[qi]
        qi += 1
        if c == e:
            break
        for n in ADJ[c]:
            if n not in prev:
                prev[n] = c
                q.append(n)
    if e not in prev:
        return [WPS[random.randrange(len(WPS))]]
    path = []
    c = e
    while c is not None:
        path.append(WPS[c])
        c = prev[c]
    path.reverse()
    return path