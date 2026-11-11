# -*- coding: utf-8 -*-
"""Sabitler, renkler ve kucuk matematik yardimcilari."""
import math

from pyray import Color

SW, SH = 1280, 720
DEG = math.pi / 180.0


def C(r, g_, b, a=255):
    return Color(int(r), int(g_), int(b), int(a))


def cl(v, a, b):
    return a if v < a else b if v > b else v


def lerpf(a, b, t):
    return a + (b - a) * t


def wrap(a):
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


CYAN = C(0, 230, 200)
RED = C(255, 60, 80)
GOLD = C(255, 205, 70)

cfg = dict(sens=1.2, fov=95, bob=True, sway=True, fx=True, fps=True, crosshair=2)
