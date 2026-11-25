# -*- coding: utf-8 -*-
"""Ana menu: editoryal/askeri minimal duzen, sol ray ve kelebek animasyonu.

Tasarim referansi: WAR (Hadjoudj Idris) ve CS2 tarzi sade, duz, acili arayuz.
Gereksiz grid/scanline/readout yok; hiyerarsi agirlik, olcek ve tek beyaz
secim cubugundan gelir.
"""
import math

from pyray import *

import characters
import knives
import playerdata
import skins
from config import C, SH, SW, cl
from state import g
from ui import R, ctxt, mouse_in, mouse_pos, rtxt, txt, tw

_ITEMS = [
    ("OZEL MAC KUR", "Botlari, tur hedefini ve haritayi ayarla", "setup", "01"),
    ("KARAKTER", "Skill setini ve savas stilini sec", "char", "02"),
    ("MAGAZA", "Bicak ve silah kaplamalari", "shop", "03"),
    ("AYARLAR", "Hassasiyet, FOV ve efektler", "settings", "04"),
    ("CIKIS", "Oyunu kapat", "quit", "05"),
]

_INK = C(236, 238, 240)
_MUTED = C(128, 136, 146)
_LINE = C(255, 255, 255, 34)
_ACCENT = C(214, 255, 66)   # tek vurgu: asit yesili
_AMBER = C(255, 166, 64)


def _skew_quad(x, y, w, h, skew, col):
    draw_triangle(Vector2(x + skew, y), Vector2(x + w + skew, y),
                  Vector2(x + w, y + h), col)
    draw_triangle(Vector2(x + skew, y), Vector2(x + w, y + h),
                  Vector2(x, y + h), col)


def _butterfly(x, y, size, t, phase, col, col2):
    flap = 0.18 + 0.82 * abs(math.sin(t * 8.2 + phase))
    x += math.sin(t * 0.8 + phase) * size * 2.0
    y += math.sin(t * 1.5 + phase) * size * 0.9
    for side in (-1, 1):
        wx = x + side * size * (0.35 + flap * 1.15)
        wy = y - size * (0.15 + flap * 0.75)
        draw_triangle(Vector2(x, y), Vector2(wx, wy),
                      Vector2(x + side * size * 0.16, y + size * 0.72),
                      col)
        wx2 = x + side * size * (0.28 + flap * 0.78)
        wy2 = y + size * (0.12 + flap * 0.45)
        draw_triangle(Vector2(x, y), Vector2(wx2, wy2),
                      Vector2(x + side * size * 0.20, y + size * 0.92),
                      col2)
    draw_line_ex(Vector2(x, y - size * 0.35), Vector2(x, y + size * 0.95),
                 1.2, C(18, 20, 24, 235))


def _swarm(t):
    for px, py, sz, sp, c1, c2 in (
            (SW * 0.72, SH * 0.24, 9, 0.0, C(214, 255, 66, 120), C(255, 255, 255, 55)),
            (SW * 0.82, SH * 0.46, 6, 2.2, C(255, 166, 64, 120), C(255, 255, 255, 45)),
            (SW * 0.66, SH * 0.66, 7, 4.0, C(255, 255, 255, 95), C(214, 255, 66, 45)),
            (SW * 0.88, SH * 0.30, 4, 5.1, C(255, 255, 255, 80), C(255, 166, 64, 45))):
        _butterfly(px, py, sz, t, sp, c1, c2)


def _contours(t):
    # harita izgara hissi yerine hafif topografya cizgileri (cok dusuk kontrast)
    for i in range(14):
        yy = 90 + i * 46
        amp = 14 + (i % 4) * 9
        prev = None
        for sx in range(0, SW + 40, 40):
            v = yy + math.sin(sx * 0.004 + i * 0.7 + t * 0.08) * amp
            if prev is not None:
                draw_line_ex(Vector2(sx - 40, prev), Vector2(sx, v), 1,
                             C(255, 255, 255, 8))
            prev = v


def _rail(t):
    x = 40
    R(x, 0, 2, SH, C(255, 255, 255, 26))
    R(x + 2, 0, 6, SH, C(0, 0, 0, 60))
    # asagi akan asit noktasi
    yy = (t * 90) % SH
    R(x - 1, yy, 4, 34, C(_ACCENT.r, _ACCENT.g, _ACCENT.b, 210))
    for i in range(11):
        R(x - 7, 40 + i * 60, 14, 1, C(255, 255, 255, 38))


