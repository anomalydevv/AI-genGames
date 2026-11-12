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
import knives
from config import CYAN, DEG, SW, SH, C, cfg, cl, lerpf
from fighter import look
from shaders import FS_LIT, FS_POST, VS_LIT, VS_POST
from state import g
from viewmodel import GLOVE, METAL, SLEEVE, VM
from weapons import WEAPONS
from world import BOX

CUBE = SPHERE = LIT = POST = None
AX_Y = Vector3(0, 1, 0)
AX_X = Vector3(1, 0, 0)
AX_Z = Vector3(0, 0, 1)
_f = _v2 = _v3 = None
LOCS = {}


def init_gfx():
    global CUBE, SPHERE, LIT, POST, _f, _v2, _v3
    _f = ffi.new("float *")
    _v2 = ffi.new("float[2]")
    _v3 = ffi.new("float[3]")
    font = None
    ldir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
    for pth in (os.path.join(ldir, "Rajdhani-Regular.ttf"), os.path.join(ldir, "Orbitron.ttf"),
                "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans.ttf"):
        if os.path.exists(pth):
            try:
                cps = list(range(32, 127)) + [ord(c) for c in "ğüşıöçĞÜŞİÖÇ"]
                arr = ffi.new("int[]", cps)
                font = load_font_ex(pth, 48, arr, len(cps))
                set_texture_filter(font.texture, TEXTURE_FILTER_BILINEAR)
                break
            except Exception:
                font = None
    ui.set_font(font)
    LIT = load_shader_from_memory(VS_LIT, FS_LIT)
    POST = load_shader_from_memory(VS_POST, FS_POST)
    LOCS["viewPos"] = get_shader_location(LIT, "viewPos")
    LOCS["pattern"] = get_shader_location(LIT, "pattern")
    LOCS["vm"] = get_shader_location(LIT, "vm")
    for nm in ("res", "time", "wave", "hurt", "digital", "ult", "fx"):
        LOCS[nm] = get_shader_location(POST, nm)
    CUBE = load_model_from_mesh(gen_mesh_cube(1.0, 1.0, 1.0))
    SPHERE = load_model_from_mesh(gen_mesh_sphere(0.5, 16, 16))
    CUBE.materials[0].shader = LIT
    SPHERE.materials[0].shader = LIT
    g.rt = load_render_texture(SW, SH)
    g.vmrt = load_render_texture(SW, SH)


def sf(sh, loc, v):
    _f[0] = v
    set_shader_value(sh, loc, _f, SHADER_UNIFORM_FLOAT)


def draw_body(x, y, z, yaw, acc, wi, tip, glitch, walk):
    sn, cs = math.sin(yaw), math.cos(yaw)
    dark, suit, pants = C(34, 37, 45), C(58, 64, 78), C(42, 46, 56)
    if glitch > 0:
        suit = C(0, 190, 170)
        pants = C(0, 140, 130)
        acc = C(180, 255, 245)
    sw = math.sin(walk) * 0.16
    gl = VM[wi][1][2] if wi in VM else 0.4
    parts = [(0.11, 0.06, sw, 0.14, 0.12, 0.26, dark), (-0.11, 0.06, -sw, 0.14, 0.12, 0.26, dark),
             (0.11, 0.46, sw * 0.7, 0.15, 0.72, 0.17, pants), (-0.11, 0.46, -sw * 0.7, 0.15, 0.72, 0.17, pants),
             (0, 1.12, 0, 0.46, 0.62, 0.26, suit), (0, 0.82, 0, 0.48, 0.1, 0.28, dark),
             (0, 1.2, -0.14, 0.3, 0.3, 0.05, acc), (0.3, 1.18, 0.05, 0.13, 0.5, 0.15, suit),
             (-0.3, 1.18, 0.05, 0.13, 0.5, 0.15, suit), (0.28, 1.1, 0.25, 0.1, 0.1, 0.35, GLOVE),
             (0.2, 1.12, 0.2 + gl / 2, 0.07, 0.1, gl, METAL), (0, 1.68, 0.1, 0.27, 0.07, 0.14, acc)]
    for (r, yy, ff, sx, sy_, sz, col) in parts:
        yy2 = lerpf(yy, 0.14, tip)
        ff2 = lerpf(ff, -yy, tip)
        s1, s2 = lerpf(sy_, sz, tip), lerpf(sz, sy_, tip)
        wx = x + r * (-cs) + ff2 * sn
        wz = z + r * sn + ff2 * cs
        draw_model_ex(CUBE, Vector3(wx, y + yy2, wz), AX_Y, yaw / DEG, Vector3(sx, s1, s2), col)
    hy = lerpf(1.6, 0.17, tip)
    hf = lerpf(0.0, -1.6, tip)
    draw_model_ex(SPHERE, Vector3(x + hf * sn, y + hy, z + hf * cs), AX_Y, 0, Vector3(0.36, 0.38, 0.36), C(190, 150, 125))
    draw_model_ex(CUBE, Vector3(x + hf * sn, y + hy + 0.08, z + hf * cs), AX_Y, yaw / DEG, Vector3(0.4, 0.14, 0.4), dark)


