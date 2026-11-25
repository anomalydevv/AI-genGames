# -*- coding: utf-8 -*-
"""3B kaynaklar, kamera, dunya/silah cizimi ve post-process uygulamasi."""
import math
import os
import random

from pyray import *
try:
    from pyray import ffi
except Exception:
    from raylib import ffi

import ui
import bomb
import characters
import human
import knives
import KnivesAnim
import skins
from config import CYAN, DEG, SW, SH, C, cfg, cl, lerpf
from fighter import look
from shaders import FS_LIT, FS_POST, VS_LIT, VS_POST
from state import g
from viewmodel import GLOVE, METAL, SLEEVE, VM
from weapons import WEAPONS
from world import BOX, BOUND, DECOR, THEME

CUBE = SPHERE = LIT = POST = None
AX_Y = Vector3(0, 1, 0)
AX_X = Vector3(1, 0, 0)
AX_Z = Vector3(0, 0, 1)
_f = _v2 = _v3 = None
LOCS = {}
VIEW_SCALE = 1.0
VIEW_OX = 0.0
VIEW_OY = 0.0


def update_view():
    global VIEW_SCALE, VIEW_OX, VIEW_OY
    sw, sh = get_screen_width(), get_screen_height()
    if sw <= 0 or sh <= 0:
        sw, sh = SW, SH
    sc = min(sw / SW, sh / SH)
    dw, dh = SW * sc, SH * sc
    # Tam ekranda yari piksel kaymayi onle: offsetleri tam piksele sabitle.
    ox, oy = round((sw - dw) * 0.5), round((sh - dh) * 0.5)
    VIEW_SCALE, VIEW_OX, VIEW_OY = sc, float(ox), float(oy)
    ui.set_view(VIEW_SCALE, VIEW_OX, VIEW_OY)
    return VIEW_SCALE, VIEW_OX, VIEW_OY


def ui_camera():
    return Camera2D(Vector2(VIEW_OX, VIEW_OY), Vector2(0, 0), 0.0, VIEW_SCALE)


def init_gfx():
    global CUBE, SPHERE, LIT, POST, _f, _v2, _v3
    _f = ffi.new("float *")
    _v2 = ffi.new("float[2]")
    _v3 = ffi.new("float[3]")
    font = None
    ldir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
    cps = list(range(32, 127)) + [ord(c) for c in "ğüşıöçĞÜŞİÖÇ"]
    for pth in (os.path.join(ldir, "Rajdhani-Regular.ttf"), os.path.join(ldir, "Orbitron.ttf"),
                "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf"):
        if not os.path.exists(pth):
            continue
        try:
            # Raylib mutlak Turkce yolda fopen edemiyor; fontu bellekten yukle.
            with open(pth, "rb") as f:
                data = f.read()
            arr = ffi.new("int[]", cps)
            ext = os.path.splitext(pth)[1].lower() or ".ttf"
            font = load_font_from_memory(ext, data, len(data), 48, ffi.cast("int *", arr), len(cps))
            if font.texture.id == 0:
                font = load_font_ex(pth, 48, arr, len(cps))
        except Exception:
            font = None
        if font is not None and font.texture.id != 0:
            set_texture_filter(font.texture, TEXTURE_FILTER_BILINEAR)
            break
        font = None
    ui.set_font(font)
    LIT = load_shader_from_memory(VS_LIT, FS_LIT)
    POST = load_shader_from_memory(VS_POST, FS_POST)
    LOCS["viewPos"] = get_shader_location(LIT, "viewPos")
    LOCS["pattern"] = get_shader_location(LIT, "pattern")
    LOCS["vm"] = get_shader_location(LIT, "vm")
    LOCS["skinMode"] = get_shader_location(LIT, "skinMode")
    LOCS["skinA"] = get_shader_location(LIT, "skinA")
    LOCS["skinB"] = get_shader_location(LIT, "skinB")
    LOCS["time"] = get_shader_location(LIT, "time")
    for nm in ("res", "time", "wave", "hurt", "digital", "ult", "fx"):
        LOCS[nm] = get_shader_location(POST, nm)
    CUBE = load_model_from_mesh(gen_mesh_cube(1.0, 1.0, 1.0))
    SPHERE = load_model_from_mesh(gen_mesh_sphere(0.5, 16, 16))
    CUBE.materials[0].shader = LIT
    SPHERE.materials[0].shader = LIT
    human.set_models(CUBE, SPHERE)
    g.rt = load_render_texture(SW, SH)
    g.vmrt = load_render_texture(SW, SH)


def sf(sh, loc, v):
    _f[0] = v
    set_shader_value(sh, loc, _f, SHADER_UNIFORM_FLOAT)


def _drop_col(wi):
    price = WEAPONS[wi].price
    if price >= 1500:
        return C(255, 205, 70)
    if price >= 800:
        return C(170, 120, 255)
    return C(0, 230, 200)


def draw_drop(d):
    parts = VM[d["wi"]][0]
    yaw = d["yaw"]
    cs, sn = math.cos(yaw), math.sin(yaw)
    sc = 0.55
    glow = _drop_col(d["wi"])
    t = get_time()
    pu = 0.5 + 0.5 * math.sin(t * 4.5 + d["x"] * 0.6 + d["z"] * 0.3)
    bob = 0.03 * pu
    for part in parts:
        x, y, z, sx, sy_, sz, col = part[:7]
        if col is GLOVE or col is SLEEVE:
            continue
        wx = d["x"] - x * cs * sc + z * sn * sc
        wz = d["z"] + x * sn * sc + z * cs * sc
        draw_model_ex(CUBE, Vector3(wx, 0.12 + y * sc + bob, wz), AX_Y, yaw / DEG,
                      Vector3(sx * sc, sy_ * sc, sz * sc), col)
    begin_blend_mode(BLEND_ADDITIVE)
    draw_circle_3d(Vector3(d["x"], 0.045, d["z"]), 0.42 + 0.16 * pu, AX_X, 90.0,
                   C(glow.r, glow.g, glow.b, int(55 + 55 * pu)))
    draw_circle_3d(Vector3(d["x"], 0.05, d["z"]), 0.20 + 0.08 * pu, AX_X, 90.0,
                   C(glow.r, glow.g, glow.b, int(70 + 50 * pu)))
    draw_cube(Vector3(d["x"], 0.55, d["z"]), 0.05, 1.0, 0.05,
              C(glow.r, glow.g, glow.b, 46))
    draw_sphere(Vector3(d["x"], 0.42 + bob, d["z"]), 0.10 + 0.05 * pu,
                C(glow.r, glow.g, glow.b, int(70 + 60 * pu)))
    end_blend_mode()