def _nav_row(x, y, w, idx, title, desc, hovered, number):
    if hovered:
        _skew_quad(x - 14, y - 6, w, 50, -13, _INK)
        col = C(12, 14, 16)
    else:
        col = _INK
    txt(number, x, y - 2, 13, C(12, 14, 16) if hovered else _MUTED)
    txt(title, x + 42, y - 12, 31, col)
    if hovered:
        txt(desc, x + 44, y + 22, 13, C(38, 42, 46))
    draw_line_ex(Vector2(x, y + 48), Vector2(x + w, y + 48), 1,
                 C(12, 14, 16, 120) if hovered else _LINE)
    return mouse_in(x - 14, y - 10, w + 20, 58) and is_mouse_button_pressed(MOUSE_BUTTON_LEFT)


def screen_main():
    t = get_time()
    R(0, 0, SW, SH, C(3, 5, 7, 130))
    # sol taraf koyu kagit, saga dogru seffaf
    for i in range(28):
        a = int(236 - i * 8)
        R(i * 16, 0, 18, SH, C(4, 6, 8, max(30, a)))
    _contours(t)
    _rail(t)

    # dev dikey watermark
    txt("07", SW - 300, SH * 0.16, 300, C(255, 255, 255, 10))
    txt("TACTICAL / BOMB DEFUSE", SW - 296, SH * 0.16 + 292, 12, C(255, 255, 255, 46))

    # kelime isareti: iki satir, keskin slash
    txt("HEX", 78, 64, 118, _INK)
    txt("ARENA", 80, 172, 118, C(255, 255, 255, 255))
    _skew_quad(80, 296, 300, 4, -10, _ACCENT)
    txt("OZEL MAC  //  BOMBA MODU", 82, 308, 14, _MUTED)
    txt("BIR SONRAKI ROUND SENIN.", 82, 328, 14, C(255, 255, 255, 120))

    # ust bilgi
    souls = playerdata.souls()
    txt("RUH", SW - 250, 42, 12, _MUTED)
    rtxt("%d" % souls, SW - 70, 34, 30, _ACCENT)
    txt("AKTIF PROFIL", SW - 250, 66, 12, _MUTED)
    rtxt(g.names[7][:12], SW - 70, 62, 16, _INK)

    # navigasyon
    hover_idx = -1
    ny = 358
    for i, (title, desc, target, num) in enumerate(_ITEMS):
        yy = ny + i * 50
        if mouse_in(64, yy - 10, 440, 54):
            hover_idx = i
    for i, (title, desc, target, num) in enumerate(_ITEMS):
        yy = ny + i * 50
        if _nav_row(78, yy, 400, i, title, desc, hover_idx == i, num):
            if target == "quit":
                g.quit = True
            else:
                if target == "settings":
                    g.back = "main"
                g.state = target

    # alt bilgi: ince cizgi + profil
    by = SH - 104
    draw_line_ex(Vector2(64, by), Vector2(500, by), 1, C(255, 255, 255, 50))
    d = playerdata.data()
    ch = characters.get(g.char)
    kn = knives.by_id(g.p.knife if g.p is not None else d.get("knife", "knife"))
    txt("KARAKTER", 66, by + 10, 10, _MUTED)
    txt(ch.name, 66, by + 22, 19, _INK)
    txt("BICAK", 262, by + 10, 10, _MUTED)
    txt(kn.name, 262, by + 22, 19, _INK)
    txt("KAPLAMA: %s / %s" % (skins.gun_skin(d.get("gun_skin", "none")).name,
                              skins.knife_skin(d.get("knife_skin", "none")).name),
        66, by + 48, 10, C(255, 255, 255, 90))
    # secili/aciklama satiri
    desc = _ITEMS[hover_idx][1] if hover_idx >= 0 else "Bir secenek uzerine gel."
    txt(">", 66, SH - 26, 13, _ACCENT)
    txt(desc.upper(), 82, SH - 27, 12, C(255, 255, 255, 160))

    _swarm(t)
