#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORMAN  -  PS1 tarzı Slenderman korku oyunu   (pyray / raylib + GLSL shader)

Kurulum :  pip install raylib
Çalıştır:  python orman_slender.py

Kontroller:  WASD yürü | SHIFT koş | Fare bak | F fener | E kağıt topla
             SPACE giriş sinematiğini atla | R yeniden başla | F11 tam ekran | ESC çık

Hikaye: Gün batımında ormana geldiniz, araba bozuldu, tamir edemediniz.
        Yardım edecek birini ararken ağaçlardaki 8 kağıdı toplayın... O sizi izliyor.
"""
import math
import os
import random
import tempfile
import wave
from array import array

import pyray as rl
from pyray import Vector2, Vector3, Color, Camera3D, Rectangle
try:
    from pyray import ffi
except ImportError:
    from raylib import ffi

W, H = 1280, 720          # pencere
RW, RH = 320, 180         # PS1 benzeri düşük çözünürlük (render texture)
K = (RH / 2) / math.tan(math.radians(35))   # piksel / radyan (fov 70)
WORLD = 85
TR = str.maketrans("ğĞıİşŞçÇöÖüÜâÂîÎ", "gGiIsScCoOuUaAiI")   # varsayılan font ASCII/Latin


# ----------------------------------------------------------------------------- yardımcılar
def clamp(v, a, b):
    return a if v < a else b if v > b else v


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(a, b, x):
    t = clamp((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def wrap(a):
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def mix3(a, b, t):
    return (lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t))


def ramp(s, d):
    return mix3(s[0], s[1], d * 2) if d < 0.5 else mix3(s[1], s[2], (d - 0.5) * 2)


def col(c, a=255):
    return Color(int(clamp(c[0], 0, 255)), int(clamp(c[1], 0, 255)), int(clamp(c[2], 0, 255)), int(a))


def set_uniform(sh, loc, v):
    if loc < 0:
        return
    if isinstance(v, (int, float)):
        rl.set_shader_value(sh, loc, ffi.new("float *", float(v)), rl.SHADER_UNIFORM_FLOAT)
    elif len(v) == 2:
        rl.set_shader_value(sh, loc, ffi.new("float[]", [float(x) for x in v]), rl.SHADER_UNIFORM_VEC2)
    else:
        rl.set_shader_value(sh, loc, ffi.new("float[]", [float(x) for x in v]), rl.SHADER_UNIFORM_VEC3)


# ----------------------------------------------------------------------------- shaderlar
VS_WORLD = """#version 330
in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec4 vertexColor;
uniform mat4 mvp;
uniform vec2 res;
out vec4 fragColor;
out float depth;
out vec3 wpos;
void main(){
    vec4 p = mvp*vec4(vertexPosition,1.0);
    depth = p.w;
    wpos = vertexPosition;
    if (p.w > 0.1){                       // PS1 vertex snapping (titreyen köşeler)
        vec2 g = res*0.32;
        vec2 n = p.xy/p.w;
        n = floor(n*g+0.5)/g;
        p.xy = n*p.w;
    }
    fragColor = vertexColor;
    gl_Position = p;
}
"""

FS_WORLD = """#version 330
in vec4 fragColor;
in float depth;
in vec3 wpos;
uniform vec2 res;
uniform vec3 fogColor;
uniform float fogNear;
uniform float fogFar;
uniform vec3 ambient;
uniform float torch;
uniform vec3 camPos;
out vec4 finalColor;
void main(){
    vec3 cx = cross(dFdx(wpos), dFdy(wpos));
    float ln = length(cx);
    vec3 n = ln > 1e-8 ? cx/ln : vec3(0.0,1.0,0.0);
    if (dot(n, camPos-wpos) < 0.0) n = -n;
    float sh = 0.55 + 0.45*clamp(dot(n, normalize(vec3(-0.35,0.85,0.4))),0.0,1.0);

    vec2 p = (gl_FragCoord.xy/res - 0.5)*vec2(res.x/res.y,1.0);
    float cone = smoothstep(0.55,0.03,length(p));
    float reach = clamp(1.0-depth/30.0,0.0,1.0);
    float beam = torch*cone*reach;

    float em = fragColor.a < 0.99 ? 1.0 : 0.0;      // alpha<1 => kendi ışığını yayar
    vec3 c = fragColor.rgb*sh*(ambient + vec3(1.0,0.95,0.8)*beam*1.3);
    c = mix(c, fragColor.rgb, em);
    float f = clamp((depth-fogNear)/(fogFar-fogNear),0.0,1.0);
    f *= 1.0 - beam*0.45;
    c = mix(c, fogColor, f);
    finalColor = vec4(c,1.0);
}
"""

VS_POST = """#version 330
in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec4 vertexColor;
uniform mat4 mvp;
out vec2 fragTexCoord;
out vec4 fragColor;
void main(){
    fragTexCoord = vertexTexCoord;
    fragColor = vertexColor;
    gl_Position = mvp*vec4(vertexPosition,1.0);
}
"""

FS_POST = """#version 330
in vec2 fragTexCoord;
uniform sampler2D texture0;
uniform vec2 res;
uniform float time;
uniform float fear;
out vec4 finalColor;
float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)))*43758.5453); }
void main(){
    vec2 uv = fragTexCoord;
    float g = clamp(fear,0.0,1.5);
    float row = floor(uv.y*res.y/3.0);
    float tt = floor(time*14.0);
    float band = step(1.0 - g*0.18, h(vec2(row,tt)));
    uv.x += band*(h(vec2(tt,row))-0.5)*0.12*g;
    uv += (vec2(h(vec2(tt,1.0)),h(vec2(tt,2.0)))-0.5)*0.01*g*g;
    float ca = 0.002 + 0.01*g*g;
    vec3 c;
    c.r = texture(texture0, uv+vec2(ca,0.0)).r;
    c.g = texture(texture0, uv).g;
    c.b = texture(texture0, uv-vec2(ca,0.0)).b;
    vec2 px = floor(uv*res);
    float n = h(px + floor(time*24.0)*7.13);
    c = mix(c, vec3(n), 0.035 + g*g*0.45);                 // film greni / statik
    float bayer[16] = float[16](0.,8.,2.,10.,12.,4.,14.,6.,3.,11.,1.,9.,15.,7.,13.,5.);
    int bi = int(mod(px.x,4.0)) + 4*int(mod(px.y,4.0));
    float dth = bayer[bi]/16.0 - 0.5;
    c = floor(c*31.0 + dth + 0.5)/31.0;                     // 15-bit renk + dither (PS1)
    vec2 q = fragTexCoord-0.5;
    float vig = 1.0 - dot(q,q)*1.6*(1.0+g);
    c *= clamp(vig,0.0,1.0);
    float l = dot(c, vec3(0.3,0.59,0.11));
    c = mix(c, vec3(l), g*0.5);
    finalColor = vec4(c,1.0);
}
"""


# ----------------------------------------------------------------------------- ses (kodla üretilir)
SR = 22050


def _save(path, data):
    a = array("h", (int(clamp(x, -1, 1) * 30000) for x in data))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(a.tobytes())


def make_sounds():
    d = tempfile.mkdtemp(prefix="orman_")
    R = random.random
    TAU = 2 * math.pi

    def noise_lp(n, k):
        y, o = 0.0, []
        for _ in range(n):
            y += (R() * 2 - 1 - y) * k
            o.append(y)
        return o

    data = {}
    n = SR * 6                                   # rüzgar + alçak drone (döngü)
    wind = noise_lp(n, 0.015)
    amb = []
    for i in range(n):
        t = i / SR
        lfo = 0.6 + 0.4 * math.sin(TAU * t / 6)
        v = 0.22 * (math.sin(TAU * 55 * t) + 0.8 * math.sin(TAU * 58 * t) + 0.4 * math.sin(TAU * 110.5 * t)) * lfo
        v += wind[i] * 3.2 * (0.6 + 0.4 * math.sin(TAU * t / 3 + 1))
        amb.append(v)
    data["amb"] = amb

    heart = [0.0] * SR                           # kalp atışı
    for s0, a in ((0, 1.0), (int(0.3 * SR), 0.7)):
        for j in range(int(0.2 * SR)):
            tt = j / SR
            if s0 + j < SR:
                heart[s0 + j] += a * math.sin(TAU * (70 - 120 * tt) * tt) * math.exp(-tt * 18)
    data["heart"] = heart

    data["stat"] = [(R() * 2 - 1) * 0.5 for _ in range(int(0.5 * SR))]     # statik

    ph, sc = 0.0, []                             # çığlık
    for i in range(int(1.8 * SR)):
        t = i / SR
        ph += (600 + 700 * math.sin(TAU * 6 * t) + 1000 * t) / SR
        saw = 2 * (ph % 1.0) - 1
        v = math.tanh(2.5 * (saw * 0.8 + (R() * 2 - 1) * 0.5))
        sc.append(v * min(1, t * 40) * clamp(1 - (t - 1.2) / 0.6, 0, 1))
    data["scream"] = sc

    ph, st = 0.0, []                             # Slender göründüğünde keman gibi iniş
    for i in range(int(1.6 * SR)):
        t = i / SR
        ph += (420 - 250 * t / 1.6 + 6 * math.sin(TAU * 5 * t)) / SR
        v = (math.sin(TAU * ph) + 0.5 * math.sin(TAU * 2 * ph) + 0.35 * math.sin(TAU * 3 * ph)) * 0.4
        st.append(v * min(1, t * 8) * math.exp(-t * 1.6))
    data["sting"] = st

    pk = []                                      # kağıt alma
    for i in range(int(0.4 * SR)):
        t = i / SR
        f = 520 if t < 0.12 else 780
        pk.append(0.5 * math.sin(TAU * f * t) * math.exp(-(t % 0.12) * 14) * (1 if t < 0.35 else 0))
    data["pick"] = pk

    ns = noise_lp(int(0.2 * SR), 0.2)            # adım
    data["step"] = [ns[i] * 3 * math.exp(-(i / SR) * 28) for i in range(len(ns))]

    ph, z, eng = 0.0, 0.0, []                    # bozulan motor
    for i in range(int(3.6 * SR)):
        t = i / SR
        ph += (26 * (1 - t / 3.6) ** 1.5 + 2.5) / SR
        gate = 1.0 if (ph % 1.0) < 0.45 else 0.15
        if t > 2.6 and R() < 0.5:
            gate = 0.0
        z += (R() * 2 - 1 - z) * 0.1
        eng.append((0.5 * math.sin(TAU * 70 * t) + z * 1.5) * gate * clamp(1 - (t - 3.0) / 0.6, 0, 1) * 0.8)
    data["eng"] = eng

    snd = {}
    for name, samples in data.items():
        p = os.path.join(d, name + ".wav")
        _save(p, samples)
        snd[name] = rl.load_sound(p)
    return snd


def sfx(snd, name, vol=1.0, pitch=1.0):
    s = snd.get(name)
    if s is not None:
        rl.set_sound_volume(s, vol)
        rl.set_sound_pitch(s, pitch)
        rl.play_sound(s)


def loop(snd, name, vol, pitch=1.0):
    s = snd.get(name)
    if s is None:
        return
    rl.set_sound_volume(s, clamp(vol, 0, 1))
    rl.set_sound_pitch(s, pitch)
    if not rl.is_sound_playing(s):
        rl.play_sound(s)


def stop(snd, name):
    s = snd.get(name)
    if s is not None and rl.is_sound_playing(s):
        rl.stop_sound(s)


# ----------------------------------------------------------------------------- dünya
def gkey(x, z):
    return (int(math.floor(x / 10)), int(math.floor(z / 10)))


def gen_world():
    trees, grid = [], {}

    def near(x, z, r2):
        kx, kz = gkey(x, z)
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for t in grid.get((kx + i, kz + j), ()):
                    if (t[0] - x) ** 2 + (t[1] - z) ** 2 < r2:
                        return True
        return False

    for _ in range(3600):
        x, z = random.uniform(-WORLD, WORLD), random.uniform(-WORLD, WORLD)
        if abs(x) < 5.5 and z > -36:               # yol koridoru
            continue
        if math.hypot(x - 4, z - 14) < 4.5 or near(x, z, 7.5):
            continue
        v = random.uniform(0.75, 1.2)
        bare = random.random() < 0.22
        ct = col((78 * v, 72 * v, 66 * v)) if bare else col((70 * v, 50 * v, 36 * v))
        t = (x, z, random.uniform(6, 11), random.uniform(0.18, 0.3), random.uniform(1.6, 2.4), bare,
             ct, col((20 * v, 50 * v, 26 * v)), col((26 * v, 60 * v, 30 * v)))
        trees.append(t)
        grid.setdefault(gkey(x, z), []).append(t)
    return trees, grid


TREES, GRID = gen_world()
BLOCK = [(0.0, 8.8, 1.5), (0.0, 10.0, 1.5), (0.0, 11.2, 1.5)]      # araba çarpışması
STARS = [(random.uniform(-math.pi, math.pi), random.uniform(0.05, 1.2), random.randint(110, 255)) for _ in range(130)]

PAGE_TEXTS = [
    ["Araba neden durdu sanıyorsun?", "Orman seni buraya çağırdı."],
    ["Bu kağıtları ben astım.", "Onu görme. Sakın bakma."],
    ["Arkana bakma."],
    ["Yardım arayan herkesi", "önce o buldu."],
    ["O sessizken yaklaşır.", "Bakarsan durur. Bakmazsan yürür."],
    ["Fener onu uzak tutmaz."],
    ["O her ağacın arkasında."],
    ["SON SAYFA", "Hazır mısın? O hazır."],
]
INTRO_SUBS = [
    (0.6, 4.0, "Gün batımı... bu orman yolu hiç bitmiyor."),
    (4.2, 7.0, "Telefon çekmiyor. Haritada da yol görünmüyor."),
    (7.3, 10.0, "Motor tuhaf sesler çıkarıyor..."),
    (10.4, 13.2, "Durdu. Hayır, hayır... şimdi olmaz!"),
    (13.6, 17.0, "Tamir edemiyoruz. Güneş batıyor, vakit geçiyor."),
    (17.4, 20.8, "Ormanın içinde bir ışık gördüm. Biri olmalı."),
    (21.0, 24.0, "Yardım bulmalıyız. Hava tamamen kararmadan..."),
]
END_SUBS = [
    (0.5, 3.5, "Sekizinci kağıt..."),
    (3.8, 7.0, "Orman bir anda sessizleşti."),
    (7.3, 10.5, "Işık yok. Telefon yok. Yardım yok."),
    (10.8, 14.0, "O hep buradaydı. Seni bekliyordu."),
    (14.3, 17.0, "Yardım arıyordun... sonunda bulundun."),
]


def make_pages():
    cand = [t for t in TREES if 24 < math.hypot(t[0], t[1] - 10) < 75]
    random.shuffle(cand)
    spacing, chosen = 26.0, []
    while len(chosen) < 8:
        chosen = []
        for t in cand:
            if all(math.hypot(t[0] - c[0], t[1] - c[1]) > spacing for c in chosen):
                chosen.append(t)
                if len(chosen) == 8:
                    break
        spacing -= 2
    pages = []
    for t in chosen:
        a = random.uniform(0, 2 * math.pi)
        pages.append(dict(x=t[0] + math.cos(a) * (t[3] + 0.04), z=t[1] + math.sin(a) * (t[3] + 0.04),
                          rot=math.degrees(math.pi / 2 - a), got=False))
    return pages


def collide(x, z):
    kx, kz = gkey(x, z)
    lst = []
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for t in GRID.get((kx + i, kz + j), ()):
                lst.append((t[0], t[1], t[3] + 0.5))
    lst.extend((bx, bz, br + 0.5) for bx, bz, br in BLOCK)
    for bx, bz, m in lst:
        dx, dz = x - bx, z - bz
        d2 = dx * dx + dz * dz
        if d2 < m * m:
            d = math.sqrt(d2) or 0.001
            x, z = bx + dx / d * m, bz + dz / d * m
    return clamp(x, -WORLD + 3, WORLD - 3), clamp(z, -WORLD + 3, WORLD - 3)


# ----------------------------------------------------------------------------- çizim parçaları
V3 = Vector3
PAGE_C = Color(240, 238, 225, 250)
INK_C = Color(8, 8, 8, 255)
BLACK_C = Color(10, 10, 12, 255)
SUIT_C = Color(14, 14, 18, 255)
WHITE_C = Color(215, 215, 210, 255)
RED_C = Color(150, 10, 10, 255)


def draw_trees(px, pz, fx, fz, far):
    kx, kz = gkey(px, pz)
    R = int(far // 10) + 1
    far2 = far * far
    for i in range(-R, R + 1):
        for j in range(-R, R + 1):
            for t in GRID.get((kx + i, kz + j), ()):
                dx, dz = t[0] - px, t[1] - pz
                d2 = dx * dx + dz * dz
                if d2 > far2:
                    continue
                if d2 > 25 and dx * fx + dz * fz < -0.35 * math.sqrt(d2):
                    continue
                x, z, h = t[0], t[1], t[2]
                if t[5]:                                   # çıplak, ölü ağaç
                    rl.draw_cylinder(V3(x, 0, z), t[3] * 0.6, t[3], h * 0.8, 5, t[6])
                    a = x * 7.3
                    for k in range(2):
                        b = a + k * 2.4
                        rl.draw_cylinder_ex(V3(x, h * (0.5 + 0.1 * k), z),
                                            V3(x + 1.3 * math.cos(b), h * (0.5 + 0.1 * k) + 1.1, z + 1.3 * math.sin(b)),
                                            0.07, 0.02, 3, t[6])
                else:
                    rl.draw_cylinder(V3(x, 0, z), t[3] * 0.7, t[3], h * 0.55, 5, t[6])
                    rl.draw_cylinder(V3(x, h * 0.25, z), 0.0, t[4], h * 0.45, 7, t[7])
                    rl.draw_cylinder(V3(x, h * 0.5, z), 0.0, t[4] * 0.68, h * 0.4, 7, t[8])


def draw_ground(px, pz):
    T = 12
    gx, gz = int(math.floor(px / T)), int(math.floor(pz / T))
    for i in range(-4, 5):
        for j in range(-4, 5):
            ix, iz = gx + i, gz + j
            v = 0.8 + 0.4 * (((ix * 73856093) ^ (iz * 19349663)) & 255) / 255
            rl.draw_plane(V3(ix * T + T / 2, 0, iz * T + T / 2), Vector2(T, T),
                          Color(int(34 * v), int(44 * v), int(26 * v), 255))
    rl.draw_cube(V3(0, 0.015, 35), 6.5, 0.03, 130, Color(52, 50, 48, 255))
    dash = Color(200, 190, 120, 255)
    for z in range(-28, 100, 6):
        rl.draw_cube(V3(0, 0.035, z), 0.2, 0.02, 2.2, dash)


def draw_car(z, tm, stalled):
    rl.rl_push_matrix()
    rl.rl_translatef(0.0, 0.0, z)
    body = Color(135, 32, 28, 255)
    rl.draw_cube(V3(0, 0.75, 0), 1.9, 0.7, 4.3, body)
    rl.draw_cube(V3(0, 1.35, 0.35), 1.7, 0.6, 2.2, body)
    rl.draw_cube(V3(0, 1.4, 0.35), 1.76, 0.34, 1.9, Color(20, 26, 32, 255))
    for sx in (-1, 1):
        for sz in (-1.35, 1.35):
            rl.rl_push_matrix()
            rl.rl_translatef(sx * 1.0, 0.4, sz)
            rl.rl_rotatef(90, 0, 0, 1)
            rl.draw_cylinder(V3(0, -0.15, 0), 0.4, 0.4, 0.3, 8, Color(14, 14, 14, 255))
            rl.rl_pop_matrix()
    lamp = Color(255, 240, 150, 250)
    tail = Color(210, 20, 20, 250)
    on = (not stalled) or tm < 0.0
    for sx in (-0.65, 0.65):
        rl.draw_cube(V3(sx, 0.85, -2.17), 0.4, 0.22, 0.05, lamp if on else Color(120, 115, 80, 255))
        rl.draw_cube(V3(sx, 0.85, 2.17), 0.4, 0.2, 0.05, tail)
    if stalled and int(tm * 1.6) % 2 == 0:                  # tehlike lambaları
        hz = Color(255, 150, 20, 250)
        for sx in (-0.9, 0.9):
            for sz in (-2.1, 2.1):
                rl.draw_cube(V3(sx, 0.95, sz), 0.25, 0.2, 0.2, hz)
    rl.rl_pop_matrix()


def draw_page(p):
    rl.rl_push_matrix()
    rl.rl_translatef(p["x"], 1.5, p["z"])
    rl.rl_rotatef(p["rot"], 0, 1, 0)
    rl.draw_cube(V3(0, 0, 0), 0.55, 0.75, 0.03, PAGE_C)
    for k in range(4):
        rl.draw_cube(V3(0, 0.25 - k * 0.14, 0.02), 0.4 if k < 3 else 0.2, 0.03, 0.01, INK_C)
    rl.rl_pop_matrix()


def draw_slender(sx, sz, px, pz, tm, fear):
    ang = math.degrees(math.atan2(px - sx, pz - sz))
    rl.rl_push_matrix()
    rl.rl_translatef(sx, 0.0, sz)
    rl.rl_rotatef(ang, 0, 1, 0)
    sw = math.sin(tm * 1.7)
    rl.draw_cube(V3(-0.17, 0.8, 0), 0.26, 1.6, 0.3, SUIT_C)                    # bacaklar
    rl.draw_cube(V3(0.17, 0.8, 0), 0.26, 1.6, 0.3, SUIT_C)
    rl.draw_cube(V3(0, 2.15, 0), 0.74, 1.35, 0.36, SUIT_C)                     # gövde
    rl.draw_cube(V3(0, 2.3, 0.19), 0.2, 1.0, 0.02, WHITE_C)                    # gömlek
    rl.draw_cube(V3(0, 2.2, 0.205), 0.1, 0.8, 0.02, RED_C)                     # kırmızı kravat
    rl.draw_cube(V3(0, 2.95, 0), 0.16, 0.2, 0.16, WHITE_C)                     # boyun
    rl.draw_cube(V3(0, 3.2, 0), 0.38, 0.52, 0.38, WHITE_C)                     # yüzsüz kafa
    for sx_ in (-1, 1):                                                         # upuzun kollar
        rl.rl_push_matrix()
        rl.rl_translatef(sx_ * 0.46, 2.7, 0)
        rl.rl_rotatef(sx_ * (4 + 3 * sw), 0, 0, 1)
        rl.draw_cube(V3(sx_ * 0.04, -1.0, 0), 0.12, 2.1, 0.12, SUIT_C)
        rl.draw_cube(V3(sx_ * 0.04, -2.1, 0), 0.1, 0.35, 0.1, WHITE_C)
        rl.rl_pop_matrix()
    for k in range(4):                                                          # sırttaki dokunaçlar
        a = (k - 1.5) * 0.7
        w = math.sin(tm * 2.0 + k) * (0.25 + fear * 0.5)
        rl.draw_cylinder_ex(V3(0, 2.6, -0.2), V3(math.sin(a) * 1.8 + w, 3.3 + 0.3 * math.cos(tm + k), -1.5),
                            0.06, 0.015, 3, SUIT_C)
    rl.rl_pop_matrix()


# ----------------------------------------------------------------------------- oyun
class Game:
    def __init__(self, snd):
        self.snd = snd
        self.reset(False)

    def reset(self, skip_intro):
        self.state = "intro"
        self.t = 0.0
        self.time = 0.0
        self.px, self.pz = 4.0, 14.0
        self.yaw = math.pi / 2
        self.pitch = 0.0
        self.stamina = 1.0
        self.bob = 0.0
        self.last_step = 0
        self.dusk = 0.0
        self.torch_on = True
        self.torch = 1.0
        self.pages = make_pages()
        self.got = 0
        self.note, self.note_t = [], 0.0
        self.prompt = None
        self.fear = 0.0
        self.vfear = 0.0
        self.sl = dict(on=False, x=0.0, z=0.0, tp=0.0, seen=False)
        self.sl_wait = 45.0
        self.fade = 0.0
        self.smoke = []
        self.smoke_acc = 0.0
        self.car_z = 70.0
        self.play_t = 0.0
        self.eng_played = False
        self.screamed = False
        self.cam_pos = V3(4, 1.7, 14)
        self.cam_tgt = V3(5, 1.7, 14)
        for n in ("amb", "heart", "stat"):
            stop(self.snd, n)
        if skip_intro:
            self.begin_play()

    def begin_play(self):
        self.state = "play"
        self.car_z = 10.0
        self.dusk = max(self.dusk, 0.3)
        self.fade = 1.0
        self.play_t = 0.0

    # ------------------------------------------------------------------ güncelleme
    def update(self, dt):
        self.time += dt
        self.t += dt
        if rl.is_key_pressed(rl.KEY_F11):
            rl.toggle_fullscreen()
        st = self.state
        if st == "intro":
            self.up_intro(dt)
        elif st == "play":
            self.up_play(dt)
        elif st == "dead":
            self.up_dead(dt)
        elif st == "ending":
            self.up_ending(dt)
        elif st == "end":
            if rl.is_key_pressed(rl.KEY_R):
                self.reset(True)
        if st in ("play", "dead"):
            self.fade = max(0.0, self.fade - dt * 0.8)
        # duman
        stalled = (st == "intro" and self.t > 7.6) or st in ("play", "dead", "ending")
        if stalled:
            self.smoke_acc += dt * (10 if st == "intro" else 3)
            while self.smoke_acc > 1 and len(self.smoke) < 60:
                self.smoke_acc -= 1
                self.smoke.append([random.uniform(-0.3, 0.3), 1.2, self.car_z - 1.9 + random.uniform(-0.2, 0.2), 0.0])
            self.smoke_acc = min(self.smoke_acc, 1.0)
        for p in self.smoke:
            p[3] += dt
            p[1] += dt * 1.1
            p[0] += dt * 0.3
        self.smoke = [p for p in self.smoke if p[3] < 3.2]

    def up_intro(self, dt):
        t = self.t
        if rl.is_key_pressed(rl.KEY_SPACE):
            t = self.t = 24.0
        p = min(t / 10, 1.0)
        self.car_z = 70 - 60 * (1 - (1 - p) ** 2)
        self.dusk = 0.3 * min(t / 24, 1.0)
        if t > 5.8 and not self.eng_played:
            self.eng_played = True
            sfx(self.snd, "eng", 0.8)
        loop(self.snd, "amb", 0.3)
        sm1 = smooth(10, 17, t)
        phi = 0.35 + 2.4 * sm1
        Rr = 7.0 + 5.0 * (1 - smooth(0, 4, t))
        hh = 2.2 - 0.7 * sm1
        pos = V3(math.sin(phi) * Rr, hh, self.car_z + math.cos(phi) * Rr)
        tgt = V3(0.0, 1.0, self.car_z - 1.0)
        if 7 < t < 10.5:
            s = 0.04
            tgt = V3(tgt.x + random.uniform(-s, s), tgt.y + random.uniform(-s, s), tgt.z)
        sm2 = smooth(17, 24, t)
        eye = V3(4.0, 1.7, 14.0)
        look = V3(4.0 + 5, 1.7, 14.0)
        self.cam_pos = V3(lerp(pos.x, eye.x, sm2), lerp(pos.y, eye.y, sm2), lerp(pos.z, eye.z, sm2))
        self.cam_tgt = V3(lerp(tgt.x, look.x, sm2), lerp(tgt.y, look.y, sm2), lerp(tgt.z, look.z, sm2))
        if t >= 24.0:
            self.begin_play()

    def audio_play(self, d):
        on = self.sl["on"]
        prox = clamp(1 - d / 16, 0, 1) if on else 0.0
        loop(self.snd, "amb", 0.55)
        hv = clamp(self.fear * 0.9 + prox * 0.8 - 0.05, 0, 1)
        if hv > 0.05:
            loop(self.snd, "heart", hv, 1 + hv * 0.4)
        else:
            stop(self.snd, "heart")
        sv = clamp(self.fear * 0.8 + prox * 0.3 - 0.1, 0, 1)
        if sv > 0.04:
            loop(self.snd, "stat", sv * 0.7)
        else:
            stop(self.snd, "stat")
        self.vfear = clamp(self.fear + prox * 0.25, 0, 1.4)

    def up_play(self, dt):
        self.play_t += dt
        self.dusk = min(1.0, self.dusk + dt / 90.0)
        md = rl.get_mouse_delta()
        self.yaw += md.x * 0.0022
        self.pitch = clamp(self.pitch - md.y * 0.0022, -1.2, 1.2)
        fx, fz = math.sin(self.yaw), -math.cos(self.yaw)
        rx, rz = -fz, fx
        mx = mz = 0.0
        if rl.is_key_down(rl.KEY_W):
            mx += fx; mz += fz
        if rl.is_key_down(rl.KEY_S):
            mx -= fx; mz -= fz
        if rl.is_key_down(rl.KEY_D):
            mx += rx; mz += rz
        if rl.is_key_down(rl.KEY_A):
            mx -= rx; mz -= rz
        moving = abs(mx) + abs(mz) > 0.01
        run = moving and rl.is_key_down(rl.KEY_LEFT_SHIFT) and self.stamina > 0.05
        speed = 5.4 if run else 3.0
        self.stamina = clamp(self.stamina + (-dt * 0.22 if run else dt * 0.15), 0, 1)
        if moving:
            n = math.hypot(mx, mz)
            self.px, self.pz = collide(self.px + mx / n * speed * dt, self.pz + mz / n * speed * dt)
            self.bob += speed * dt * 2.2
            stp = int(self.bob / math.pi)
            if stp != self.last_step:
                self.last_step = stp
                sfx(self.snd, "step", 0.35, random.uniform(0.8, 1.1))
        # fener
        if rl.is_key_pressed(rl.KEY_F):
            self.torch_on = not self.torch_on
        fl = 1.0
        if self.fear > 0.25 and random.random() < self.fear * 0.25:
            fl = random.uniform(0.0, 0.4)
        self.torch = (1.0 if self.torch_on else 0.0) * fl
        # kağıtlar
        self.prompt = None
        for p in self.pages:
            if p["got"]:
                continue
            dx, dz = p["x"] - self.px, p["z"] - self.pz
            d = math.hypot(dx, dz)
            if d < 3.2 and math.acos(clamp((dx * fx + dz * fz) / (d or 1), -1, 1)) < 0.6:
                self.prompt = p
        if self.prompt and rl.is_key_pressed(rl.KEY_E):
            self.prompt["got"] = True
            self.got += 1
            self.note, self.note_t = PAGE_TEXTS[self.got - 1], 5.0
            sfx(self.snd, "pick", 0.8)
            self.fear += 0.08
            self.sl_wait = min(self.sl_wait, 3.0)
            if self.got >= 8:
                self.begin_ending()
                return
        self.note_t = max(0.0, self.note_t - dt)
        d = self.update_slender(dt, fx, fz)
        self.audio_play(d)
        if self.state != "play":
            return
        by = math.sin(self.bob * 1.0) * 0.05 if moving else 0.0
        pos = V3(self.px, 1.7 + by, self.pz)
        cp = math.cos(self.pitch)
        self.cam_pos = pos
        self.cam_tgt = V3(pos.x + fx * cp, pos.y + math.sin(self.pitch), pos.z + fz * cp)

    def relocate(self, fx, fz):
        s = self.sl
        dist = max(9.0, 32 - self.got * 3.0 + random.uniform(-3, 3))
        base = math.atan2(fz, fx)
        off = random.uniform(-1.05, 1.05) if random.random() < 0.65 else random.uniform(-math.pi, math.pi)
        a = base + off
        s["x"] = clamp(self.px + math.cos(a) * dist, -WORLD + 2, WORLD - 2)
        s["z"] = clamp(self.pz + math.sin(a) * dist, -WORLD + 2, WORLD - 2)
        s["tp"] = max(3.0, 11 - self.got) + random.uniform(0, 3)
        s["seen"] = False

    def update_slender(self, dt, fx, fz):
        s = self.sl
        if not s["on"]:
            self.sl_wait -= dt
            if self.sl_wait <= 0:
                s["on"] = True
                self.relocate(fx, fz)
            self.fear = max(0.0, self.fear - dt * 0.12)
            return 99.0
        dx, dz = s["x"] - self.px, s["z"] - self.pz
        d = math.hypot(dx, dz)
        ang = math.acos(clamp((dx * fx + dz * fz) / (d or 1), -1, 1))
        seen = ang < math.radians(42) and d < 44
        if seen and not s["seen"]:
            sfx(self.snd, "sting", 0.7)
        s["seen"] = seen
        if seen:
            self.fear += dt * (0.10 + max(0.0, 30 - d) / 30 * 0.45 + self.got * 0.025 + (0.3 if d < 9 else 0.0))
        else:
            self.fear = max(0.0, self.fear - dt * 0.12)
            if d > 2.4:
                sp = 1.1 + 0.35 * self.got
                s["x"] -= dx / d * sp * dt
                s["z"] -= dz / d * sp * dt
        s["tp"] -= dt
        if s["tp"] <= 0:
            self.relocate(fx, fz)
        if d < 2.0 or self.fear >= 1.0:
            self.die()
        return d

    def die(self):
        self.state = "dead"
        self.t = 0.0
        fx, fz = math.sin(self.yaw), -math.cos(self.yaw)
        self.sl["on"] = True
        self.sl["x"], self.sl["z"] = self.px + fx * 1.9, self.pz + fz * 1.9
        self.fear = 1.5
        self.vfear = 1.5
        for n in ("amb", "heart", "stat"):
            stop(self.snd, n)
        sfx(self.snd, "scream", 1.0)

    def up_dead(self, dt):
        t = self.t
        sh = 0.08 * max(0.0, 1 - t / 2.5)
        self.cam_pos = V3(self.px, 1.7, self.pz)
        self.cam_tgt = V3(self.sl["x"] + random.uniform(-sh, sh), 2.9 + random.uniform(-sh, sh), self.sl["z"])
        self.torch = 0.5 if random.random() < 0.5 else 0.0
        self.vfear = 1.5
        if t > 2.8 and rl.is_key_pressed(rl.KEY_R):
            self.reset(True)

    def begin_ending(self):
        self.state = "ending"
        self.t = 0.0
        self.dusk = 1.0
        self.sl["on"] = True
        self.yaw0 = self.yaw
        for n in ("amb", "heart", "stat"):
            stop(self.snd, n)
        loop(self.snd, "heart", 0.7)

    def up_ending(self, dt):
        t = self.t
        fx, fz = math.sin(self.yaw0), -math.cos(self.yaw0)
        d = 16 - 12.8 * smooth(3, 15, t)
        self.sl["x"], self.sl["z"] = self.px + fx * d, self.pz + fz * d
        self.fear = clamp(t / 16, 0, 1) * 0.9
        self.vfear = self.fear + smooth(15, 19, t) * 0.6
        self.torch = 1.0 if random.random() > 0.25 * self.fear * 2 else random.uniform(0.0, 0.3)
        pitch = 0.55 * smooth(12, 16, t)
        sh = 0.02 + 0.05 * smooth(12, 19, t)
        cp = math.cos(pitch)
        pos = V3(self.px, 1.7, self.pz)
        self.cam_pos = pos
        self.cam_tgt = V3(pos.x + fx * cp + random.uniform(-sh, sh), pos.y + math.sin(pitch) + random.uniform(-sh, sh),
                          pos.z + fz * cp)
        if t > 16.3 and not self.screamed:
            self.screamed = True
            stop(self.snd, "heart")
            sfx(self.snd, "scream", 1.0)
        if t >= 19.5:
            self.state = "end"
            self.t = 0.0
            self.vfear = 0.0

    # ------------------------------------------------------------------ çizim
    def txt(self, s, x, y, size=10, c=(235, 235, 235), a=255, center=False):
        s = s.translate(TR)
        if center:
            x = x - rl.measure_text(s, size) // 2
        rl.draw_text(s, int(x) + 1, int(y) + 1, size, Color(0, 0, 0, int(a)))
        rl.draw_text(s, int(x), int(y), size, col(c, a))

    def hud(self):
        st, t = self.state, self.t
        if st == "end":
            a = int(255 * clamp(t / 2, 0, 1))
            self.txt("SON", RW // 2, 44, 30, (220, 220, 220), a, True)
            self.txt("Araba hâlâ yolda duruyor. Boş.", RW // 2, 90, 10, (200, 200, 200), a, True)
            self.txt("Yardım gelmedi. Kimse aramadı.", RW // 2, 104, 10, (200, 200, 200), a, True)
            if t > 3:
                self.txt("[R] Tekrar oyna     [ESC] Çıkış", RW // 2, 150, 10, (150, 150, 150), a, True)
            return
        if st in ("intro", "ending"):
            rl.draw_rectangle(0, 0, RW, 18, rl.BLACK)
            rl.draw_rectangle(0, RH - 18, RW, 18, rl.BLACK)
        if st == "intro":
            for a, b, s in INTRO_SUBS:
                if a <= t < b:
                    self.txt(s, RW // 2, RH - 36, 10, (235, 235, 235), 255, True)
            if t < 4:
                al = int(255 * clamp(1 - (t - 2.5) / 1.5, 0, 1))
                self.txt("O R M A N", RW // 2, 62, 30, (200, 30, 30), al, True)
                self.txt("SPACE: atla", RW // 2, 100, 10, (140, 140, 140), al, True)
            al = 0
            if t < 1.2:
                al = 255 * (1 - t / 1.2)
            elif t > 23:
                al = 255 * clamp(t - 23, 0, 1)
            if al > 0:
                rl.draw_rectangle(0, 0, RW, RH, Color(0, 0, 0, int(al)))
        elif st == "play":
            rl.draw_rectangle(RW // 2 - 1, RH // 2 - 1, 2, 2, Color(255, 255, 255, 110))
            self.txt("KAĞIT %d/8" % self.got, 6, 6)
            rl.draw_rectangle(6, RH - 12, 40, 3, Color(40, 40, 40, 255))
            rl.draw_rectangle(6, RH - 12, int(40 * self.stamina), 3, Color(200, 200, 200, 255))
            if self.play_t < 14:
                a = int(255 * clamp((14 - self.play_t) / 3, 0, 1))
                self.txt("Yardım edecek birini bul.", RW // 2, RH - 52, 10, (255, 220, 160), a, True)
                self.txt("Ağaçlardaki kağıtlar sana yol gösterecek.", RW // 2, RH - 40, 10, (255, 220, 160), a, True)
                self.txt("WASD yürü  SHIFT koş  F fener  E topla", RW // 2, RH - 24, 10, (170, 170, 170), a, True)
            if self.prompt:
                self.txt("[E] Kağıdı topla", RW // 2, RH // 2 + 14, 10, (255, 255, 255), 255, True)
            if self.note_t > 0:
                a = int(255 * clamp(self.note_t, 0, 1))
                y0 = RH // 2 - 48
                rl.draw_rectangle(RW // 2 - 116, y0 - 6, 232, 14 * len(self.note) + 10, Color(0, 0, 0, int(a * 0.7)))
                for i, ln in enumerate(self.note):
                    self.txt(ln, RW // 2, y0 + i * 14, 10, (235, 225, 200), a, True)
            if self.fade > 0:
                rl.draw_rectangle(0, 0, RW, RH, Color(0, 0, 0, int(255 * self.fade)))
        elif st == "dead":
            if t < 0.15:
                rl.draw_rectangle(0, 0, RW, RH, Color(255, 255, 255, int(255 * (1 - t / 0.15))))
            if t > 1.8:
                a = int(255 * clamp((t - 1.8) / 1.0, 0, 1))
                rl.draw_rectangle(0, 0, RW, RH, Color(0, 0, 0, int(a * 0.55)))
                self.txt("SEN ÖLDÜN", RW // 2, 70, 30, (200, 20, 20), a, True)
                self.txt("O seni buldu.", RW // 2, 106, 10, (220, 220, 220), a, True)
                if t > 2.8:
                    self.txt("[R] Tekrar dene", RW // 2, 140, 10, (170, 170, 170), a, True)
        elif st == "ending":
            for a, b, s in END_SUBS:
                if a <= t < b:
                    self.txt(s, RW // 2, RH - 36, 10, (235, 235, 235), 255, True)
            if t > 16.2:
                al = int(255 * smooth(16.2, 17.4, t))
                if t > 18.2:
                    al = int(255 * (1 - smooth(18.2, 19.4, t)))
                    rl.draw_rectangle(0, 0, RW, RH, Color(0, 0, 0, 255))
                rl.draw_rectangle(0, 0, RW, RH, Color(255, 255, 255, al))

    def draw_sky(self, ycam, pcam, d, top, hor):
        hy = int(clamp(RH / 2 + math.tan(pcam) * K, -300, RH + 300))
        rl.clear_background(col(top))
        rl.draw_rectangle_gradient_v(0, hy - 110, RW, 110, col(top), col(hor))
        if d < 0.55:                                                   # batan güneş
            da = wrap(0.0 - ycam)
            if abs(da) < 1.2:
                sx = RW / 2 + math.tan(da) * K
                sy = hy - math.tan(0.10 - d * 0.26) * K
                rl.draw_circle(int(sx), int(sy), 32.0, Color(255, 150, 60, 50))
                rl.draw_circle(int(sx), int(sy), 16.0, Color(255, 215, 130, 255))
        if d > 0.5:                                                    # yıldızlar + ay
            k = clamp((d - 0.5) * 2, 0, 1)
            for az, el, b in STARS:
                da = wrap(az - ycam)
                if abs(da) < 1.2:
                    y = hy - math.tan(el) * K
                    if 0 <= y < hy:
                        v = int(b * k)
                        rl.draw_pixel(int(RW / 2 + math.tan(da) * K), int(y), Color(v, v, v, 255))
            da = wrap(0.9 - ycam)
            if abs(da) < 1.2:
                rl.draw_circle(int(RW / 2 + math.tan(da) * K), int(hy - math.tan(0.6) * K), 6.0,
                               Color(int(210 * k), int(210 * k), int(190 * k), 255))
        rl.draw_rectangle(0, hy, RW, RH - hy + 2, col(hor))

    def draw_scene(self, ws, L):
        d = self.dusk
        top = ramp([(80, 60, 120), (25, 18, 50), (3, 4, 10)], d)
        hor = ramp([(235, 120, 55), (90, 45, 75), (8, 10, 18)], d)
        amb = ramp([(1.0, 0.75, 0.55), (0.45, 0.3, 0.4), (0.12, 0.14, 0.22)], d)
        near = lerp(6, 2, d)
        far = max(16.0, lerp(48, 26, d) - self.got * 1.0)
        p, tg = self.cam_pos, self.cam_tgt
        dx, dy, dz = tg.x - p.x, tg.y - p.y, tg.z - p.z
        ycam = math.atan2(dx, -dz)
        pcam = math.atan2(dy, math.hypot(dx, dz))
        set_uniform(ws, L["res"], (RW, RH))
        set_uniform(ws, L["fogColor"], (hor[0] / 255, hor[1] / 255, hor[2] / 255))
        set_uniform(ws, L["fogNear"], near)
        set_uniform(ws, L["fogFar"], far)
        set_uniform(ws, L["ambient"], amb)
        set_uniform(ws, L["torch"], self.torch)
        set_uniform(ws, L["camPos"], (p.x, p.y, p.z))
        self.draw_sky(ycam, pcam, d, top, hor)
        cam = Camera3D(p, tg, V3(0.0, 1.0, 0.0), 70.0, rl.CAMERA_PERSPECTIVE)
        rl.begin_mode_3d(cam)
        rl.begin_shader_mode(ws)
        fl = math.hypot(dx, dz) or 1.0
        draw_ground(p.x, p.z)
        draw_trees(p.x, p.z, dx / fl, dz / fl, far)
        stalled = not (self.state == "intro" and self.t < 7.5)
        draw_car(self.car_z, self.time, stalled)
        for pg in self.pages:
            if not pg["got"] and math.hypot(pg["x"] - p.x, pg["z"] - p.z) < far:
                draw_page(pg)
        for sm in self.smoke:
            s = 0.25 + sm[3] * 0.35
            rl.draw_cube(V3(sm[0], sm[1], sm[2]), s, s, s, Color(70, 70, 74, 255))
        if self.sl["on"]:
            draw_slender(self.sl["x"], self.sl["z"], p.x, p.z, self.time, clamp(self.vfear, 0, 1))
        rl.end_shader_mode()
        rl.end_mode_3d()

    def render(self, target, ws, L, post, PL):
        rl.begin_texture_mode(target)
        if self.state == "end":
            rl.clear_background(rl.BLACK)
        else:
            self.draw_scene(ws, L)
        self.hud()
        rl.end_texture_mode()

        sw, sh = rl.get_screen_width(), rl.get_screen_height()
        sc = min(sw / RW, sh / RH)
        dw, dh = RW * sc, RH * sc
        set_uniform(post, PL["res"], (RW, RH))
        set_uniform(post, PL["time"], self.time)
        set_uniform(post, PL["fear"], self.vfear if self.state != "end" else 0.0)
        rl.begin_drawing()
        rl.clear_background(rl.BLACK)
        rl.begin_shader_mode(post)
        rl.draw_texture_pro(target.texture, Rectangle(0, 0, RW, -RH),
                            Rectangle((sw - dw) / 2, (sh - dh) / 2, dw, dh), Vector2(0, 0), 0.0, rl.WHITE)
        rl.end_shader_mode()
        rl.end_drawing()


# ----------------------------------------------------------------------------- main
def main():
    rl.set_config_flags(rl.FLAG_WINDOW_RESIZABLE)
    rl.init_window(W, H, "ORMAN")
    rl.set_target_fps(60)
    snd = {}
    try:
        rl.init_audio_device()
        snd = make_sounds()
    except Exception as e:                      # ses olmasa da oyun çalışsın
        print("Ses yüklenemedi:", e)
    try:
        rl.rl_set_clip_planes(0.1, 150.0)
    except Exception:
        pass
    target = rl.load_render_texture(RW, RH)
    rl.set_texture_filter(target.texture, rl.TEXTURE_FILTER_POINT)
    ws = rl.load_shader_from_memory(VS_WORLD, FS_WORLD)
    post = rl.load_shader_from_memory(VS_POST, FS_POST)
    L = {n: rl.get_shader_location(ws, n) for n in
         ("res", "fogColor", "fogNear", "fogFar", "ambient", "torch", "camPos")}
    PL = {n: rl.get_shader_location(post, n) for n in ("res", "time", "fear")}

    rl.disable_cursor()
    rl.get_mouse_delta()
    game = Game(snd)
    while not rl.window_should_close():
        dt = min(rl.get_frame_time(), 0.05)
        game.update(dt)
        game.render(target, ws, L, post, PL)

    rl.unload_shader(ws)
    rl.unload_shader(post)
    rl.unload_render_texture(target)
    try:
        rl.close_audio_device()
    except Exception:
        pass
    rl.close_window()


if __name__ == "__main__":
    main()