# -*- coding: utf-8 -*-
"""Harita havuzu: 3 farkli, odali ve buyuk arena; A/B bombalari, spawnlar ve
bot yol agi.

Haritalar -42..42 araliginda, 180 derece donusle simetrik oda izgaralarindan
olusturulur; boylece A/B bolgeleri ve takim spawnlari adildir.

Koordinat: x dogu(+)/bati(-), z guney(+)/kuzey(-).
Savunan (DFN) spawn: kuzey-bati kose  |  Saldiran (ATK) spawn: guney-dogu kose
A sitesi: kuzey-dogu oda              |  B sitesi: guney-bati oda
"""
import math
import random

from config import C

BOUND = 42.0
SITE_R = 3.8

BOX = []
ZONES = []
SITES = {}
SPAWNS_ATK = []
SPAWNS_DFN = []
SPAWNS = []
WPS = []
ADJ = []
MAP_INDEX = 0
MAP_NAME = ""

WALL, WALL2, DARK = C(108, 114, 128), C(82, 88, 102), C(64, 70, 84)
CR, CR2, PLANT = C(150, 108, 62), C(112, 96, 80), C(54, 92, 66)
F_ATK, F_DFN = C(122, 58, 58), C(52, 84, 128)
F_A, F_B = C(156, 112, 48), C(52, 132, 122)
F_MID, F_LANE = C(78, 82, 94), C(70, 74, 86)

S_WALL, S_WALL2 = C(92, 116, 124), C(70, 94, 104)
S_F0, S_F1 = C(64, 98, 102), C(74, 108, 110)
K_WALL, K_WALL2 = C(132, 116, 92), C(104, 90, 72)
K_F0, K_F1 = C(104, 92, 74), C(116, 102, 82)

MAPS = [
    dict(name="HEX Bölgesi", short="HEX", cols=5, rows=5, seed=11,
         wall=WALL, wall2=WALL2, base=F_MID, f1=F_LANE,
         atk=F_ATK, dfn=F_DFN, site_a=F_A, site_b=F_B,
         cover1=CR, cover2=CR2, plant=PLANT,
         accent=C(0, 230, 200), accent2=C(255, 60, 140)),
    dict(name="Sarnıç", short="SARNIC", cols=6, rows=4, seed=27,
         wall=S_WALL, wall2=S_WALL2, base=S_F0, f1=S_F1,
         atk=C(110, 66, 54), dfn=C(46, 78, 112),
         site_a=C(150, 126, 66), site_b=C(58, 130, 124),
         cover1=C(66, 118, 94), cover2=C(96, 108, 88), plant=C(44, 128, 102),
         accent=C(80, 240, 210), accent2=C(80, 165, 255)),
    dict(name="Kule", short="KULE", cols=4, rows=4, seed=42,
         wall=K_WALL, wall2=K_WALL2, base=K_F0, f1=K_F1,
         atk=C(124, 74, 48), dfn=C(58, 82, 118),
         site_a=C(166, 132, 58), site_b=C(70, 138, 110),
         cover1=C(174, 128, 72), cover2=C(136, 104, 74), plant=C(92, 122, 84),
         accent=C(255, 190, 80), accent2=C(255, 96, 120)),
]

THEME = {"accent": C(0, 230, 200), "accent2": C(255, 60, 140)}


def add_box(boxes, cx, cz, sx, sy, sz, col, y0=0.0):
    boxes.append((cx - sx / 2, y0, cz - sz / 2, cx + sx / 2, y0 + sy, cz + sz / 2, col))


def floor(boxes, x0, z0, x1, z1, col):
    """Zemin renk yamasi (yurunebilir, sadece gorsel)."""
    add_box(boxes, (x0 + x1) / 2, (z0 + z1) / 2, x1 - x0, 1.02, z1 - z0, col, y0=-1.0)


def _segments(a, b, gaps):
    segs, cur = [], a
    for g0, g1 in sorted(gaps):
        if g0 > cur:
            segs.append((cur, g0))
        cur = max(cur, g1)
    if cur < b:
        segs.append((cur, b))
    return segs


def wall_z(boxes, z, x0, x1, gaps=(), h=5, col=None, t=1.0):
    """Yatay duvar (z sabit, x0..x1). gaps = kapi bosluklari."""
    for a, b in _segments(x0, x1, gaps):
        add_box(boxes, (a + b) / 2, z, b - a, h, t, col or WALL)


