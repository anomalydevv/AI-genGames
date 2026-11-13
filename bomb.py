# -*- coding: utf-8 -*-
"""Bomba kurma/defuse/timer mantigi ve bomba bolgeleri."""
import math

from state import g
from world import SITE_R, SITES

BOMB_TIME = 45.0
PLANT_TIME = 3.0
DEFUSE_TIME = 8.0


def new_round(x=0.0, z=0.0):
    g.bomb = {
        "carrier": None,
        "planted": False,
        "dropped": True,
        "x": float(x),
        "z": float(z),
        "site": "",
        "timer": 0.0,
        "plant_t": 0.0,
        "defuse_t": 0.0,
        "defuser": None,
        "exploded": False,
        "defused": False,
        "tick": 0.0,
    }


def in_site(x, z):
    for name, (sx, sz) in SITES.items():
        if (x - sx) ** 2 + (z - sz) ** 2 <= SITE_R * SITE_R:
            return name
    return None


def site_dist(x, z):
    best, bd = "A", 1e18
    for name, (sx, sz) in SITES.items():
        d = (x - sx) ** 2 + (z - sz) ** 2
        if d < bd:
            bd, best = d, name
    return best, math.sqrt(bd)


def drop(actor):
    b = g.bomb
    if b and b["carrier"] is actor and not b["planted"]:
        b["carrier"] = None
        b["dropped"] = True
        b["x"], b["z"] = actor.x, actor.z


def try_pickup(actor, radius=2.2):
    b = g.bomb
    if not b or b["planted"] or b["carrier"] is not None or not b["dropped"]:
        return False
    if not actor.alive or actor.team != 0:
        return False
    if (actor.x - b["x"]) ** 2 + (actor.z - b["z"]) ** 2 > radius * radius:
        return False
    b["carrier"] = actor
    b["dropped"] = False
    return True


def update(dt):
    b = g.bomb
    if not b:
        return
    if b["planted"]:
        if b["defuser"] is not None:
            d = b["defuser"]
            if not d.alive or (d.x - b["x"]) ** 2 + (d.z - b["z"]) ** 2 > 2.2 ** 2:
                b["defuse_t"] = 0.0
                b["defuser"] = None
        if not b["defused"] and not b["exploded"]:
            b["timer"] -= dt
            b["tick"] += dt
            if b["timer"] <= 0:
                b["timer"] = 0.0
                b["exploded"] = True
        return
    if b["carrier"] is not None:
        c = b["carrier"]
        if not c.alive:
            drop(c)
        else:
            b["x"], b["z"] = c.x, c.z
    if b["dropped"]:
        best, bd = None, 2.2 ** 2
        for f in g.FS:
            if f.alive and not f.player and f.team == 0:
                d = (f.x - b["x"]) ** 2 + (f.z - b["z"]) ** 2
                if d < bd:
                    bd, best = d, f
        if best is not None:
            b["carrier"] = best
            b["dropped"] = False


def update_plant(actor, dt):
    b = g.bomb
    if not b or b["planted"] or b["carrier"] is not actor:
        return False
    if not actor.alive or g.phase != "live":
        b["plant_t"] = 0.0
        return False
    if in_site(actor.x, actor.z) is None:
        b["plant_t"] = 0.0
        return False
    b["plant_t"] += dt
    if b["plant_t"] >= PLANT_TIME:
        b["planted"] = True
        b["carrier"] = None
        b["dropped"] = False
        b["site"] = in_site(actor.x, actor.z)
        b["x"], b["z"] = actor.x, actor.z
        b["timer"] = BOMB_TIME
        b["plant_t"] = 0.0
        return True
    return False


def update_defuse(actor, dt):
    b = g.bomb
    if not b or not b["planted"] or b["defused"] or b["exploded"]:
        return False
    if not actor.alive or actor.team != 1:
        return False
    if (actor.x - b["x"]) ** 2 + (actor.z - b["z"]) ** 2 > 2.2 ** 2:
        if b["defuser"] is actor:
            b["defuse_t"] = 0.0
            b["defuser"] = None
        return False
    if b["defuser"] is not actor:
        b["defuse_t"] = 0.0
    b["defuser"] = actor
    b["defuse_t"] += dt
    if b["defuse_t"] >= DEFUSE_TIME:
        b["defused"] = True
        return True
    return False


def plant_progress():
    if not g.bomb:
        return 0.0
    return min(1.0, g.bomb["plant_t"] / PLANT_TIME)


def defuse_progress():
    if not g.bomb:
        return 0.0
    return min(1.0, g.bomb["defuse_t"] / DEFUSE_TIME)


def render_pos():
    if not g.bomb:
        return None
    return g.bomb["x"], g.bomb["z"]
