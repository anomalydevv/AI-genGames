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
from viewmodel import GLOVE, METAL, VM
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
    for nm in ("res", "time", "wave", "hurt", "digital", "ult", "fx"):
        LOCS[nm] = get_shader_location(POST, nm)
    CUBE = load_model_from_mesh(gen_mesh_cube(1.0, 1.0, 1.0))
    SPHERE = load_model_from_mesh(gen_mesh_sphere(0.5, 16, 16))
    CUBE.materials[0].shader = LIT
    SPHERE.materials[0].shader = LIT
    g.rt = load_render_texture(SW, SH)


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
    gl = [0.3, 0.45, 0.7, 0.6, 0.9][wi] if wi >= 0 else 0.4
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


def set_view(sh_pos, pattern):
    _v3[0], _v3[1], _v3[2] = sh_pos
    set_shader_value(LIT, LOCS["viewPos"], _v3, SHADER_UNIFORM_VEC3)
    sf(LIT, LOCS["pattern"], pattern)


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
    set_view((g.cam.position.x, g.cam.position.y, g.cam.position.z), 0.0)
    for f in g.FS:
        if f is p:
            continue
        if f.alive or f.death_t < 20:
            tip = 1.0 if not f.alive and f.death_t > 0.4 else (f.death_t / 0.4 if not f.alive else 0.0)
            draw_body(f.x, f.y, f.z, f.yaw, f.col, f.weapon, tip, f.glitch, f.walk)
    # golge
    for f in g.FS:
        if f.alive and f is not p:
            draw_circle_3d(Vector3(f.x, f.y + 0.03, f.z), 0.55, AX_X, 90.0, C(0, 0, 0, 90))
    for t in g.tracers:
        draw_line_3d(Vector3(t[0], t[1], t[2]), Vector3(t[3], t[4], t[5]), C(255, 235, 160))
    for q in g.parts:
        draw_cube(Vector3(q[0], q[1], q[2]), 0.05, 0.05, 0.05, q[7])
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


def draw_viewmodel():
    p = g.p
    w = WEAPONS[p.weapon]
    if w.scope and p.ads > 0.85:
        return
    vcam = Camera3D(Vector3(0, 0, 0), Vector3(0, 0, 1), Vector3(0, 1, 0), 58.0, 0)
    parts, muz = VM[p.weapon]
    ads = p.ads
    hip = (0.21, -0.19, 0.42)
    adsp = (0.0, -0.105, 0.36) if not w.scope else hip
    bx = lerpf(hip[0], adsp[0], ads) + (p.sway if cfg["sway"] else 0)
    by = lerpf(hip[1], adsp[1], ads) + (p.swayy if cfg["sway"] else 0)
    bz = lerpf(hip[2], adsp[2], ads) - p.kick * 0.008
    bob = p.bobamp * (1 - ads * 0.8) if cfg["bob"] else 0
    bx += math.cos(p.bobt) * 0.012 * bob
    by += -abs(math.sin(p.bobt)) * 0.016 * bob
    ang = -p.kick * 0.35 * DEG
    if p.reload_t > 0:
        k = math.sin(cl(1 - p.reload_t / w.reload, 0, 1) * math.pi)
        by -= 0.12 * k
        ang += 0.5 * k
    if p.switch_t > 0:
        k = cl(p.switch_t / 0.35, 0, 1)
        by -= 0.3 * k
        ang += 0.8 * k
    cs, sn = math.cos(ang), math.sin(ang)
    out = []
    alpha = 130 if p.ghost > 0 else 255
    for (r, y, z, sx, sy, sz, col) in parts:
        y2 = y * cs - z * sn
        z2 = y * sn + z * cs
        out.append((z2, -(bx + r), by + y2, bz + z2, sx, sy, sz, col))
    out.sort(key=lambda t: -t[0])
    begin_mode_3d(vcam)
    rl_disable_depth_test()
    set_view((0, 0, 0), 0.0)
    for (_, x, y, z, sx, sy, sz, col) in out:
        draw_model_ex(CUBE, Vector3(x, y, z), AX_X, ang / DEG, Vector3(sx, sy, sz), Color(col.r, col.g, col.b, alpha))
    if p.flash > 0:
        y2 = muz[1] * cs - muz[2] * sn
        z2 = muz[1] * sn + muz[2] * cs
        begin_blend_mode(BLEND_ADDITIVE)
        s = 0.07 + random.random() * 0.06
        draw_cube(Vector3(-(bx + muz[0]), by + y2, bz + z2 + 0.05), s, s, 0.12, C(255, 190, 80))
        draw_cube(Vector3(-(bx + muz[0]), by + y2, bz + z2 + 0.05), s * 2, s * 0.4, 0.05, C(255, 120, 30))
        end_blend_mode()
    end_mode_3d()