def draw_drop(d):
    parts = VM[d["wi"]][0]
    yaw = d["yaw"]
    cs, sn = math.cos(yaw), math.sin(yaw)
    sc = 0.55
    for part in parts:
        x, y, z, sx, sy_, sz, col = part[:7]
        if col is GLOVE or col is SLEEVE:
            continue
        wx = d["x"] - x * cs * sc + z * sn * sc
        wz = d["z"] + x * sn * sc + z * cs * sc
        draw_model_ex(CUBE, Vector3(wx, 0.12 + y * sc, wz), AX_Y, yaw / DEG,
                      Vector3(sx * sc, sy_ * sc, sz * sc), col)
    draw_circle_3d(Vector3(d["x"], 0.035, d["z"]), 0.38, AX_X, 90.0, C(0, 230, 200, 30))


def set_view(sh_pos, pattern):
    _v3[0], _v3[1], _v3[2] = sh_pos
    set_shader_value(LIT, LOCS["viewPos"], _v3, SHADER_UNIFORM_VEC3)
    sf(LIT, LOCS["pattern"], pattern)
    sf(LIT, LOCS["vm"], 0.0)


def draw_env():
    cam = g.cam
    set_view((cam.position.x, cam.position.y, cam.position.z), 1.0)
    draw_model_ex(CUBE, Vector3(0, -0.5, 0), AX_Y, 0, Vector3(120, 1, 120), C(98, 100, 106))
    for b in BOX:
        draw_model_ex(CUBE, Vector3((b[0] + b[3]) / 2, (b[1] + b[4]) / 2, (b[2] + b[5]) / 2), AX_Y, 0,
                      Vector3(b[3] - b[0], b[4] - b[1], b[5] - b[2]), b[6])
    for (x, y, z, sx, sz) in [(0, 5.5, -29.95, 40, 0.06), (0, 5.5, 29.95, 40, 0.06), (-29.95, 5.5, 0, 0.06, 40),
                              (29.95, 5.5, 0, 0.06, 40)]:
        draw_cube(Vector3(x, y, z), sx, 0.12, sz, C(0, 230, 200))
    for (x, z) in ((-20, -20), (20, 20), (-20, 20), (20, -20)):
        draw_cube(Vector3(x, 5.2, z), 3.1, 0.1, 3.1, C(255, 60, 140))