def set_view(sh_pos, pattern):
    _v3[0], _v3[1], _v3[2] = sh_pos
    set_shader_value(LIT, LOCS["viewPos"], _v3, SHADER_UNIFORM_VEC3)
    sf(LIT, LOCS["pattern"], pattern)
    sf(LIT, LOCS["vm"], 0.0)
    sf(LIT, LOCS["skinMode"], 0.0)
    sf(LIT, LOCS["time"], get_time())


def _set_skin(sid):
    mode = skins.shader_mode(sid)
    sf(LIT, LOCS["skinMode"], float(mode))
    if mode:
        a, b = skins.shader_palette(sid)
        _v3[0], _v3[1], _v3[2] = a.r / 255.0, a.g / 255.0, a.b / 255.0
        set_shader_value(LIT, LOCS["skinA"], _v3, SHADER_UNIFORM_VEC3)
        _v3[0], _v3[1], _v3[2] = b.r / 255.0, b.g / 255.0, b.b / 255.0
        set_shader_value(LIT, LOCS["skinB"], _v3, SHADER_UNIFORM_VEC3)


def draw_env():
    cam = g.cam
    set_view((cam.position.x, cam.position.y, cam.position.z), 1.0)
    draw_model_ex(CUBE, Vector3(0, -0.5, 0), AX_Y, 0, Vector3(120, 1, 120), C(98, 100, 106))
    for b in BOX:
        draw_model_ex(CUBE, Vector3((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2), AX_Y, 0,
                      Vector3(b[3] - b[0], b[4] - b[1], b[5] - b[2]), b[6])
    for d in DECOR:
        draw_model_ex(CUBE, Vector3((d[0] + d[3]) / 2, (d[1] + d[4]) / 2, (d[2] + d[5]) / 2), AX_Y, 0,
                      Vector3(d[3] - d[0], d[4] - d[1], d[5] - d[2]), d[6])
    # zemin derz izgara + vurgu seritleri
    acc = THEME["accent"]
    for gx in range(-40, 41, 4):
        draw_line_3d(Vector3(gx, 0.035, -BOUND), Vector3(gx, 0.035, BOUND),
                     C(acc.r, acc.g, acc.b, 16))
        draw_line_3d(Vector3(-BOUND, 0.035, gx), Vector3(BOUND, 0.035, gx),
                     C(acc.r, acc.g, acc.b, 16))
    for s in range(-2, 3):
        draw_line_3d(Vector3(s * 4, 0.04, -BOUND), Vector3(s * 4, 0.04, BOUND),
                     C(255, 255, 255, 10))
    for (x, y, z, sx, sz) in [(0, 5.5, -BOUND + 0.05, 2 * BOUND - 2, 0.06), (0, 5.5, BOUND - 0.05, 2 * BOUND - 2, 0.06),
                              (-BOUND + 0.05, 5.5, 0, 0.06, 2 * BOUND - 2), (BOUND - 0.05, 5.5, 0, 0.06, 2 * BOUND - 2)]:
        draw_cube(Vector3(x, y, z), sx, 0.12, sz, THEME["accent"])
    for (x, z) in ((-BOUND + 10, -BOUND + 10), (BOUND - 10, BOUND - 10),
                   (-BOUND + 10, BOUND - 10), (BOUND - 10, -BOUND + 10)):
        draw_cube(Vector3(x, 5.2, z), 3.1, 0.1, 3.1, THEME["accent2"])


def _draw_enemy_aura(f):
    """Ulti sirasinda dusman glow: simetrik, yumusak isik. Derinlik testi ACIK:
    duvar arkasi gorunmez. Kutu/wire yok."""
    t = get_time()
    pu = 0.5 + 0.5 * math.sin(t * 5.0 + f.x * 0.7 + f.z * 0.4)
    # Derinlik testi bilerek kapatilmiyor: duvar arkasi aura sizmasin.
    begin_blend_mode(BLEND_ADDITIVE)
    draw_circle_3d(Vector3(f.x, 0.045, f.z), 0.75 + 0.12 * pu, AX_X, 90.0,
                   C(255, 35, 45, 90))
    draw_circle_3d(Vector3(f.x, 0.05, f.z), 0.52 + 0.09 * pu, AX_X, 90.0,
                   C(255, 60, 70, 110))
    draw_circle_3d(Vector3(f.x, 0.055, f.z), 0.30 + 0.06 * pu, AX_X, 90.0,
                   C(255, 120, 130, 120))
    draw_sphere(Vector3(f.x, f.y + 1.0, f.z), 0.22 + 0.06 * pu,
                C(255, 45, 60, 60))
    draw_sphere(Vector3(f.x, f.y + 1.0, f.z), 0.10 + 0.03 * pu,
                C(255, 160, 170, 90))
    end_blend_mode()


def draw_world_play():
    p = g.p
    viewer = p if p.alive else g.spec
    vteam = getattr(viewer, "team", getattr(p, "team", 0)) if viewer is not None else getattr(p, "team", 0)
    ult_on = getattr(g, "ult_t", 0.0) > 0.0
    set_view((g.cam.position.x, g.cam.position.y, g.cam.position.z), 0.0)
    for f in g.FS:
        if f is viewer:
            continue
        if f.alive or f.death_t < 20:
            tip = 1.0 if not f.alive and f.death_t > 0.4 else (f.death_t / 0.4 if not f.alive else 0.0)
            if ult_on and f.alive and getattr(f, "team", -1) != vteam:
                _draw_enemy_aura(f)
            human.draw(f, tip)
    # golge
    for f in g.FS:
        if f.alive and f is not viewer:
            draw_circle_3d(Vector3(f.x, f.y + 0.03, f.z), 0.55, AX_X, 90.0, C(0, 0, 0, 90))
    for t in g.tracers:
        tcol = t[7] if len(t) > 7 and t[7] is not None else C(255, 235, 160)
        draw_line_3d(Vector3(t[0], t[1], t[2]), Vector3(t[3], t[4], t[5]), tcol)
    for q in g.parts:
        draw_cube(Vector3(q[0], q[1], q[2]), 0.05, 0.05, 0.05, q[7])
    for d in g.drops:
        draw_drop(d)
    for letter, (sx, sz) in bomb.SITES.items():
        active = g.site_plan == letter
        hot = THEME["accent"] if active else THEME["accent2"]
        draw_circle_3d(Vector3(sx, 0.04, sz), bomb.SITE_R, AX_X, 90.0,
                       C(hot.r, hot.g, hot.b, 55) if active else C(hot.r, hot.g, hot.b, 35))
        draw_circle_3d(Vector3(sx, 0.05, sz), bomb.SITE_R * 0.55, AX_X, 90.0, C(hot.r, hot.g, hot.b, 22))
    b = g.bomb
    if b and (b["planted"] or b["dropped"]):
        blink = int(get_time() * 8) % 2 == 0
        col = (C(255, 40, 40) if blink else C(90, 10, 10)) if b["planted"] else (C(255, 205, 70) if blink else C(120, 80, 20))
        draw_cube(Vector3(b["x"], 0.14, b["z"]), 0.34, 0.28, 0.22, C(28, 30, 36))
        draw_cube(Vector3(b["x"], 0.33, b["z"]), 0.10, 0.10, 0.10, col)
        draw_sphere(Vector3(b["x"], 0.40, b["z"]), 0.11 + 0.03 * math.sin(get_time() * 12), C(col.r, col.g, col.b, 120))
    if g.explode_t > 0:
        k = 1.0 - g.explode_t
        ex, ey, ez = g.explode_pos
        draw_sphere(Vector3(ex, ey, ez), 2 + 24 * k, C(255, 160, 60, int(200 * g.explode_t)))
        draw_sphere(Vector3(ex, ey, ez), 1 + 13 * k, C(255, 255, 220, int(220 * g.explode_t)))
    if g.soul_t > 0:
        s = g.soul_pos
        pu = 0.5 + 0.5 * math.sin(get_time() * 10)
        draw_sphere(Vector3(s[0], s[1] + 0.2 * pu, s[2]), 0.18 + 0.05 * pu, C(80, 255, 230, 200))
    # Ulti duvar-arkasi kutusu kaldirildi: aura depth-testli glow ile veriliyor.


# ---------------------------------------------------------------------------
#  VIEWMODEL DONUSUMLERI (sert govde: her parca ayni donusle hareket eder)
# ---------------------------------------------------------------------------
_IDENT = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
_MIRROR = ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def _mm(a, b):
    return tuple(tuple(a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j]
                       for j in range(3)) for i in range(3))


