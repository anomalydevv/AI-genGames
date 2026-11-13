# -*- coding: utf-8 -*-
"""Bicak gorunus, inceleme ve saldiri animasyonlari.

Animasyon prensipleri (12 principles of animation):
  * Anticipation   : vurustan once geri cekilme (wind-up)
  * Follow-through : vurustan sonra yumusak toparlanma / hafif overshoot
  * Ease in/out    : tum gecislerde smootherstep / cubic egri
  * Spring physics : kelebek bicagi mentesesi sabit adimli yay-sonum modeli
  * Squash/punch   : vurus aninda hafif olcek vurgusu
Tum dis API (fonksiyon adlari / imzalari) orijinaliyle uyumludur.
"""
import math

from pyray import *

import knives
import skins
from config import C, cfg, cl, lerpf

KNIFE_RIG = {
    "knife": dict(pos=(-0.30, -0.22, 0.66), scale=0.62, roll=0.52,
                  pivot=(0.0, -0.010, -0.130), hand=0.00,
                  insp=(-0.14, -0.03, 0.84), iscale=0.62,
                  arm_side=-1.0, arm_offset=(-0.22, -0.34, -0.13),
                  arm_length=1.10, thumb_side=1.0, thumb_angle=0.65),
    "karambit": dict(pos=(-0.30, -0.23, 0.66), scale=0.55, roll=0.58,
                     pivot=(0.0, -0.030, -0.370), hand=0.09,
                     insp=(-0.12, -0.02, 0.88), iscale=0.52,
                     arm_side=-1.0, arm_offset=(-0.22, -0.34, -0.13),
                     arm_length=1.10, thumb_side=1.0, thumb_angle=0.65),
    "butterfly": dict(pos=(-0.30, -0.22, 0.66), scale=0.62, roll=0.55,
                      pivot=(0.0, -0.005, 0.030), hand=0.01,
                      insp=(-0.14, -0.08, 0.78), iscale=0.70,
                      arm_side=-1.0, arm_offset=(-0.22, -0.34, -0.13),
                      arm_length=1.10, thumb_side=1.0, thumb_angle=0.65),
}

SLASH_ANIM_TIME = 0.34
INSPECT_IN_TIME = 0.35
INSPECT_OUT_TIME = 0.22

# Slash fazlari (normalize 0..1)
_WINDUP_END = 0.18
_STRIKE_END = 0.52
_WINDUP_DEPTH = 0.22

# Kelebek mentese yayi
_HINGE_STIFFNESS = 220.0
_HINGE_DAMPING_RATIO = 0.42
_HINGE_OPEN = 1.30
_HINGE_MIN, _HINGE_MAX = -0.18, 1.45


# ----------------------------------------------------------------------------
# Matematik yardimcilari
# ----------------------------------------------------------------------------
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


def _a(x):
    """Alpha degerini 0..255 araliginda tam sayiya sabitle."""
    return 0 if x < 0 else 255 if x > 255 else int(x)


def _col(color, alpha):
    return C(color.r, color.g, color.b, _a(alpha))


# ----------------------------------------------------------------------------
# Easing fonksiyonlari
# ----------------------------------------------------------------------------
def _smooth(k):
    k = cl(k, 0.0, 1.0)
    return k * k * (3.0 - 2.0 * k)


def _smoother(k):
    k = cl(k, 0.0, 1.0)
    return k * k * k * (k * (k * 6.0 - 15.0) + 10.0)


def _ease_out_cubic(k):
    k = 1.0 - cl(k, 0.0, 1.0)
    return 1.0 - k * k * k


def _ease_in_out_cubic(k):
    k = cl(k, 0.0, 1.0)
    return 4.0 * k * k * k if k < 0.5 else 1.0 - ((-2.0 * k + 2.0) ** 3) / 2.0


def _spring_step(x, v, target, stiffness, ratio, dt, substeps=4):
    """Yari-ortuk Euler, alt adimli yay-sonum. Dusuk FPS'te de kararli."""
    h = dt / substeps
    damping = 2.0 * ratio * math.sqrt(stiffness)
    for _ in range(substeps):
        v += ((target - x) * stiffness - v * damping) * h
        x += v * h
    return x, v


