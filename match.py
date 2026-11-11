# -*- coding: utf-8 -*-
"""Mac akisi: 5v5 takimlar, bomba roundlari, karakter yetenekleri, bicak."""
import math
import random

from pyray import *

import bomb
import characters
import knives
import playerdata
from bot import bot_update
from combat import apply_damage, shoot
from config import C, CYAN, DEG, cl, cfg, lerpf
from fighter import F, look
from modes import MODES
from physics import los, phys
from state import g
from weapons import WEAPONS
from world import SPAWNS_ATK, SPAWNS_DFN

ALLY_COLS = [C(90, 160, 255), C(120, 255, 220), C(160, 200, 255), C(80, 220, 255)]
ENEMY_COLS = [C(255, 90, 90), C(255, 150, 60), C(255, 100, 160), C(220, 80, 80), C(255, 180, 90)]


def start_match():
    pd = playerdata.data()
    g.char = characters.index_of(pd.get("character", "hex"))
    g.target = MODES[g.mode][1]
    g.atk_wins = 0
    g.dfn_wins = 0
    g.FS = []
    g.p = F(g.names[7].strip() or "Oyuncu", CYAN, True, 0)
    g.p.knife = knives.by_id(pd.get("knife", "knife")).kid
    g.FS.append(g.p)
    for i in range(4):
        nm = g.names[i].strip() or "Müttefik%d" % (i + 1)
        g.FS.append(F(nm, ALLY_COLS[i % len(ALLY_COLS)], False, 0))
    for i in range(5):
        nm = (g.names[8 + i].strip() if 8 + i < len(g.names) else "") or "Düşman%d" % (i + 1)
        g.FS.append(F(nm, ENEMY_COLS[i % len(ENEMY_COLS)], False, 1))
    g.kills_show = []
    g.money = 1000
    g.ult = 0.0
    g.ult_t = 0.0
    g.ult_kind = ""
    g.x_ready = True
    g.v_cd = 0.0
    g.c_cd = 0.0
    g.soul_t = 0.0
    g.soul_pos = (0, 0, 0)
    g.wave_on = False
    g.wave_t = 0.0
    g.wave_hit = set()
    g.round = 0
    g.feed = []
    g.paused = False
    g.market = False
    g.phase_t = 5
    g.round_t = 120
    g.last_winner = None
    g.p.owned = {0}
    g.cursor_dead = False
    g.match_rewarded = False
    g.mvp = ""
    g.souls_earned = 0
    g.winner_team = None
    g.explode_t = 0.0
    start_round()
    g.state = "play"


def start_round():
    g.round += 1
    g.site_plan = random.choice(("A", "B"))
    atk_sp = SPAWNS_ATK[:]
    dfn_sp = SPAWNS_DFN[:]
    random.shuffle(atk_sp)
    random.shuffle(dfn_sp)
    ia = idf = 0
    for i, f in enumerate(g.FS):
        f.site_target = g.site_plan if f.team == 0 else ("A" if i % 2 == 0 else "B")
        if f.player:
            wi = f.weapon if f.weapon in f.owned else 0
        else:
            wl = [3, 0.9, 2, 3, 1.2, 2.2, 0.8, 1.6] if g.round > 1 else [5, 2, 0.5, 0.5, 0.2, 0.4, 0.2, 0.3]
            wi = random.choices(range(len(WEAPONS)), weights=wl)[0]
        if f.team == 0:
            x, z = atk_sp[ia % len(atk_sp)]
            ia += 1
        else:
            x, z = dfn_sp[idf % len(dfn_sp)]
            idf += 1
        f.reset(x, z, wi)
    p = g.p
    p.switch_t = 0.0
    p.kick = 0.0
    bomb.new_round(p)
    g.phase = "freeze"
    g.phase_t = 5.0
    g.round_t = 120.0
    g.x_ready = True
    g.v_cd = 0.0
    g.c_cd = 0.0
    g.ult = min(100.0, g.ult + 15)
    g.ult_t = 0.0
    g.ult_kind = ""
    g.soul_t = 0.0
    g.wave_on = False
    g.tracers = []
    g.parts = []
    g.hurt = 0.0
    g.cursor_dead = False
    g.market = False
    g.explode_t = 0.0
    g.kills_show = []