def wall_x(boxes, x, z0, z1, gaps=(), h=5, col=None, t=1.0):
    """Dikey duvar (x sabit, z0..z1)."""
    for a, b in _segments(z0, z1, gaps):
        add_box(boxes, x, (a + b) / 2, t, h, b - a, col or WALL)


def _build_room_map(spec):
    rnd = random.Random(spec["seed"])
    boxes, zones = [], []
    cols, rows = spec["cols"], spec["rows"]
    b = BOUND
    span = 2 * b
    cw, ch = span / cols, span / rows

    add_box(boxes, 0, -b - 0.5, span + 2, 8, 1, spec["wall"])
    add_box(boxes, 0, b + 0.5, span + 2, 8, 1, spec["wall"])
    add_box(boxes, -b - 0.5, 0, 1, 8, span + 2, spec["wall"])
    add_box(boxes, b + 0.5, 0, 1, 8, span + 2, spec["wall"])

    dfn_cell = (0, 0)
    atk_cell = (cols - 1, rows - 1)
    a_cell = (cols - 1, 0)
    b_cell = (0, rows - 1)
    reserved = {dfn_cell, atk_cell, a_cell, b_cell}

    def rect(ix, iz):
        return (-b + ix * cw, -b + iz * ch, -b + (ix + 1) * cw, -b + (iz + 1) * ch)

    def center(ix, iz):
        x0, z0, x1, z1 = rect(ix, iz)
        return (x0 + x1) / 2, (z0 + z1) / 2

    for iz in range(rows):
        for ix in range(cols):
            x0, z0, x1, z1 = rect(ix, iz)
            col = spec["f1"] if (ix + iz) % 2 else spec["base"]
            if (ix, iz) == dfn_cell:
                col = spec["dfn"]
            elif (ix, iz) == atk_cell:
                col = spec["atk"]
            elif (ix, iz) == a_cell:
                col = spec["site_a"]
            elif (ix, iz) == b_cell:
                col = spec["site_b"]
            floor(boxes, x0 + 0.06, z0 + 0.06, x1 - 0.06, z1 - 0.06, col)
            name = {(0, 0): "Savunan Spawn", (cols - 1, rows - 1): "Saldiran Spawn",
                    (cols - 1, 0): "A Sitesi", (0, rows - 1): "B Sitesi"}.get((ix, iz))
            zones.append((name or "Oda %d-%d" % (ix + 1, iz + 1), x0, z0, x1, z1))

    for ix in range(1, cols):
        x = -b + ix * cw
        for iz in range(rows):
            z0, z1 = -b + iz * ch, -b + (iz + 1) * ch
            if rnd.random() < 0.22:
                continue
            zc = (z0 + z1) / 2
            dw = min(6.4, ch * 0.42)
            col = spec["wall"] if rnd.random() < 0.5 else spec["wall2"]
            wall_x(boxes, x, z0, z1, [(zc - dw / 2, zc + dw / 2)], col=col)
    for iz in range(1, rows):
        z = -b + iz * ch
        for ix in range(cols):
            x0, x1 = -b + ix * cw, -b + (ix + 1) * cw
            if rnd.random() < 0.22:
                continue
            xc = (x0 + x1) / 2
            dw = min(6.4, cw * 0.42)
            col = spec["wall"] if rnd.random() < 0.5 else spec["wall2"]
            wall_z(boxes, z, x0, x1, [(xc - dw / 2, xc + dw / 2)], col=col)

    for iz in range(rows):
        for ix in range(cols):
            if (ix, iz) in reserved:
                continue
            cx, cz = center(ix, iz)
            for _ in range(rnd.randint(1, 3)):
                ox = rnd.choice((-1.0, 1.0)) * cw * 0.27
                oz = rnd.choice((-1.0, 1.0)) * ch * 0.27
                size = 1.2 + rnd.random() * 1.1
                add_box(boxes, cx + ox, cz + oz, size, 0.8 + rnd.random() * 0.5, size,
                        rnd.choice((spec["cover1"], spec["cover2"], spec["plant"])))
            if rnd.random() < 0.3:
                add_box(boxes, cx + rnd.choice((-1.0, 1.0)) * cw * 0.18, cz,
                        1.0, 4.8, 1.0, DARK)

    for cell in (dfn_cell, atk_cell):
        cx, cz = center(*cell)
        add_box(boxes, cx + cw * 0.34, cz + ch * 0.34, 1.5, 1.0, 1.5, spec["cover2"])
        add_box(boxes, cx - cw * 0.34, cz - ch * 0.34, 1.5, 1.0, 1.5, spec["cover1"])
    for cell in (a_cell, b_cell):
        cx, cz = center(*cell)
        add_box(boxes, cx + cw * 0.32, cz - ch * 0.32, 1.8, 1.1, 1.8, spec["cover1"])
        add_box(boxes, cx - cw * 0.30, cz + ch * 0.30, 1.5, 0.9, 1.5, spec["plant"])
        add_box(boxes, cx + cw * 0.30, cz + ch * 0.30, 1.2, 4.8, 1.2, spec["wall2"])

    def spawn_pts(cell):
        cx, cz = center(*cell)
        off = min(cw, ch) * 0.17
        return [(cx - off, cz - off), (cx + off, cz - off),
                (cx - off, cz + off), (cx + off, cz + off), (cx, cz)]

    atk = spawn_pts(atk_cell)
    dfn = spawn_pts(dfn_cell)
    sites = {"A": center(*a_cell), "B": center(*b_cell)}
    wps, adj = _waypoints(boxes)
    return dict(boxes=boxes, zones=zones, sites=sites, atk=atk, dfn=dfn, wps=wps, adj=adj)


