# -*- coding: utf-8 -*-
"""Kill hype arayuzu: gaza getiren banner, seri gostergesi ve ekran efekti."""
import math

from pyray import *

import icons
from config import C, CYAN, GOLD, RED, SH, SW, cl
from state import g
from ui import R, RL, ctxt, txt, rtxt

_CY = C(0, 235, 210)
_MAG = C(255, 70, 120)
_HOT = C(255, 205, 90)


def _ease_out(k):
    k = cl(k, 0.0, 1.0)
    return 1.0 - (1.0 - k) ** 3


def draw_kill_feed():
    """Her kill icin sagdan kayarak giren, seri vurgulu hype banner'i."""
    base = SH - 250
    t_now = get_time()
    for j, e in enumerate(reversed(g.kills_show)):
        t = e["t"]
        a = min(1.0, t / 0.35)
        slide = _ease_out(min(1.0, (2.8 - t) / 0.28))
        ai = int(255 * a)
        w, h = 520, 66
        x = SW - 24 - w + (1.0 - slide) * 120
        y = base - j * (h + 8)
        hot = _HOT if e["hs"] else _CY
        # govde
        R(x + 4, y + 5, w, h, C(0, 0, 0, int(140 * a)))
        for i in range(6):
            R(x + i * 3, y, 3, h, C(4, 8, 13, int((215 - i * 20) * a)))
        R(x, y, w, h, C(6, 12, 18, int(228 * a)))
        R(x, y, 6, h, C(hot.r, hot.g, hot.b, ai))
        RL(x, y, w, h, C(hot.r, hot.g, hot.b, int(120 * a)), 1.5)
        # ikon
        if e["knife"]:
            icons.draw_knife(e["kid"], x + 16, y + 14, 116, 40, ai)
        else:
            icons.draw_weapon(e["w"], x + 16, y + 14, 116, 40, ai)
        # etiketler
        txt("ELIMINATED", x + 146, y + 6, 13, C(hot.r, hot.g, hot.b, ai))
        if e["hs"]:
            txt("KAFA VURUSU", x + 146 + 96, y + 6, 13, _HOT if ai else _HOT)
        txt(e["name"][:22], x + 146, y + 20, 27, C(255, 255, 255, ai))
        rtxt(e["wname"][:24], x + w - 16, y + 42, 14, C(180, 195, 210, ai))
        # kucuk seri gostergesi
        if g.streak >= 2 and j == 0:
            ctxt("x%d" % g.streak, x - 26, y + 14, 34, _MAG)


def draw_kill_effect():
    """Sessiz hype: kill aninda ekran yumrugu + buyuyen seri (ses yok)."""
    if g.killfx <= 0.0:
        return
    k = cl(g.killfx, 0.0, 1.0)
    fade = k * k
    cx, cy = SW / 2, SH / 2
    col = _HOT if g.killfx_hs else _CY
    # ekran kenari vurgusu (kalin, cift katman)
    th = int(10 + 16 * fade)
    a = int(150 * fade)
    R(0, 0, SW, th, C(col.r, col.g, col.b, a))
    R(0, SH - th, SW, th, C(col.r, col.g, col.b, a))
    R(0, 0, th, SH, C(col.r, col.g, col.b, a))
    R(SW - th, 0, th, SH, C(col.r, col.g, col.b, a))
    th2 = max(2, th // 3)
    a2 = int(200 * fade)
    R(th, th, SW - th * 2, th2, C(255, 255, 255, a2 // 3))
    # merkezden yayilan cift halka + capraz parlama
    rad = 60 + (1.0 - k) * 300
    draw_circle_lines(int(cx), int(cy), int(rad), C(col.r, col.g, col.b, int(150 * fade)))
    draw_circle_lines(int(cx), int(cy), int(rad * 0.72), C(255, 255, 255, int(80 * fade)))
    draw_circle_lines(int(cx), int(cy), int(rad * 0.45), C(col.r, col.g, col.b, int(90 * fade)))
    # kill sayaci / seri (buyuyerek oturan yazi)
    zoom = 1.0 + 0.35 * fade
    if g.streak >= 2:
        ctxt("x%d" % g.streak, cx, cy - 150 - (1 - k) * 24, int(54 * zoom),
             C(col.r, col.g, col.b, int(230 * fade)))
    if g.killfx_hs:
        ctxt("KAFA VURUSU", cx, cy + 90 + (1 - k) * 18, int(30 * zoom),
             C(_HOT.r, _HOT.g, _HOT.b, int(230 * fade)))
    elif g.killfx_knife:
        ctxt("BICAKLA ALDIN", cx, cy + 90 + (1 - k) * 18, int(26 * zoom),
             C(col.r, col.g, col.b, int(220 * fade)))
    if g.streak_t > 0 and g.streak >= 2:
        ctxt("SERI %d  -  DURMA!" % g.streak, cx, SH * 0.72, 26,
             C(_MAG.r, _MAG.g, _MAG.b, int(220 * min(1.0, g.streak_t / 1.0))))
    elif g.streak_t > 0 or (g.killfx > 0.6 and g.streak <= 1):
        ctxt("DEVAM ET", cx, SH * 0.72, 20, C(255, 255, 255, int(150 * fade)))
