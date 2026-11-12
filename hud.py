# -*- coding: utf-8 -*-
"""HUD, bomba uyarilari, skor tablosu, market, magaza ve tum menu ekranlari."""
import math

from pyray import *

import bomb
import characters
import icons
import knives
import playerdata
from config import C, CYAN, GOLD, RED, SH, SW, cfg, lerpf
from match import start_match
from modes import MODES
from state import g
from ui import R, RL, button, ctxt, mouse_in, panel, rtxt, slider, toggle, txt
from weapons import DIFFS, WEAPONS, WNAMES_TR, slot_of

CROSS_NAMES = ["Nokta", "Sabit +", "Standart"]


def draw_crosshair(p, w, cx, cy):
    if not p.alive or p.knife_active or p.inspect:
        return
    if w.scope and p.ads > 0.85:
        return
    style = int(cfg.get("crosshair", 2))
    col = C(255, 255, 255, 220)
    if style == 0:
        draw_circle(cx, cy, 2, col)
        draw_circle(cx, cy, 1, WHITE)
        return
    if style == 1:
        gap = 7
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            draw_line_ex(Vector2(cx + dx * gap, cy + dy * gap), Vector2(cx + dx * (gap + 8), cy + dy * (gap + 8)), 2, col)
        draw_circle(cx, cy, 1, col)
        return
    gap = 6 + (lerpf(w.hip, w.ads, p.ads) + math.hypot(p.vx, p.vz) * 0.1 + p.heat) * 5
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        draw_line_ex(Vector2(cx + dx * gap, cy + dy * gap), Vector2(cx + dx * (gap + 8), cy + dy * (gap + 8)), 2, col)
    draw_circle(cx, cy, 1, col)


def _preview_crosshair(cx, cy):
    style = int(cfg.get("crosshair", 2))
    col = C(0, 230, 200, 230)
    if style == 0:
        draw_circle(cx, cy, 2, col)
    elif style == 1:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            draw_line_ex(Vector2(cx + dx * 7, cy + dy * 7), Vector2(cx + dx * 15, cy + dy * 15), 2, col)
    else:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            draw_line_ex(Vector2(cx + dx * 6, cy + dy * 6), Vector2(cx + dx * 14, cy + dy * 14), 2, col)
        draw_circle(cx, cy, 1, col)