def _in_boxes(x, z, m, boxes):
    for b in boxes:
        if b[0] - m < x < b[3] + m and b[2] - m < z < b[5] + m and b[1] < 1.5 and b[4] > 0.3 and b[1] > -0.5:
            return True
    return False


def _waypoints(boxes):
    step = 3.0
    base = -BOUND + step
    lim = BOUND - step
    pts = []
    v = base
    while v <= lim + 0.01:
        w = base
        while w <= lim + 0.01:
            if not _in_boxes(v, w, 0.7, boxes):
                pts.append((v, w))
            w += step
        v += step
    cells = {}
    for i, (x, z) in enumerate(pts):
        cells[(int(round((x - base) / step)), int(round((z - base) / step)))] = i
    adj = []
    offs = ((0, 1), (0, -1), (1, 0), (-1, 0), (0, 2), (0, -2), (2, 0), (-2, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1))
    for a in pts:
        ci = int(round((a[0] - base) / step))
        cj = int(round((a[1] - base) / step))
        ns = []
        for ox, oz in offs:
            j = cells.get((ci + ox, cj + oz))
            if j is None:
                continue
            pb = pts[j]
            d = math.hypot(a[0] - pb[0], a[1] - pb[1])
            if d > 7.0:
                continue
            ok = True
            n = int(d / 0.6) + 1
            for k in range(1, n):
                t = k / n
                if _in_boxes(a[0] + (pb[0] - a[0]) * t, a[1] + (pb[1] - a[1]) * t, 0.45, boxes):
                    ok = False
                    break
            if ok:
                ns.append(j)
        adj.append(ns)
    return pts, adj


def select_map(index):
    """Harita havuzundan bir haritayi yukler; geometri listeleri yerinde guncellenir."""
    global MAP_INDEX, MAP_NAME
    index = max(0, min(len(MAPS) - 1, int(index)))
    spec = MAPS[index]
    data = spec.get("data")
    if data is None:
        data = _build_room_map(spec)
        spec["data"] = data
    MAP_INDEX, MAP_NAME = index, spec["name"]
    THEME["accent"] = spec["accent"]
    THEME["accent2"] = spec["accent2"]
    BOX[:] = data["boxes"]
    ZONES[:] = data["zones"]
    SITES.clear()
    SITES.update(data["sites"])
    SPAWNS_ATK[:] = data["atk"]
    SPAWNS_DFN[:] = data["dfn"]
    SPAWNS[:] = SPAWNS_ATK + SPAWNS_DFN
    WPS[:] = data["wps"]
    ADJ[:] = data["adj"]
    return MAP_NAME


def in_box(x, z, m):
    return _in_boxes(x, z, m, BOX)


def zone_at(x, z):
    for name, x0, z0, x1, z1 in ZONES:
        if x0 <= x <= x1 and z0 <= z <= z1:
            return name
    return "Harita"


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


select_map(0)
