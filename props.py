# -*- coding: utf-8 -*-
"""Harita dekorlari ve esyalar: sandik, varil, kolon, kum torbasi, isik."""
import math

from config import C


def _sh(col, f):
    return C(max(0, min(255, int(col.r * f))),
             max(0, min(255, int(col.g * f))),
             max(0, min(255, int(col.b * f))), col.a)


def _box(lst, cx, cz, sx, sy, sz, col, y0=0.0):
    lst.append((cx - sx / 2, y0, cz - sz / 2, cx + sx / 2, y0 + sy, cz + sz / 2, col))


def crate(boxes, decor, x, z, s, col, rnd, y0=0.0):
    h = s * 0.92
    _box(boxes, x, z, s, h, s, col, y0)
    dark = _sh(col, 0.62)
    light = _sh(col, 1.22)
    t = max(0.06, s * 0.07)
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        _box(decor, x + dx * (s / 2 - t / 2), z + dz * (s / 2 - t / 2),
             t, h, t, dark, y0)
    _box(decor, x, z, s * 1.01, t, s * 1.01, light, y0 + h - t)
    _box(decor, x, z, s * 0.96, 0.02, s * 0.96, _sh(col, 1.35), y0 + h + 0.01)
    if rnd.random() < 0.45:
        s2 = s * 0.62
        _box(boxes, x + rnd.choice((-1, 1)) * s * 0.18, z + rnd.choice((-1, 1)) * s * 0.18,
             s2, s2 * 0.85, s2, _sh(col, 0.9), y0 + h)


def barrel(boxes, decor, x, z, col, rnd):
    r = 0.44 + rnd.random() * 0.10
    h = 1.15
    seg = 10
    body = C(col.r, col.g, col.b)
    for i in range(seg):
        a = i * math.tau / seg
        bx = x + math.cos(a) * r * 0.88
        bz = z + math.sin(a) * r * 0.88
        _box(boxes, bx, bz, r * 0.72, h, r * 0.72, _sh(body, 0.88 + 0.14 * (i % 2)))
    _box(decor, x, z, r * 1.9, 0.10, r * 1.9, _sh(body, 0.55), h * 0.35)
    _box(decor, x, z, r * 1.9, 0.10, r * 1.9, _sh(body, 0.55), h * 0.72)
    _box(decor, x, z, r * 1.7, 0.06, r * 1.7, _sh(body, 1.25), h - 0.02)
    _box(decor, x, z, r * 0.55, 0.04, r * 0.55, _sh(body, 0.5), h + 0.04)


def pillar(boxes, decor, x, z, col, h=5.0, s=1.1):
    _box(boxes, x, z, s * 1.45, 0.35, s * 1.45, _sh(col, 0.72))
    _box(boxes, x, z, s, h - 0.7, s, col, 0.35)
    for i in range(3):
        _box(decor, x, z, s * 1.04, 0.10, s * 1.04, _sh(col, 0.86), 1.0 + i * 1.4)
    _box(decor, x, z, s * 1.35, 0.28, s * 1.35, _sh(col, 1.12), h - 0.35)
    _box(decor, x, z, s * 0.55, 0.05, s * 0.55, col, h - 0.05)


def sandbags(boxes, decor, x, z, col, rnd):
    for row in range(3):
        n = 3 - row
        for i in range(n):
            ox = (i - (n - 1) / 2) * 0.62
            _box(boxes, x + ox, z + row * 0.06, 0.58, 0.30, 0.82,
                 _sh(col, 0.82 + 0.16 * ((i + row) % 2)), row * 0.28)
    _box(decor, x, z, 1.9, 0.02, 0.9, _sh(col, 0.6), 0.90)


def terminal(decor, x, z, yaw, col, accent):
    c, s = math.cos(yaw), math.sin(yaw)
    _box(decor, x, z, 1.7, 0.12, 0.8, _sh(col, 0.75), 0.82)
    for ox, oz in ((-0.72, -0.3), (0.72, -0.3), (-0.72, 0.3), (0.72, 0.3)):
        _box(decor, x + ox * c - oz * s, z + ox * s + oz * c,
             0.08, 0.8, 0.08, _sh(col, 0.55), 0.02)
    _box(decor, x, z, 0.9, 0.55, 0.08, C(10, 16, 20), 0.94)
    _box(decor, x, z, 0.82, 0.44, 0.02, _sh(accent, 0.85), 0.99)
    _box(decor, x, z, 1.15, 0.10, 0.72, col, 0.72)


def pipes(decor, x, z, length, yaw, col, accent):
    c, s = math.cos(yaw), math.sin(yaw)
    for i, yy in enumerate((1.8, 2.35, 2.9)):
        px = x + (-s) * (i - 1) * 0.16
        pz = z + (c) * (i - 1) * 0.16
        _box(decor, px, pz, 0.13, 0.13, length, _sh(col, 0.7 + 0.1 * i), yy)
        _box(decor, px, pz, 0.17, 0.17, 0.06, _sh(accent, 0.9), yy + 0.05)
    for k in range(3):
        off = (k - 1) * length * 0.38
        _box(decor, x - s * off, z + c * off, 1.0, 0.08, 0.10, _sh(col, 0.55), 3.1)


def light(decor, x, z, accent, y=4.6):
    _box(decor, x, z, 1.3, 0.10, 0.32, C(20, 24, 28), y)
    _box(decor, x, z, 1.1, 0.05, 0.20, _sh(accent, 1.2), y - 0.05)
    _box(decor, x, z, 0.05, 0.55, 0.05, C(60, 64, 70), y + 0.1)


def sign(decor, x, z, yaw, col, accent):
    c, s = math.cos(yaw), math.sin(yaw)
    _box(decor, x, z, 1.5, 0.5, 0.06, _sh(col, 0.8), 2.6)
    _box(decor, x, z, 1.34, 0.34, 0.08, _sh(accent, 0.95), 2.68)
