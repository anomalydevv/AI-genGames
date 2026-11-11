# -*- coding: utf-8 -*-
"""Bot yapay zekasi: takim hedefleri, bomba kurma/defuse, nisan ve hareket."""
import math
import random

from bomb import SITES, in_site, site_dist, update_defuse, update_plant
from combat import shoot
from config import cl, wrap
from physics import los, phys
from state import g
from weapons import DIFFS, PREF, WEAPONS
from world import WPS, find_path


def _acquire(b, D):
    best, bs = None, 1e9
    ex, ey, ez = b.x, b.y + 1.6, b.z
    for o in g.FS:
        if o is b or not o.alive or o.team == b.team or o.ghost > 0:
            continue
        dx, dz = o.x - b.x, o.z - b.z
        d = math.hypot(dx, dz)
        if d > 60:
            continue
        if abs(wrap(math.atan2(dx, dz) - b.yaw)) > 2.3 and d > 9:
            continue
        if not los(ex, ey, ez, o.x, o.y + 1.2, o.z):
            continue
        score = d - (8.0 if o is g.p else 0.0)
        if score < bs:
            bs, best = score, o
    return best


def _navigate(b, tx, tz, dt, turn):
    if b.path is None or getattr(b, "nav", None) is None or (b.nav[0] - tx) ** 2 + (b.nav[1] - tz) ** 2 > 9:
        b.path = find_path(b.x, b.z, tx, tz)
        b.nav = (tx, tz)
    if not b.path:
        return 0.0, 0.0
    px, pz = b.path[0]
    dx, dz = px - b.x, pz - b.z
    d = math.hypot(dx, dz)
    if d < 1.0:
        b.path.pop(0)
        return 0.0, 0.0
    yt = math.atan2(dx, dz)
    b.yaw += cl(wrap(yt - b.yaw) * min(1, 6 * dt), -turn * dt, turn * dt)
    return dx / d, dz / d


def _plant_carrier(b, dt):
    if in_site(b.x, b.z) is None:
        return False
    b.vx *= 0.4
    b.vz *= 0.4
    update_plant(b, dt)
    return True


def _should_defuse(b):
    bomb = g.bomb
    if not bomb or not bomb["planted"] or b.team != 1:
        return False
    near = [f for f in g.FS if f.alive and f.team == 1 and (f.x - bomb["x"]) ** 2 + (f.z - bomb["z"]) ** 2 < 2.2 ** 2]
    if not near:
        return False
    closest = min(near, key=lambda f: (f.x - bomb["x"]) ** 2 + (f.z - bomb["z"]) ** 2)
    return closest is b


