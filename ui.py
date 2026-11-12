# -*- coding: utf-8 -*-
"""2B UI yardimcilari: font, metin, buton, slider, toggle, panel."""

from pyray import *
from config import C, CYAN, cl

FOLD = str.maketrans("ğüşıöçĞÜŞİÖÇ", "gusiocGUSIOC")
FONT = None
VIEW_SCALE = 1.0
VIEW_OX = 0.0
VIEW_OY = 0.0


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
    # Hafif golge, metnin okunabilirligini artirir.
    draw_text_ex(FONT, s, Vector2(x + 1, y + 1), float(size), 1.0, C(0, 0, 0, 145)) if FONT else draw_text(s, int(x + 1), int(y + 1), int(size), C(0, 0, 0, 145))
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


def RL(x, y, w, h, col, t=2):
    draw_rectangle_lines_ex(Rectangle(x, y, w, h), t, col)


def mouse_in(x, y, w, h):
    m = mouse_pos()
    return x <= m.x <= x + w and y <= m.y <= y + h


def _line(x1, y1, x2, y2, col, thick=1.0):
    draw_line_ex(Vector2(x1, y1), Vector2(x2, y2), thick, col)


def _accent(x, y, w, col=CYAN, thickness=3):
    R(x, y, w, thickness, col)


def button(x, y, w, h, label, size=24, active=False, enabled=True):
    hov = enabled and mouse_in(x, y, w, h)

    # Derinlik ve koyu cam panel hissi.
    R(x + 2, y + 3, w, h, C(0, 0, 0, 95))
    bg = C(0, 190, 175, 58) if active else (
        C(35, 70, 82, 225) if hov else C(14, 20, 29, 235)
    )
    R(x, y, w, h, bg)

    # Sol kenar vurgusu ve ince ust isik cizgisi.
    _accent(x + 1, y + 1, max(0, w - 2), C(0, 235, 210, 210 if (hov or active) else 90), 2)
    R(x + 1, y + 3, 2, max(0, h - 6), C(0, 220, 200, 190 if (hov or active) else 65))

    border = C(0, 235, 210, 235 if (hov or active) else 105)
    RL(x, y, w, h, border, 1.5)

    # Hover durumunda alt kenarda ek parlama.
    if hov:
        _line(x + 7, y + h - 2, x + w - 7, y + h - 2, C(0, 230, 205, 170), 2)

    text_col = WHITE if enabled else C(115, 125, 135, 255)
    ctxt(label, x + w / 2, y + h / 2 - size / 2 - 1, size, text_col)
    return hov and is_mouse_button_pressed(MOUSE_BUTTON_LEFT)


def slider(x, y, w, label, val, lo, hi, fmt="%.2f"):
    txt(label + ": " + (fmt % val), x, y, 22, WHITE)

    by = y + 37
    bar_h = 5
    R(x, by, w, bar_h, C(48, 59, 72, 255))

    span = hi - lo
    t = cl((val - lo) / span, 0.0, 1.0) if span else 0.0
    fill_w = w * t

    R(x, by, fill_w, bar_h, CYAN)
    # Olcek isaretleri.
    for i in range(1, 5):
        tx = x + w * i / 5
        R(tx, by - 2, 1, bar_h + 4, C(125, 145, 155, 115))

    knob_x = x + fill_w
    draw_circle(int(knob_x), int(by + bar_h / 2), 9, C(0, 220, 200, 55))
    draw_circle(int(knob_x), int(by + bar_h / 2), 6, WHITE)
    draw_circle_lines(int(knob_x), int(by + bar_h / 2), 8, CYAN)

    m = mouse_pos()
    if (
        span != 0
        and is_mouse_button_down(MOUSE_BUTTON_LEFT)
        and x - 12 <= m.x <= x + w + 12
        and by - 14 <= m.y <= by + 20
    ):
        val = lo + cl((m.x - x) / max(w, 0.0001), 0, 1) * span

    return val


def toggle(x, y, label, val):
    hov = mouse_in(x, y, 260, 30)
    R(x + 1, y + 2, 29, 27, C(0, 0, 0, 90))
    R(x, y, 28, 28, C(14, 20, 29, 240))
    RL(x, y, 28, 28, C(0, 230, 205, 210 if hov or val else 105), 1.5)

    if val:
        R(x + 5, y + 5, 18, 18, C(0, 210, 190, 255))
        _line(x + 9, y + 14, x + 13, y + 18, WHITE, 2)
        _line(x + 13, y + 18, x + 20, y + 10, WHITE, 2)
    elif hov:
        R(x + 9, y + 9, 10, 10, C(0, 210, 190, 65))

    txt(label, x + 40, y + 2, 22, WHITE if hov else C(210, 220, 228, 255))

    if hov and is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
        return not val
    return val


def panel(x, y, w, h):
    # Golge + koyu govde.
    R(x + 4, y + 5, w, h, C(0, 0, 0, 100))
    R(x, y, w, h, C(8, 12, 19, 232))

    # Ust kenar isigi, cerceve ve ic cizgi.
    _accent(x + 1, y + 1, max(0, w - 2), C(0, 225, 200, 175), 2)
    RL(x, y, w, h, C(0, 220, 200, 115), 1.5)
    if w > 12 and h > 12:
        RL(x + 5, y + 5, w - 10, h - 10, C(75, 105, 120, 45), 1)

    # Kose detaylari.
    corner = C(0, 235, 210, 210)
    arm = min(15, max(4, w / 8), max(4, h / 8))
    _line(x, y + arm, x, y, corner, 2)
    _line(x, y, x + arm, y, corner, 2)
    _line(x + w - arm, y + h, x + w, y + h, corner, 2)
    _line(x + w, y + h - arm, x + w, y + h, corner, 2)
