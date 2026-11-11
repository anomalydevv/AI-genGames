# -*- coding: utf-8 -*-
"""Silah marketi icin 2B yandan gorunum, golgeli silah ikonlari."""
from pyray import *

from config import C


def _rr(x, y, s, rx, ry, rw, rh, ang, col):
    draw_rectangle_pro(Rectangle(x + rx * s, y + ry * s, rw * s, rh * s), Vector2(0, 0), ang, col)


def _circle(x, y, s, cx, cy, r, col):
    draw_circle(int(x + cx * s), int(y + cy * s), int(r * s), col)


def _tri(x, y, s, a, b, c, col):
    draw_triangle(Vector2(x + a[0] * s, y + a[1] * s), Vector2(x + b[0] * s, y + b[1] * s),
                  Vector2(x + c[0] * s, y + c[1] * s), col)


def _shapes(wi, x, y, s, sh):
    if sh:
        body, light, dark, grip, acc = (C(0, 0, 0, 115),) * 5
    else:
        body, light, dark = C(126, 133, 146), C(176, 184, 198), C(58, 62, 72)
        grip, acc = C(74, 54, 36), C(0, 230, 200)
    if wi == 0:
        _rr(x, y, s, 6, 4, 56, 13, 0, body)
        _rr(x, y, s, 58, 6, 8, 7, 0, light)
        _rr(x, y, s, 16, 12, 17, 36, -14, grip)
        _rr(x, y, s, 18, 14, 12, 18, -14, dark)
        _circle(x, y, s, 40, 19, 5, dark)
        _rr(x, y, s, 8, 2, 6, 3, 0, acc)
    elif wi == 1:
        _rr(x, y, s, 8, 5, 62, 11, 0, body)
        _rr(x, y, s, 68, 7, 10, 5, 0, light)
        _circle(x, y, s, 38, 17, 11, dark)
        _circle(x, y, s, 38, 17, 6, body)
        _rr(x, y, s, 18, 13, 15, 34, -18, grip)
        _tri(x, y, s, (8, 5), (2, 1), (14, 8), light)
        _rr(x, y, s, 62, 2, 4, 4, 0, acc)
    elif wi == 2:
        _rr(x, y, s, 4, 7, 100, 7, 0, body)
        _rr(x, y, s, 104, 5, 8, 5, 0, light)
        _rr(x, y, s, 6, 14, 96, 5, 0, dark)
        _rr(x, y, s, 42, 17, 34, 10, 0, grip)
        _rr(x, y, s, 42, 17, 34, 4, 0, light)
        _rr(x, y, s, 0, 15, 8, 15, 8, dark)
        _rr(x, y, s, 78, 22, 5, 12, 0, dark)
        _rr(x, y, s, 15, 12, 16, 18, 22, grip)
        _rr(x, y, s, 30, 4, 6, 3, 0, acc)
    elif wi == 3:
        _rr(x, y, s, 6, 8, 72, 14, 0, body)
        _rr(x, y, s, 78, 10, 44, 6, 0, light)
        _rr(x, y, s, 122, 9, 8, 4, 0, dark)
        _rr(x, y, s, 26, 3, 30, 5, 0, dark)
        _rr(x, y, s, 30, 1, 22, 3, 0, light)
        _rr(x, y, s, 10, 22, 18, 30, -10, grip)
        _rr(x, y, s, 52, 22, 14, 24, 12, dark)
        _rr(x, y, s, 70, 20, 6, 14, 0, grip)
        _circle(x, y, s, 14, 6, 3, acc)
    else:
        _rr(x, y, s, 2, 8, 78, 11, 0, body)
        _rr(x, y, s, 80, 10, 62, 5, 0, light)
        _rr(x, y, s, 142, 11, 8, 3, 0, dark)
        _rr(x, y, s, 20, 2, 42, 6, 0, dark)
        _rr(x, y, s, 24, 0, 34, 4, 0, light)
        _circle(x, y, s, 46, 5, 4, acc)
        _rr(x, y, s, 6, 19, 20, 28, -12, grip)
        _rr(x, y, s, 28, 20, 10, 12, 0, dark)
        _rr(x, y, s, 100, 16, 3, 18, 18, dark)
        _rr(x, y, s, 100, 16, 3, 18, -18, dark)


def draw_weapon_icon(wi, x, y, scale=1.0):
    _shapes(wi, x + 6 * scale, y + 7 * scale, scale, True)
    _shapes(wi, x, y, scale, False)