# ----------------------------------------------------------------------------
# Inspect durumu
# ----------------------------------------------------------------------------
def inspect_amount(p):
    if getattr(p, "inspect", False):
        return _smoother(min(1.0, max(0.0, p.inspect_t) / INSPECT_IN_TIME))
    out = getattr(p, "inspect_out", 0.0)
    if out > 0.0:
        return _smoother(min(1.0, out / INSPECT_OUT_TIME))
    return 0.0


def toggle_inspect(p):
    if p.inspect:
        p.inspect = False
        p.inspect_out = INSPECT_OUT_TIME
    else:
        p.inspect = True
        p.inspect_out = 0.0
        p.inspect_t = 0.0


def update_slash(p, dt):
    p.slash_t = max(0.0, p.slash_t - dt)


# Butterfly inspect koreografisi: (bitis_zamani, A_hedef, B_hedef)
_BUTTERFLY_SEQ = (
    (0.5, _HINGE_OPEN, 0.0),
    (1.0, 0.0, 0.0),
    (1.5, 0.0, _HINGE_OPEN),
    (2.0, 0.0, 0.0),
    (2.4, _HINGE_OPEN, 0.0),
    (2.8, 0.0, 0.0),
)
_BUTTERFLY_LOOP = 3.6


def _butterfly_targets(t):
    t %= _BUTTERFLY_LOOP
    for end, ta, tb in _BUTTERFLY_SEQ:
        if t < end:
            return ta, tb
    return 0.0, 0.0


def update(p, dt):
    dt = min(dt, 0.05)  # buyuk frame atlamalarinda patlamayi onle
    p.inspect_t += dt
    p.inspect_out = max(0.0, p.inspect_out - dt)
    if p.knife_active and p.knife == "butterfly":
        ta, tb = _butterfly_targets(p.inspect_t) if p.inspect else (0.0, 0.0)
        a, p.hinge_v = _spring_step(p.hinge_a, p.hinge_v, ta,
                                    _HINGE_STIFFNESS, _HINGE_DAMPING_RATIO, dt)
        b, p.hinge_bv = _spring_step(p.hinge_b, p.hinge_bv, tb,
                                     _HINGE_STIFFNESS, _HINGE_DAMPING_RATIO, dt)
        p.hinge_a = cl(a, _HINGE_MIN, _HINGE_MAX)
        p.hinge_b = cl(b, _HINGE_MIN, _HINGE_MAX)
    else:
        p.hinge_a = p.hinge_b = 0.0
        p.hinge_v = p.hinge_bv = 0.0


# ----------------------------------------------------------------------------
# Slash animasyonu
# ----------------------------------------------------------------------------
def knife_base(kid):
    return _mm(_rz(KNIFE_RIG[kid]["roll"]), _ry(math.pi * 0.5))


def _slash_curve(u):
    """Anticipation -> strike -> follow-through egrisi.

    Donus degeri:  <0 geri cekilme, 1 vurus tepesi, 0 bitis.
    """
    u = cl(u, 0.0, 1.0)
    if u < _WINDUP_END:
        return -_WINDUP_DEPTH * _smooth(u / _WINDUP_END)
    if u < _STRIKE_END:
        k = (u - _WINDUP_END) / (_STRIKE_END - _WINDUP_END)
        return -_WINDUP_DEPTH + (1.0 + _WINDUP_DEPTH) * _ease_out_cubic(k)
    k = (u - _STRIKE_END) / (1.0 - _STRIKE_END)
    return (1.0 - _smoother(k)) - 0.05 * math.sin(k * math.pi)


def slash_pose(kid, progress):
    swing = _slash_curve(progress)
    windup = max(0.0, -swing) / _WINDUP_DEPTH
    if kid == "knife":
        rotation = _mm(_rz(-swing * 1.15),
                       _mm(_ry(swing * 0.35), _rx(swing * 0.18)))
    elif kid == "karambit":
        spin_k = _smoother((progress - _WINDUP_END * 0.6) / 0.80)
        spin = spin_k * math.tau - windup * 0.30
        rotation = _mm(_rz(-spin),
                       _mm(_ry(swing * 0.55), _rx(swing * 0.10)))
    else:
        rotation = _mm(_rz(-swing * 1.45),
                       _mm(_ry(swing * 0.45), _rx(swing * 0.16)))
    return rotation, swing


def slash_offset(kid, swing):
    if kid == "knife":
        return swing * 0.16, swing * 0.06, swing * 0.06
    if kid == "karambit":
        return swing * 0.20, swing * 0.08, swing * 0.04
    return swing * 0.18, swing * 0.07, swing * 0.08