def _mv(m, v):
    return (m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
            m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
            m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2])


def _rx(a):
    c, s = math.cos(a), math.sin(a)
    return ((1.0, 0.0, 0.0), (0.0, c, -s), (0.0, s, c))


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, 0.0, s), (0.0, 1.0, 0.0), (-s, 0.0, c))


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return ((c, -s, 0.0), (s, c, 0.0), (0.0, 0.0, 1.0))


def _mirror_rot(m):
    return ((m[0][0], -m[0][1], -m[0][2]),
            (-m[1][0], m[1][1], m[1][2]),
            (-m[2][0], m[2][1], m[2][2]))


def _axis_angle(m):
    tr = m[0][0] + m[1][1] + m[2][2]
    c = max(-1.0, min(1.0, (tr - 1.0) * 0.5))
    ang = math.acos(c)
    if ang < 1e-4:
        return AX_Y, 0.0
    if ang > math.pi - 1e-3:
        xx = max(0.0, (m[0][0] + 1.0) * 0.5)
        yy = max(0.0, (m[1][1] + 1.0) * 0.5)
        zz = max(0.0, (m[2][2] + 1.0) * 0.5)
        if xx >= yy and xx >= zz:
            n = math.sqrt(xx) or 1.0
            ax = (n, (m[0][1] + m[1][0]) / (4.0 * n), (m[0][2] + m[2][0]) / (4.0 * n))
        elif yy >= zz:
            n = math.sqrt(yy) or 1.0
            ax = ((m[0][1] + m[1][0]) / (4.0 * n), n, (m[1][2] + m[2][1]) / (4.0 * n))
        else:
            n = math.sqrt(zz) or 1.0
            ax = ((m[0][2] + m[2][0]) / (4.0 * n), (m[1][2] + m[2][1]) / (4.0 * n), n)
        ln = math.sqrt(ax[0] ** 2 + ax[1] ** 2 + ax[2] ** 2) or 1.0
        return Vector3(ax[0] / ln, ax[1] / ln, ax[2] / ln), ang / DEG
    s = 2.0 * math.sin(ang)
    return Vector3((m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s,
                   (m[1][0] - m[0][1]) / s), ang / DEG


def _smooth(k):
    k = cl(k, 0.0, 1.0)
    return k * k * (3.0 - 2.0 * k)


def _box(pos, R, size, col, alpha=255):
    axis, ang = _axis_angle(R)
    draw_model_ex(CUBE, Vector3(pos[0], pos[1], pos[2]), axis, ang,
                  Vector3(size[0], size[1], size[2]),
                  Color(col.r, col.g, col.b, alpha))


def _box_between(a, b, thick, col, alpha=255):
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-5:
        return
    d = (dx / length, dy / length, dz / length)
    cx, cy = -d[1], d[0]
    s = math.sqrt(cx * cx + cy * cy)
    if s < 1e-6:
        axis, ang = (AX_X, 180.0) if d[2] < 0 else (AX_Y, 0.0)
    else:
        axis = Vector3(cx / s, cy / s, 0.0)
        ang = math.acos(max(-1.0, min(1.0, d[2]))) / DEG
    mid = ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5, (a[2] + b[2]) * 0.5)
    draw_model_ex(CUBE, Vector3(mid[0], mid[1], mid[2]), axis, ang,
                  Vector3(thick, thick, length), Color(col.r, col.g, col.b, alpha))


