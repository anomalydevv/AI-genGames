# -*- coding: utf-8 -*-
"""Oyunun tum calisma zamani durumu (tek global `g` nesnesi)."""


class NS:
    pass


g = NS()

# ekran / menu
g.state = "main"
g.paused = False
g.market = False
g.edit = -1
g.locked = False
g.skip_mouse = 0
g.back = "main"
g.quit = False

# mac ayarlari
g.bots_n = 5
g.diff = 2
g.mode = 0
g.target = 5
g.names = ["Kuzgun", "Pars", "Tilki", "Bozkurt", "Ejder", "Firtina", "Golge", "Oyuncu",
           "Akrep", "Kartal", "Yilan", "Panter", "Bogaz"]

# dunya / oyuncular
g.FS = []
g.p = None
g.spec = None
g.cam = None
g.rt = None
g.vmrt = None
g.char = 0

# efektler
g.tracers = []
g.parts = []
g.drops = []
g.feed = []
g.kills_show = []
g.hurt = g.hitm = g.hit_t = g.dig = 0.0
g.hit_from = (0, 0)
g.hitm_k = False

# mac durumu
g.money = 0
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
g.phase = "freeze"
g.phase_t = 0
g.round_t = 60
g.round = 0
g.site_plan = "A"
g.atk_wins = 0
g.dfn_wins = 0
g.last_winner = None
g.round_reason = ""
g.cursor_dead = False

# bomba / mac sonu
g.bomb = None
g.explode_t = 0.0
g.explode_pos = (0, 0, 0)
g.match_rewarded = False
g.mvp = ""
g.souls_earned = 0
g.winner_team = None
