# -*- coding: utf-8 -*-
"""2B UI yardimcilari: font, metin, buton, slider, toggle, panel."""
from pyray import *

from config import C, CYAN, cl

FOLD = str.maketrans("ğüşıöçĞÜŞİÖÇ", "gusiocGUSIOC")
FONT = None


def set_font(font):
    global FONT
    FONT = font


def T(s):
    return s if FONT else s.translate(FOLD)


def txt(s, x, y, size, col):
    s = T(s)
    if FONT:
        draw_text_ex(FONT, s, Vector2(x, y), float(size), 1.0, col)
    else:
        draw_text(s, int(x), int(y), int(size), col)


def tw(s, size):
    s = T(s)
    return measure_text_ex(FONT, s, float(size), 1.0).x if FONT else measure_text(s, int(size))


def ctxt(s, cx, y, size, col):
    txt(s, cx - tw(s, size) / 2, y, size, col)


def rtxt(s, rx, y, size, col):
    txt(s, rx - tw(s, size), y, size, col)


def R(x, y, w, h, col):
    draw_rectangle(int(x), int(y), int(w), int(h), col)


def RL(x, y, w, h, col, t=2):
    draw_rectangle_lines_ex(Rectangle(x, y, w, h), t, col)


def mouse_in(x, y, w, h):
    m = get_mouse_position()
    return x <= m.x <= x + w and y <= m.y <= y + h


def button(x, y, w, h, label, size=24, active=False, enabled=True):
    hov = enabled and mouse_in(x, y, w, h)
    R(x, y, w, h, C(0, 200, 180, 110) if active else (C(0, 200, 180, 70) if hov else C(14, 20, 28, 215)))
    RL(x, y, w, h, C(0, 230, 200, 255 if (hov or active) else 110), 2)
    ctxt(label, x + w / 2, y + h / 2 - size / 2 - 1, size, WHITE if enabled else GRAY)
    return hov and is_mouse_button_pressed(MOUSE_BUTTON_LEFT)


def slider(x, y, w, label, val, lo, hi, fmt="%.2f"):
    txt(label + ": " + (fmt % val), x, y, 22, WHITE)
    by = y + 34
    R(x, by, w, 6, C(60, 70, 82))
    t = (val - lo) / (hi - lo)
    R(x, by, w * t, 6, CYAN)
    draw_circle(int(x + w * t), int(by + 3), 9, WHITE)
    m = get_mouse_position()
    if is_mouse_button_down(MOUSE_BUTTON_LEFT) and x - 12 <= m.x <= x + w + 12 and by - 14 <= m.y <= by + 20:
        val = lo + cl((m.x - x) / w, 0, 1) * (hi - lo)
    return val


def toggle(x, y, label, val):
    R(x, y, 28, 28, C(14, 20, 28, 220))
    RL(x, y, 28, 28, CYAN, 2)
    if val:
        R(x + 6, y + 6, 16, 16, CYAN)
    txt(label, x + 40, y + 2, 22, WHITE)
    if mouse_in(x, y, 260, 28) and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
        return not val
    return val


def panel(x, y, w, h):
    R(x, y, w, h, C(8, 12, 18, 215))
    RL(x, y, w, h, C(0, 230, 200, 90), 2)
