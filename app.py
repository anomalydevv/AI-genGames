# -*- coding: utf-8 -*-
"""Oyun dongusu ve baslatma (pencere, kaynaklar, ekran yonlendirmesi)."""
from pyray import *

import hud
import icons
import playerdata
import render
from config import C, SH, SW, cfg
from match import update_play
from state import g


def main():
    set_config_flags(FLAG_VSYNC_HINT)
    init_window(SW, SH, "HEX ARENA")
    set_target_fps(120)
    set_exit_key(0)
    render.init_gfx()
    try:
        icons.init()
    except Exception:
        pass
    pd = playerdata.data()
    cfg["crosshair"] = int(pd.get("crosshair", 2)) % 3
    g.quit = False

    while not window_should_close() and not g.quit:
        if is_key_pressed(KEY_F11) or (is_key_down(KEY_LEFT_ALT) and is_key_pressed(KEY_ENTER)):
            toggle_fullscreen()
        dt = min(get_frame_time(), 0.05)
        st = g.state
        if st == "play":
            update_play(dt)
        want_lock = (g.state == "play" and not g.paused and not g.market)
        if want_lock != g.locked:
            if want_lock:
                disable_cursor()
                g.skip_mouse = 3
            else:
                enable_cursor()
            g.locked = want_lock
        render.render_scene()
        begin_drawing()
        clear_background(BLACK)
        render.draw_post()
        begin_mode_2d(render.ui_camera())
        if st == "main":
            draw_rectangle(0, 0, SW, SH, C(0, 0, 0, 90))
            hud.screen_main()
        elif st == "char":
            hud.screen_char()
        elif st == "setup":
            draw_rectangle(0, 0, SW, SH, C(0, 0, 0, 110))
            hud.screen_setup()
        elif st == "settings":
            draw_rectangle(0, 0, SW, SH, C(0, 0, 0, 110))
            hud.screen_settings()
        elif st == "shop":
            draw_rectangle(0, 0, SW, SH, C(0, 0, 0, 110))
            hud.screen_shop()
        elif st == "play":
            hud.hud()
            if is_key_down(KEY_TAB):
                hud.scoreboard()
            if g.market:
                hud.market_ui()
            elif g.paused:
                hud.pause_ui()
        elif st == "end":
            hud.screen_end()
        end_mode_2d()
        end_drawing()
        if st != "setup" and g.edit != -1 and g.state != "setup":
            g.edit = -1
    close_window()
