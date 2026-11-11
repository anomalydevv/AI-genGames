# -*- coding: utf-8 -*-
"""Ates etme, hasar, oldurme, killfeed ve parcacik efektleri."""
import math
import random

import bomb
from config import C, DEG
from fighter import look
from physics import ray_fighter, ray_walls
from state import g
from weapons import WEAPONS, WNAMES_TR


def feed_add(a, w, v, head):
    g.feed.append([a, w, v, head, 5.0])
    if len(g.feed) > 6:
        g.feed.pop(0)


def spark(x, y, z, col, n=5, sp=3.0):
    for _ in range(n):
        g.parts.append([x, y, z, (random.random() - .5) * sp, random.random() * sp, (random.random() - .5) * sp,
                        0.4 + random.random() * 0.3, col])


def kill(v, a, wname, head):
    v.alive = False
    v.hp = 0
    v.deaths += 1
    v.death_t = 0.0
    if g.bomb and g.bomb["carrier"] is v:
        bomb.drop(v)
    if a is not None and a is not v:
        a.kills += 1
        a.round_kills += 1
    feed_add(a.name if a else "?", wname, v.name, head)
    if a is g.p and v is not a:
        g.money += 300
        g.ult = min(100, g.ult + 34)
        g.soul_t = 2.0
        g.soul_pos = (v.x, v.y + 1.0, v.z)
        g.hitm_k = True
        g.kills_show.append({"t": 2.8, "name": v.name, "w": g.p.weapon, "knife": g.p.knife_active,
                             "kid": g.p.knife, "wname": wname, "hs": bool(head)})
        if len(g.kills_show) > 4:
            g.kills_show.pop(0)
    if v is g.p:
        g.cursor_dead = True


def apply_damage(v, dmg, a, head, wname):
    if not v.alive or v.inv > 0 or g.phase in ("freeze", "roundend"):
        return
    if v is g.p and g.ult_t > 0 and g.ult_kind == "ult_tank":
        dmg *= 0.5
    if v.armor > 0:
        ab = min(v.armor, dmg * 0.5)
        v.armor -= ab
        dmg -= ab
    v.hp -= dmg
    if a is g.p and v is not a:
        g.hitm = 0.22
        g.hitm_k = False
        g.ult = min(100, g.ult + dmg * 0.1)
    if v is g.p:
        g.hurt = min(1.0, g.hurt + dmg / 55.0)
        g.hit_from = (a.x, a.z)
        g.hit_t = 1.3
    elif a is not None:
        v.last = (a.x, a.z)
        v.lost_t = 4.0
    if v.hp <= 0:
        kill(v, a, wname, head)


def shoot(f, spread, dmgm=1.0):
    w = WEAPONS[f.weapon]
    ox, oy, oz = f.x, f.y + f.eh, f.z
    fx, fy, fz = look(f)
    n = math.hypot(fz, fx) + 1e-9
    rx, rz = -fz / n, fx / n
    ux, uy, uz = -rz * fy, rz * fx - rx * fz, rx * fy
    cs, sn = math.cos(f.yaw), math.sin(f.yaw)
    if f.player:
        mx, my, mz = ox - cs * 0.0 + (-cs) * 0.22 + fx * 0.7, oy - 0.18 + fy * 0.7, oz + sn * 0.22 + fz * 0.7
    else:
        mx, my, mz = f.x + (-cs) * 0.3 + sn * 0.6, f.y + 1.25, f.z + sn * 0.3 + cs * 0.6
    for _ in range(w.pel):
        a = spread * DEG * math.sqrt(random.random())
        ph = random.random() * 6.2832
        t = math.tan(a)
        dx = fx + (rx * math.cos(ph) + ux * math.sin(ph)) * t
        dy = fy + (0 * math.cos(ph) + uy * math.sin(ph)) * t
        dz = fz + (rz * math.cos(ph) + uz * math.sin(ph)) * t
        dl = math.sqrt(dx * dx + dy * dy + dz * dz)
        dx /= dl
        dy /= dl
        dz /= dl
        tw_ = ray_walls(ox, oy, oz, dx, dy, dz, w.rng)
        best, bt, bh = None, tw_, False
        for o in g.FS:
            if o is f or not o.alive or o.team == f.team:
                continue
            r = ray_fighter(ox, oy, oz, dx, dy, dz, o, bt)
            if r and r[0] < bt:
                best, bt, bh = o, r[0], r[1]
        ex, ey, ez = ox + dx * bt, oy + dy * bt, oz + dz * bt
        g.tracers.append([mx, my, mz, ex, ey, ez, 0.07])
        if best is not None:
            fall = 1.0
            if bt > w.rng * 0.5:
                fall = max(0.25, 1 - (bt - w.rng * 0.5) / w.rng)
            dm = w.dmg * dmgm * fall * (w.head if bh else 1.0)
            spark(ex, ey, ez, C(200, 20, 30), 4, 2.5)
            apply_damage(best, dm, f, bh, WNAMES_TR[f.weapon])
        elif bt < w.rng:
            spark(ex, ey, ez, C(255, 210, 120), 3, 3.0)
