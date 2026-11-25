# -*- coding: utf-8 -*-
"""2B UI bilesenleri: duz, editoryal/askeri stil; fare altindaki oge beyaz parlar."""
from pyray import *
from config import C, CYAN, cl

FOLD = str.maketrans("ğüşıöçĞÜŞİÖÇ", "gusiocGUSIOC")
FONT = None
VIEW_SCALE = 1.0
VIEW_OX = 0.0
VIEW_OY = 0.0

INK = C(238, 240, 242)
MUTED = C(120, 130, 140)
HAIR = C(255, 255, 255, 40)
HAIR_HOT = C(255, 255, 255, 235)
ACCENT = C(214, 255, 66)
SURF = C(7, 10, 13, 228)
SURF_HOT = C(20, 26, 31, 240)


def set_font(font):
    global FONT
    FONT = font


def set_view(scale, ox, oy):
    global VIEW_SCALE, VIEW_OX, VIEW_OY
    VIEW_SCALE = max(0.0001, scale)
    VIEW_OX = ox
    VIEW_OY = oy


def mouse_pos():
    m = get_mouse_position()
    return Vector2((m.x - VIEW_OX) / VIEW_SCALE, (m.y - VIEW_OY) / VIEW_SCALE)


def mouse_delta():
    d = get_mouse_delta()
    return Vector2(d.x / VIEW_SCALE, d.y / VIEW_SCALE)


def T(s):
    return s if FONT else s.translate(FOLD)


def txt(s, x, y, size, col):
    s = T(s)
    draw_text_ex(FONT, s, Vector2(x + 1, y + 1), float(size), 1.0,
                 C(0, 0, 0, 150)) if FONT else draw_text(s, int(x + 1), int(y + 1), int(size), C(0, 0, 0, 150))
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
    draw_rectangle(int(x), int(y), max(0, int(w)), max(0, int(h)), col)


def RL(x, y, w, h, col, t=1):
    draw_rectangle_lines_ex(Rectangle(x, y, w, h), t, col)


def mouse_in(x, y, w, h):
    m = mouse_pos()
    return x <= m.x <= x + w and y <= m.y <= y + h


def _line(x1, y1, x2, y2, col, thick=1.0):
    draw_line_ex(Vector2(x1, y1), Vector2(x2, y2), thick, col)


def _glow(x, y, w, h, strength=1.0, rgb=(255, 255, 255)):
    for i in range(6, 0, -1):
        a = int(6 + 5 * strength * (1.0 - i / 7.0))
        R(x - i * 3, y - i * 3, w + i * 6, h + i * 6,
          C(rgb[0], rgb[1], rgb[2], max(0, a)))


def _corners(x, y, w, h, col, arm=9):
    _line(x, y + arm, x, y, col, 2)
    _line(x, y, x + arm, y, col, 2)
    _line(x + w - arm, y, x + w, y, col, 2)
    _line(x + w, y, x + w, y + arm, col, 2)
    _line(x, y + h - arm, x, y + h, col, 2)
    _line(x, y + h, x + arm, y + h, col, 2)
    _line(x + w - arm, y + h, x + w, y + h, col, 2)
    _line(x + w, y + h - arm, x + w, y + h, col, 2)


def cursor_glow():
    """Farenin altinda yumusak beyaz isik; UI bunun uzerine cizilir."""
    m = mouse_pos()
    begin_blend_mode(BLEND_ADDITIVE)
    for i in range(10, 0, -1):
        a = int(1.5 * i)
        draw_circle(int(m.x), int(m.y), int(7 * i), C(220, 235, 245, a))
    end_blend_mode()


def button(x, y, w, h, label, size=24, active=False, enabled=True):
    hov = enabled and mouse_in(x, y, w, h)
    if hov:
        _glow(x, y, w, h, 1.0)
    R(x, y, w, h, SURF_HOT if hov else SURF)
    if active:
        R(x, y, 4, h, ACCENT)
    border = HAIR_HOT if hov else (C(214, 255, 66, 200) if active else HAIR)
    RL(x, y, w, h, border, 1.5 if hov else 1)
    _corners(x, y, w, h, C(255, 255, 255, 210 if hov else 60), 8)
    if hov:
        R(x + 1, y + 1, max(0, w - 2), 1, C(255, 255, 255, 220))
    text_col = INK if enabled else C(100, 108, 116)
    ctxt(label, x + w / 2, y + h / 2 - size / 2 - 1, size, text_col)
    return hov and is_mouse_button_pressed(MOUSE_BUTTON_LEFT)


def slider(x, y, w, label, val, lo, hi, fmt="%.2f"):
    txt(label + ": " + (fmt % val), x, y, 22, INK)
    by = y + 37
    bar_h = 3
    R(x, by, w, bar_h, C(255, 255, 255, 45))
    span = hi - lo
    t = cl((val - lo) / span, 0.0, 1.0) if span else 0.0
    fill_w = w * t
    R(x, by, fill_w, bar_h, INK)
    for i in range(1, 5):
        R(x + w * i / 5, by - 3, 1, bar_h + 6, C(255, 255, 255, 55))
    knob_x = x + fill_w
    hov = mouse_in(x - 18, by - 16, w + 36, 32)
    if hov:
        for i in range(4, 0, -1):
            draw_circle(int(knob_x), int(by + 1), 6 + i * 2, C(255, 255, 255, 12))
    draw_circle(int(knob_x), int(by + 1), 5, INK)
    draw_circle_lines(int(knob_x), int(by + 1), 6, C(255, 255, 255, 200 if hov else 120))
    m = mouse_pos()
    if (span != 0 and is_mouse_button_down(MOUSE_BUTTON_LEFT)
            and x - 18 <= m.x <= x + w + 18 and by - 16 <= m.y <= by + 18):
        val = lo + cl((m.x - x) / max(w, 0.0001), 0, 1) * span
    return val


def toggle(x, y, label, val):
    hov = mouse_in(x, y, 260, 30)
    if hov:
        _glow(x, y, 28, 28, 0.8)
    R(x, y, 28, 28, SURF_HOT if hov else SURF)
    RL(x, y, 28, 28, HAIR_HOT if hov else HAIR, 1)
    if val:
        R(x + 6, y + 6, 16, 16, ACCENT)
        _line(x + 10, y + 14, x + 13, y + 17, C(8, 10, 12), 2)
        _line(x + 13, y + 17, x + 19, y + 10, C(8, 10, 12), 2)
    elif hov:
        R(x + 10, y + 10, 8, 8, C(255, 255, 255, 55))
    txt(label, x + 40, y + 2, 22, INK if hov else C(205, 212, 220))
    if hov and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
        return not val
    return val


def panel(x, y, w, h):
    R(x, y, w, h, SURF)
    RL(x, y, w, h, HAIR, 1)
    _corners(x, y, w, h, C(255, 255, 255, 120), 12)
    R(x + 10, y + 1, max(0, w - 20), 1, C(255, 255, 255, 90))