def draw_world_play():
    p = g.p
    viewer = p if p.alive else g.spec
    set_view((g.cam.position.x, g.cam.position.y, g.cam.position.z), 0.0)
    for f in g.FS:
        if f is viewer:
            continue
        if f.alive or f.death_t < 20:
            tip = 1.0 if not f.alive and f.death_t > 0.4 else (f.death_t / 0.4 if not f.alive else 0.0)
            draw_body(f.x, f.y, f.z, f.yaw, f.col, f.weapon, tip, f.glitch, f.walk)
    # golge
    for f in g.FS:
        if f.alive and f is not viewer:
            draw_circle_3d(Vector3(f.x, f.y + 0.03, f.z), 0.55, AX_X, 90.0, C(0, 0, 0, 90))
    for t in g.tracers:
        draw_line_3d(Vector3(t[0], t[1], t[2]), Vector3(t[3], t[4], t[5]), C(255, 235, 160))
    for q in g.parts:
        draw_cube(Vector3(q[0], q[1], q[2]), 0.05, 0.05, 0.05, q[7])
    for d in g.drops:
        draw_drop(d)
    for letter, (sx, sz) in bomb.SITES.items():
        active = g.site_plan == letter
        draw_circle_3d(Vector3(sx, 0.04, sz), bomb.SITE_R, AX_X, 90.0,
                       C(0, 230, 200, 45) if active else C(255, 205, 70, 35))
        draw_circle_3d(Vector3(sx, 0.05, sz), bomb.SITE_R * 0.55, AX_X, 90.0, C(0, 230, 200, 20))
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
    if g.ult_t > 0:
        rl_draw_render_batch_active()
        rl_disable_depth_test()
        for o in g.FS:
            if o is not p and o.alive:
                draw_cube_wires(Vector3(o.x, o.y + 0.9, o.z), 0.9, 1.8, 0.9, C(255, 60, 90))
        rl_draw_render_batch_active()
        rl_enable_depth_test()


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
_GUN_INSPECT = {
    0: (1.55, 1.10, 0.22, 0.26, 0.62, 1.00),
    1: (1.15, 1.05, 0.20, 0.30, 0.66, 1.00),
    2: (1.00, 0.95, 0.18, 0.22, 0.88, 0.92),
    3: (0.95, 0.90, 0.20, 0.25, 0.92, 0.92),
    4: (0.65, 0.80, 0.16, 0.20, 1.12, 0.88),
    5: (0.90, 0.90, 0.18, 0.24, 0.92, 0.92),
    6: (1.65, 1.15, 0.24, 0.28, 0.72, 1.00),
    7: (0.60, 0.75, 0.15, 0.18, 1.02, 0.90),
}


def _gun_pose(p, wi):
    w = WEAPONS[wi]
    parts, muz = VM[wi]
    pivot = (0.0, -0.08, 0.02)
    if p.inspect:
        t = p.inspect_t
        spd, ya, pa, ra, dist, sc_t = _GUN_INSPECT.get(wi, (1.0, 0.95, 0.20, 0.24, 0.80, 0.95))
        k = _smooth(t / 0.35)
        yaw = math.sin(t * spd) * ya
        pitch = 0.12 + math.sin(t * spd * 2.0 + 0.9) * pa
        roll = math.sin(t * spd + 1.7) * ra
        R = _mm(_rz(roll), _mm(_rx(pitch), _ry(yaw)))
        bx = lerpf(0.21, 0.02, k)
        by = lerpf(-0.19, -0.10, k) + math.sin(t * spd * 1.6) * 0.012
        bz = lerpf(0.42, dist, k) + math.sin(t * spd * 0.8) * 0.010
        return parts, muz, pivot, R, (bx, by, bz), lerpf(1.0, sc_t, k)
    ads = p.ads
    hip = (0.21, -0.19, 0.42)
    adsp = (0.0, -0.105, 0.36) if not w.scope else hip
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
    return parts, muz, pivot, _rx(ang), (bx, by, bz), 1.0


