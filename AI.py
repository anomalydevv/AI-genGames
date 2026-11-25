# -*- coding: utf-8 -*-

"""Bot yapay zekasi: ekonomi, satin alma, takim hedefleri, nisan ve hareket (gelismis surum).



Disariya acilan arayuz ayni: bot_buy(b), bot_update(b, dt).

Diger modullere (bomb, combat, config, physics, state, weapons, world) dokunmaz.

"""

import math

import random



from bomb import SITES, in_site, site_dist, update_defuse, update_plant

from combat import shoot
try:
    from knives import try_slash as _knife_slash
except Exception:
    _knife_slash = None

from config import cl, wrap

from physics import los, phys

from state import g

from weapons import DIFFS, PREF, WEAPONS

from world import WPS, find_path





# --------------------------------------------------------------------------

# Satin alma

# --------------------------------------------------------------------------

def bot_buy(b):

    b.owned = {0}

    b.weapon = 0

    b.knife_active = False

    b.inspect = False

    b.switch_cd = 0.0



    # Takimda zaten durbunlu (sniper) silahi olan var mi?

    scope_taken = 0

    team_rifles = 0

    for o in g.FS:

        if o is b or o.team != b.team:

            continue

        for wi in getattr(o, "owned", ()):

            if WEAPONS[wi].scope:

                scope_taken += 1

                break

            if WEAPONS[wi].price >= 1500:

                team_rifles += 1



    tier = getattr(b, "diff", g.diff)

    # Rol: yuksek zorlukta bazi botlar keskin nisanci, bazi botlar giris fragger'i.

    role = "rifle"

    if tier >= 2 and scope_taken == 0 and b.team == 1 and random.random() < 0.22:

        role = "sniper"

    elif tier >= 3 and random.random() < 0.18:

        role = "entry"



    best = None

    for i in range(1, len(WEAPONS)):

        wd = WEAPONS[i]

        if wd.price > b.money:

            continue

        score = wd.price + random.random() * 260.0

        # Zirh icin para kalacaksa tercih et.

        if b.money - wd.price >= 150:

            score += 140.0

        else:

            score -= 90.0

        # Rol ve taraf tercihi.

        if role == "sniper" and wd.scope:

            score += 600.0

        if role == "entry" and wd.auto and wd.price >= 1100:

            score += 260.0

        if b.team == 1 and wd.rng >= 90:

            score += 200.0

        if b.team == 0 and wd.auto:

            score += 160.0

        # Pompali sadece yakin dovus icin, dusuk zorlukta.

        if wd.pel > 1 and tier >= 2:

            score -= 180.0

        # Takimda cok sniper olmasin.

        if wd.scope and scope_taken >= 1:

            score -= 520.0

        # Takimda zaten cok tufek varsa ucuz secenek.

        if team_rifles >= 2 and wd.price >= 2000:

            score -= 220.0

        if best is None or score > best[0]:

            best = (score, i)

    # Birincil silah alamiyorsak para biriktir; sadece tabanca + zirh.

    if best is not None and best[1] >= 2 and b.money < 1500:

        cheap = [i for i in range(1, len(WEAPONS))

                 if WEAPONS[i].price <= b.money and not WEAPONS[i].scope]

        best = (0.0, max(cheap, key=lambda i: WEAPONS[i].price)) if cheap else best

    if best is not None:

        wi = best[1]

        b.money -= WEAPONS[wi].price

        b.owned.add(wi)

        b.weapon = wi

        b.mag[wi] = WEAPONS[wi].mag

        b.res[wi] = 999

        # Tabanca da yedek olarak kalsin.

        b.owned.add(0)

        b.mag[0] = WEAPONS[0].mag

    if b.money >= 150:

        b.money -= 150

        b.armor = 50.0

    b.reload_t = b.cd = b.burst_pause = 0.0

    b.burst_left = 0

    b.hp_prev = b.hp

    b.lost_t = 0.0

    b.unstick = 0.0

    b.stuck_n = 0





# --------------------------------------------------------------------------

# Algi

# --------------------------------------------------------------------------