def slash_progress(slash_t):
    return max(0.0, 1.0 - slash_t / SLASH_ANIM_TIME)


def slash_ghosts(kid, slash_t):
    progress = slash_progress(slash_t)
    current_offset = slash_offset(kid, _slash_curve(progress))
    ghosts = []
    for back, alpha in ((0.18, 25), (0.10, 45), (0.04, 70)):
        rotation, swing = slash_pose(kid, max(0.0, progress - back))
        ghosts.append((back, alpha, rotation, swing))
    return progress, current_offset, ghosts


# ----------------------------------------------------------------------------
# Bicak pozu
# ----------------------------------------------------------------------------
_INSPECT_MOTION = {
    # yaw_amp, yaw_f, pitch_amp, pitch_f, pitch_ph, roll terimleri, bob
    "karambit": dict(yaw=(0.58, 0.78, 0.0), pitch=(0.22, 1.45, 0.6),
                     roll=((0.78, 0.56, 0.3), (0.16, 2.25, 0.0)),
                     bob=((0.014, 1.1), (0.022, 1.8), (0.012, 1.35, True))),
    "butterfly": dict(yaw=(0.42, 0.84, 0.0), pitch=(0.18, 1.3, 0.4),
                      roll=((0.38, 1.05, 0.0), (0.14, 2.6, 0.0)),
                      bob=((0.018, 0.9), (0.020, 1.6), (0.010, 1.1))),
    "knife": dict(yaw=(0.32, 0.9, 0.0), pitch=(0.14, 1.5, 0.0),
                  roll=((0.45, 0.7, 0.0),),
                  bob=((0.008, 1.2), (0.015, 1.7), (0.0, 1.0))),
}


def _inspect_motion(kid, t):
    m = _INSPECT_MOTION.get(kid, _INSPECT_MOTION["knife"])
    yaw = m["yaw"][0] * math.sin(t * m["yaw"][1] + m["yaw"][2])
    pitch = m["pitch"][0] * math.sin(t * m["pitch"][1] + m["pitch"][2])
    roll = sum(a * math.sin(t * f + ph) for a, f, ph in m["roll"])
    bx, by, bz = m["bob"]
    bob = (bx[0] * math.sin(t * bx[1]),
           by[0] * math.sin(t * by[1]),
           bz[0] * (math.cos(t * bz[1]) if len(bz) > 2 else math.sin(t * bz[1])))
    return yaw, pitch, roll, bob


def knife_pose(p, kid):
    rig = KNIFE_RIG[kid]
    base_rotation = knife_base(kid)
    bx, by, bz = rig["pos"]
    bx -= p.sway if cfg["sway"] else 0.0
    by += p.swayy if cfg["sway"] else 0.0
    bob = p.bobamp if cfg["bob"] else 0.0
    bx += math.cos(p.bobt) * 0.008 * bob
    by -= abs(math.sin(p.bobt)) * 0.012 * bob
    by -= p.land * 0.4
    neutral = (bx, by, bz)
    inspect = inspect_amount(p)

    if inspect <= 0.001:
        if p.slash_t > 0:
            progress = slash_progress(p.slash_t)
            rotation, swing = slash_pose(kid, progress)
            offset = slash_offset(kid, swing)
            punch = 1.0 + 0.06 * max(0.0, swing)  # vurus aninda olcek vurgusu
            return ((bx + offset[0], by + offset[1], bz + offset[2]),
                    _mm(rotation, base_rotation), rig["scale"] * punch, 0.0)
        return neutral, base_rotation, rig["scale"], 0.0

    yaw, pitch, roll, bob_v = _inspect_motion(kid, p.inspect_t)
    rotation = _mm(_rz(roll * inspect),
                   _mm(_rx(pitch * inspect), _ry(yaw * inspect)))
    ix, iy, iz = rig["insp"]
    inspected = (ix + bob_v[0], iy + bob_v[1], iz + bob_v[2])
    base = tuple(lerpf(neutral[i], inspected[i], inspect) for i in range(3))
    scale = lerpf(rig["scale"], rig["iscale"], inspect)
    return base, _mm(rotation, base_rotation), scale, inspect


# ----------------------------------------------------------------------------
# Bicak ucu + slash izi
# ----------------------------------------------------------------------------
_TIP_CACHE = {}