def draw_viewmodel():
    p = g.p
    wi = p.weapon
    w = WEAPONS[wi]
    if w.scope and p.ads > 0.85:
        return
    parts, muz, pivot, R, base, sc = _gun_pose(p, wi)
    axis, ang = _axis_angle(_mirror_rot(R))
    back = math.sin(cl(p.cycle, 0.0, 1.0) * math.pi)
    insp = p.inspect
    vcam = Camera3D(Vector3(0, 0, 0), Vector3(0, 0, 1), Vector3(0, 1, 0), 58.0, 0)
    begin_mode_3d(vcam)
    rl_enable_depth_test()
    rl_enable_depth_mask()
    set_view((0, 0, 0), 0.0)
    sf(LIT, LOCS["vm"], 1.0)
    for part in parts:
        x, y, z, sx, sy_, sz, col = part[:7]
        tag = part[7] if len(part) > 7 else ""
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
        if insp and wi == 2 and tag == "pump":
            dz -= 0.055 * (0.5 + 0.5 * math.sin(p.inspect_t * 3.2))
        d = _mv(R, ((x - pivot[0]) * sc, (y - pivot[1]) * sc, (dz - pivot[2]) * sc))
        pos = Vector3(-(base[0] + pivot[0] + d[0]),
                      base[1] + pivot[1] + d[1],
                      base[2] + pivot[2] + d[2])
        draw_model_ex(CUBE, pos, axis, ang, Vector3(sx * sc, sy_ * sc, sz * sc),
                      Color(col.r, col.g, col.b, 255))
    if p.flash > 0 and not insp:
        d = _mv(R, ((muz[0] - pivot[0]) * sc, (muz[1] - pivot[1]) * sc, (muz[2] - pivot[2]) * sc))
        fx = -(base[0] + pivot[0] + d[0])
        fy = base[1] + pivot[1] + d[1]
        fz = base[2] + pivot[2] + d[2] + 0.05
        rl_disable_depth_test()
        begin_blend_mode(BLEND_ADDITIVE)
        s = 0.07 + random.random() * 0.06
        draw_cube(Vector3(fx, fy, fz), s, s, 0.12, C(255, 190, 80))
        draw_cube(Vector3(fx, fy, fz), s * 2, s * 0.4, 0.05, C(255, 120, 30))
        end_blend_mode()
        rl_enable_depth_test()
    end_mode_3d()


# ---------------------------------------------------------------------------
#  BICAK viewmodel: sag elde tutus + bicaga ozel inceleme animasyonlari
# ---------------------------------------------------------------------------
_KNIFE_RIG = {
    "knife": dict(pos=(-0.30, -0.22, 0.72), scale=0.62, roll=0.52,
                  pivot=(0.0, -0.010, -0.130), hand=0.00,
                  insp=(-0.14, -0.03, 0.88), iscale=0.62),
    "karambit": dict(pos=(-0.30, -0.23, 0.72), scale=0.55, roll=0.58,
                     pivot=(0.0, -0.030, -0.370), hand=0.09,
                     insp=(-0.12, -0.02, 0.92), iscale=0.52),
    "butterfly": dict(pos=(-0.30, -0.22, 0.72), scale=0.62, roll=0.55,
                      pivot=(0.0, -0.005, 0.030), hand=0.01,
                      insp=(-0.14, -0.08, 0.82), iscale=0.70),
}


def _knife_base(kid):
    return _mm(_rz(_KNIFE_RIG[kid]["roll"]), _ry(math.pi * 0.5))


def _knife_slash_A(kid, prog):
    swing = math.sin(prog * math.pi)
    if kid == "knife":
        return _mm(_rz(-swing * 1.15), _mm(_ry(swing * 0.35), _rx(swing * 0.18))), swing
    if kid == "karambit":
        return _mm(_rz(-swing * 1.65), _mm(_ry(swing * 0.55), _rx(swing * 0.10))), swing
    return _mm(_rz(-swing * 1.45), _mm(_ry(swing * 0.45), _rx(swing * 0.16))), swing


def _slash_offset(kid, swing):
    if kid == "knife":
        return (swing * 0.16, swing * 0.06, swing * 0.06)
    if kid == "karambit":
        return (swing * 0.20, swing * 0.08, swing * 0.04)
    return (swing * 0.18, swing * 0.07, swing * 0.08)