# ---------------------------------------------------------------------------
#  SILAH (gun) viewmodel: tutus + Valorant tarzi inceleme
# ---------------------------------------------------------------------------
def _revolver_cyl(inspect_t):
    """Top koreografisi (2.6sn dongu): acil -> hizli don -> kapan."""
    cyc = inspect_t % 2.6
    if cyc < 0.30:
        open_k = cyc / 0.30
    elif cyc < 1.90:
        open_k = 1.0
    elif cyc < 2.20:
        open_k = 1.0 - (cyc - 1.90) / 0.30
    else:
        open_k = 0.0
    spin = max(0.0, min(cyc, 1.75) - 0.45) * 16.0
    return open_k, spin


_GUN_INSPECT = {
    0: (1.55, 1.10, 0.22, 0.26, 0.62, 1.00),
    1: (1.15, 1.05, 0.20, 0.30, 0.66, 1.00),
    2: (1.00, 0.95, 0.18, 0.22, 0.88, 0.92),
    3: (0.95, 0.90, 0.20, 0.25, 0.92, 0.92),
    4: (0.65, 0.80, 0.16, 0.20, 1.12, 0.88),
    5: (0.90, 0.90, 0.18, 0.24, 0.92, 0.92),
    6: (1.65, 1.15, 0.24, 0.28, 0.72, 1.00),
    7: (0.60, 0.75, 0.15, 0.18, 1.02, 0.90),
    8: (0.85, 0.90, 0.18, 0.22, 0.95, 0.92),
}


_inspect_k = KnivesAnim.inspect_amount


def _draw_arm(wrist, side, scale, cuff, shoulder_offset=None, limb_length=1.0):
    """Bilekten omuza iki kemikli, uzamayan kol."""
    if shoulder_offset is None:
        shoulder_offset = (side * 0.17, -0.34, -0.13)
    shoulder = tuple(wrist[i] + shoulder_offset[i] * scale for i in range(3))
    dx, dy, dz = shoulder[0] - wrist[0], shoulder[1] - wrist[1], shoulder[2] - wrist[2]
    dist = math.sqrt(dx * dx + dy * dy + dz * dz) or 0.001
    upper = 0.205 * scale * limb_length
    fore = 0.185 * scale * limb_length
    reach = min(dist, upper + fore - 0.002)
    ux, uy, uz = dx / dist, dy / dist, dz / dist
    a = (upper * upper - fore * fore + reach * reach) / (2.0 * reach)
    h = math.sqrt(max(0.0, upper * upper - a * a))
    px, py = -uy, ux
    pn = math.sqrt(px * px + py * py)
    if pn < 1e-4:
        px, py, pn = side, 0.0, 1.0
    elbow = (wrist[0] + ux * a + px / pn * h * side,
             wrist[1] + uy * a + py / pn * h * side,
             wrist[2] + uz * a)
    _box_between(shoulder, elbow, 0.105 * scale, SLEEVE)
    _box_between(elbow, wrist, 0.092 * scale, SLEEVE)
    cuff_end = (wrist[0] + ux * 0.055 * scale, wrist[1] + uy * 0.055 * scale,
                wrist[2] + uz * 0.055 * scale)
    _box_between(wrist, cuff_end, 0.116 * scale, cuff)


