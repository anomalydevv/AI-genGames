# -*- coding: utf-8 -*-
"""Savasci (oyuncu/bot) veri modeli ve bakis vektoru."""
import math
import random

from weapons import WEAPONS


class F:
    def __init__(s, name, col, player=False, team=0):
        s.name, s.col, s.player, s.team = name, col, player, team
        s.kills = s.deaths = s.wins = s.round_kills = 0
        s.assists = 0
        s.dmg_by = {}
        s.diff = 2
        s.greed = random.random()
        s.money = 800
        s.burst_left = 0
        s.burst_pause = 0.0
        s.alive = False
        s.x = s.y = s.z = s.vx = s.vy = s.vz = 0.0
        s.yaw = s.pitch = 0.0
        s.hp, s.armor, s.h, s.eh = 100.0, 0.0, 1.8, 1.62
        s.weapon = 0
        s.mag = [w.mag for w in WEAPONS]
        s.res = [w.res for w in WEAPONS]
        s.cd = s.reload_t = 0.0
        s.ghost = s.inv = s.glitch = 0.0
        s.death_t = 0.0
        s.grounded = True
        s.landed = 0.0
        s.walk = 0.0
        s.target = None
        s.react = 0.0
        s.aim_h = 1.2
        s.path = []
        s.last = (0, 0)
        s.lost_t = 0.0
        s.strafe = 1.0
        s.strafe_t = 0.0
        s.think = random.random() * 0.2
        s.stuck_t = 0.0
        s.lastpos = (0, 0)
        s.afk_t = 0.0
        s.roam_t = 0.0
        s.roam_ang = 0.0
        s.site_target = "A"
        # bicak
        s.knife = "knife"
        s.knife_active = False
        s.gun_skin = "none"
        s.knife_skin = "none"
        s.slash_t = 0.0
        s.slash_cd = 0.0
        s.slash_n = 0
        s.hinge_a = 0.0
        s.hinge_v = 0.0
        s.hinge_b = 0.0
        s.hinge_bv = 0.0
        # oyuncu
        s.owned = {0}
        s.slots = [None, None]
        s.inspect = False
        s.inspect_t = 0.0
        s.inspect_out = 0.0
        s.cycle = 0.0
        s.bobt = 0.0
        s.ads = 0.0
        s.kick = 0.0
        s.heat = 0.0
        s.sway = 0.0
        s.swayy = 0.0
        s.switch_t = 0.0
        s.land = 0.0
        s.flash = 0.0
        s.dash_t = 0.0
        s.dash = (0, 0)
        s.bobamp = 0.0

    def reset(s, x, z, weapon):
        s.x, s.y, s.z, s.vx, s.vy, s.vz = x, 0.0, z, 0, 0, 0
        s.yaw = math.atan2(-x, -z)
        s.pitch = 0.0
        s.hp = 100.0
        s.armor = 0.0
        s.alive = True
        s.h = 1.8
        s.eh = 1.62
        s.weapon = weapon
        s.mag = [w.mag for w in WEAPONS]
        s.res = [w.res if s.player else 999 for w in WEAPONS]
        s.cd = s.reload_t = 0.0
        s.ghost = s.inv = s.glitch = 0.0
        s.death_t = 0.0
        s.target = None
        s.path = []
        s.lost_t = 0.0
        s.round_kills = 0
        s.dmg_by = {}
        s.stuck_t = 0.0
        s.lastpos = (x, z)
        s.afk_t = 0.0
        s.roam_t = 0.0
        s.roam_ang = 0.0
        s.knife_active = False
        s.slash_t = 0.0
        s.slash_cd = 0.0
        s.burst_left = 0
        s.burst_pause = 0.0
        s.hinge_a = 0.0
        s.hinge_v = 0.0
        s.hinge_b = 0.0
        s.hinge_bv = 0.0
        s.inspect = False
        s.inspect_t = 0.0
        s.inspect_out = 0.0
        s.cycle = 0.0


def look(f):
    cp = math.cos(f.pitch)
    return math.sin(f.yaw) * cp, math.sin(f.pitch), math.cos(f.yaw) * cp
