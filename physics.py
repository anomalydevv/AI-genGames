# -*- coding: utf-8 -*-
"""Ray-cast, carpisma (pushout) ve fizik guncellemesi."""
import math

from config import cl
from world import BOX


def ray_box(ox, oy, oz, dx, dy, dz, b, tmax):
    tmin = 0.0
    for o, d, lo, hi in ((ox, dx, b[0], b[3]), (oy, dy, b[1], b[4]), (oz, dz, b[2], b[5])):
        if abs(d) < 1e-9:
            if o < lo or o > hi:
                return None
        else:
            t1 = (lo - o) / d
            t2 = (hi - o) / d
            if t1 > t2:
                t1, t2 = t2, t1
            if t1 > tmin:
                tmin = t1
            if t2 < tmax:
                tmax = t2
            if tmin > tmax:
                return None
    return tmin


def ray_walls(ox, oy, oz, dx, dy, dz, tmax):
    best = tmax
    for b in BOX:
        t = ray_box(ox, oy, oz, dx, dy, dz, b, best)
        if t is not None and t < best:
            best = t
    if dy < -1e-6:
        t = -oy / dy
        if 0 < t < best:
            best = t
    return best


def los(ax, ay, az, bx, by, bz):
    dx, dy, dz = bx - ax, by - ay, bz - az
    d = math.sqrt(dx * dx + dy * dy + dz * dz)
    if d < 1e-4:
        return True
    return ray_walls(ax, ay, az, dx / d, dy / d, dz / d, d) >= d - 0.15


def ray_fighter(ox, oy, oz, dx, dy, dz, f, tmax):
    a = dx * dx + dz * dz
    if a < 1e-9:
        return None
    ex, ez = ox - f.x, oz - f.z
    b = 2 * (ex * dx + ez * dz)
    c = ex * ex + ez * ez - 0.42 * 0.42
    disc = b * b - 4 * a * c
    if disc < 0:
        return None
    t = (-b - math.sqrt(disc)) / (2 * a)
    if t < 0 or t > tmax:
        return None
    y = oy + dy * t
    h = f.h
    if y < f.y or y > f.y + h:
        return None
    return t, y > f.y + h - 0.3


def pushout(f):
    R = 0.38
    for b in BOX:
        if f.y + 1.7 <= b[1] or f.y >= b[4] - 0.4:
            continue
        if f.x + R < b[0] or f.x - R > b[3] or f.z + R < b[2] or f.z - R > b[5]:
            continue
        cx = cl(f.x, b[0], b[3])
        cz = cl(f.z, b[2], b[5])
        dx, dz = f.x - cx, f.z - cz
        d2 = dx * dx + dz * dz
        if d2 < R * R:
            if d2 > 1e-9:
                d = math.sqrt(d2)
                f.x = cx + dx / d * R
                f.z = cz + dz / d * R
            else:
                opts = [(f.x - b[0], -1, 0), (b[3] - f.x, 1, 0), (f.z - b[2], 0, -1), (b[5] - f.z, 0, 1)]
                m = min(opts)
                if m[1]:
                    f.x = (b[0] - R) if m[1] < 0 else (b[3] + R)
                else:
                    f.z = (b[2] - R) if m[2] < 0 else (b[5] + R)


def phys(f, dt):
    f.vy -= 24 * dt
    f.x += f.vx * dt
    f.z += f.vz * dt
    pushout(f)
    f.y += f.vy * dt
    ground = 0.0
    for b in BOX:
        if b[0] - 0.2 <= f.x <= b[3] + 0.2 and b[2] - 0.2 <= f.z <= b[5] + 0.2:
            if f.y >= b[4] - 0.4 and b[4] > ground:
                ground = b[4]
    f.grounded = False
    f.landed = 0.0
    if f.y <= ground:
        if f.vy < -6:
            f.landed = -f.vy
        f.y = ground
        if f.vy < 0:
            f.vy = 0
        f.grounded = True