def _rot2(a, b, ang):
    c, s = math.cos(ang), math.sin(ang)
    return a * c - b * s, a * s + b * c


def draw_knife_viewmodel():
    p = g.p
    prog = 1.0 - p.slash_t / 0.30 if p.slash_t > 0 else 0.0
    swing = math.sin(prog * math.pi)
    bx, by, bz = 0.26, -0.22, 0.5
    bx += p.sway if cfg["sway"] else 0
    by += p.swayy if cfg["sway"] else 0
    bob = p.bobamp if cfg["bob"] else 0
    bx += math.cos(p.bobt) * 0.010 * bob
    by += -abs(math.sin(p.bobt)) * 0.012 * bob
    by += -p.land * 0.4
    axis_name, parts = knives.model(p.knife)
    if p.knife == "karambit":
        ang = prog * math.tau * 1.5
        thrust = swing * 0.18
    elif p.knife == "butterfly":
        ang = prog * math.tau * 2.0
        thrust = swing * 0.20
    else:
        ang = -swing * 0.9
        thrust = swing * 0.34
    axis = AX_Z if axis_name == "Z" else AX_X
    vcam = Camera3D(Vector3(0, 0, 0), Vector3(0, 0, 1), Vector3(0, 1, 0), 58.0, 0)
    begin_mode_3d(vcam)
    rl_disable_depth_test()
    set_view((0, 0, 0), 0.0)
    for lx, ly, lz, sx, sy, sz, col in parts:
        if axis is AX_Z:
            rx, ry = _rot2(lx, ly, ang)
            px, py, pz = rx, ry, lz + thrust
        else:
            ry, rz = _rot2(ly, lz, ang)
            px, py, pz = lx, ry, rz + thrust
        draw_model_ex(CUBE, Vector3(-(bx + px), by + py, bz + pz), axis, ang / DEG,
                      Vector3(sx, sy, sz), col)
    if p.slash_t > 0 and p.knife != "knife":
        a2 = ang * 0.82
        for lx, ly, lz, sx, sy, sz, col in parts[1:3]:
            if axis is AX_Z:
                rx, ry = _rot2(lx, ly, a2)
                px, py, pz = rx, ry, lz + thrust
            else:
                ry, rz = _rot2(ly, lz, a2)
                px, py, pz = lx, ry, rz + thrust
            draw_model_ex(CUBE, Vector3(-(bx + px), by + py, bz + pz), axis, a2 / DEG,
                          Vector3(sx, sy, sz), Color(col.r, col.g, col.b, 60))
    end_mode_3d()


def play_camera():
    p = g.p
    asp = SW / SH
    vf = 2 * math.atan(math.tan(cfg["fov"] * DEG / 2) / asp)
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
    draw_env()
    if st == "play":
        draw_world_play()
    elif st == "char":
        set_view((100, 1.5, 104.2), 0.0)
        ch = characters.get(g.char)
        draw_body(100, 0, 100, math.sin(get_time() * 0.8) * 0.7 + 0.2, ch.color, 3, 0.0, 0.0, 0.0)
    end_mode_3d()
    if st == "play" and g.p.alive:
        if g.p.knife_active:
            draw_knife_viewmodel()
        else:
            draw_viewmodel()
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