def _void_storm_fx(p, base, scale, k, muzzle):
    if k <= 0.01:
        return
    t = p.inspect_t
    cx = -base[0]
    cy = base[1] + 0.03
    cz = base[2] + 0.08
    ac = C(60, 225, 255)
    ac2 = C(150, 75, 255)
    hot = C(225, 255, 255)
    rl_disable_depth_test()
    rl_disable_depth_mask()
    begin_blend_mode(BLEND_ADDITIVE)
    for i in range(92):
        seed = (i * 0.61803398875) % 1.0
        life = (t * 0.60 + seed) % 1.0
        ang = t * (3.8 + (i % 5) * 0.22) + seed * math.tau * 2.0
        rad = (0.08 + 0.42 * math.sin(life * math.pi)) * scale
        rad += 0.035 * math.sin(t * 3.4 + i * 1.7)
        px = cx + math.cos(ang) * rad
        py = cy + math.sin(ang) * rad * 0.72 + (life - 0.5) * 0.24 * scale
        pz = cz + (life - 0.5) * 0.78 * scale + 0.045 * math.cos(ang * 1.6)
        a = int((45 + 185 * math.sin(life * math.pi)) * k)
        s = (0.008 + 0.020 * math.sin(life * math.pi)) * scale
        col = ac2 if i % 7 == 0 else ac
        draw_cube(Vector3(px, py, pz), s, s, s, C(col.r, col.g, col.b, a))
        if i % 8 == 0:
            draw_cube(Vector3(px, py, pz), s * 0.45, s * 0.45, s * 0.45,
                      C(hot.r, hot.g, hot.b, min(255, int(a * 1.35))))
    for i in range(28):
        seed = (i * 0.41421356237) % 1.0
        life = (t * 0.85 + seed) % 1.0
        ang = -t * 6.2 + i * math.tau / 28.0
        rad = (0.045 + 0.075 * life) * scale
        px = muzzle[0] + math.cos(ang) * rad
        py = muzzle[1] + math.sin(ang) * rad
        pz = muzzle[2] + (life - 0.2) * 0.32 * scale
        a = int(170 * (1.0 - life) * k)
        s = (0.010 + 0.012 * (1.0 - life)) * scale
        col = hot if i % 5 == 0 else ac
        draw_cube(Vector3(px, py, pz), s, s, s, C(col.r, col.g, col.b, a))
    for i in range(18):
        seed = (i * 0.73205080757) % 1.0
        life = (t * 0.50 + seed) % 1.0
        ang = t * 2.7 + seed * math.tau
        rad = (0.16 + 0.30 * math.sin(life * math.pi)) * scale
        z0 = cz + (life - 0.5) * 0.72 * scale
        a = int(95 * math.sin(life * math.pi) * k)
        p1 = Vector3(cx + math.cos(ang) * rad, cy + math.sin(ang) * rad * 0.65, z0)
        p2 = Vector3(cx + math.cos(ang - 0.28) * rad,
                     cy + math.sin(ang - 0.28) * rad * 0.65,
                     z0 + 0.13 * scale)
        draw_line_3d(p1, p2, C(ac.r, ac.g, ac.b, a))
    pu = 0.5 + 0.5 * math.sin(t * 5.2)
    draw_sphere(Vector3(cx, cy, cz), (0.075 + 0.045 * pu) * scale,
                C(ac.r, ac.g, ac.b, int(55 * k)))
    draw_sphere(Vector3(muzzle[0], muzzle[1], muzzle[2]),
                (0.06 + 0.05 * pu) * scale, C(ac2.r, ac2.g, ac2.b, int(75 * k)))
    end_blend_mode()
    rl_enable_depth_test()
    rl_enable_depth_mask()


def _gun_pose(p, wi):
    w = WEAPONS[wi]
    parts, muz = VM[wi]
    pivot = (0.0, -0.08, 0.02)
    ads = p.ads
    hip = (0.21, -0.19, 0.38)
    adsp = (0.0, -0.105, 0.33) if not w.scope else hip
    bx = lerpf(hip[0], adsp[0], ads) + (p.sway if cfg["sway"] else 0.0)
    by = lerpf(hip[1], adsp[1], ads) + (p.swayy if cfg["sway"] else 0.0)
    bz = lerpf(hip[2], adsp[2], ads) - p.kick * 0.008
    bob = p.bobamp * (1.0 - ads * 0.8) if cfg["bob"] else 0.0
    bx += -math.cos(p.bobt) * 0.012 * bob
    by += -abs(math.sin(p.bobt)) * 0.016 * bob
    ang = -p.kick * 0.35 * DEG
    if p.reload_t > 0:
        k = math.sin(cl(1.0 - p.reload_t / w.reload, 0.0, 1.0) * math.pi)
        by -= 0.12 * k
        ang += 0.5 * k
    if p.switch_t > 0:
        k = cl(p.switch_t / 0.35, 0.0, 1.0)
        by -= 0.3 * k
        ang += 0.8 * k
    nbase = (bx, by, bz)
    nrx = _rx(ang)
    k = _inspect_k(p)
    if k <= 0.001:
        return parts, muz, pivot, nrx, nbase, 1.0, 0.0

    t = p.inspect_t
    spd, ya, pa, ra, dist, sc_t = _GUN_INSPECT.get(wi, (1.0, 0.95, 0.20, 0.24, 0.80, 0.95))
    yaw = math.sin(t * spd) * ya
    pitch = 0.10 + math.sin(t * spd * 2.0 + 0.9) * pa
    roll = math.sin(t * spd + 1.7) * ra
    R = _mm(_mm(_rz(roll * k), _mm(_rx(pitch * k), _ry(yaw * k))), nrx)
    ib = (0.20, -0.10 + math.sin(t * spd * 1.6) * 0.012,
          dist + math.sin(t * spd * 0.8) * 0.010)
    base = (lerpf(nbase[0], ib[0], k), lerpf(nbase[1], ib[1], k), lerpf(nbase[2], ib[2], k))
    return parts, muz, pivot, R, base, lerpf(1.0, sc_t, k), k