def hud():
    p = g.p
    spec = g.spec if (not p.alive and g.spec is not None and g.spec.alive) else None
    v = spec if spec is not None else p
    w = WEAPONS[p.weapon]
    vw = WEAPONS[v.weapon]
    cx, cy = SW // 2, SH // 2
    scoped = w.scope and p.ads > 0.85 and p.alive and not p.knife_active and not p.inspect
    if scoped:
        draw_ring(Vector2(cx, cy), 300, 1600, 0, 360, 64, BLACK)
        draw_line_ex(Vector2(cx - 300, cy), Vector2(cx + 300, cy), 1, C(0, 0, 0, 200))
        draw_line_ex(Vector2(cx, cy - 300), Vector2(cx, cy + 300), 1, C(0, 0, 0, 200))
    draw_crosshair(p, w, cx, cy)
    if g.hitm > 0:
        c = RED if g.hitm_k else WHITE
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            draw_line_ex(Vector2(cx + dx * 9, cy + dy * 9), Vector2(cx + dx * 18, cy + dy * 18), 3, c)
    if g.hit_t > 0:
        dx, dz = g.hit_from[0] - p.x, g.hit_from[1] - p.z
        a = dx * math.sin(p.yaw) + dz * math.cos(p.yaw)
        b = dx * (-math.cos(p.yaw)) + dz * math.sin(p.yaw)
        th = math.atan2(b, a)
        draw_line_ex(Vector2(cx + math.sin(th) * 120, cy - math.cos(th) * 120),
                     Vector2(cx + math.sin(th) * 150, cy - math.cos(th) * 150), 8, C(255, 40, 40, int(255 * min(1, g.hit_t))))
    # ust takim bilgisi
    panel(SW / 2 - 230, 10, 460, 56)
    ctxt("SALDIRICI %d   -   %d SAVUNMACI" % (g.atk_wins, g.dfn_wins), SW / 2, 14, 22, WHITE)
    alive = sum(1 for f in g.FS if f.alive)
    ctxt("ROUND %d   HEDEF %d   %d sn   CANLI %d" % (g.round, g.target, max(0, int(g.round_t)), alive), SW / 2, 39, 17, CYAN)
    # killfeed
    for i, f in enumerate(g.feed):
        s = "%s  [%s]  %s%s" % (f[0], f[1], f[2], "  (HS)" if f[3] else "")
        rtxt(s, SW - 20, 20 + i * 26, 20, WHITE if f[0] != p.name else GOLD)
    # bomba durumu
    b = g.bomb
    if b:
        if b["planted"]:
            t = max(0, int(math.ceil(b["timer"])))
            blink = int(get_time() * 6) % 2 == 0
            ctxt("BOMB PLANTED - T MINUS %d SECONDS" % t, SW / 2, 118, 34, RED if blink else WHITE)
            ctxt("BOLGE %s   |   SAVUNMACILAR DEFUSE EDIYOR" % b["site"], SW / 2, 158, 20, GOLD)
            if b["defuse_t"] > 0:
                dp = bomb.defuse_progress()
                R(SW / 2 - 160, 184, 320, 12, C(40, 40, 46))
                R(SW / 2 - 160, 184, 320 * dp, 12, CYAN)
        elif b["dropped"]:
            ctxt("BOMBA DUSTU - E ile AL", SW / 2, 120, 30, GOLD)
        elif b["carrier"] is p:
            ctxt("BOMBA SENDE - %s BOLGESINE KUR (E)" % g.site_plan, SW / 2, 120, 26, GOLD)
        if b["plant_t"] > 0:
            pp = bomb.plant_progress()
            R(SW / 2 - 150, 118, 300, 14, C(40, 40, 46))
            R(SW / 2 - 150, 118, 300 * pp, 14, GOLD)
            ctxt("BOMBA KURULUYOR", SW / 2, 140, 22, WHITE)
    # bolge harfleri
    for letter, (sx, sz) in bomb.SITES.items():
        sp = get_world_to_screen_ex(Vector3(sx, 1.8, sz), g.cam, SW, SH)
        if sp.x > 0 and sp.y > 0:
            ctxt(letter, sp.x, sp.y, 34, C(0, 230, 200, 200) if g.site_plan == letter else C(255, 205, 70, 160))
    # sol alt: can
    panel(20, SH - 100, 270, 80)
    txt("CAN", 34, SH - 94, 18, GRAY)
    R(34, SH - 70, 240, 14, C(40, 40, 46))
    R(34, SH - 70, 240 * max(0, v.hp) / 100, 14, C(80, 230, 110) if v.hp > 35 else RED)
    rtxt("%d" % math.ceil(max(0, v.hp)), 274, SH - 94, 20, WHITE)
    R(34, SH - 46, 240, 8, C(40, 40, 46))
    R(34, SH - 46, 240 * v.armor / 100, 8, C(90, 160, 255))
    txt("$ %d" % g.money, 34, SH - 36, 20, GOLD)
    # sag alt: mermi / bicak
    if v.knife_active:
        icons.draw_knife(v.knife, SW - 452, SH - 96, 128, 51)
    else:
        icons.draw_weapon(v.weapon, SW - 452, SH - 96, 128, 51)
    panel(SW - 310, SH - 100, 290, 80)
    if v.knife_active:
        k = knives.by_id(v.knife)
        rtxt(k.name, SW - 34, SH - 96, 20, CYAN)
        rtxt("BICAK", SW - 34, SH - 70, 34, WHITE)
        rtxt("SOL TIK: KES  |  1-2: SILAH  |  SCROLL", SW - 34, SH - 28, 13, GRAY)
    else:
        rtxt(vw.name, SW - 34, SH - 96, 20, CYAN)
        rtxt("%d / %d" % (v.mag[v.weapon], v.res[v.weapon]), SW - 34, SH - 70, 38, WHITE if v.mag[v.weapon] > 0 else RED)
        rtxt("Y: INCELE  |  SCROLL: DEGISTIR", SW - 34, SH - 28, 13, GRAY)
        if v.reload_t > 0:
            ctxt("YENIDEN DOLDURULUYOR", SW / 2, SH / 2 + 80, 22, WHITE)
    if p.inspect and p.alive:
        ctxt("INCELEME   |   Y: BITIR", SW / 2, SH - 132, 18, CYAN)
    # skill bari
    ch = characters.get(g.char)
    skills = [(ch.x.key, ch.x.name), (ch.c.key, ch.c.name), (ch.v.key, ch.v.name), (ch.g.key, ch.g.name)]
    bx = SW / 2 - 4 * 82 / 2
    for i, (k, nm) in enumerate(skills):
        x = bx + i * 82
        y = SH - 104
        ready = False
        sub = ""
        if k == "X":
            ready = g.x_ready
            sub = "HAZIR" if ready else "KULLANILDI"
        elif k == "C":
            if ch.c.kind == "soul":
                ready = g.soul_t > 0
                sub = "RUH AL!" if ready else "kill bekle"
            else:
                ready = g.c_cd <= 0
                sub = "HAZIR" if ready else "%.1fs" % g.c_cd
        elif k == "V":
            ready = g.v_cd <= 0
            sub = "HAZIR" if ready else "%.1fs" % g.v_cd
        else:
            if g.ult_t > 0:
                sub = "AKTIF"
            else:
                ready = g.ult >= 100
                sub = "HAZIR" if ready else "%d%%" % g.ult
        R(x, y, 76, 76, C(10, 14, 20, 220))
        if k == "G" and g.ult < 100 and g.ult_t <= 0:
            R(x, y + 76 * (1 - g.ult / 100), 76, 76 * g.ult / 100, C(255, 60, 140, 90))
        RL(x, y, 76, 76, CYAN if ready else C(90, 100, 110), 3 if ready else 2)
        ctxt(k, x + 38, y + 6, 30, WHITE if ready else GRAY)
        ctxt(nm[:11], x + 38, y + 40, 13, WHITE if ready else GRAY)
        ctxt(sub, x + 38, y + 58, 13, GOLD if ready else GRAY)
    if ch.c.kind == "soul" and g.soul_t > 0:
        ctxt("[C] RUHU AL  %.1f" % g.soul_t, SW / 2, SH / 2 + 110, 26, C(80, 255, 230))
    if p.ghost > 0:
        ctxt("GORUNMEZ %.1f" % p.ghost, SW / 2, 80, 26, C(80, 255, 230))
    if g.ult_t > 0:
        ctxt("%s AKTIF %.1f" % (ch.g.name, g.ult_t), SW / 2, 106, 24, RED)
    if g.phase == "freeze":
        ctxt("BASLAMAYA %d" % math.ceil(g.phase_t), SW / 2, 210, 44, WHITE)
        ctxt("B: Market   |   E: Bomba   |   1-2: Silah   |   3: Bicak   |   Y: Incele", SW / 2, 258, 22, CYAN)
    if g.phase == "roundend" and g.last_winner:
        ctxt("%s KAZANDI  (%s)" % (g.last_winner, g.round_reason), SW / 2, 210, 40, GOLD)
    if not p.alive and g.phase == "live":
        ctxt("ELENDIN", SW / 2, 210, 44, RED)
        if g.spec is not None:
            ctxt("IZLENIYOR: %s" % g.spec.name, SW / 2, 258, 24, CYAN)
        ctxt("SOL TIK / SCROLL / OK: takim arkadasi", SW / 2, 286, 16, GRAY)
    kill_banners()
    if cfg["fps"]:
        txt("%d FPS" % get_fps(), 10, 10, 18, C(255, 255, 255, 150))


