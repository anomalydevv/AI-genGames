# -*- coding: utf-8 -*-
"""Insan modeli, yurume/nsian animasyonu ve ragdoll olum pozu.

Model kutulardan ve kurelerden kurulur; ragdoll tam fizik motoru degil,
sonumlu salinim + yer cekimi egimi ile gercekci bir dusme ve donma taklidi
yapar. Parcalar eklem noktalarindan baglanir, boylece govde bir butun kalir.
"""
import math
import random

from pyray import *

from config import C, cl, lerpf
from state import g

CUBE = SPHERE = None
AX_Y = Vector3(0, 1, 0)

# uniform renkleri
DARK = C(30, 33, 40)
MID = C(52, 58, 70)
BOOT = C(22, 24, 30)
SKIN = C(186, 146, 116)
SKIN_D = C(150, 112, 88)
GLOVE = C(28, 30, 36)
METAL = C(58, 62, 72)
VISOR = C(60, 220, 210)


def set_models(cube, sphere):
    global CUBE, SPHERE
    CUBE, SPHERE = cube, sphere


def _rot_axis(ax, ang, v):
    c, s = math.cos(ang), math.sin(ang)
    x, y, z = ax
    d = x * v[0] + y * v[1] + z * v[2]
    cx = y * v[2] - z * v[1]
    cy = z * v[0] - x * v[2]
    cz = x * v[1] - y * v[0]
    return (v[0] * c + cx * s + x * d * (1 - c),
            v[1] * c + cy * s + y * d * (1 - c),
            v[2] * c + cz * s + z * d * (1 - c))


def _rot_y(ang, v):
    c, s = math.cos(ang), math.sin(ang)
    return (v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c)


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def _norm(v):
    d = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / d, v[1] / d, v[2] / d)


def _limb(a, b, tx, tz, col):
    d = _sub(b, a)
    length = math.sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2])
    if length < 1e-5:
        return
    nd = _mul(d, 1.0 / length)
    axis = (nd[2], 0.0, -nd[0])
    if abs(nd[1]) > 0.9999:
        axis, ang = AX_Y, 0.0
    else:
        al = math.sqrt(axis[0] ** 2 + axis[2] ** 2) or 1.0
        axis = Vector3(axis[0] / al, 0.0, axis[2] / al)
        ang = math.degrees(math.acos(cl(nd[1], -1.0, 1.0)))
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
    draw_model_ex(CUBE, Vector3(*mid), axis, ang, Vector3(tx, length, tz), col)


def _box(pos, size, col, yaw=0.0):
    draw_model_ex(CUBE, Vector3(*pos), AX_Y, yaw / (math.pi / 180.0),
                  Vector3(*size), col)


def _sphere(pos, size, col):
    draw_model_ex(SPHERE, Vector3(*pos), AX_Y, 0.0, Vector3(*size), col)


def _aim_hands(phase, speed, aiming):
    """Ellerin govdeye gore konumu (omuzdan bagimsiz hedef noktalari)."""
    if aiming:
        sway = math.sin(phase * 0.7) * 0.012
        return ((0.02 + sway, 1.20, 0.44), (-0.10 + sway, 1.24, 0.52))
    swing = math.sin(phase) * 0.32 * (0.4 + 0.6 * speed)
    return ((0.30, 1.05 - abs(swing) * 0.1, 0.10 + swing * 0.5),
            (-0.30, 1.05 - abs(swing) * 0.1, 0.10 - swing * 0.5))


def _gait(f, phase, speed, aiming):
    """Kalca/diz noktalari ve ayaklar."""
    amp = 0.34 * (0.35 + 0.65 * speed)
    legs = []
    for side in (-1, 1):
        p = phase + (0 if side > 0 else math.pi)
        hip = (side * 0.115, 0.92, 0.0)
        knee = (side * 0.12, 0.50 + 0.03 * math.sin(p * 2), math.sin(p) * amp)
        bend = max(0.0, -math.sin(p + 0.6)) * 0.22 * (0.3 + 0.7 * speed)
        if aiming and speed < 0.2:
            knee = (side * 0.12, 0.52, 0.0)
        foot = (side * 0.13, 0.05, knee[2] + math.sin(p + 0.9) * amp * 0.5)
        foot = (foot[0], foot[1] + bend, foot[2])
        legs.append((hip, knee, foot))
    return legs


