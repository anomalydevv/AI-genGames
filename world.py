# -*- coding: utf-8 -*-
"""Harita geometrisi, A/B bomba bolgeleri, takim spawnlari ve bot yol agi."""
import math
import random

from config import C

BOX = []


def add_box(cx, cz, sx, sy, sz, col, y0=0.0):
    BOX.append((cx - sx / 2, y0, cz - sz / 2, cx + sx / 2, y0 + sy, cz + sz / 2, col))


def build_map():
    WALL, WALL2, DARK = C(108, 114, 128), C(82, 88, 102), C(64, 70, 84)
    CR, CR2, PLANT = C(150, 108, 62), C(112, 96, 80), C(54, 92, 66)
    # sinirlar
    add_box(0, -30.5, 64, 8, 1, WALL)
    add_box(0, 30.5, 64, 8, 1, WALL)
    add_box(-30.5, 0, 1, 8, 62, WALL)
    add_box(30.5, 0, 1, 8, 62, WALL)
    # A bolgesi (kuzey dogu) - yari kapali oda
    add_box(9, -22.5, 1, 5, 3, WALL)
    add_box(9, -12.5, 1, 5, 9, WALL)
    add_box(16, -8, 14, 5, 1, WALL)
    add_box(23, -1.5, 1, 5, 11, WALL)
    add_box(23, 15.5, 1, 5, 11, WALL)
    add_box(24, -11, 2.4, 1.3, 2.4, CR)
    add_box(13, -22, 2.6, 1.1, 2.6, CR2)
    add_box(18, -20, 4, 1, 1, CR2)
    add_box(11, -12, 1.6, 0.9, 1.6, PLANT)
    # A heaven
    add_box(21, -25, 10, 1.1, 7, DARK)
    add_box(25.5, -25, 1, 1.2, 7, WALL, y0=1.1)
    add_box(16.5, -25, 1, 1.2, 7, WALL, y0=1.1)
    add_box(21, -28.5, 10, 1.2, 1, WALL, y0=1.1)
    # B bolgesi (guney bati) - yari kapali oda
    add_box(-9, 11.5, 1, 5, 7, WALL)
    add_box(-9, 21.5, 1, 5, 5, WALL)
    add_box(-16, 8, 14, 5, 1, WALL)
    add_box(-23, -15.5, 1, 5, 11, WALL)
    add_box(-23, 1.5, 1, 5, 11, WALL)
    add_box(-24, 11, 2.4, 1.3, 2.4, CR2)
    add_box(-13, 22, 2.6, 1.1, 2.6, CR)
    add_box(-18, 20, 4, 1, 1, CR)
    add_box(-11, 10, 1.6, 0.9, 1.6, PLANT)
    # B heaven
    add_box(-21, 25, 10, 1.1, 7, DARK)
    add_box(-25.5, 25, 1, 1.2, 7, WALL, y0=1.1)
    add_box(-16.5, 25, 1, 1.2, 7, WALL, y0=1.1)
    add_box(-21, 28.5, 10, 1.2, 1, WALL, y0=1.1)
    # merkez kapali oda
    add_box(-5, -5, 6, 5, 1, WALL)
    add_box(5, -5, 6, 5, 1, WALL)
    add_box(-5, 5, 6, 5, 1, WALL)
    add_box(5, 5, 6, 5, 1, WALL)
    add_box(-8, 0, 1, 5, 12, WALL2)
    add_box(8, 0, 1, 5, 12, WALL2)
    add_box(0, 0, 2.2, 1.2, 2.2, CR)
    # merkez kuzey koridoru
    add_box(8, -22.5, 1, 5, 3, WALL2)
    add_box(8, -12.5, 1, 5, 9, WALL2)
    add_box(-8, -22.5, 1, 5, 3, WALL2)
    add_box(-8, -12.5, 1, 5, 9, WALL2)
    # merkez guney koridoru
    add_box(13, 10.5, 1, 5, 9, WALL2)
    add_box(13, 19.5, 1, 5, 1, WALL2)
    add_box(-13, 10.5, 1, 5, 9, WALL2)
    add_box(-13, 19.5, 1, 5, 1, WALL2)
    # bati kapali oda
    add_box(-23.5, -6, 5, 5, 1, WALL)
    add_box(-15.5, -6, 3, 5, 1, WALL)
    add_box(-23.5, 6, 5, 5, 1, WALL)
    add_box(-15.5, 6, 3, 5, 1, WALL)
    add_box(-26, 0, 1, 5, 12, WALL)
    add_box(-14, 0, 1, 5, 12, WALL)
    add_box(-20, 0, 2, 1.2, 2, CR2)
    # dogu kapali oda
    add_box(15.5, -6, 3, 5, 1, WALL)
    add_box(23.5, -6, 5, 5, 1, WALL)
    add_box(15.5, 6, 3, 5, 1, WALL)
    add_box(23.5, 6, 5, 5, 1, WALL)
    add_box(14, 0, 1, 5, 12, WALL)
    add_box(26, 0, 1, 5, 12, WALL)
    add_box(20, 0, 2, 1.2, 2, CR)
    # acik avlular ve kapaklar
    add_box(18, 12, 2.4, 1.2, 2.4, CR)
    add_box(19, 17, 1.8, 1, 1.8, CR2)
    add_box(15, 8, 1.6, 0.9, 1.6, PLANT)
    add_box(-18, -12, 2.4, 1.2, 2.4, CR2)
    add_box(-19, -17, 1.8, 1, 1.8, CR)
    add_box(-15, -8, 1.6, 0.9, 1.6, PLANT)
    add_box(-6, 15, 2.4, 1.2, 2.4, CR)
    add_box(6, 11, 2.4, 1.2, 2.4, CR2)
    add_box(0, 18, 3, 0.9, 1.2, PLANT)
    add_box(-4, -10, 2.4, 1.1, 2.4, CR2)
    add_box(4, -19, 1.8, 1, 1.8, CR)
    # spawn kapaklari
    add_box(-8, 24, 2.2, 1.2, 2.2, CR2)
    add_box(8, 25, 2.2, 1.2, 2.2, CR)
    add_box(0, 23, 6, 1, 1, WALL2)
    add_box(0, -24.5, 6, 1, 1, WALL2)
    # dekor pilonlari
    add_box(9, -8, 1, 6, 1, DARK)
    add_box(-9, 8, 1, 6, 1, DARK)
    # karakter sahnesi
    add_box(100, 100, 14, 1.02, 14, C(70, 74, 82), y0=-1.0)


build_map()

SPAWNS_ATK = [(-12, 27), (-6, 27), (0, 27), (6, 27), (12, 27)]
SPAWNS_DFN = [(-12, -27), (-6, -27), (0, -27), (6, -27), (12, -27)]
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