def _knife_pose(p, kid):
    rig = _KNIFE_RIG[kid]
    B = _knife_base(kid)
    bx, by, bz = rig["pos"]
    if p.inspect:
        t = p.inspect_t
        if kid == "karambit":
            A = _mm(_rz(t * 3.1), _mm(_ry(0.18 * math.sin(t * 1.7)),
                                      _rx(0.12 * math.sin(t * 1.3))))
            bob = (0.0, 0.020 * math.sin(t * 2.2), 0.0)
        elif kid == "butterfly":
            A = _mm(_rz(0.52 * math.sin(t * 0.9)), _mm(_ry(0.40 * math.sin(t * 0.63)),
                                                        _rx(0.14 * math.sin(t * 1.25))))
            bob = (0.018 * math.sin(t * 0.8), 0.020 * math.sin(t * 1.6),
                   0.010 * math.sin(t * 1.1))
        else:
            A = _mm(_rz(t * 2.2), _mm(_ry(0.16 * math.sin(t * 1.4)),
                                      _rx(0.10 * math.sin(t * 1.1))))
            bob = (0.0, 0.015 * math.sin(t * 1.7), 0.0)
        k = _smooth(t / 0.30)
        ix, iy, iz = rig["insp"]
        bx = lerpf(-0.26, ix, k) + bob[0]
        by = lerpf(-0.24, iy, k) + bob[1]
        bz = lerpf(0.62, iz, k) + bob[2]
        return (bx, by, bz), _mm(A, B), lerpf(rig["scale"], rig["iscale"], k)
    bx += -(p.sway if cfg["sway"] else 0.0)
    by += (p.swayy if cfg["sway"] else 0.0)
    bob = p.bobamp if cfg["bob"] else 0.0
    bx += math.cos(p.bobt) * 0.008 * bob
    by += -abs(math.sin(p.bobt)) * 0.012 * bob
    by -= p.land * 0.4
    if p.slash_t > 0:
        prog = 1.0 - p.slash_t / 0.30
        A, swing = _knife_slash_A(kid, prog)
        off = _slash_offset(kid, swing)
        return (bx + off[0], by + off[1], bz + off[2]), _mm(A, B), rig["scale"]
    return (bx, by, bz), B, rig["scale"]


def _draw_knife_group(parts, base, R, pivot, scale, hinge, alpha, hinge_b=0.0):
    for part in parts:
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
        d = _mv(R, d)
        Rp = _mm(R, Rh)
        axis, ang = _axis_angle(Rp)
        draw_model_ex(CUBE, Vector3(base[0] + d[0], base[1] + d[1], base[2] + d[2]),
                      axis, ang, Vector3(sx * scale, sy * scale, sz * scale),
                      Color(col.r, col.g, col.b, alpha))


def _draw_knife_hand(base, B, kid, scale):
    rig = _KNIFE_RIG[kid]
    hdir = _mv(B, (0.0, 0.0, -1.0))
    off = rig["hand"] * scale
    palm = (base[0] + hdir[0] * off, base[1] + hdir[1] * off, base[2] + hdir[2] * off)
    _box(palm, B, (0.10 * scale, 0.13 * scale, 0.17 * scale), GLOVE)
    for i in range(3):
        u = (0.02 + i * 0.05) * scale
        fp = (palm[0] + hdir[0] * u, palm[1] + hdir[1] * u, palm[2] + hdir[2] * u - 0.055 * scale)
        _box(fp, B, (0.095 * scale, 0.042 * scale, 0.042 * scale), GLOVE)
    if kid == "karambit":
        _box((base[0], base[1], base[2] - 0.045 * scale), _IDENT,
             (0.042 * scale, 0.042 * scale, 0.14 * scale), GLOVE)
    wrist = (palm[0] + hdir[0] * 0.10 * scale, palm[1] + hdir[1] * 0.10 * scale,
             palm[2] + hdir[2] * 0.10 * scale)
    elbow = (wrist[0] - 0.30 * scale, wrist[1] - 0.38 * scale, wrist[2] - 0.10 * scale)
    acc = knives.by_id(kid).color
    _box_between(wrist, elbow, 0.105 * scale, SLEEVE)
    _box_between(wrist, (wrist[0] - 0.06 * scale, wrist[1] - 0.075 * scale,
                         wrist[2] - 0.018 * scale), 0.118 * scale, acc)


