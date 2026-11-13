# -*- coding: utf-8 -*-
"""Silah/bicak kaplamalari, prosedurel kaplama dokulari ve efekt renkleri.

Kaplamalar Python ile uretilir: hem 3B parcalarin renk paleti hem de
magazada kullanilan prosedurel doku gorselleri bu modulden gelir.
"""
import math

from pyray import (TEXTURE_FILTER_BILINEAR, draw_texture_pro, gen_image_color,
                   image_draw_pixel, load_texture_from_image, set_texture_filter,
                   unload_image)
from pyray import Rectangle, Vector2

from config import C


class Skin:
    def __init__(self, sid, name, price, desc, accent, best=False, note=""):
        self.sid = sid
        self.name = name
        self.price = price
        self.desc = desc
        self.accent = accent
        self.best = best
        self.note = note


GUN_SKINS = [
    Skin("none", "Fabrika", 0, "Silahin ozgun metal ve ahsap kaplamasi.",
         C(180, 190, 205)),
    Skin("tiger", "Kaplan Kaplamasi", 4200,
         "Altin-turuncu kaplan cizgileri. Koleksiyonun en prestijli kaplamasi.",
         C(255, 170, 45), best=True, note="EFSANE"),
    Skin("void", "Void Seti", 3200,
         "Her silahta gecerli. Cyan neon cizgiler, mavi iz ve mavi namlu atesi. Hasar bonusu yok.",
         C(70, 225, 255), note="TUM SILAHLAR"),
    Skin("neon", "Neon Agi", 1600,
         "Koyu govde uzerinde cyan ve magenta enerji damarlari.",
         C(80, 255, 230)),
    Skin("crimson", "Kizil Catlak", 1100,
         "Kan kirmizisi catlaklar ve kor gibi parlayan kenarlar.",
         C(255, 80, 65)),
    Skin("glacier", "Buz Kristali", 1400,
         "Buz mavisi kristal yuzey, keskin beyaz kirilmalar.",
         C(155, 225, 255)),
]

KNIFE_SKINS = [
    Skin("none", "Fabrika", 0, "Bicagin orijinal celik ve sap gorunumu.",
         C(180, 190, 205)),
    Skin("voidstone", "Void Tasi", 2800,
         "Mor-cyan firtina tasi. Karambitte donen void parcaciklari ve neon iz.",
         C(165, 85, 255), note="KARAMBIT EFEKTI"),
    Skin("ember", "Kor Kelebek", 1900,
         "Altin kor cizgiler; kelebek bicakta alev parcaciklari.",
         C(255, 145, 55)),
    Skin("tigerknife", "Kaplan Pencesi", 2400,
         "Altin kaplan cizgili bicak kabugu.", C(255, 185, 60), best=True),
]

_GUN = {s.sid: s for s in GUN_SKINS}
_KNIFE = {s.sid: s for s in KNIFE_SKINS}

_MODE = {
    "none": 0,
    "tiger": 1,
    "tigerknife": 1,
    "void": 2,
    "voidstone": 2,
    "neon": 3,
    "crimson": 4,
    "glacier": 5,
    "ember": 6,
}

_ACCENT = {
    "none": C(200, 210, 225),
    "tiger": C(255, 170, 45),
    "tigerknife": C(255, 190, 65),
    "void": C(70, 225, 255),
    "voidstone": C(165, 105, 255),
    "neon": C(80, 255, 230),
    "crimson": C(255, 75, 60),
    "glacier": C(155, 225, 255),
    "ember": C(255, 145, 55),
}

_DARK = {
    "tiger": C(24, 15, 9),
    "tigerknife": C(26, 16, 9),
    "void": C(5, 8, 20),
    "voidstone": C(10, 5, 24),
    "neon": C(6, 14, 28),
    "crimson": C(24, 5, 8),
    "glacier": C(8, 22, 38),
    "ember": C(28, 9, 8),
}

_MID = {
    "tiger": C(106, 55, 16),
    "tigerknife": C(118, 64, 18),
    "void": C(17, 24, 63),
    "voidstone": C(40, 18, 78),
    "neon": C(18, 50, 72),
    "crimson": C(82, 15, 20),
    "glacier": C(45, 92, 132),
    "ember": C(100, 30, 16),
}

