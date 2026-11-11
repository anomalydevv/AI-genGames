# -*- coding: utf-8 -*-
"""Silah ve bicaklarin 3B modelini ayri sahnede cekip PNG ikon olarak kaydeder."""
import math
import os

from pyray import *
try:
    from pyray import ffi
except Exception:
    from raylib import ffi

import knives as knives_mod
import viewmodel
import weapons as weapons_mod
from config import C
from shaders import FS_LIT, VS_LIT
from viewmodel import GLOVE, SLEEVE, VM
from weapons import WEAPONS

ROOT = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(ROOT, "assets", "icons")
IW, IH = 640, 256
ASPECT = IW / IH
FOVY = 26.0

_tex = {}
_rt = _cube = _lit = None
_view_loc = _pattern_loc = None
_vp = _pat = None
_ready = False

_AXIS_POS = {"X": Vector3(1, 0, 0), "Y": Vector3(0, 1, 0), "Z": Vector3(0, 0, 1)}


def _gun_parts(wi):
    return [p for p in VM[wi][0] if p[6] is not GLOVE and p[6] is not SLEEVE]


def _bounds(parts):
    xs, ys, zs = [], [], []
    for p in parts:
        x, y, z, sx, sy, sz = p[:6]
        xs += [x - sx / 2, x + sx / 2]
        ys += [y - sy / 2, y + sy / 2]
        zs += [z - sz / 2, z + sz / 2]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def _norm(v):
    n = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _tint(col):
    return C(min(255, col.r * 1.55 + 18), min(255, col.g * 1.55 + 18),
             min(255, col.b * 1.55 + 18), col.a)


def _camera(parts):
    lo, hi = _bounds(parts)
    cx, cy, cz = [(lo[i] + hi[i]) / 2 for i in range(3)]
    d = _norm((0.995, 0.08, 0.06))
    fwd = (-d[0], -d[1], -d[2])
    right = _norm(_cross(fwd, (0, 1, 0)))
    up = _cross(right, fwd)
    hr = hu = 0.0
    for p in parts:
        x, y, z, sx, sy, sz = p[:6]
        for ix in (-1, 1):
            for iy in (-1, 1):
                for iz in (-1, 1):
                    v = (x + ix * sx / 2, y + iy * sy / 2, z + iz * sz / 2)
                    hr = max(hr, abs(_dot(v, right)))
                    hu = max(hu, abs(_dot(v, up)))
    m = 1.15
    fovy = max(2 * hu * m, 2 * hr * m / ASPECT)
    cam = Camera3D(Vector3(cx + d[0] * 3.0, cy + d[1] * 3.0, cz + d[2] * 3.0),
                   Vector3(cx, cy, cz), Vector3(0, 1, 0), fovy, CAMERA_ORTHOGRAPHIC)
    return cam


def _png(kind, name):
    return os.path.join(ICON_DIR, "%s_%s.png" % (kind, name))


def _sources():
    return [weapons_mod.__file__, viewmodel.__file__, knives_mod.__file__, __file__]


def _stale(path):
    if not os.path.exists(path):
        return True
    try:
        newest = max(os.path.getmtime(p) for p in _sources())
        return os.path.getmtime(path) < newest
    except OSError:
        return True


def _render(parts, path):
    global _rt, _cube, _lit
    cam = _camera(parts)
    begin_texture_mode(_rt)
    clear_background(C(11, 15, 22))
    for i, r in enumerate(range(150, 24, -9)):
        t = i / 14.0
        draw_circle(IW // 2, IH // 2, r, C(13 + 11 * t, 19 + 27 * t, 26 + 31 * t))
    for i in range(8):
        t = i / 7.0
        draw_rectangle(0, IH - 42 + i * 6, IW, 7, C(11 - 6 * t, 15 - 7 * t, 22 - 10 * t))
    begin_mode_3d(cam)
    vp = cam.position
    _vp[0], _vp[1], _vp[2] = vp.x, vp.y, vp.z
    set_shader_value(_lit, _view_loc, _vp, SHADER_UNIFORM_VEC3)
    _pat[0] = 0.0
    set_shader_value(_lit, _pattern_loc, _pat, SHADER_UNIFORM_FLOAT)
    for p in parts:
        x, y, z, sx, sy, sz, col = p[:7]
        draw_model_ex(_cube, Vector3(x, y, z), _AXIS_POS.get("Y"), 0.0,
                      Vector3(sx, sy, sz), _tint(col))
    end_mode_3d()
    end_texture_mode()
    img = load_image_from_texture(_rt.texture)
    image_flip_vertical(img)
    export_image(img, path)
    unload_image(img)


def init():
    global _rt, _cube, _lit, _view_loc, _pattern_loc, _vp, _pat, _ready
    if _ready:
        return
    os.makedirs(ICON_DIR, exist_ok=True)
    _rt = load_render_texture(IW, IH)
    _cube = load_model_from_mesh(gen_mesh_cube(1.0, 1.0, 1.0))
    _lit = load_shader_from_memory(VS_LIT, FS_LIT)
    _cube.materials[0].shader = _lit
    _view_loc = get_shader_location(_lit, "viewPos")
    _pattern_loc = get_shader_location(_lit, "pattern")
    _vp = ffi.new("float[3]")
    _pat = ffi.new("float[1]")
    for wi in range(len(WEAPONS)):
        path = _png("weapon", str(wi))
        if _stale(path):
            _render(_gun_parts(wi), path)
        t = load_texture(path)
        set_texture_filter(t, TEXTURE_FILTER_BILINEAR)
        _tex[("w", wi)] = t
    for k in knives_mod.KNIVES:
        path = _png("knife", k.kid)
        if _stale(path):
            _render(knives_mod.model(k.kid)[1], path)
        t = load_texture(path)
        set_texture_filter(t, TEXTURE_FILTER_BILINEAR)
        _tex[("k", k.kid)] = t
    _ready = True


def _draw(tex, x, y, w, h, alpha):
    if tex is None:
        return False
    dw = w
    dh = dw * IH / IW
    if dh > h:
        dh = h
        dw = dh * IW / IH
    draw_texture_pro(tex, Rectangle(0, 0, tex.width, tex.height),
                     Rectangle(x + (w - dw) / 2, y + (h - dh) / 2, dw, dh),
                     Vector2(0, 0), 0.0, Color(255, 255, 255, alpha))
    return True


def draw_weapon(wi, x, y, w, h, alpha=255):
    if _draw(_tex.get(("w", wi)), x, y, w, h, alpha):
        return
    from weapon_icons import draw_weapon_icon
    draw_weapon_icon(wi, x, y, max(0.5, h / 70.0))


def draw_knife(kid, x, y, w, h, alpha=255):
    if _draw(_tex.get(("k", kid)), x, y, w, h, alpha):
        return
    knives_mod.draw_knife_icon(kid, x, y, max(0.6, h / 80.0))