def draw_viewmodel(viewer=None):
    p = g.p if viewer is None else viewer
    if p is None:
        return
    wi = p.weapon
    w = WEAPONS[wi]
    if w.scope and p.ads > 0.85:
        return
    parts, muz, pivot, R, base, sc, insp = _gun_pose(p, wi)
    axis, ang = _axis_angle(_mirror_rot(R))
    back = math.sin(cl(p.cycle, 0.0, 1.0) * math.pi)
    skin = getattr(p, "gun_skin", "none")
    vcam = Camera3D(Vector3(0, 0, 0), Vector3(0, 0, 1), Vector3(0, 1, 0), 58.0, 0)
    begin_mode_3d(vcam)
    rl_enable_depth_test()
    rl_enable_depth_mask()
    set_view((0, 0, 0), 0.0)
    sf(LIT, LOCS["vm"], 1.0)
    _set_skin(skin)
    wrists = []
    for idx, part in enumerate(parts):
        x, y, z, sx, sy_, sz, col = part[:7]
        tag = part[7] if len(part) > 7 else ""
        if insp > 0.001 and col is SLEEVE:
            continue
        dz = z
        if tag and back > 0:
            if tag == "slide":
                dz -= 0.042 * back
            elif tag == "bolt":
                dz -= 0.028 * back
            elif tag == "pump":
                dz -= 0.075 * back
            elif tag == "hammer":
                dz -= 0.012 * back
        if insp > 0.001 and wi == 2 and tag == "pump":
            dz -= 0.055 * (0.5 + 0.5 * math.sin(p.inspect_t * 3.2))
        rel = ((x - pivot[0]) * sc, (y - pivot[1]) * sc, (dz - pivot[2]) * sc)
        if insp > 0.001 and wi == 1 and tag == "cyl":
            # Top disari acilir, hizli doner, kapanir. Donus top ekseni (z) etrafinda.
            open_k, spin = _revolver_cyl(p.inspect_t)
            if open_k > 0.001 or spin > 0.001:
                cs, sn = math.cos(spin), math.sin(spin)
                rx, ry = rel[0], rel[1]
                rel = (rx * cs - ry * sn, rx * sn + ry * cs, rel[2])
                ca, sa = math.cos(open_k * 0.9), math.sin(open_k * 0.9)
                rx, rz = rel[0], rel[2]
                rel = (rx * ca + rz * sa - open_k * 0.09 * sc, rel[1], -rx * sa + rz * ca)
        d = _mv(R, rel)
        pos = (-(base[0] + pivot[0] + d[0]),
               base[1] + pivot[1] + d[1],
               base[2] + pivot[2] + d[2])
        if col is GLOVE:
            wrists.append(pos)
        pcol = skins.part_color(skin, col, x, y, z, idx)
        draw_model_ex(CUBE, Vector3(pos[0], pos[1], pos[2]), axis, ang,
                      Vector3(sx * sc, sy_ * sc, sz * sc),
                      Color(pcol.r, pcol.g, pcol.b, 255))
    _set_skin("none")
    if insp > 0.001 and wrists:
        cuff = skins.accent(skin)
        _draw_arm(wrists[0], 1.0, sc, cuff)
        if len(wrists) > 1:
            _draw_arm(wrists[-1], -1.0, sc, cuff)
    d = _mv(R, ((muz[0] - pivot[0]) * sc, (muz[1] - pivot[1]) * sc, (muz[2] - pivot[2]) * sc))
    mpos = (-(base[0] + pivot[0] + d[0]),
            base[1] + pivot[1] + d[1],
            base[2] + pivot[2] + d[2])
    if insp > 0.001 and skin == "void":
        _void_storm_fx(p, base, sc, insp, mpos)
    if p.flash > 0 and insp <= 0.001:
        fx, fy, fz = mpos[0], mpos[1], mpos[2] + 0.05
        mc = skins.muzzle_color(skin)
        rl_disable_depth_test()
        begin_blend_mode(BLEND_ADDITIVE)
        s = 0.07 + random.random() * 0.06
        draw_cube(Vector3(fx, fy, fz), s, s, 0.12, C(mc.r, mc.g, mc.b))
        draw_cube(Vector3(fx, fy, fz), s * 2, s * 0.4, 0.05,
                  C(min(255, mc.r), max(0, mc.g - 50), max(0, mc.b - 100)))
        if skins.shader_mode(skin) == 2:
            draw_sphere(Vector3(fx, fy, fz), 0.10 + random.random() * 0.05,
                        C(mc.r, mc.g, mc.b, 150))
        end_blend_mode()
        rl_enable_depth_test()
    end_mode_3d()


def _draw_knife_group(parts, base, R, pivot, scale, hinge, alpha, hinge_b=0.0,
                      skin="none", offsets=None):
    for idx, part in enumerate(parts):
        x, y, z, sx, sy, sz, col = part[:7]
        tag = part[7] if len(part) > 7 else ""
        Rh = _IDENT
        if hinge and tag == "hA":
            Rh = _rx(hinge)
        elif hinge_b and tag == "hB":
            Rh = _rx(-hinge_b)
        d = ((x - pivot[0]) * scale, (y - pivot[1]) * scale, (z - pivot[2]) * scale)
        if Rh is not _IDENT:
            d = _mv(Rh, d)
        if offsets is not None and idx < len(offsets):
            off = offsets[idx]
            d = (d[0] + off[0], d[1] + off[1], d[2] + off[2])
        Rp = _mm(R, Rh)
        d = _mv(R, d)
        pcol = skins.part_color(skin, col, x, y, z, idx)
        axis, ang = _axis_angle(Rp)
        draw_model_ex(CUBE, Vector3(base[0] + d[0], base[1] + d[1], base[2] + d[2]),
                      axis, ang, Vector3(sx * scale, sy * scale, sz * scale),
                      Color(pcol.r, pcol.g, pcol.b, alpha))


