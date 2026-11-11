# -*- coding: utf-8 -*-
"""Kalici oyuncu verisi: ruh puani (souls), MVP, karakter, bicak ve crosshair."""
import json
import os

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playerdata.json")

_DEFAULT = {
    "souls": 500,
    "matches": 0,
    "mvps": 0,
    "character": "hex",
    "knives": ["knife"],
    "knife": "knife",
    "crosshair": 2,
}

_data = None


def _load():
    global _data
    if _data is not None:
        return
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _data = dict(_DEFAULT)
        _data.update(raw if isinstance(raw, dict) else {})
    except Exception:
        _data = dict(_DEFAULT)
        save()


def data():
    _load()
    return _data


def save():
    _load()
    try:
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def souls():
    return int(data().get("souls", 0))


def spend(amount):
    d = data()
    if int(d.get("souls", 0)) < amount:
        return False
    d["souls"] = int(d.get("souls", 0)) - amount
    save()
    return True


def award_match(fs, player, player_won):
    d = data()
    mvp = max(fs, key=lambda f: (f.wins, f.kills, -f.deaths))
    earned = 20 + int(player.kills) * 3 + (30 if player_won else 0) + (60 if mvp is player else 0)
    d["souls"] = int(d.get("souls", 0)) + earned
    d["matches"] = int(d.get("matches", 0)) + 1
    if mvp is player:
        d["mvps"] = int(d.get("mvps", 0)) + 1
    save()
    return earned, mvp
