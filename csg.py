# -*- coding: utf-8 -*-
"""Kucuk, eksen hizali CSG yardimcisi: AABB kutulardan kutu cikarma.

Harita duvarlarinda kapi/pencere acmak icin kullanilir. Cikarma islemi
kaynak kutuyu en fazla 6 parcaya boler; parcalar ayni renk/malzemeyi korur.
"""
from config import C


def _ov(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0)


def intersects(a, b, eps=1e-6):
    return (_ov(a[0], a[3], b[0], b[3]) > eps and
            _ov(a[1], a[4], b[1], b[4]) > eps and
            _ov(a[2], a[5], b[2], b[5]) > eps)


def subtract(a, b):
    """a - b; a'nin rengini koruyan eksen hizali kutular dondurur."""
    if not intersects(a, b):
        return [a]
    col = a[6]
    ax0, ay0, az0, ax1, ay1, az1 = a[:6]
    bx0, by0, bz0 = max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2])
    bx1, by1, bz1 = min(a[3], b[3]), min(a[4], b[4]), min(a[5], b[5])
    out = []

    def put(x0, y0, z0, x1, y1, z1):
        if x1 - x0 > 1e-4 and y1 - y0 > 1e-4 and z1 - z0 > 1e-4:
            out.append((x0, y0, z0, x1, y1, z1, col))

    put(ax0, ay0, az0, bx0, ay1, az1)
    put(bx1, ay0, az0, ax1, ay1, az1)
    put(bx0, ay0, az0, bx1, by0, az1)
    put(bx0, by1, az0, bx1, ay1, az1)
    put(bx0, by0, az0, bx1, by1, bz0)
    put(bx0, by0, bz1, bx1, by1, az1)
    return out


def subtract_all(boxes, cutters):
    out = list(boxes)
    for c in cutters:
        nxt = []
        for b in out:
            nxt.extend(subtract(b, c))
        out = nxt
    return out


def cutter(cx, cy, cz, sx, sy, sz):
    return (cx - sx / 2, cy - sy / 2, cz - sz / 2,
            cx + sx / 2, cy + sy / 2, cz + sz / 2, C(0, 0, 0))


def doorway(x, z, width, height=3.1, thickness=1.4):
    """Zemin seviyesinden yukari acilan kapi boslugu (lintel ustte kalir)."""
    return cutter(x, height / 2, z, width, height, thickness)


def window(x, y, z, width, height, thickness=1.4):
    return cutter(x, y, z, width, height, thickness)