def end_round(winner, reason):
    if g.phase == "roundend":
        return
    if winner == 0:
        g.atk_wins += 1
        g.last_winner = "SALDIRICILAR"
    else:
        g.dfn_wins += 1
        g.last_winner = "SAVUNMACILAR"
    g.round_reason = reason
    for f in g.FS:
        if f.team == winner:
            f.wins += 1
    g.money += 1000 if winner == g.p.team else 300
    g.phase = "roundend"
    g.phase_t = 4.0


def finish_match():
    winner = 0 if g.atk_wins >= g.target else 1
    g.winner_team = winner
    if not g.match_rewarded:
        earned, mvp = playerdata.award_match(g.FS, g.p, winner == g.p.team)
        g.souls_earned = earned
        g.mvp = mvp.name
        g.match_rewarded = True
    g.state = "end"


def start_reload(f):
    w = WEAPONS[f.weapon]
    if f.reload_t <= 0 and f.mag[f.weapon] < w.mag and f.res[f.weapon] > 0:
        f.reload_t = w.reload


def _use_character_c(p, frozen):
    ch = characters.get(g.char)
    kind = ch.c.kind
    if kind == "soul":
        if g.soul_t > 0:
            g.soul_t = 0
            p.ghost = 2.0
            for b in g.FS:
                if b.team != p.team and b.target is p:
                    b.target = None
                    b.lost_t = 0
        return
    if g.c_cd > 0:
        return
    if kind == "updraft":
        p.vy = 10.0
        p.grounded = False
    elif kind == "ghost_cd":
        p.ghost = 3.0
    elif kind == "shield":
        p.armor = min(100.0, p.armor + 50.0)
    g.c_cd = ch.c.cd