def _acquire(b, D):

    """Gorunen en tehlikeli/uygun dusmani sec (mevcut hedefe yapisma bonusu var)."""

    best, bs = None, 1e9

    ex, ey, ez = b.x, b.y + 1.6, b.z

    bomb = g.bomb

    cur = b.target

    for o in g.FS:

        if o is b or not o.alive or o.team == b.team or o.ghost > 0:

            continue

        dx, dz = o.x - b.x, o.z - b.z

        d = math.hypot(dx, dz)

        if d > 52:

            continue

        if abs(wrap(math.atan2(dx, dz) - b.yaw)) > 2.05 and d > 9:

            continue

        if not los(ex, ey, ez, o.x, o.y + 1.2, o.z):

            continue

        score = d - (8.0 if o is g.p else 0.0)

        if o is cur:

            score -= 6.0  # sik sik hedef degistirip tepki suresini sifirlama

        if getattr(o, "target", None) is b:

            score -= 4.0  # beni vuran once

        if bomb and bomb.get("planted"):

            bd = math.hypot(o.x - bomb["x"], o.z - bomb["z"])

            if bd < 8.0:

                score -= 10.0

        if b.team == 1 and bomb and bomb.get("carrier") is o:

            score -= 8.0

        if o.hp < 45:

            score -= (45 - o.hp) * 0.12

        if score < bs:

            bs, best = score, o

    return best





def _hear(b):

    """Yakinda kosan/yuruyen (gorunmeyen) dusmanin konumu: ayak sesi."""

    best, bd = None, 14.0 ** 2

    for o in g.FS:

        if o is b or not o.alive or o.team == b.team or o.ghost > 0:

            continue

        if o.vx * o.vx + o.vz * o.vz < 3.2 ** 2:

            continue

        dd = (o.x - b.x) ** 2 + (o.z - b.z) ** 2

        if dd < bd:

            bd, best = dd, (o.x, o.z)

    return best





def _nearest_enemy(b, maxd):

    best, bd = None, maxd * maxd

    for o in g.FS:

        if o is b or not o.alive or o.team == b.team or o.ghost > 0:

            continue

        dd = (o.x - b.x) ** 2 + (o.z - b.z) ** 2

        if dd < bd:

            bd, best = dd, (o.x, o.z)

    return best





# --------------------------------------------------------------------------

# Hareket / hedefler

# --------------------------------------------------------------------------

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

    if not bomb or not bomb.get("planted") or b.team != 1:

        return False

    near = [f for f in g.FS if f.alive and f.team == 1 and (f.x - bomb["x"]) ** 2 + (f.z - bomb["z"]) ** 2 < 2.2 ** 2]

    if not near:

        return False

    closest = min(near, key=lambda f: (f.x - bomb["x"]) ** 2 + (f.z - bomb["z"]) ** 2)

    return closest is b





def _teammate_defusing(b):

    """Baska bir CT bombanin hemen yaninda (defuse edecek konumda) mi?"""

    bomb = g.bomb

    for f in g.FS:

        if f is b or not f.alive or f.team != 1:

            continue

        if (f.x - bomb["x"]) ** 2 + (f.z - bomb["z"]) ** 2 < 2.2 ** 2:

            return True

    return False





def _weapon_score(b, wi, dist):

    w = WEAPONS[wi]

    pref = PREF[wi]

    fit = 1.0 - min(1.0, abs(pref - dist) / max(pref, dist, 1.0))

    ammo = b.mag[wi] / max(1.0, float(w.mag))

    score = fit * 1.6 + w.price / 2400.0 + ammo * 0.45

    if w.scope and dist < 12.0:

        score -= 1.8

    if w.pel > 1 and dist > 18.0:

        score -= 0.9

    if not w.auto and dist > 26.0:

        score -= 0.35

    if wi == 0:

        score -= 0.3

    return score


def _switch_weapon(b, dist):

    """Mesafeye ve mermi durumuna gore en iyi sahip olunan silaha gec."""

    if getattr(b, "switch_cd", 0.0) > 0.0 or b.reload_t > 0 or b.glitch > 0:

        return

    best = b.weapon

    bs = _weapon_score(b, b.weapon, dist) - 0.30  # histerezis: surekli salinma yok

    for wi in getattr(b, "owned", ()):

        if wi == b.weapon or b.mag[wi] <= 0:

            continue

        sc = _weapon_score(b, wi, dist)

        if sc > bs:

            bs, best = sc, wi

    if best != b.weapon:

        b.weapon = best

        b.switch_cd = 1.0

        b.burst_left = 0

        b.cd = max(b.cd, 0.22)