def _knife_tip(kid):
    if kid not in _TIP_CACHE:
        _axis, parts = knives.model(kid)
        best = max(parts, key=lambda part: part[2] + part[5] * 0.5)
        _TIP_CACHE[kid] = (best[0], best[1], best[2] + best[5] * 0.5)
    return _TIP_CACHE[kid]


_TRAIL_SAMPLES = 14
_TRAIL_STEP = 0.016


def _trail_point(kid, base, base_rotation, progress, pivot, scale, tip):
    rotation, swing = slash_pose(kid, progress)
    offset = slash_offset(kid, swing)
    delta = _mv(_mm(rotation, base_rotation),
                ((tip[0] - pivot[0]) * scale,
                 (tip[1] - pivot[1]) * scale,
                 (tip[2] - pivot[2]) * scale))
    return (base[0] + offset[0] + delta[0],
            base[1] + offset[1] + delta[1],
            base[2] + offset[2] + delta[2])


def draw_slash_trail(kid, base, base_rotation, progress, pivot, scale, color):
    tip = _knife_tip(kid)
    pts = [_trail_point(kid, base, base_rotation,
                        max(0.0, progress - i * _TRAIL_STEP),
                        pivot, scale, tip)
           for i in range(_TRAIL_SAMPLES)]
    hot = C(235, 255, 255)
    rl_disable_depth_mask()
    begin_blend_mode(BLEND_ADDITIVE)
    # Serit (ribbon): ardisik noktalar arasi cift cizgi, kuyruga dogru solar
    for i in range(_TRAIL_SAMPLES - 1):
        fade = 1.0 - i / float(_TRAIL_SAMPLES - 1)
        a = pts[i]
        b = pts[i + 1]
        va = Vector3(*a)
        vb = Vector3(*b)
        draw_line_3d(va, vb, _col(color, 190 * fade * fade))
        thick = 0.006 * fade
        draw_line_3d(Vector3(a[0], a[1] + thick, a[2]),
                     Vector3(b[0], b[1] + thick, b[2]),
                     _col(hot, 150 * fade * fade))
        draw_line_3d(Vector3(a[0], a[1] - thick, a[2]),
                     Vector3(b[0], b[1] - thick, b[2]),
                     _col(color, 110 * fade * fade))
    # Parlak parcaciklar (sadece one yakin ornekler)
    for i in range(0, _TRAIL_SAMPLES, 2):
        fade = 1.0 - i / float(_TRAIL_SAMPLES)
        size = 0.032 * (0.30 + 0.70 * fade)
        pos = Vector3(*pts[i])
        draw_cube(pos, size, size, size, _col(color, 150 * fade * fade))
        draw_cube(pos, size * 0.5, size * 0.5, size * 0.5,
                  _col(hot, 210 * fade * fade))
    end_blend_mode()
    rl_enable_depth_mask()


# ----------------------------------------------------------------------------
# Inspect efektleri
# ----------------------------------------------------------------------------
def _cube(x, y, z, size, color, alpha):
    draw_cube(Vector3(x, y, z), size, size, size, _col(color, alpha))


def _fx_core_orbit(base, scale, t, inspect, kid, skin, accent, violet, hot, count):
    for i in range(count):
        angle = t * (3.0 if kid == "karambit" else 2.3) + i * math.tau / count
        radius = (0.18 + 0.10 * math.sin(t * 1.9 + i * 0.7)) * scale
        x = base[0] + math.cos(angle) * radius
        y = base[1] + math.sin(angle * 1.6 + i * 0.4) * 0.13 * scale
        z = base[2] + math.sin(angle) * radius
        color = violet if skin == "voidstone" and kid == "karambit" and i % 3 == 0 else accent
        alpha = (90 + 145 * (0.5 + 0.5 * math.sin(t * 5.0 + i))) * inspect
        size = (0.011 + 0.017 * ((i % 5) / 4.0)) * scale
        _cube(x, y, z, size, color, alpha)
        if i % 6 == 0:
            _cube(x, y, z, size * 0.5, hot, alpha * 1.4)


def _fx_outer_ring(base, scale, t, inspect, skin, accent, violet):
    for i in range(26):
        angle = -t * 2.2 + i * math.tau / 26.0
        radius = (0.29 + 0.045 * math.sin(t * 2.7 + i * 1.3)) * scale
        x = base[0] + math.cos(angle) * radius
        y = base[1] + 0.11 * math.sin(t * 1.4 + i) * scale
        z = base[2] + math.sin(angle) * radius
        color = violet if skin == "voidstone" and i % 4 == 0 else accent
        alpha = (35 + 55 * (0.5 + 0.5 * math.sin(t * 3.8 + i))) * inspect
        _cube(x, y, z, 0.008 * scale, color, alpha)