def player_update(dt):
    p = g.p
    md = get_mouse_delta()
    if g.skip_mouse > 0:
        g.skip_mouse -= 1
        md = Vector2(0, 0)
    w = WEAPONS[p.weapon]
    ch = characters.get(g.char)
    frozen = g.phase == "freeze"
    p.flash = max(0, p.flash - dt)
    p.inv = max(0, p.inv - dt)
    p.slash_t = max(0.0, p.slash_t - dt)
    p.slash_cd = max(0.0, p.slash_cd - dt)
    p.kick = max(0, p.kick - dt * 14 * (0.4 + p.kick * 0.15))
    p.land = max(0, p.land - dt * 0.6)
    p.heat = max(0, p.heat - dt * 3)
    if not p.alive:
        p.death_t += dt
        p.yaw -= md.x * 0.0022 * cfg["sens"]
        p.pitch = cl(p.pitch - md.y * 0.0022 * cfg["sens"], -1.5, 1.5)
        p.vx = p.vz = 0
        phys(p, dt)
        return
    p.ghost = max(0, p.ghost - dt)
    if g.ult_t > 0 and g.ult_kind == "ult_stealth":
        p.ghost = max(p.ghost, 0.2)
    sens = 0.0022 * cfg["sens"] * (1 - p.ads * (0.85 if w.scope else 0.35))
    p.yaw -= md.x * sens
    p.pitch = cl(p.pitch - md.y * sens, -1.5, 1.5)
    sn, cs = math.sin(p.yaw), math.cos(p.yaw)
    ix = (1 if is_key_down(KEY_D) else 0) - (1 if is_key_down(KEY_A) else 0)
    iz = (1 if is_key_down(KEY_W) else 0) - (1 if is_key_down(KEY_S) else 0)
    if frozen:
        ix = iz = 0
    wx = sn * iz + (-cs) * ix
    wz = cs * iz + sn * ix
    n = math.hypot(wx, wz)
    if n > 0:
        wx /= n
        wz /= n
    crouch = is_key_down(KEY_LEFT_CONTROL)
    want_ads = is_mouse_button_down(MOUSE_BUTTON_RIGHT) and p.reload_t <= 0 and not frozen and not p.knife_active
    p.ads += ((1.0 if want_ads else 0.0) - p.ads) * min(1, dt * 12)
    speed = 6.2 * w.spd
    if crouch:
        speed = 3.4
    if p.ads > 0.5:
        speed *= 0.62
    if g.ult_t > 0:
        speed *= 1.3 if g.ult_kind == "ult_wind" else 1.1
    p.eh += ((1.15 if crouch else 1.62) - p.eh) * min(1, dt * 12)
    p.h = 1.35 if crouch else 1.8
    if p.dash_t > 0:
        p.dash_t -= dt
        p.vx, p.vz = p.dash[0] * 26, p.dash[1] * 26
    else:
        acc = 70 if p.grounded else 14
        tx, tz = wx * speed, wz * speed
        dx, dz = tx - p.vx, tz - p.vz
        dl = math.hypot(dx, dz)
        st = acc * dt
        if dl <= st:
            p.vx, p.vz = tx, tz
        else:
            p.vx += dx / dl * st
            p.vz += dz / dl * st
        if p.grounded and n == 0:
            f = max(0, 1 - 12 * dt)
            p.vx *= f
            p.vz *= f
    if is_key_pressed(KEY_SPACE) and p.grounded and not frozen:
        p.vy = 8.0
        p.grounded = False
    phys(p, dt)
    if p.landed > 0:
        p.land = min(0.16, p.landed * 0.014)
    sp = math.hypot(p.vx, p.vz)
    if p.grounded and sp > 0.5:
        p.bobt += dt * sp * 1.15
    tgt = min(1.0, sp / 6.0) if p.grounded else 0.0
    p.bobamp += (tgt - p.bobamp) * min(1, dt * 8)
    p.sway += (cl(-md.x * 0.0012, -0.05, 0.05) - p.sway) * min(1, dt * 10)
    p.swayy += (cl(md.y * 0.0012, -0.04, 0.04) - p.swayy) * min(1, dt * 10)
    # silah / bicak secimi
    for i in range(len(WEAPONS)):
        if is_key_pressed(KEY_ONE + i) and i in p.owned:
            p.weapon = i
            p.reload_t = 0
            p.switch_t = 0.35
            p.knife_active = False
            break
    if is_key_pressed(KEY_ZERO):
        p.knife_active = True
        p.reload_t = 0
        p.switch_t = 0.35
    wh = get_mouse_wheel_move()
    if wh != 0:
        p.knife_active = False
        own = sorted(p.owned)
        k = own.index(p.weapon)
        p.weapon = own[(k + (1 if wh < 0 else -1)) % len(own)]
        p.reload_t = 0
        p.switch_t = 0.35
    w = WEAPONS[p.weapon]
    p.switch_t = max(0, p.switch_t - dt)
    p.cd -= dt
    if p.reload_t > 0:
        p.reload_t -= dt
        if p.reload_t <= 0:
            need = w.mag - p.mag[p.weapon]
            take = min(need, p.res[p.weapon])
            p.mag[p.weapon] += take
            p.res[p.weapon] -= take
    if is_key_pressed(KEY_R):
        start_reload(p)
    # bomba kurma
    if is_key_down(KEY_E) and g.phase == "live":
        if p.team == 0:
            bomb.update_plant(p, dt)
        else:
            bomb.update_defuse(p, dt)
    # ates / bicak
    if p.knife_active:
        if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
            knives.try_slash(p)
    else:
        fire = is_mouse_button_down(MOUSE_BUTTON_LEFT) if w.auto else is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
        if fire and p.cd <= 0 and p.reload_t <= 0 and p.switch_t <= 0 and not frozen:
            if p.mag[p.weapon] > 0:
                spread = lerpf(w.hip, w.ads, p.ads) + sp * 0.1 + (2.0 if not p.grounded else 0) + p.heat
                shoot(p, spread, 1.25 if g.ult_t > 0 else 1.0)
                p.mag[p.weapon] -= 1
                p.cd = w.rof / (1.5 if g.ult_t > 0 else 1.0)
                p.kick += w.kick
                p.flash = 0.05
                p.pitch += w.kick * 0.3 * DEG
                p.yaw += (random.random() - .5) * w.kick * 0.25 * DEG
                if w.auto:
                    p.heat = min(2.5, p.heat + 0.12)
            else:
                start_reload(p)
    # skiller
    if is_key_pressed(KEY_X) and g.x_ready and g.phase != "freeze":
        g.x_ready = False
        g.wave_on = True
        g.wave_t = 0.0
        g.wave_hit = set()
    if is_key_pressed(KEY_C) and g.phase != "freeze":
        _use_character_c(p, frozen)
    if is_key_pressed(KEY_V) and g.v_cd <= 0 and g.phase != "freeze":
        g.v_cd = 9.0
        p.dash_t = 0.18
        p.inv = 0.3
        if n > 0:
            p.dash = (wx, wz)
        else:
            fl = math.hypot(sn, cs)
            p.dash = (sn / fl, cs / fl)
    if is_key_pressed(KEY_G) and g.ult >= 100 and g.phase != "freeze":
        g.ult = 0
        g.ult_t = 6.0
        g.ult_kind = ch.g.kind
        if g.ult_kind == "ult_tank":
            p.hp = 100.0
            p.armor = max(p.armor, 75.0)


