# -*- coding: utf-8 -*-
"""Karakter sinifi, yetenek tanimlari ve karakter listesi."""
from config import C, CYAN


class Skill:
    def __init__(self, key, name, kind, cd=0.0):
        self.key = key
        self.name = name
        self.kind = kind
        self.cd = cd


class Character:
    def __init__(self, cid, name, title, color, x, c, v, g):
        self.cid = cid
        self.name = name
        self.title = title
        self.color = color
        self.x = x
        self.c = c
        self.v = v
        self.g = g


CHARACTERS = [
    Character("hex", "HEX", "Dijital Duellocu", CYAN,
              Skill("X", "Sifir-Bir Dalgasi", "wave"),
              Skill("C", "Ruh Hirsizi", "soul"),
              Skill("V", "Kuantum Atilis", "dash"),
              Skill("G", "Sistem Cokusu", "ult_slow")),
    Character("zephyr", "ZEPHYR", "Ruzgar Ustasi", C(120, 230, 255),
              Skill("X", "Kasirga", "wave"),
              Skill("C", "Yukselis", "updraft", 7.0),
              Skill("V", "Ruzgar Atilisi", "dash"),
              Skill("G", "Firtina", "ult_wind")),
    Character("nyx", "NYX", "Golge Avcisi", C(170, 120, 255),
              Skill("X", "Golge Ok", "wave"),
              Skill("C", "Sise Karis", "ghost_cd", 16.0),
              Skill("V", "Golge Adimi", "dash"),
              Skill("G", "Perde", "ult_stealth")),
    Character("titan", "TITAN", "Kalkan Bekcisi", C(255, 180, 80),
              Skill("X", "Sismik Yumruk", "wave"),
              Skill("C", "Kalkan", "shield", 20.0),
              Skill("V", "Omuz Darbesi", "dash"),
              Skill("G", "Kale", "ult_tank")),
    Character("volt", "VOLT", "Akrobasi", C(255, 220, 90),
              Skill("X", "Zincir Carpma", "wave"),
              Skill("C", "Asiri Yuk", "overload", 14.0),
              Skill("V", "Surge", "dash"),
              Skill("G", "Firtina Hatti", "ult_storm")),
]


def get(i):
    return CHARACTERS[i % len(CHARACTERS)]


def index_of(cid):
    for i, c in enumerate(CHARACTERS):
        if c.cid == cid:
            return i
    return 0