_PALETTE = {
    "tiger": (C(22, 14, 8), C(90, 45, 12), C(176, 96, 24), C(238, 158, 46), C(255, 226, 145)),
    "tigerknife": (C(24, 15, 8), C(102, 52, 13), C(188, 105, 27), C(246, 170, 52), C(255, 232, 160)),
    "void": (C(4, 6, 18), C(14, 24, 62), C(38, 80, 142), C(38, 185, 226), C(175, 250, 255)),
    "voidstone": (C(8, 4, 20), C(36, 16, 72), C(88, 38, 150), C(70, 210, 240), C(220, 245, 255)),
    "neon": (C(5, 9, 18), C(19, 38, 67), C(74, 46, 150), C(35, 206, 208), C(215, 255, 250)),
    "crimson": (C(16, 3, 5), C(67, 9, 13), C(143, 22, 27), C(242, 64, 48), C(255, 205, 160)),
    "glacier": (C(7, 17, 31), C(25, 60, 92), C(68, 134, 175), C(165, 223, 250), C(245, 255, 255)),
    "ember": (C(22, 5, 4), C(78, 18, 10), C(168, 54, 16), C(255, 132, 34), C(255, 238, 170)),
}


def gun_skin(sid):
    return _GUN.get(sid, _GUN["none"])


def knife_skin(sid):
    return _KNIFE.get(sid, _KNIFE["none"])


def shader_mode(sid):
    return _MODE.get(sid, 0)


def accent(sid):
    return _ACCENT.get(sid, _ACCENT["none"])


def dark(sid):
    return _DARK.get(sid, C(20, 22, 28))


def mid(sid):
    return _MID.get(sid, C(70, 76, 90))


def shader_palette(sid):
    return accent(sid), dark(sid)


def muzzle_color(sid):
    if sid in ("void", "voidstone", "neon", "glacier"):
        return C(70, 220, 255)
    if sid in ("tiger", "tigerknife", "ember"):
        return C(255, 178, 55)
    if sid == "crimson":
        return C(255, 85, 55)
    return C(255, 190, 80)


def tracer_color(sid):
    if sid in ("void", "voidstone"):
        return C(45, 180, 255, 220)
    if sid == "neon":
        return C(65, 255, 225, 220)
    if sid in ("tiger", "tigerknife", "ember"):
        return C(255, 190, 70, 220)
    if sid == "crimson":
        return C(255, 80, 55, 220)
    if sid == "glacier":
        return C(165, 225, 255, 220)
    return None


def hit_spark(sid):
    if sid in ("void", "voidstone"):
        return C(60, 190, 255)
    if sid == "neon":
        return C(70, 255, 225)
    if sid in ("tiger", "tigerknife", "ember"):
        return C(255, 190, 70)
    if sid == "crimson":
        return C(255, 80, 55)
    if sid == "glacier":
        return C(175, 230, 255)
    return C(200, 20, 30)


def _lum(c):
    return c.r * 0.299 + c.g * 0.587 + c.b * 0.114


def _hash(*v):
    h = 0x811C9DC5
    for n in v:
        h ^= int(n * 977.0) & 0xFFFFFFFF
        h = (h * 16777619) & 0xFFFFFFFF
    return (h & 0xFFFF) / 65535.0


_COL_CACHE = {}


def part_color(sid, col, x=0.0, y=0.0, z=0.0, idx=0):
    """Bir 3B parcanin kaplama rengini dondurur (onbellekli)."""
    if sid in (None, "", "none") or sid not in _PALETTE:
        return col
    pal = _PALETTE[sid]
    lum = _lum(col)
    bucket = int(_hash(x, y, z, idx) * 4.0)
    if lum < 38:
        level = 0
    elif lum < 78:
        level = 1
    elif lum < 132:
        level = 2
    elif lum < 184:
        level = 3
    else:
        level = 4
    level = max(0, min(4, level + (1 if bucket == 3 and level < 4 else 0)))
    key = (sid, level)
    if key not in _COL_CACHE:
        _COL_CACHE[key] = pal[level]
    return _COL_CACHE[key]


def apply(p, data):
    gs = data.get("gun_skin", "none") if isinstance(data, dict) else "none"
    ks = data.get("knife_skin", "none") if isinstance(data, dict) else "none"
    p.gun_skin = gs if gs in _GUN else "none"
    p.knife_skin = ks if ks in _KNIFE else "none"