def bot_update(b, dt):
    if not b.alive:
        b.death_t += dt
        return
    D = DIFFS[g.diff][1]
    w = WEAPONS[b.weapon]
    bomb = g.bomb
    if g.phase == "freeze":
        b.vx = b.vz = 0
        phys(b, dt)
        return
    b.cd -= dt
    b.slash_cd = max(0.0, getattr(b, "slash_cd", 0.0) - dt)
    if b.glitch > 0:
        b.glitch -= dt
    if b.reload_t > 0:
        b.reload_t -= dt
        if b.reload_t <= 0:
            b.mag[b.weapon] = w.mag
    b.think -= dt
    if b.target is not None and (not b.target.alive or b.target.ghost > 0 or b.target.team == b.team):
        b.target = None
    if b.think <= 0:
        b.think = 0.12 if g.diff >= 2 else 0.2
        best = _acquire(b, D)
        if best is not None:
            if b.target is not best:
                b.target = best
                b.react = D["react"] * (0.7 + random.random() * 0.6)
                b.aim_h = 1.55 if random.random() < D["head"] else 1.15
            b.lost_t = 4.0
            b.last = (best.x, best.z)
        else:
            b.target = None
    sp = 6.0 * D["speed"] * w.spd
    tgt = b.target
    mvx = mvz = 0.0
    want_move = True
    action = ""
    # hedef pozisyon
    if b.team == 0:
        if bomb and bomb["planted"]:
            aim = (bomb["x"], bomb["z"])
        elif bomb and bomb["carrier"] is b:
            aim = SITES[b.site_target]
            if in_site(b.x, b.z) is not None:
                action = "plant"
        elif bomb and bomb["dropped"]:
            atk = [f for f in g.FS if f.alive and f.team == 0]
            closest = min(atk, key=lambda f: (f.x - bomb["x"]) ** 2 + (f.z - bomb["z"]) ** 2) if atk else b
            aim = (bomb["x"], bomb["z"]) if closest is b else SITES[b.site_target]
        else:
            aim = SITES[b.site_target]
    else:
        if bomb and bomb["planted"]:
            aim = (bomb["x"], bomb["z"])
            if _should_defuse(b):
                action = "defuse"
        else:
            aim = SITES[b.site_target]
    if action == "plant":
        _plant_carrier(b, dt)
        mvx = mvz = 0.0
    elif action == "defuse":
        b.vx *= 0.5
        b.vz *= 0.5
        update_defuse(b, dt)
        mvx = mvz = 0.0
    elif tgt is not None:
        dx, dz = tgt.x - b.x, tgt.z - b.z
        d = math.hypot(dx, dz) + 1e-6
        tof = d / 90.0
        lead = D["lead"]
        px = tgt.x + tgt.vx * tof * lead
        pz = tgt.z + tgt.vz * tof * lead
        yt = math.atan2(px - b.x, pz - b.z)
        pt = math.atan2(tgt.y + b.aim_h - (b.y + 1.6), d)
        rate = D["turn"] * dt
        if b.glitch > 0:
            b.yaw += (random.random() - .5) * 0.3
        else:
            dy_ = wrap(yt - b.yaw)
            b.yaw += cl(dy_ * min(1, 10 * dt), -rate, rate)
            b.pitch += cl((pt - b.pitch) * min(1, 10 * dt), -rate, rate)
        b.strafe_t -= dt
        if b.strafe_t <= 0:
            b.strafe = random.choice((-1.0, 1.0))
            b.strafe_t = 0.5 + random.random() * 1.2
        pref = PREF[b.weapon]
        fc = 1.0 if d > pref + 3 else (-1.0 if d < pref - 3 else 0.0)
        ux, uz = dx / d, dz / d
        mvx = ux * fc + (-uz) * b.strafe * 0.8
        mvz = uz * fc + (ux) * b.strafe * 0.8
        b.react -= dt
        err = abs(wrap(yt - b.yaw))
        if b.mag[b.weapon] <= 0 and b.reload_t <= 0:
            b.reload_t = w.reload
        elif b.react <= 0 and b.cd <= 0 and b.reload_t <= 0 and b.glitch <= 0 and err < 0.07 and d < w.rng:
            spread = (w.ads if w.scope else w.hip * 0.6) + D["spread"]
            shoot(b, spread, D["dmg"])
            b.mag[b.weapon] -= 1
            b.cd = w.rof * (1.0 + random.random() * (0.9 if w.auto else 0.6))
        if abs(mvx) + abs(mvz) < 0.01:
            want_move = False
    else:
        b.pitch += (0 - b.pitch) * min(1, 4 * dt)
        dx, dz = _navigate(b, aim[0], aim[1], dt, D["turn"])
        if dx or dz:
            mvx, mvz = dx, dz
        else:
            ax, az = aim[0] - b.x, aim[1] - b.z
            dd = math.hypot(ax, az)
            if dd > 1.2:
                mvx, mvz = ax / dd, az / dd
            else:
                want_move = False
        if b.lost_t > 0:
            b.lost_t -= dt
        if b.team == 1 and bomb and bomb["planted"]:
            if _should_defuse(b):
                update_defuse(b, dt)
                mvx = mvz = 0.0
        if b.team == 0 and bomb and bomb["carrier"] is b and in_site(b.x, b.z) is not None:
            _plant_carrier(b, dt)
            mvx = mvz = 0.0
    # hareket
    tvx, tvz = mvx * sp, mvz * sp
    if b.glitch > 0:
        tvx *= 0.3
        tvz *= 0.3
    b.vx += (tvx - b.vx) * min(1, 10 * dt)
    b.vz += (tvz - b.vz) * min(1, 10 * dt)
    for o in g.FS:
        if o is not b and o.alive and o.team == b.team:
            ddx, ddz = b.x - o.x, b.z - o.z
            dd = ddx * ddx + ddz * ddz
            if dd < 0.64 and dd > 1e-6:
                dd = math.sqrt(dd)
                b.vx += ddx / dd * 2.0
                b.vz += ddz / dd * 2.0
    phys(b, dt)
    b.walk += math.hypot(b.vx, b.vz) * dt * 2.2
    b.stuck_t += dt
    if b.stuck_t > 0.7:
        if want_move and math.hypot(b.x - b.lastpos[0], b.z - b.lastpos[1]) < 0.3:
            b.path = None
            b.nav = None
            b.strafe *= -1
        b.lastpos = (b.x, b.z)
        b.stuck_t = 0