def kill_banners():
    w, h = 400, 52
    base = SH - 210
    for j, e in enumerate(reversed(g.kills_show)):
        a = min(1.0, e["t"] / 0.35)
        ai = int(255 * a)
        x = SW / 2 - w / 2
        y = base - j * (h + 6)
        R(x, y, w, h, C(8, 12, 18, int(215 * a)))
        R(x, y, 4, h, C(255, 50, 70, ai))
        if e["knife"]:
            icons.draw_knife(e["kid"], x + 12, y + 8, 92, 36, ai)
        else:
            icons.draw_weapon(e["w"], x + 12, y + 8, 92, 36, ai)
        txt("OLDURDUN", x + 116, y + 6, 13, C(255, 90, 100, ai))
        txt(e["name"][:20], x + 116, y + 20, 22, C(255, 255, 255, ai))
        if e["hs"]:
            txt("KAFA", x + w - 54, y + 6, 13, C(255, 205, 70, ai))
        rtxt(e["wname"][:24], x + w - 14, y + 30, 13, C(190, 196, 210, ai))


def scoreboard():
    fs = sorted(g.FS, key=lambda f: (f.team, -f.kills, f.deaths))
    w, h = 780, 110 + len(fs) * 36
    x, y = SW / 2 - w / 2, SH / 2 - h / 2
    panel(x, y, w, h)
    ctxt("SKOR TABLOSU", SW / 2, y + 12, 28, CYAN)
    hdr = y + 56
    for tx, s in ((x + 30, "#"), (x + 80, "ISIM"), (x + 380, "TAKIM"), (x + 470, "KILL"), (x + 550, "OLUM"), (x + 630, "K/D"), (x + 700, "ROUND")):
        txt(s, tx, hdr, 18, GRAY)
    for i, f in enumerate(fs):
        yy = hdr + 28 + i * 36
        if f.player:
            R(x + 10, yy - 4, w - 20, 32, C(0, 230, 200, 40))
        col = WHITE if f.alive else C(150, 150, 150)
        team = "SALDIRI" if f.team == 0 else "SAVUNMA"
        tcol = C(120, 200, 255) if f.team == 0 else C(255, 120, 100)
        txt(str(i + 1), x + 30, yy, 22, col)
        txt(f.name + ("" if f.alive else "  (oldu)"), x + 80, yy, 22, col)
        txt(team, x + 380, yy, 18, tcol)
        txt(str(f.kills), x + 470, yy, 22, GOLD)
        txt(str(f.deaths), x + 550, yy, 22, col)
        txt("%.2f" % (f.kills / max(1, f.deaths)), x + 630, yy, 22, col)
        txt(str(f.wins), x + 700, yy, 22, col)


