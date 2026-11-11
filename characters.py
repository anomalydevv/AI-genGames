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
              Skill("X", "Ruzgar Dalgasi", "wave"),
              Skill("C", "Yukselis", "updraft", 7.0),
              Skill("V", "Ruzgar Atilisi", "dash"),
              Skill("G", "Firtina", "ult_wind")),
    Character("nyx", "NYX", "Golge Avcisi", C(170, 120, 255),
              Skill("X", "Golge Dalgasi", "wave"),
              Skill("C", "Sise Karis", "ghost_cd", 16.0),
              Skill("V", "Golge Atilisi", "dash"),
              Skill("G", "Kabuk", "ult_stealth")),
    Character("titan", "TITAN", "Kalkan Bekcisi", C(255, 180, 80),
              Skill("X", "Sok Dalgasi", "wave"),
              Skill("C", "Kalkan", "shield", 20.0),
              Skill("V", "Agir Atilis", "dash"),
              Skill("G", "Kale", "ult_tank")),
]


def get(i):
    return CHARACTERS[i % len(CHARACTERS)]


def index_of(cid):
    for i, c in enumerate(CHARACTERS):
        if c.cid == cid:
            return i
    return 0