# ---------------------------------------------------------------------------
#  Prosedurel magazali doku gorselleri (Python ile uretilir)
# ---------------------------------------------------------------------------
_TEX = {}
_TEX_SIZE = (192, 74)


def _pixel_color(sid, u, v):
    pal = _PALETTE.get(sid)
    if pal is None:
        return C(38, 44, 58)
    if sid in ("tiger", "tigerknife"):
        stripe = math.sin(u * 30.0 + v * 13.0 + math.sin(u * 11.0 + v * 19.0) * 3.2)
        stripe += 0.35 * math.sin(u * 73.0 - v * 41.0)
        if stripe > 0.38:
            return pal[0]
        if stripe > 0.05:
            return pal[1]
        if stripe > -0.34:
            return pal[2]
        if stripe > -0.68:
            return pal[3]
        return pal[4]
    if sid in ("void", "voidstone"):
        n = math.sin(u * 23.0 + math.sin(v * 17.0) * 3.0) * math.cos(v * 19.0 - u * 8.0)
        nebula = 0.5 + 0.5 * math.sin(u * 9.0 + v * 12.0 + n * 2.6)
        if n > 0.72:
            return pal[4]
        if n > 0.35:
            return pal[3]
        if nebula > 0.72:
            return pal[2]
        if nebula > 0.43:
            return pal[1]
        return pal[0]
    if sid == "neon":
        gx = abs(((u * 18.0) % 1.0) - 0.5)
        gy = abs(((v * 12.0) % 1.0) - 0.5)
        if gx < 0.055 or gy < 0.09:
            return pal[3] if (int(u * 18) + int(v * 12)) % 3 else pal[4]
        if math.sin(u * 51.0 + v * 27.0) > 0.76:
            return pal[2]
        return pal[0]
    if sid == "crimson":
        crack = abs(math.sin(u * 19.0 + math.sin(v * 14.0) * 2.8))
        if crack < 0.09:
            return pal[4]
        if crack < 0.19:
            return pal[3]
        return pal[0] if (int(u * 65) + int(v * 39)) % 5 else pal[1]
    if sid == "glacier":
        crystal = math.sin(u * 17.0 + v * 29.0) * math.cos(v * 12.0 - u * 6.0)
        if crystal > 0.67:
            return pal[4]
        if crystal > 0.22:
            return pal[3]
        if crystal < -0.58:
            return pal[1]
        return pal[2]
    if sid == "ember":
        crack = abs(math.sin(u * 17.0 + math.sin(v * 21.0) * 3.0))
        if crack < 0.10:
            return pal[4]
        if crack < 0.22:
            return pal[3]
        return pal[0] if (int(u * 53) + int(v * 31)) % 4 else pal[1]
    return pal[2]


def _build_texture(sid):
    w, h = _TEX_SIZE
    img = gen_image_color(w, h, C(8, 10, 16))
    pal = _PALETTE.get(sid)
    for y in range(h):
        v = y / float(h - 1)
        for x in range(w):
            u = x / float(w - 1)
            col = _pixel_color(sid, u, v)
            shade = 0.58 + 0.42 * (1.0 - abs(v - 0.5) * 1.15)
            if pal is not None and sid != "none":
                col = C(int(col.r * shade), int(col.g * shade), int(col.b * shade), 255)
            image_draw_pixel(img, x, y, col)
    tex = load_texture_from_image(img)
    unload_image(img)
    if tex.id:
        set_texture_filter(tex, TEXTURE_FILTER_BILINEAR)
    return tex if tex.id else None


def texture(sid):
    if sid not in _TEX:
        _TEX[sid] = _build_texture(sid)
    return _TEX[sid]


def init_textures():
    for s in GUN_SKINS + KNIFE_SKINS:
        if s.sid not in _TEX:
            try:
                texture(s.sid)
            except Exception:
                _TEX[s.sid] = None


def draw_swatch(sid, x, y, w, h, alpha=255):
    tex = texture(sid)
    if tex is not None:
        draw_texture_pro(tex, Rectangle(0, 0, tex.width, tex.height),
                         Rectangle(x, y, w, h), Vector2(0, 0), 0.0,
                         C(255, 255, 255, alpha))
        return True
    pal = _PALETTE.get(sid, (C(24, 28, 36),) * 5)
    for i in range(5):
        draw_rectangle(int(x), int(y + h * i / 5), int(w), int(h / 5 + 1), pal[i])
    return False