def wave_update(dt):
    if not g.wave_on:
        return
    p = g.p
    g.wave_t += dt / 0.95
    rng = 32 * g.wave_t
    ex, ey, ez = p.x, p.y + p.eh, p.z
    fx, fy, fz = look(p)
    for o in g.FS:
        if o is p or not o.alive or o.team == p.team or id(o) in g.wave_hit:
            continue
        dx, dy, dz = o.x - ex, o.y + 1.1 - ey, o.z - ez
        d = math.sqrt(dx * dx + dy * dy + dz * dz)
        if d > rng or d < 0.01:
            continue
        ca = (dx * fx + dy * fy + dz * fz) / d
        if ca < math.cos(40 * DEG):
            continue
        if not los(ex, ey, ez, o.x, o.y + 1.1, o.z):
            continue
        ang = math.acos(cl(ca, -1, 1))
        dmg = lerpf(95, 40, min(1, d / 32)) * (1 - 0.45 * ang / (40 * DEG))
        g.wave_hit.add(id(o))
        o.glitch = 1.5
        apply_damage(o, dmg, p, False, "Hex Dalgasi")
    if g.wave_t >= 1:
        g.wave_on = False


def update_play(dt):
    p = g.p
    if is_key_pressed(KEY_ESCAPE):
        if g.market:
            g.market = False
        else:
            g.paused = not g.paused
    if g.paused:
        return
    if is_key_pressed(KEY_B):
        g.market = not g.market
    if g.market:
        return
    g.hurt = max(0, g.hurt - dt * 1.8)
    g.hitm = max(0, g.hitm - dt)
    g.hit_t = max(0, g.hit_t - dt)
    g.soul_t = max(0, g.soul_t - dt)
    g.v_cd = max(0, g.v_cd - dt)
    g.c_cd = max(0, g.c_cd - dt)
    if g.ult_t > 0 and g.ult_kind == "ult_wind":
        g.v_cd = 0.0
    g.dig += ((1.0 if p.ghost > 0 else 0.0) - g.dig) * min(1, dt * 10)
    if g.ult_t > 0:
        g.ult_t -= dt
    g.explode_t = max(0.0, g.explode_t - dt)
    for f in g.feed:
        f[4] -= dt
    g.feed = [f for f in g.feed if f[4] > 0]
    for e in g.kills_show:
        e["t"] -= dt
    g.kills_show = [e for e in g.kills_show if e["t"] > 0]
    g.phase_t -= dt
    if g.phase == "freeze":
        if g.phase_t <= 0:
            g.phase = "live"
            g.phase_t = 0.0
    elif g.phase == "live":
        bomb.update(dt)
        g.round_t -= dt
        b = g.bomb
        if b and b.get("exploded"):
            g.explode_t = 1.0
            g.explode_pos = (b["x"], 1.0, b["z"])
            end_round(0, "BOMB")
        elif b and b.get("defused"):
            end_round(1, "DEFUSE")
        elif b and not b["planted"]:
            atk_alive = any(f.alive and f.team == 0 for f in g.FS)
            dfn_alive = any(f.alive and f.team == 1 for f in g.FS)
            if not atk_alive:
                end_round(1, "ELIM")
            elif not dfn_alive:
                end_round(0, "ELIM")
            elif g.round_t <= 0:
                end_round(1, "TIME")
    elif g.phase == "roundend":
        if g.phase_t <= 0:
            if g.atk_wins >= g.target or g.dfn_wins >= g.target:
                finish_match()
            else:
                start_round()
            return
    player_update(dt)
    wave_update(dt)
    bdt = dt * (0.45 if g.ult_t > 0 else 1.0)
    for f in g.FS:
        if not f.player:
            bot_update(f, bdt)
    for t in g.tracers:
        t[6] -= dt
    g.tracers = [t for t in g.tracers if t[6] > 0]
    for q in g.parts:
        q[6] -= dt
        q[4] -= 9 * dt
        q[0] += q[3] * dt
        q[1] = max(0.02, q[1] + q[4] * dt)
        q[2] += q[5] * dt
    g.parts = [q for q in g.parts if q[6] > 0]
    if g.hitm_k and g.hitm <= 0:
        g.hitm_k = False