def _pickup(b):

    if not g.drops:

        return

    ref = b.target

    dist = math.hypot(ref.x - b.x, ref.z - b.z) if ref is not None else 16.0

    cur_score = _weapon_score(b, b.weapon, dist)

    cur_empty = b.mag[b.weapon] <= 0

    best, bd = None, 2.4 ** 2

    for d in g.drops:

        wi = d["wi"]

        dd = (d["x"] - b.x) ** 2 + (d["z"] - b.z) ** 2

        if dd >= bd:

            continue

        drop_mag = d.get("mag", 0)

        if wi == b.weapon:

            # Ayni silah: sadece mermi doldurmaya yarar.

            want = drop_mag > b.mag[wi] + 1

        elif b.mag[wi] <= 0 and wi in b.owned:

            want = False

        else:

            new_score = _weapon_score(b, wi, dist)

            want = cur_empty and drop_mag > 0 or new_score > cur_score + 0.22

        if want:

            bd, best = dd, d

    if best is None:

        return

    wi = best["wi"]

    if wi == b.weapon:

        b.mag[wi] = max(b.mag[wi], best.get("mag", WEAPONS[wi].mag))

    else:

        b.weapon = wi

    b.owned.add(wi)

    b.knife_active = False

    b.mag[wi] = max(1, best.get("mag", WEAPONS[wi].mag))

    b.res[wi] = 999

    b.reload_t = 0.0

    b.cd = max(b.cd, 0.25)

    b.switch_cd = 0.6

    g.drops.remove(best)





# --------------------------------------------------------------------------

# Ana guncelleme

# --------------------------------------------------------------------------