def draw_knife_viewmodel():
    p = g.p
    kid = p.knife
    rig = _KNIFE_RIG[kid]
    base, R, sc = _knife_pose(p, kid)
    B = _knife_base(kid)
    _axis_name, parts = knives.model(kid)
    hinge = p.hinge_a if kid == "butterfly" else 0.0
    hinge_b = p.hinge_b if kid == "butterfly" else 0.0
    vcam = Camera3D(Vector3(0, 0, 0), Vector3(0, 0, 1), Vector3(0, 1, 0), 58.0, 0)
    begin_mode_3d(vcam)
    rl_enable_depth_test()
    rl_enable_depth_mask()
    set_view((0, 0, 0), 0.0)
    sf(LIT, LOCS["vm"], 1.0)
    _draw_knife_hand(base, B, kid, sc)
    if p.slash_t > 0 and not p.inspect:
        prog = 1.0 - p.slash_t / 0.30
        cur = _slash_offset(kid, math.sin(prog * math.pi))
        gbase = (base[0] - cur[0], base[1] - cur[1], base[2] - cur[2])
        rl_disable_depth_mask()
        for back, alpha in ((0.18, 25), (0.10, 45), (0.04, 70)):
            A, sw = _knife_slash_A(kid, max(0.0, prog - back))
            off = _slash_offset(kid, sw)
            gb = (gbase[0] + off[0], gbase[1] + off[1], gbase[2] + off[2])
            _draw_knife_group(parts, gb, _mm(A, B), rig["pivot"], sc, 0.0, alpha)
        rl_enable_depth_mask()
    _draw_knife_group(parts, base, R, rig["pivot"], sc, hinge, 255, hinge_b)
    end_mode_3d()



def play_camera():
    p = g.p
    asp = SW / SH
    vf = 2 * math.atan(math.tan(cfg["fov"] * DEG / 2) / asp)
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
    return Camera3D(Vector3(math.cos(t) * 40, 15, math.sin(t) * 40), Vector3(0, 1.5, 0), Vector3(0, 1, 0), 55.0, 0)


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
        draw_body(100, 0, 100, math.sin(get_time() * 0.8) * 0.7 + 0.2, ch.color, 3, 0.0, 0.0, 0.0)
    end_mode_3d()
    end_texture_mode()
    if st == "play" and g.p.alive:
        begin_texture_mode(g.vmrt)
        clear_background(BLANK)
        if g.p.knife_active:
            draw_knife_viewmodel()
        else:
            draw_viewmodel()
        end_texture_mode()
        begin_texture_mode(g.rt)
        rl_disable_depth_test()
        begin_blend_mode(BLEND_ALPHA)
        draw_texture_rec(g.vmrt.texture, Rectangle(0, 0, SW, -SH), Vector2(0, 0), WHITE)
        end_blend_mode()
        end_texture_mode()


def draw_post():
    st = g.state
    _v2[0], _v2[1] = SW, SH
    set_shader_value(POST, LOCS["res"], _v2, SHADER_UNIFORM_VEC2)
    sf(POST, LOCS["time"], get_time())
    sf(POST, LOCS["wave"], g.wave_t if (g.wave_on and st == "play") else -1.0)
    sf(POST, LOCS["hurt"], g.hurt if st == "play" else 0.0)
    sf(POST, LOCS["digital"], g.dig if st == "play" else 0.0)
    sf(POST, LOCS["ult"], (1.0 if g.ult_t > 0 else 0.0) if st == "play" else 0.0)
    sf(POST, LOCS["fx"], 1.0 if cfg["fx"] else 0.0)
    begin_shader_mode(POST)
    draw_texture_rec(g.rt.texture, Rectangle(0, 0, SW, -SH), Vector2(0, 0), WHITE)
    end_shader_mode()
