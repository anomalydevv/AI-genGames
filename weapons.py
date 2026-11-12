# -*- coding: utf-8 -*-
"""Silah tanimlari, isimler ve bot zorluk seviyeleri."""


class Wp:
    def __init__(s, name, dmg, pel, rof, mag, res, hip, ads, auto, price, rng, head, kick, spd, reload, scope=False):
        s.name, s.dmg, s.pel, s.rof, s.mag, s.res = name, dmg, pel, rof, mag, res
        s.hip, s.ads, s.auto, s.price, s.rng, s.head = hip, ads, auto, price, rng, head
        s.kick, s.spd, s.reload, s.scope = kick, spd, reload, scope


WEAPONS = [
    Wp("Hex-9 Tabanca", 24, 1, 0.20, 14, 56, 0.9, 0.3, False, 0, 70, 2.0, 1.6, 1.0, 1.3),
    Wp("Kasirga Revolver", 62, 1, 0.60, 6, 30, 0.6, 0.15, False, 600, 80, 1.9, 4.5, 0.97, 2.0),
    Wp("Gurz Pompali", 12, 9, 0.85, 6, 24, 4.8, 3.6, False, 800, 24, 1.6, 7.0, 0.95, 2.4),
    Wp("VX-7 Tufek", 26, 1, 0.095, 30, 90, 1.5, 0.8, True, 1100, 90, 2.0, 1.0, 0.93, 2.0),
    Wp("Hayalet Keskin Nisanci", 120, 1, 1.30, 5, 20, 3.8, 0.02, False, 1500, 220, 3.0, 7.0, 0.88, 2.6, True),
    Wp("Kral-47 Piyade", 31, 1, 0.10, 30, 90, 1.9, 0.85, True, 1800, 95, 2.2, 1.25, 0.92, 2.2),
    Wp("Çelik .50 Tabanca", 70, 1, 0.50, 7, 35, 1.0, 0.15, False, 2100, 100, 2.4, 5.0, 0.96, 2.0),
    Wp("M-249 Baskı Makinesi", 30, 1, 0.085, 60, 120, 2.6, 1.2, True, 2400, 100, 1.8, 0.8, 0.86, 3.2),
]
WNAMES_TR = ["Hex-9 Tabanca", "Kasırga Revolver", "Gürz Pompalı", "VX-7 Tüfek", "Hayalet Keskin Nişancı",
             "Kral-47 Piyade", "Çelik .50 Tabanca", "M-249 Baskı Makinesi"]
PREF = [10, 11, 6, 14, 26, 18, 20, 16]
SLOT_OF = [1, 1, 0, 0, 0, 0, 1, 0]


def slot_of(wi):
    return SLOT_OF[wi] if 0 <= wi < len(SLOT_OF) else 1


DIFFS = [
    ("Kolay", dict(turn=2.4, react=0.75, spread=3.5, speed=0.75, dmg=0.7, head=0.05, lead=0.1)),
    ("Orta", dict(turn=3.8, react=0.45, spread=2.2, speed=0.88, dmg=0.85, head=0.12, lead=0.3)),
    ("Zor", dict(turn=6.0, react=0.28, spread=1.3, speed=1.0, dmg=1.0, head=0.25, lead=0.6)),
    ("Acımasız", dict(turn=9.0, react=0.14, spread=0.6, speed=1.1, dmg=1.1, head=0.4, lead=1.0)),
]
