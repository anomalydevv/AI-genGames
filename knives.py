# -*- coding: utf-8 -*-
"""Bicak tanimlari, 3B modeller, yakin dovus ve 2B yedek ikonlar."""
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


def model(kid):
    k = by_id(kid)
    dark = C(40, 44, 54)
    blade = C(196, 204, 216)
    edge = C(150, 162, 178)
    if kid == "karambit":
        return "Z", [
            (0, -0.03, -0.16, 0.05, 0.075, 0.28, dark),
            (0, 0.06, -0.33, 0.014, 0.02, 0.10, dark),
            (0, -0.08, -0.33, 0.014, 0.02, 0.10, dark),
            (0, -0.01, -0.38, 0.014, 0.16, 0.02, dark),
            (0, -0.01, -0.28, 0.014, 0.16, 0.02, dark),
            (0, 0.02, 0.09, 0.022, 0.10, 0.18, blade),
            (0, 0.10, 0.22, 0.02, 0.09, 0.17, blade),
            (0, 0.19, 0.33, 0.018, 0.07, 0.15, blade),
            (0, 0.26, 0.41, 0.014, 0.04, 0.11, edge),
            (0, -0.085, -0.05, 0.042, 0.012, 0.08, k.color),
        ]
    if kid == "butterfly":
        return "X", [
            (0, -0.055, -0.10, 0.045, 0.055, 0.24, dark),
            (0, 0.045, -0.10, 0.045, 0.055, 0.24, dark),
            (0, -0.055, -0.25, 0.045, 0.045, 0.07, k.color),
            (0, 0.045, -0.25, 0.045, 0.045, 0.07, k.color),
            (0, 0.0, 0.04, 0.03, 0.07, 0.08, edge),
            (0, 0.02, 0.25, 0.02, 0.10, 0.40, blade),
            (0, 0.07, 0.44, 0.014, 0.06, 0.14, edge),
        ]
    return "X", [
        (0, -0.02, -0.11, 0.045, 0.075, 0.28, dark),
        (0, 0.0, 0.04, 0.075, 0.11, 0.04, edge),
        (0, 0.03, 0.22, 0.018, 0.10, 0.32, blade),
        (0, 0.05, 0.42, 0.014, 0.06, 0.16, blade),
        (0, 0.08, 0.53, 0.01, 0.025, 0.10, edge),
        (0, -0.055, -0.13, 0.042, 0.012, 0.10, k.color),
    ]


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


def _tri(x, y, s, a, b, c, col):
    draw_triangle(Vector2(x + a[0] * s, y + a[1] * s), Vector2(x + b[0] * s, y + b[1] * s),
                  Vector2(x + c[0] * s, y + c[1] * s), col)


def _rect(x, y, s, rx, ry, rw, rh, ang, col):
    draw_rectangle_pro(Rectangle(x + rx * s, y + ry * s, rw * s, rh * s), Vector2(0, 0), ang, col)


def _draw(kid, x, y, s, sh):
    metal = C(0, 0, 0, 120) if sh else C(200, 208, 220)
    dark = C(0, 0, 0, 120) if sh else C(48, 52, 62)
    if kid == "karambit":
        _rect(x, y, s, 2, 12, 26, 9, -18, dark)
        _tri(x, y, s, (24, 8), (58, 2), (26, 22), metal)
        _tri(x, y, s, (48, 4), (62, 16), (38, 24), metal)
        if not sh:
            draw_circle(int(x + 8 * s), int(y + 17 * s), int(3 * s), C(0, 230, 200))
    elif kid == "butterfly":
        _rect(x, y, s, 0, 10, 24, 8, 24, dark)
        _rect(x, y, s, 0, 22, 24, 8, -12, dark)
        _tri(x, y, s, (24, 6), (76, 10), (30, 24), metal)
        if not sh:
            draw_circle(int(x + 12 * s), int(y + 12 * s), int(2 * s), C(255, 205, 70))
    else:
        _rect(x, y, s, 0, 12, 24, 10, -12, dark)
        _tri(x, y, s, (22, 6), (80, 4), (24, 20), metal)
        if not sh:
            draw_rectangle(int(x + 4 * s), int(y + 13 * s), int(14 * s), int(4 * s), C(0, 230, 200))


def draw_knife_icon(kid, x, y, scale=1.0):
    _draw(kid, x + 6 * scale, y + 7 * scale, scale, True)
    _draw(kid, x, y, scale, False)