def bot_update(b, dt):

    if not b.alive:

        b.death_t += dt

        return

    b_diff = getattr(b, "diff", g.diff)

    D = DIFFS[b_diff][1]

    w = WEAPONS[b.weapon]

    bomb = g.bomb

    if g.phase == "freeze":

        b.vx = b.vz = 0

        b.scan = getattr(b, "scan", random.random() * 6.0) + dt

        b.yaw += math.sin(b.scan * 1.1) * 0.5 * dt

        phys(b, dt)

        b.hp_prev = b.hp

        return

    b.cd -= dt

    b.switch_cd = max(0.0, getattr(b, "switch_cd", 0.0) - dt)

    b.burst_pause = max(0.0, b.burst_pause - dt)

    b.slash_cd = max(0.0, getattr(b, "slash_cd", 0.0) - dt)

    if b.glitch > 0:

        b.glitch -= dt

    if b.reload_t > 0:

        b.reload_t -= dt

        if b.reload_t <= 0:

            b.mag[b.weapon] = w.mag



    # Hasar aldiysem: yon degistir, kaynagi aramaya basla

    hp0 = getattr(b, "hp_prev", b.hp)

    b.hp_prev = b.hp

    if b.hp < hp0 - 0.5:

        b.strafe = -b.strafe

        b.strafe_t = 0.25 + random.random() * 0.4

        if b.target is None and b_diff >= 1:

            src = _nearest_enemy(b, 30.0)

            if src is not None:

                b.last = src

                b.lost_t = 3.0



    b.think -= dt

    if b.target is not None and (not b.target.alive or b.target.ghost > 0 or b.target.team == b.team):

        b.target = None

    if b.think <= 0:

        b.think = 0.05 if b_diff >= 4 else (0.12 if b_diff >= 2 else 0.2)

        best = _acquire(b, D)

        if best is not None:

            if b.target is not best:

                b.target = best

                b.react = D["react"] * (1.15 + random.random() * 0.55) + 0.08

                b.aim_h = 1.55 if random.random() < D["head"] else 1.15

            b.lost_t = 4.0

            b.last = (best.x, best.z)

        else:

            b.target = None

            # Ayak sesi: gorunmeyen ama yakin ve hareketli dusman

            if b_diff >= 2 and b.lost_t < 1.0:

                heard = _hear(b)

                if heard is not None:

                    b.last = heard

                    b.lost_t = 2.5



    sp = 6.0 * D["speed"] * w.spd

    tgt = b.target

    mvx = mvz = 0.0

    want_move = True

    action = ""

    hold = False



    if tgt is not None:

        td = math.hypot(tgt.x - b.x, tgt.z - b.z)

        _switch_weapon(b, td)

        w = WEAPONS[b.weapon]

    else:

        td = 1e9

    # Yakinda gorunen dusman varken bomba kurma/cozme riskli: once savas

    can_obj = tgt is None or td > 22.0



    # ---------------- Takim hedefi ----------------

    if b.team == 0:

        if bomb and bomb.get("planted"):

            aim = (bomb["x"], bomb["z"])

            bd = math.hypot(b.x - bomb["x"], b.z - bomb["z"])

            gr = getattr(b, "guard_r", None)

            if gr is None:

                gr = b.guard_r = 3.5 + random.random() * 4.5

            if bd < gr:

                hold = True  # bombayi koru, defuse'u engelle

        elif bomb and bomb.get("carrier") is b:

            aim = SITES[b.site_target]

            if in_site(b.x, b.z) is not None and can_obj:

                action = "plant"

        elif bomb and bomb.get("carrier") is not None and getattr(bomb.get("carrier"), "alive", False):

            cx, cz = bomb["carrier"].x, bomb["carrier"].z

            sx, sy = SITES[b.site_target]

            dxc, dzc = sx - cx, sy - cz

            dc = math.hypot(dxc, dzc) + 1e-6

            back = getattr(b, "escort_a", None)

            if back is None:

                back = b.escort_a = random.random() * math.tau

            aim = (cx - dxc / dc * 5.5 + math.cos(back) * 2.5, cz - dzc / dc * 5.5 + math.sin(back) * 2.5)

        elif bomb and bomb.get("dropped"):

            atk = [f for f in g.FS if f.alive and f.team == 0 and not f.player]

            closest = min(atk, key=lambda f: (f.x - bomb["x"]) ** 2 + (f.z - bomb["z"]) ** 2) if atk else b

            aim = (bomb["x"], bomb["z"]) if closest is b else SITES[b.site_target]

        else:

            aim = SITES[b.site_target]

    else:

        if bomb and bomb.get("planted"):

            aim = (bomb["x"], bomb["z"])

            if _should_defuse(b):

                if can_obj:

                    action = "defuse"

            else:

                bd = math.hypot(b.x - bomb["x"], b.z - bomb["z"])

                if bd < 4.0 and _teammate_defusing(b):

                    hold = True  # defuse eden arkadasi kolla

                elif tgt is None and bd > 12.0:

                    mates = [f for f in g.FS if f is not b and f.alive and f.team == 1]

                    near = any((f.x - b.x) ** 2 + (f.z - b.z) ** 2 < 100.0 for f in mates)

                    bt = float(bomb.get("t", 30.0)) if bomb else 30.0

                    if mates and not near and bt > 8.0:

                        hold = True  # daginik retake yok: arkadasi bekle

        else:

            aim = SITES[b.site_target]

            if bomb and bomb.get("dropped"):

                db = math.hypot(b.x - bomb["x"], b.z - bomb["z"])

                if db < 10.0:

                    aim = (bomb["x"], bomb["z"])



    # ---------------- Davranis ----------------

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

        err = abs(wrap(yt - b.yaw))



        b.strafe_t -= dt

        if b.strafe_t <= 0:

            b.strafe = random.choice((-1.0, 1.0))

            b.strafe_t = 0.5 + random.random() * 1.2



        pref = PREF[b.weapon]

        fc = 1.0 if d > pref + 3 else (-1.0 if d < pref - 3 else 0.0)

        # Can azsa: geri cekilerek vur

        if b.hp < 35 and fc >= 0.0 and d < pref + 10:

            fc = -0.6

        # Nisan almadan hemen once yan hareketi azalt (duran nisan daha isabetli)

        precise = w.scope or w.rng >= 90

        aiming = b.react <= 0.15 and err < 0.25

        sf = (0.15 if precise else 0.5) if aiming else 0.8

        if precise and aiming:

            fc = 0.0

        ux, uz = dx / d, dz / d

        mvx = ux * fc + (-uz) * b.strafe * sf

        mvz = uz * fc + (ux) * b.strafe * sf



        b.react -= dt

        tol = cl(1.1 / d, 0.035, 0.10)  # uzakta daha siki nisan

        if w.scope:

            tol = min(tol, 0.04)

        if d < 2.4 and getattr(b, "slash_cd", 0.0) <= 0 and err < 0.5 and _knife_slash is not None:

            try:

                _knife_slash(b)

            except Exception:

                pass

        if b.mag[b.weapon] <= 0 and b.reload_t <= 0:

            b.reload_t = w.reload

        elif (b.react <= 0 and b.cd <= 0 and b.burst_pause <= 0 and b.reload_t <= 0

              and b.glitch <= 0 and err < tol and d < w.rng and d >= 2.2):

            spread = (w.ads if w.scope else w.hip * 0.6) + D["spread"]

            shoot(b, spread, D["dmg"])

            b.mag[b.weapon] -= 1

            if w.auto:

                if b.burst_left <= 0:

                    b.burst_left = random.randint(2, 4)

                b.burst_left -= 1

                if b.burst_left <= 0:

                    b.burst_pause = (0.14 + random.random() * 0.16) if b_diff >= 4 else (0.24 + random.random() * 0.32)

                    b.cd = 0.0

                else:

                    jit = 0.18 if b_diff >= 4 else 0.45

                    b.cd = w.rof * (1.0 + random.random() * jit)

            else:

                jit = 0.25 if b_diff >= 4 else 0.6

                b.cd = w.rof * (1.0 + random.random() * jit)

        if abs(mvx) + abs(mvz) < 0.01:

            want_move = False

    else:

        b.pitch += (0 - b.pitch) * min(1, 4 * dt)

        carrier = b.team == 0 and bomb and bomb.get("carrier") is b

        hunting = b.lost_t > 0 and not carrier

        if hunting:

            aim = b.last



        # Hedef yokken taktik sarjor degisimi

        if (b.reload_t <= 0 and w.mag > 0 and b.mag[b.weapon] < w.mag * 0.35

                and not hunting):

            b.reload_t = w.reload



        if hold:

            want_move = False

        else:

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

        if not hunting and not carrier:

            moving = abs(mvx) + abs(mvz) > 0.01

            if getattr(b, "roam_t", 0.0) > 0.0:

                b.roam_t -= dt

                ang = getattr(b, "roam_ang", 0.0)

                mvx, mvz = math.sin(ang), math.cos(ang)

                want_move = True

                if b.roam_t <= 0.0:

                    b.afk_t = 0.0

            elif moving:

                b.afk_t = 0.0

            else:

                b.afk_t = getattr(b, "afk_t", 0.0) + dt

                if b.afk_t > 1.2:

                    b.roam_t = 0.28 + random.random() * 0.3

                    b.roam_ang = random.random() * math.tau

                    b.afk_t = 0.0

        if not hunting and abs(mvx) + abs(mvz) < 0.01:

            b.scan = getattr(b, "scan", random.random() * 6.0) + dt

            b.yaw += math.sin(b.scan * 1.3) * 0.7 * dt

        if b.lost_t > 0:

            b.lost_t -= dt

            if hunting and math.hypot(b.last[0] - b.x, b.last[1] - b.z) < 2.0:

                b.lost_t = 0.0  # son bilinen noktaya vardim, gorev devam

        if b.team == 1 and bomb and bomb.get("planted") and _should_defuse(b):

            update_defuse(b, dt)

            mvx = mvz = 0.0

        if carrier and in_site(b.x, b.z) is not None:

            _plant_carrier(b, dt)

            mvx = mvz = 0.0



    # Takilma kurtarma: yolu dik yone cevir

    us = getattr(b, "unstick", 0.0)

    if us > 0:

        b.unstick = us - dt

        sd = getattr(b, "unstick_dir", 1.0)

        if abs(mvx) + abs(mvz) < 0.05:

            ang = random.random() * math.tau

            mvx, mvz = math.sin(ang), math.cos(ang)

        else:

            mvx, mvz = -mvz * sd + mvx * 0.3, mvx * sd + mvz * 0.3



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

            b.stuck_n = getattr(b, "stuck_n", 0) + 1

            if b.stuck_n >= 2:

                b.unstick = 0.9

                b.unstick_dir = random.choice((-1.0, 1.0))

                b.stuck_n = 0

                b.roam_t = 0.0

        else:

            b.stuck_n = 0

        b.lastpos = (b.x, b.z)

        b.stuck_t = 0

    _pickup(b)