def _draw_knife_hand(base, B, kid, scale, skin="none"):
    rig = KnivesAnim.KNIFE_RIG[kid]
    hdir = _mv(B, (0.0, 0.0, -1.0))
    off = rig["hand"] * scale
    palm = (base[0] + hdir[0] * off, base[1] + hdir[1] * off, base[2] + hdir[2] * off)
    glove = GLOVE
    plate = C(48, 50, 58)
    wrap = C(34, 38, 46)
    _box(palm, B, (0.098 * scale, 0.118 * scale, 0.165 * scale), glove)
    # sirt / knuckle plakasi ve bilek sargisi
    _box((palm[0] + _mv(B, (0, 0.045 * scale, -0.01 * scale))[0],
          palm[1] + _mv(B, (0, 0.045 * scale, -0.01 * scale))[1],
          palm[2] + _mv(B, (0, 0.045 * scale, -0.01 * scale))[2]),
         B, (0.072 * scale, 0.026 * scale, 0.12 * scale), plate)
    _box((palm[0] + hdir[0] * 0.075 * scale, palm[1] + hdir[1] * 0.075 * scale,
          palm[2] + hdir[2] * 0.075 * scale),
         B, (0.104 * scale, 0.092 * scale, 0.055 * scale), wrap)

    def lp(x, y, z):
        d = _mv(B, (x * scale, y * scale, z * scale))
        return (palm[0] + d[0], palm[1] + d[1], palm[2] + d[2])

    fingers = 4
    for i in range(fingers):
        fx = -0.033 + i * 0.022
        if kid == "karambit" and i == 0:
            continue
        knuckle = lp(fx, -0.010, -0.060)
        mid = lp(fx * 0.92, -0.052, -0.108)
        tip = lp(fx * 0.80, -0.078, -0.090)
        _box_between(knuckle, mid, 0.030 * scale, glove)
        _box_between(mid, tip, 0.026 * scale, plate)
    if kid == "karambit":
        # index finger ringin icinden: palm -> ring -> geri kivrilir
        ib = lp(-0.045, 0.010, -0.030)
        ring = (base[0] + _mv(B, (0.0, -0.030 * scale, -0.370 * scale))[0],
                base[1] + _mv(B, (0.0, -0.030 * scale, -0.370 * scale))[1],
                base[2] + _mv(B, (0.0, -0.030 * scale, -0.370 * scale))[2])
        mid = (ring[0] - hdir[0] * 0.010 * scale, ring[1] - hdir[1] * 0.010 * scale,
               ring[2] - hdir[2] * 0.010 * scale)
        tip = lp(-0.020, -0.060, -0.048)
        _box_between(ib, mid, 0.032 * scale, glove)
        _box_between(mid, tip, 0.028 * scale, plate)
        # bas parmak sirt/but uzerinde
        tb = lp(rig["thumb_side"] * 0.052, 0.020, -0.020)
        tm = lp(rig["thumb_side"] * 0.038, -0.026, -0.092)
        tt = lp(rig["thumb_side"] * 0.018, -0.006, -0.150)
        _box_between(tb, tm, 0.034 * scale, glove)
        _box_between(tm, tt, 0.028 * scale, plate)
    else:
        tb = lp(rig["thumb_side"] * 0.052, 0.018, -0.015)
        tm = lp(rig["thumb_side"] * 0.040, -0.024, -0.090)
        tt = lp(rig["thumb_side"] * 0.022, -0.006, -0.132)
        _box_between(tb, tm, 0.034 * scale, glove)
        _box_between(tm, tt, 0.028 * scale, plate)
    wrist = (palm[0] + hdir[0] * 0.095 * scale, palm[1] + hdir[1] * 0.095 * scale,
             palm[2] + hdir[2] * 0.095 * scale)
    acc = skins.accent(skin) if skin != "none" else knives.by_id(kid).color
    _draw_arm(wrist, rig["arm_side"], scale, acc,
              rig["arm_offset"], rig["arm_length"])


def draw_knife_viewmodel(viewer=None):
    p = g.p if viewer is None else viewer
    if p is None:
        return
    kid = p.knife
    rig = KnivesAnim.KNIFE_RIG[kid]
    base, R, sc, insp = KnivesAnim.knife_pose(p, kid)
    B = KnivesAnim.knife_base(kid)
    _axis_name, parts = knives.model(kid)
    skin = getattr(p, "knife_skin", "none")
    hinge = p.hinge_a if kid == "butterfly" else 0.0
    hinge_b = p.hinge_b if kid == "butterfly" else 0.0
    vcam = Camera3D(Vector3(0, 0, 0), Vector3(0, 0, 1), Vector3(0, 1, 0), 58.0, 0)
    begin_mode_3d(vcam)
    rl_enable_depth_test()
    rl_enable_depth_mask()
    set_view((0, 0, 0), 0.0)
    sf(LIT, LOCS["vm"], 1.0)
    _set_skin("none")
    _draw_knife_hand(base, B, kid, sc, skin)
    if p.slash_t > 0 and insp <= 0.001:
        prog, current_offset, ghosts = KnivesAnim.slash_ghosts(kid, p.slash_t)
        trail = skins.accent(skin) if skin != "none" else knives.by_id(kid).color
        KnivesAnim.draw_slash_trail(kid, base, B, prog, rig["pivot"], sc, trail)
        gbase = tuple(base[i] - current_offset[i] for i in range(3))
        rl_disable_depth_mask()
        for _back, alpha, A, swing in ghosts:
            off = KnivesAnim.slash_offset(kid, swing)
            gb = (gbase[0] + off[0], gbase[1] + off[1], gbase[2] + off[2])
            _draw_knife_group(parts, gb, _mm(A, B), rig["pivot"], sc, 0.0, alpha,
                              skin=skin)
        rl_enable_depth_mask()
    _set_skin(skin)
    offsets = None
    if skin == "voidstone" and insp > 0.001:
        offsets, _groups, _targets = KnivesAnim.group_shatter(
            parts, rig["pivot"], kid, p.inspect_t, insp, sc)
    _draw_knife_group(parts, base, R, rig["pivot"], sc, hinge, 255, hinge_b,
                      skin=skin, offsets=offsets)
    if skin == "voidstone" and insp > 0.001:
        KnivesAnim.draw_atom_trails(base, R, sc, p.inspect_t, insp,
                                    max(_groups) + 1)
        KnivesAnim.draw_void_shatter_fx(base, sc, p.inspect_t, insp)
    _set_skin("none")
    if skin in (None, "", "none") and insp > 0.001:
        _sang, level = KnivesAnim.spin_state(kid, p.inspect_t)
        if level > 0.50:
            tip = KnivesAnim.tip_point(kid, base, R, rig["pivot"], sc)
            col = knives.by_id(kid).color
            KnivesAnim.draw_tip_smoke(tip, level, col, p.inspect_t, kid, insp)
    KnivesAnim.draw_inspect_fx(p, kid, base, sc, insp)
    end_mode_3d()