def _rag_pose(f):
    """Olum sonrasi: dusme, savrulma ve 2.6 sn sonra donma."""
    t = min(2.6, max(0.0, f.death_t))
    sd = getattr(f, "rag_seed", 0.5) * 6.283
    fall = 1.0 - (1.0 - cl(t / 0.65, 0.0, 1.0)) ** 3
    settle = cl((t - 0.65) / 0.9, 0.0, 1.0)
    bounce = math.sin(t * 13.0) * math.exp(-4.5 * t) * 0.10
    tilt = cl(fall * 1.42 + bounce, 0.0, 1.58) * (1.0 - 0.0 * settle)
    axis = (math.cos(sd), 0.0, math.sin(sd))
    flail = math.exp(-1.6 * t)
    jitter = (math.sin(t * 17.0 + sd) * 0.55 * flail,
              math.sin(t * 13.0 + sd * 1.7) * 0.45 * flail,
              math.sin(t * 21.0 + sd * 2.3) * 0.35 * flail)
    return t, tilt, axis, jitter, settle


def draw(f, tip=0.0):
    """Savasciyi cizer. f.player ise kendi govdesi cizilmez (cagiran karar verir)."""
    if CUBE is None:
        return
    dead = not f.alive
    phase = getattr(f, "walk", 0.0) * 2.0
    speed = cl(math.hypot(getattr(f, "vx", 0.0), getattr(f, "vz", 0.0)) / 5.0, 0.0, 1.3)
    aiming = (not dead) and not getattr(f, "knife_active", False)
    suit = MID
    accent = f.col
    if getattr(f, "glitch", 0.0) > 0:
        suit = C(0, 175, 160)
        accent = C(180, 255, 245)

    t, tilt, axis, jitter, settle = _rag_pose(f) if dead else (0.0, 0.0, AX_Y, (0, 0, 0), 0)
    root_y = 0.0
    if dead:
        root_y = -0.05 * (1.0 - cl(t / 0.8, 0.0, 1.0))
    bob = 0.0
    if not dead:
        bob = math.sin(phase * 2) * 0.022 * (0.3 + 0.7 * speed)

    def xf(v):
        # ragdoll egimi + yaw ile dunya uzayina tasi
        p = (v[0], v[1] + bob, v[2])
        if dead:
            p = _rot_axis(axis, tilt, p)
            p = (p[0] + jitter[0] * 0.05, p[1] - abs(jitter[1]) * 0.02, p[2] + jitter[2] * 0.05)
        p = _rot_y(f.yaw, p)
        return (f.x + p[0], f.y + root_y + p[1], f.z + p[2])

    # govde
    pelvis = xf((0.0, 0.96, 0.0))
    chest = xf((0.0, 1.34, 0.0))
    _limb(pelvis, chest, 0.40, 0.24, suit)
    _box(xf((0.0, 1.10, 0.0)), (0.46, 0.20, 0.27), DARK, f.yaw)
    _box(xf((0.0, 1.30, -0.02)), (0.42, 0.34, 0.28), suit, f.yaw)
    _box(xf((0.0, 1.32, 0.14)), (0.34, 0.26, 0.06), accent, f.yaw)
    _box(xf((0.0, 1.12, 0.13)), (0.16, 0.10, 0.06), DARK, f.yaw)
    # omuz pedleri
    for side in (-1, 1):
        _box(xf((side * 0.28, 1.44, 0.0)), (0.20, 0.14, 0.26), C(accent.r, accent.g, accent.b), f.yaw)

    # bas / kask
    neck = xf((0.0, 1.50, 0.0))
    head = xf((0.0, 1.65, 0.02))
    _limb(neck, head, 0.12, 0.12, SKIN_D)
    _sphere(head, (0.34, 0.36, 0.34), SKIN)
    _box(xf((0.0, 1.74, 0.0)), (0.36, 0.14, 0.36), DARK, f.yaw)
    _box(xf((0.0, 1.64, 0.17)), (0.26, 0.08, 0.04), VISOR, f.yaw)
    _box(xf((0.0, 1.62, -0.16)), (0.30, 0.14, 0.06), DARK, f.yaw)
    # sirt cantasi
    _box(xf((0.0, 1.28, -0.20)), (0.30, 0.34, 0.16), C(28, 30, 34), f.yaw)

    # bacaklar
    legs = _gait(f, phase, speed, aiming)
    if dead:
        j0, j1, j2 = jitter
        legs = [((-0.12, 0.92, 0.0), (-0.27 - j1 * 0.10, 0.48, 0.16 + j0 * 0.10),
                 (-0.34, 0.06, 0.34 + j0 * 0.12)),
                ((0.12, 0.92, 0.0), (0.30 + j2 * 0.10, 0.44, 0.10 + j1 * 0.10),
                 (0.38, 0.06, 0.26 + j2 * 0.12))]
    for hip_l, knee_l, foot_l in legs:
        hip = xf(hip_l)
        knee = xf(knee_l)
        foot = xf(foot_l)
        _limb(hip, knee, 0.17, 0.18, C(44, 48, 58))
        _limb(knee, foot, 0.14, 0.15, C(38, 42, 50))
        _box((foot[0], foot[1] + 0.04, foot[2] + 0.05), (0.16, 0.10, 0.28), BOOT,
             f.yaw)

    # kollar
    hands = _aim_hands(phase, speed, aiming)
    if dead:
        j0, j1, j2 = jitter
        hands = ((0.56 + j0 * 0.22, 0.56 + abs(j1) * 0.18, 0.22 + j2 * 0.16),
                 (-0.58 + j2 * 0.22, 0.52 + abs(j0) * 0.18, 0.16 + j1 * 0.16))
    for side, hand_l in ((-1, hands[0]), (1, hands[1])):
        shoulder_l = (side * 0.27, 1.42, 0.0)
        shoulder = xf(shoulder_l)
        hand = xf(hand_l)
        mid = ((shoulder[0] + hand[0]) / 2, (shoulder[1] + hand[1]) / 2,
               (shoulder[2] + hand[2]) / 2)
        if aiming:
            elbow_l = (side * 0.30, 1.12, 0.24)
        else:
            elbow_l = (side * 0.29, 1.16, hand_l[2] * 0.5)
        elbow = xf(elbow_l)
        _limb(shoulder, elbow, 0.13, 0.13, suit)
        _limb(elbow, hand, 0.11, 0.11, C(40, 44, 52))
        _box((hand[0], hand[1], hand[2]), (0.10, 0.10, 0.12), GLOVE, f.yaw)
        if dead:
            # savrulmus parmak/eldiven detayi
            _box((hand[0], hand[1] + 0.02, hand[2]), (0.11, 0.05, 0.13), GLOVE, f.yaw)

    # elde silah (canliyken nisan aliyorsa)
    if aiming and not dead:
        rhand = xf(hands[1])
        fwd = (math.sin(f.yaw), 0.0, math.cos(f.yaw))
        right = (math.cos(f.yaw), 0.0, -math.sin(f.yaw))
        bodyp = (rhand[0] + fwd[0] * 0.18, rhand[1] + 0.05, rhand[2] + fwd[2] * 0.18)
        _box(bodyp, (0.08, 0.09, 0.26), METAL, f.yaw)
        _box((bodyp[0] + fwd[0] * 0.22 + right[0] * 0.02,
              bodyp[1] + 0.01,
              bodyp[2] + fwd[2] * 0.22 + right[2] * 0.02),
             (0.04, 0.04, 0.20), C(34, 36, 42), f.yaw)
        _box((rhand[0] - fwd[0] * 0.06, rhand[1] - 0.09, rhand[2] - fwd[2] * 0.06),
             (0.06, 0.12, 0.08), DARK, f.yaw)