def market_ui():
    p = g.p
    R(0, 0, SW, SH, C(0, 0, 0, 160))
    w, h = 1060, 600
    x, y = SW / 2 - w / 2, SH / 2 - h / 2
    panel(x, y, w, h)
    ctxt("SILAH MARKETI", SW / 2, y + 14, 34, CYAN)
    rtxt("$ %d" % g.money, x + w - 30, y + 18, 28, GOLD)
    items = [("Kevlar Yelek", "armor", 150, "+50 zirh | hasarin yarisini emer")]
    for i in range(1, len(WEAPONS)):
        wd = WEAPONS[i]
        slot = "ANA SILAH" if slot_of(i) == 0 else "TABANCA"
        items.append((WNAMES_TR[i], i, wd.price, "%s  |  Hasar %d  |  Sarjor %d  |  x%d" % (slot, wd.dmg, wd.mag, wd.pel)))
    cw, chh = 497, 92
    gx, gy = 18, 10
    x0, y0 = x + 24, y + 68
    for idx, (nm, key, price, desc) in enumerate(items):
        cx = x0 + (idx % 2) * (cw + gx)
        yy = y0 + (idx // 2) * (chh + gy)
        if key == "armor":
            owned = p.armor >= 50
        else:
            owned = key in p.owned
        R(cx, yy, cw, chh, C(16, 22, 30, 228))
        RL(cx, yy, cw, chh, C(0, 230, 200, 70), 1)
        if key == "armor":
            R(cx + 62, yy + 24, 40, 42, C(70, 110, 170))
            RL(cx + 62, yy + 24, 40, 42, C(140, 190, 255), 2)
            R(cx + 76, yy + 14, 12, 10, C(140, 190, 255))
        else:
            icons.draw_weapon(key, cx + 12, yy + 14, 132, 64)
        txt(nm, cx + 156, yy + 10, 19, WHITE)
        txt(desc, cx + 156, yy + 42, 13, GRAY)
        if key == "armor":
            lab = "SAHIP" if owned else "$ %d" % price
            enabled = not owned and g.money >= price
        elif owned and p.weapon == key and not p.knife_active:
            lab = "AKTIF"
            enabled = False
        elif owned:
            lab = "KUSAN"
            enabled = True
        else:
            lab = "$ %d" % price
            enabled = g.money >= price
        if button(cx + cw - 132, yy + 24, 118, 44, lab, 20, enabled=enabled):
            if key == "armor":
                g.money -= price
                p.armor = 50.0
            elif owned:
                p.slots[slot_of(key)] = key
                p.weapon = key
                p.knife_active = False
                p.inspect = False
                p.switch_t = 0.35
            else:
                g.money -= price
                p.owned.add(key)
                p.slots[slot_of(key)] = key
                p.weapon = key
                p.knife_active = False
                p.inspect = False
                p.switch_t = 0.35
    ctxt("B / ESC: kapat   |   1-2: Silah   |   3: Bicak   |   Y: Incele   |   Market acikken oyun durur",
         SW / 2, y + h - 26, 17, GRAY)


def pause_ui():
    R(0, 0, SW, SH, C(0, 0, 0, 160))
    ctxt("DURAKLATILDI", SW / 2, 180, 48, CYAN)
    if button(SW / 2 - 150, 280, 300, 56, "Devam", 26):
        g.paused = False
    if button(SW / 2 - 150, 350, 300, 56, "Ayarlar", 26):
        g.back = "play"
        g.state = "settings"
    if button(SW / 2 - 150, 420, 300, 56, "Ana Menü", 26):
        g.paused = False
        g.state = "main"


def title(s, sub=None):
    ctxt(s, SW / 2, 40, 64, CYAN)
    if sub:
        ctxt(sub, SW / 2, 110, 22, GRAY)


def screen_main():
    title("HEX ARENA", "Özel Maç - Bomba Modu")
    rtxt("RUH: %d" % playerdata.souls(), SW - 24, 22, 24, GOLD)
    labels = [("Özel Maç Kur", "setup"), ("Karakter Secimi", "char"), ("Magaza", "shop"), ("Ayarlar", "settings")]
    y = 220
    for i, (lab, target) in enumerate(labels):
        if button(SW / 2 - 160, y + i * 70, 320, 56, lab, 26):
            if target == "settings":
                g.back = "main"
            g.state = target
    if button(SW / 2 - 160, y + 4 * 70, 320, 56, "Cikis", 26):
        g.quit = True


def screen_char():
    title("KARAKTER SECIMI", "Secili karakterle maca cik")
    d = playerdata.data()
    for i, ch in enumerate(characters.CHARACTERS):
        x = 35 + i * 302
        y = 150
        sel = g.char == i
        panel(x, y, 290, 380)
        if sel:
            RL(x + 4, y + 4, 282, 372, ch.color, 3)
        txt(ch.name, x + 18, y + 14, 30, ch.color)
        txt(ch.title, x + 18, y + 52, 16, GOLD)
        R(x + 18, y + 82, 254, 1, C(70, 80, 95))
        skills = [ch.x, ch.c, ch.v, ch.g]
        for j, sk in enumerate(skills):
            yy = y + 102 + j * 54
            R(x + 18, yy, 38, 40, C(10, 15, 22, 230))
            RL(x + 18, yy, 38, 40, ch.color if sel else C(70, 80, 95), 2)
            ctxt(sk.key, x + 37, yy + 6, 22, WHITE)
            txt(sk.name, x + 68, yy + 4, 16, WHITE)
            if sk.cd > 0:
                txt("CD %.0fs" % sk.cd, x + 68, yy + 24, 12, GRAY)
        if sel:
            button(x + 75, y + 322, 140, 40, "SECILI", 18, active=True, enabled=False)
        else:
            if button(x + 75, y + 322, 140, 40, "SEC", 18):
                g.char = i
                d["character"] = ch.cid
                playerdata.save()
    if button(SW / 2 - 130, 620, 260, 52, "Geri", 24):
        g.state = "main"


def screen_setup():
    title("ÖZEL MAÇ KUR", "Botları, tur hedefini ve zorluğu ayarla")
    panel(60, 130, 560, 540)
    txt("Oyun Modu", 90, 146, 20, WHITE)
    for i, (nm, tgt, _) in enumerate(MODES):
        if button(90 + i * 250, 176, 230, 42, "%s (Hedef %d)" % (nm, tgt), 17, active=(g.target == tgt)):
            g.mode = i
            g.target = tgt
    g.target = int(round(slider(90, 238, 480, "Tur hedefi", g.target, 1, 30, "%.0f")))
    txt("Zorluk", 90, 304, 20, WHITE)
    for i, (nm, _) in enumerate(DIFFS):
        if button(90 + i * 104, 336, 96, 38, nm, 14, active=(g.diff == i)):
            g.diff = i
    txt("Takım botları", 90, 394, 20, WHITE)
    txt("Müttefik bot:", 90, 432, 19, WHITE)
    if button(250, 426, 40, 36, "-", 22):
        g.ally_bots = max(0, g.ally_bots - 1)
    ctxt(str(g.ally_bots), 310, 432, 22, CYAN)
    if button(350, 426, 40, 36, "+", 22):
        g.ally_bots = min(4, g.ally_bots + 1)
    txt("Düşman bot:", 90, 480, 19, WHITE)
    if button(250, 474, 40, 36, "-", 22):
        g.enemy_bots = max(0, g.enemy_bots - 1)
    ctxt(str(g.enemy_bots), 310, 480, 22, CYAN)
    if button(350, 474, 40, 36, "+", 22):
        g.enemy_bots = min(5, g.enemy_bots + 1)
    txt("0 = bot kapalı", 410, 452, 14, GRAY)
    txt("Oyuncu adı:", 90, 528, 20, WHITE)
    name_field(7, 90, 560, 480)
    if button(90, 610, 220, 50, "MAÇI BAŞLAT", 20):
        start_match()
    if button(330, 610, 220, 50, "Geri", 20):
        g.state = "main"
    panel(650, 130, 570, 540)
    txt("MAC KURALLARI", 675, 146, 24, CYAN)
    lines = [
        "Takımlar: %d bot müttefik + %d bot düşman." % (g.ally_bots, g.enemy_bots),
        "Tur hedefi: ilk %d roundu alan kazanır." % g.target,
        "Zorluk: %s" % DIFFS[g.diff][0],
        "Saldırıcı takım bombayı A veya B'ye kurar.",
        "Tur süresi: 60 saniye. Bomba: 30 saniye.",
        "Savunmacılar bombayı 8 sn'de defuse eder.",
        "Bomba patlarsa saldırıcılar roundu alır.",
        "Rakip takımı yok et veya bombayı koru.",
        "Market: B (sadece freeze) | Bıçak: 3 | E: Bomba",
        "Tek silah inceleme: Y | Scroll: slot seç",
    ]
    for i, s in enumerate(lines):
        txt(s, 675, 188 + i * 36, 18, GRAY if i % 2 else WHITE)
    txt("ÖZEL MAÇ: %d bot müttefik, %d bot düşman" % (g.ally_bots, g.enemy_bots), 675, 590, 17, GOLD)


def name_field(i, x, y, w):
    act = g.edit == i
    R(x, y, w, 38, C(20, 28, 38, 240))
    RL(x, y, w, 38, CYAN if act else C(0, 230, 200, 90), 2)
    txt(g.names[i] + ("_" if act and int(get_time() * 2) % 2 == 0 else ""), x + 10, y + 7, 22, WHITE)
    if is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
        if mouse_in(x, y, w, 38):
            g.edit = i
    if act:
        while True:
            ch = get_char_pressed()
            if ch == 0:
                break
            if ch >= 32 and len(g.names[i]) < 14:
                g.names[i] += chr(ch)
        rep = is_key_pressed_repeat(KEY_BACKSPACE) if 'is_key_pressed_repeat' in globals() else is_key_pressed(KEY_BACKSPACE)
        if (rep or is_key_pressed(KEY_BACKSPACE)) and g.names[i]:
            g.names[i] = g.names[i][:-1]
        if is_key_pressed(KEY_ENTER):
            g.edit = -1


def screen_settings():
    title("AYARLAR")
    panel(300, 130, 680, 500)
    cfg["sens"] = slider(340, 150, 600, "Mouse hassasiyeti", cfg["sens"], 0.3, 3.0)
    cfg["fov"] = slider(340, 220, 600, "Gorus acisi (FOV)", cfg["fov"], 70, 110, "%.0f")
    cfg["bob"] = toggle(340, 300, "View bobbing (yurume sallanmasi)", cfg["bob"])
    cfg["sway"] = toggle(340, 340, "Silah sallanmasi (sway)", cfg["sway"])
    cfg["fx"] = toggle(340, 380, "Gercekci shader (bloom, tonemap, grain)", cfg["fx"])
    cfg["fps"] = toggle(340, 420, "FPS goster", cfg["fps"])
    style = int(cfg.get("crosshair", 2))
    txt("Crosshair", 340, 462, 22, WHITE)
    if button(460, 456, 220, 36, CROSS_NAMES[style], 18, active=True):
        cfg["crosshair"] = (style + 1) % 3
        d = playerdata.data()
        d["crosshair"] = cfg["crosshair"]
        playerdata.save()
    _preview_crosshair(900, 474)
    txt("WASD hareket | Ctrl comel | Space zipla | R reload | 1-2 silah | 3 bicak | Y incele", 330, 520, 15, GRAY)
    txt("X / C / V skill | G ulti | Scroll slot | TAB skor | ESC duraklat | E bomba", 330, 544, 15, GRAY)
    txt("F11 veya Alt+Enter: tam ekran", 330, 568, 15, GRAY)
    if button(SW / 2 - 130, 650, 260, 52, "Geri", 24):
        g.state = g.back


def screen_shop():
    title("MAGAZA", "Ruh puaniyla bicak satin al")
    rtxt("RUH: %d" % playerdata.souls(), SW - 24, 22, 24, GOLD)
    d = playerdata.data()
    owned = d.get("knives", ["knife"])
    for i, k in enumerate(knives.KNIVES):
        x = 55 + i * 395
        y = 165
        panel(x, y, 365, 360)
        icons.draw_knife(k.kid, x + 30, y + 18, 305, 122)
        txt(k.name, x + 22, y + 152, 28, k.color)
        txt(k.desc, x + 22, y + 190, 15, GRAY)
        is_owned = k.kid in owned
        if is_owned:
            if d.get("knife") == k.kid:
                button(x + 100, y + 270, 165, 44, "SECILI", 18, active=True, enabled=False)
            else:
                if button(x + 100, y + 270, 165, 44, "KUSAN", 18):
                    d["knife"] = k.kid
                    playerdata.save()
        else:
            if button(x + 100, y + 270, 165, 44, "%d RUH" % k.price, 18, enabled=playerdata.souls() >= k.price):
                if playerdata.spend(k.price):
                    owned.append(k.kid)
                    d["knives"] = owned
                    d["knife"] = k.kid
                    playerdata.save()
    if button(SW / 2 - 130, 600, 260, 52, "Geri", 24):
        g.state = "main"


def screen_end():
    R(0, 0, SW, SH, C(0, 0, 0, 170))
    fs = sorted(g.FS, key=lambda f: (-f.wins, -f.kills))
    wname = "SALDIRICILAR" if g.winner_team == 0 else "SAVUNMACILAR"
    ctxt("MAC BITTI", SW / 2, 70, 52, CYAN)
    ctxt("%s KAZANDI   %d - %d" % (wname, g.atk_wins, g.dfn_wins), SW / 2, 132, 34, GOLD)
    ctxt("MVP: %s   |   Kazanilan RUH: +%d   |   Toplam RUH: %d" % (g.mvp, g.souls_earned, playerdata.souls()),
         SW / 2, 178, 22, WHITE)
    for i, f in enumerate(fs):
        ctxt("%d. %s   %s   round %d   kill %d   olum %d" % (
            i + 1, f.name, "SAL" if f.team == 0 else "SAV", f.wins, f.kills, f.deaths),
            SW / 2, 225 + i * 30, 20, GOLD if f.player else WHITE)
    if button(SW / 2 - 240, 590, 220, 54, "Tekrar Oyna", 22):
        start_match()
    if button(SW / 2 + 20, 590, 220, 54, "Ana Menu", 22):
        g.state = "main"