def play_camera():
    p = g.p
    sw, sh = get_screen_width(), get_screen_height()
    if sw <= 0 or sh <= 0:
        sw, sh = SW, SH
    asp = sw / max(1, sh)
    base_asp = SW / SH
    vf = 2 * math.atan(math.tan(cfg["fov"] * DEG / 2) * base_asp / asp)
    if not p.alive and g.spec is not None and g.spec.alive:
        s = g.spec
        f = look(s)
        ey = s.y + s.eh
        return Camera3D(Vector3(s.x, ey, s.z), Vector3(s.x + f[0], ey + f[1], s.z + f[2]),
                        Vector3(0, 1, 0), vf / DEG, 0)
    w = WEAPONS[p.weapon]
    zoom = lerpf(1.0, 0.2 if w.scope else 0.78, p.ads)
    if p.dash_t > 0:
        zoom *= 1.12
    fov = vf * zoom / DEG
    bob = p.bobamp if cfg["bob"] else 0
    ey = p.y + p.eh + math.sin(p.bobt * 2) * 0.035 * bob - p.land
    if not p.alive:
        ey = lerpf(p.y + 1.6, 0.35, cl(p.death_t * 2, 0, 1))
    rx, rz = -math.cos(p.yaw), math.sin(p.yaw)
    px = p.x + rx * math.cos(p.bobt) * 0.02 * bob
    pz = p.z + rz * math.cos(p.bobt) * 0.02 * bob
    f = look(p)
    return Camera3D(Vector3(px, ey, pz), Vector3(px + f[0], ey + f[1], pz + f[2]), Vector3(0, 1, 0), fov, 0)


def menu_camera():
    t = get_time() * 0.12
    return Camera3D(Vector3(math.cos(t) * 54, 18, math.sin(t) * 54), Vector3(0, 1.5, 0), Vector3(0, 1, 0), 55.0, 0)


def preview_camera():
    return Camera3D(Vector3(100, 1.5, 104.2), Vector3(100, 1.1, 100), Vector3(0, 1, 0), 50.0, 0)


def render_scene():
    st = g.state
    if st == "play" and g.p and not (g.paused and False):
        cam = play_camera()
    elif st == "char":
        cam = preview_camera()
    else:
        cam = menu_camera()
    g.cam = cam
    begin_texture_mode(g.rt)
    clear_background(BLACK)
    draw_rectangle_gradient_v(0, 0, SW, SH, C(70, 112, 170), C(185, 198, 212))
    begin_mode_3d(cam)
    rl_enable_depth_test()
    rl_enable_depth_mask()
    draw_env()
    if st == "play":
        draw_world_play()
    elif st == "char":
        set_view((100, 1.5, 104.2), 0.0)
        ch = characters.get(g.char)
        pv = type("Preview", (object,), {})()
        pv.alive, pv.walk, pv.vx, pv.vz = True, 0.0, 0.0, 0.0
        pv.knife_active, pv.glitch, pv.death_t, pv.rag_seed = False, 0.0, 0.0, 0.5
        pv.x, pv.y, pv.z = 100.0, 0.0, 100.0
        pv.yaw = math.sin(get_time() * 0.8) * 0.7 + 0.2
        pv.col = ch.color
        human.draw(pv, 0.0)
    end_mode_3d()
    end_texture_mode()
    viewer = g.p
    if viewer is not None and not viewer.alive and g.spec is not None and g.spec.alive:
        viewer = g.spec
    if st == "play" and viewer is not None and viewer.alive:
        begin_texture_mode(g.vmrt)
        clear_background(BLANK)
        if viewer.knife_active:
            draw_knife_viewmodel(viewer)
        else:
            draw_viewmodel(viewer)
        end_texture_mode()
        begin_texture_mode(g.rt)
        rl_disable_depth_test()
        begin_blend_mode(BLEND_ALPHA)
        draw_texture_rec(g.vmrt.texture, Rectangle(0, 0, SW, -SH), Vector2(0, 0), WHITE)
        end_blend_mode()
        end_texture_mode()


def draw_post():
    st = g.state
    sc, ox, oy = update_view()
    _v2[0], _v2[1] = SW, SH
    set_shader_value(POST, LOCS["res"], _v2, SHADER_UNIFORM_VEC2)
    sf(POST, LOCS["time"], get_time())
    sf(POST, LOCS["wave"], g.wave_t if (g.wave_on and st == "play") else -1.0)
    sf(POST, LOCS["hurt"], g.hurt if st == "play" else 0.0)
    sf(POST, LOCS["digital"], g.dig if st == "play" else 0.0)
    sf(POST, LOCS["ult"], (1.0 if g.ult_t > 0 else 0.0) if st == "play" else 0.0)
    sf(POST, LOCS["fx"], 1.0 if cfg["fx"] else 0.0)
    sw, sh = get_screen_width(), get_screen_height()
    # Letterbox barlarini once siyaha gom (eski kare kalintisi kayma hissi verir).
    clear_background(BLACK)
    begin_shader_mode(POST)
    draw_texture_pro(g.rt.texture, Rectangle(0, 0, SW, -SH),
                     Rectangle(ox, oy, SW * sc, SH * sc), Vector2(0, 0), 0.0, WHITE)
    end_shader_mode()
    if ox > 1:
        draw_rectangle(0, 0, int(ox), sh, BLACK)
        draw_rectangle(int(ox + SW * sc), 0, int(sw - ox - SW * sc) + 2, sh, BLACK)
    if oy > 1:
        draw_rectangle(0, 0, sw, int(oy), BLACK)
        draw_rectangle(0, int(oy + SH * sc), sw, int(sh - oy - SH * sc) + 2, BLACK)