def _fx_streaks(base, scale, t, inspect, accent):
    for i in range(14):
        seed = (i * 0.61803398875) % 1.0
        angle = t * 2.6 + seed * math.tau
        outer = 0.26 * scale
        inner = (0.10 + 0.05 * seed) * scale
        start = Vector3(base[0] + math.cos(angle) * outer,
                        base[1] + math.sin(angle * 1.3) * 0.10 * scale,
                        base[2] + math.sin(angle) * outer)
        end = Vector3(base[0] + math.cos(angle + 0.20) * inner,
                      base[1] + math.sin(angle + 0.20) * 0.05 * scale,
                      base[2] + math.sin(angle + 0.20) * inner)
        alpha = (45 + 55 * math.sin(t * 4.4 + i)) * inspect
        draw_line_3d(start, end, _col(accent, alpha))


def _fx_rising_motes(base, scale, t, inspect, accent):
    for i in range(12):
        life = (t * 1.3 + i * 0.083) % 1.0
        x = base[0] + 0.035 * math.sin(t * 4.0 + i * 2.1) * scale
        y = base[1] + (0.16 - life * 0.24) * scale
        z = base[2] + (life - 0.5) * 0.34 * scale
        # fade-in + fade-out (daha yumusak dogus/olus)
        env = math.sin(life * math.pi)
        _cube(x, y, z, 0.010 * scale, accent, 150 * env * inspect)


def draw_inspect_fx(p, kid, base, scale, inspect):
    if inspect <= 0.01:
        return
    skin = getattr(p, "knife_skin", "none")
    accent = skins.accent(skin)
    if skin == "none":
        accent = C(0, 230, 255) if kid == "karambit" else C(255, 190, 80)
    violet = C(165, 95, 255)
    hot = C(235, 255, 255)
    t = p.inspect_t
    if kid == "karambit" and skin == "voidstone":
        count = 54
    elif kid == "karambit":
        count = 38
    elif kid == "butterfly":
        count = 30
    else:
        count = 22

    rl_disable_depth_test()
    rl_disable_depth_mask()
    begin_blend_mode(BLEND_ADDITIVE)

    _fx_core_orbit(base, scale, t, inspect, kid, skin, accent, violet, hot, count)
    _fx_outer_ring(base, scale, t, inspect, skin, accent, violet)
    _fx_streaks(base, scale, t, inspect, accent)
    _fx_rising_motes(base, scale, t, inspect, accent)

    pulse = 0.5 + 0.5 * math.sin(t * 6.0)
    draw_sphere(Vector3(*base), (0.05 + 0.025 * pulse) * scale,
                _col(accent, 75 * inspect))
    # Cekirdek parlamasi: ic icerisine kucuk sicak sfer
    draw_sphere(Vector3(*base), (0.018 + 0.010 * pulse) * scale,
                _col(hot, 90 * inspect))

    if skin == "voidstone" and kid == "karambit":
        for i in range(10):
            angle = -t * 1.7 + i * math.tau / 10.0
            radius = (0.14 + 0.025 * math.sin(t * 2.4 + i)) * scale
            draw_cube(Vector3(base[0] + math.cos(angle) * radius,
                              base[1] + 0.09 * math.sin(t * 2.1 + i) * scale,
                              base[2] + math.sin(angle) * radius),
                      0.014, 0.014, 0.014, _col(violet, 150 * inspect))
        draw_sphere(Vector3(*base), (0.10 + 0.05 * pulse) * scale,
                    _col(violet, 55 * inspect))
    elif kid == "butterfly":
        for i in range(14):
            angle = t * 2.0 + i * math.tau / 14.0
            radius = (0.16 + 0.03 * math.sin(t * 3.0 + i)) * scale
            draw_cube(Vector3(base[0] + math.cos(angle) * radius,
                              base[1] + 0.12 * math.sin(t * 3.0 + i) * scale,
                              base[2] + math.sin(angle) * radius),
                      0.013, 0.013, 0.013, C(255, 190, 80, _a(135 * inspect)))

    end_blend_mode()
    rl_enable_depth_test()
    rl_enable_depth_mask()