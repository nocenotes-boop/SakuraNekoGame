# -*- coding: utf-8 -*-
"""
SAKURA NEKO OPEN WORLD - Teko & Tomás
RPG 2D de mundo abierto + Simulación Felina + Gacha + Estética Kawaii
Protagonistas: TEKO (blanco ojos rojos) & TOMÁS (gris/blanco ojos amarillos)
Pareja homosexual explícita.

Ejecutar: pip install pygame && python sakura_neko_openworld.py
"""

import json
import math
import os
import platform
import random
import sys
import array
import wave
from collections import OrderedDict

try:
    import pygame
    from pygame.locals import *
except ImportError:
    print("[ERROR] Requiere pygame>=2. Instalar con: pip install pygame")
    sys.exit(1)

# =============================================================================
# CONSTANTES GLOBALES
# =============================================================================
VERSION = "1.0.0"
FPS = 60
BASE_FRAME = 64

# Plataformas
IS_MOBILE = "android" in sys.platform.lower() or "ANDROID" in os.environ or platform.system() == "Android"

# Tamaños del mundo por bioma
BIOME_SIZE = 2400
BIOME_GRID = {
    "sakura": (0, 0),
    "cristal": (1, 0),
    "neon": (0, 1),
    "flotantes": (1, 1),
    "desierto": (2, 0),
}

# Direcciones
DIR_DOWN, DIR_RIGHT, DIR_LEFT, DIR_UP = 0, 1, 2, 3
ANIM_FRAMES = 4

# Colores pastel kawaii
PASTEL_PINK = (255, 182, 193)
PASTEL_BLUE = (186, 225, 255)
PASTEL_YELLOW = (255, 240, 185)
PASTEL_GREEN = (200, 255, 200)
PASTEL_PURPLE = (230, 200, 255)

RARITY_COLORS = {"N": (170, 170, 170), "R": (110, 190, 255),
                 "SR": (255, 190, 90), "SSR": (255, 110, 170)}

# Progresión exponencial: XP(n) = BASE * GROWTH^(n-1)
XP_BASE, XP_GROWTH = 20, 1.28
COUPLE_THRESHOLDS = [0, 40, 100, 180, 280, 400]

# =============================================================================
# UTILIDADES
# =============================================================================
def clamp(v, a, b):
    return max(a, min(b, v))

def lerp(a, b, t):
    return a + (b - a) * t

def distance(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def draw_round_rect(surface, color, rect, radius, alpha=255):
    if alpha >= 255:
        pygame.draw.rect(surface, color, rect, border_radius=radius)
    else:
        s = pygame.Surface((max(1, rect[2]), max(1, rect[3])), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
        surface.blit(s, (rect[0], rect[1]))

def vertical_gradient(w, h, top, bottom):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / max(1, h - 1)
        col = (int(lerp(top[0], bottom[0], t)), int(lerp(top[1], bottom[1], t)),
               int(lerp(top[2], bottom[2], t)))
        pygame.draw.line(s, col, (0, y), (w, y))
    return s

# =============================================================================
# ASSET MANAGER (caché global)
# =============================================================================
class AssetManager:
    _surfaces = {}
    _sheets = {}
    _gradients = {}
    _mounts = OrderedDict()
    MOUNT_CAP = 200

    @classmethod
    def put_surface(cls, key, surf):
        cls._surfaces[key] = surf
        return surf

    @classmethod
    def get_surface(cls, key):
        return cls._surfaces.get(key)

    @classmethod
    def put_sheet(cls, key, sheet):
        cls._sheets[key] = sheet
        return sheet

    @classmethod
    def get_sheet(cls, key):
        return cls._sheets.get(key)

    @classmethod
    def get_gradient(cls, w, h, top, bottom):
        key = (w, h, top, bottom)
        if key not in cls._gradients:
            cls._gradients[key] = vertical_gradient(w, h, top, bottom)
        return cls._gradients[key]

    @classmethod
    def get_mount(cls, key, builder):
        if key not in cls._mounts:
            cls._mounts[key] = builder()
            if len(cls._mounts) > cls.MOUNT_CAP:
                cls._mounts.popitem(last=False)
        else:
            cls._mounts.move_to_end(key)
        return cls._mounts[key]


# =============================================================================
# SPRITESHEET
# =============================================================================
class Spritesheet:
    def __init__(self, surface, fw=BASE_FRAME, fh=BASE_FRAME):
        self.surface = surface
        self.fw, self.fh = fw, fh
        self._cache = {}

    def frame(self, col, row):
        key = (col, row)
        if key not in self._cache:
            r = pygame.Rect(col * self.fw, row * self.fh, self.fw, self.fh)
            self._cache[key] = self.surface.subsurface(r).copy()
        return self._cache[key]


# =============================================================================
# PROCEDURAL ART FACTORY
# =============================================================================
class ArtFactory:
    @staticmethod
    def _tmp(w=BASE_FRAME, h=BASE_FRAME):
        return pygame.Surface((w, h), pygame.SRCALPHA)

    @classmethod
    def _draw_cat(cls, s, fur, fur2, eyes, pattern, orient, f):
        dark = (max(0, fur[0]-45), max(0, fur[1]-45), max(0, fur[2]-45))
        tuxedo = pattern == "tuxedo"
        paw_a = -2 if f == 1 else 0
        paw_b = -2 if f == 2 else 0
        bob = 1 if f == 1 else 0

        if orient == "right":
            pygame.draw.circle(s, fur, (14, 40), 7)
            pygame.draw.ellipse(s, fur, (16, 36+bob, 32, 20))
            if tuxedo:
                pygame.draw.ellipse(s, fur2, (36, 42+bob, 14, 12))
            pygame.draw.circle(s, fur2 if tuxedo else fur, (24, 56+paw_a), 4)
            pygame.draw.circle(s, fur2 if tuxedo else fur, (40, 56+paw_b), 4)
            pygame.draw.circle(s, fur, (44, 22+bob), 14)
            pygame.draw.polygon(s, fur, [(34, 12), (37, 1), (43, 10)])
            pygame.draw.polygon(s, fur, [(46, 10), (51, 0), (54, 11)])
            pygame.draw.polygon(s, (255, 170, 180), [(36, 10), (38, 4), (41, 9)])
            pygame.draw.polygon(s, (255, 170, 180), [(48, 9), (51, 4), (52, 10)])
            if tuxedo:
                pygame.draw.circle(s, fur2, (50, 27+bob), 5)
            pygame.draw.circle(s, eyes, (48, 21+bob), 4)
            pygame.draw.circle(s, (255, 255, 255), (49, 20+bob), 1)
            pygame.draw.circle(s, (255, 150, 160), (43, 28+bob), 3)
        elif orient == "up":
            pygame.draw.circle(s, fur, (33, 10), 5)
            pygame.draw.ellipse(s, fur, (18, 38+bob, 28, 20))
            pygame.draw.circle(s, fur, (26, 58+paw_a), 4)
            pygame.draw.circle(s, fur, (38, 58+paw_b), 4)
            pygame.draw.circle(s, fur, (32, 24+bob), 16)
            pygame.draw.polygon(s, fur, [(18, 14), (22, 2), (28, 12)])
            pygame.draw.polygon(s, fur, [(36, 12), (42, 2), (46, 14)])
            pygame.draw.polygon(s, (255, 170, 180), [(20, 12), (22, 6), (26, 11)])
            pygame.draw.polygon(s, (255, 170, 180), [(38, 11), (41, 6), (44, 12)])
        else:  # down (frontal)
            pygame.draw.circle(s, fur, (50, 44), 6)
            pygame.draw.ellipse(s, fur, (18, 38+bob, 28, 20))
            if tuxedo:
                pygame.draw.ellipse(s, fur2, (24, 44+bob, 16, 12))
            pygame.draw.circle(s, fur2 if tuxedo else fur, (26, 58+paw_a), 4)
            pygame.draw.circle(s, fur2 if tuxedo else fur, (38, 58+paw_b), 4)
            pygame.draw.circle(s, fur, (32, 24+bob), 16)
            pygame.draw.polygon(s, fur, [(18, 14), (22, 2), (28, 12)])
            pygame.draw.polygon(s, fur, [(36, 12), (42, 2), (46, 14)])
            pygame.draw.polygon(s, (255, 170, 180), [(20, 12), (22, 6), (26, 11)])
            pygame.draw.polygon(s, (255, 170, 180), [(38, 11), (41, 6), (44, 12)])
            if tuxedo:
                pygame.draw.circle(s, fur2, (32, 30+bob), 7)
            pygame.draw.circle(s, eyes, (26, 24+bob), 4)
            pygame.draw.circle(s, eyes, (38, 24+bob), 4)
            pygame.draw.circle(s, (255, 255, 255), (27, 23+bob), 1)
            pygame.draw.circle(s, (255, 255, 255), (39, 23+bob), 1)
            pygame.draw.circle(s, (255, 150, 160), (20, 30+bob), 3)
            pygame.draw.circle(s, (255, 150, 160), (44, 30+bob), 3)
            pygame.draw.arc(s, (90, 60, 70), (28, 28+bob, 5, 5), 3.2, 6.2, 1)
            pygame.draw.arc(s, (90, 60, 70), (32, 28+bob, 5, 5), 3.2, 6.2, 1)

    @classmethod
    def build_cat_sheet(cls, fur, fur2, eyes, pattern):
        sheet = cls._tmp(BASE_FRAME * ANIM_FRAMES, BASE_FRAME * 4)
        for f in range(ANIM_FRAMES):
            down = cls._tmp(); cls._draw_cat(down, fur, fur2, eyes, pattern, "down", f)
            right = cls._tmp(); cls._draw_cat(right, fur, fur2, eyes, pattern, "right", f)
            left = pygame.transform.flip(right, True, False)
            up = cls._tmp(); cls._draw_cat(up, fur, fur2, eyes, pattern, "up", f)
            sheet.blit(down, (f * BASE_FRAME, 0))
            sheet.blit(right, (f * BASE_FRAME, BASE_FRAME))
            sheet.blit(left, (f * BASE_FRAME, BASE_FRAME * 2))
            sheet.blit(up, (f * BASE_FRAME, BASE_FRAME * 3))
        return sheet

    @classmethod
    def _draw_unicorn(cls, s, body, mane, orient, f):
        gold = (255, 215, 130)
        la = 0 if f != 1 else -2
        lb = 0 if f != 2 else -2
        if orient == "right":
            for i, x in enumerate((18, 26, 36, 44)):
                off = la if i % 2 == 0 else lb
                pygame.draw.rect(s, body, (x, 44+off, 5, 12), border_radius=2)
            pygame.draw.ellipse(s, body, (14, 30, 36, 18))
            for i, c in enumerate(mane):
                pygame.draw.circle(s, c, (13-i, 32+i*3), 5-i)
            pygame.draw.circle(s, body, (46, 22), 9)
            pygame.draw.polygon(s, gold, [(47, 13), (51, 1), (53, 14)])
            pygame.draw.polygon(s, body, [(41, 13), (43, 7), (46, 12)])
            for i, c in enumerate(mane):
                pygame.draw.circle(s, c, (40-i*4, 16+i*4), 4)
            pygame.draw.circle(s, (60, 50, 70), (48, 21), 2)
            pygame.draw.circle(s, (255, 255, 255), (49, 20), 1)
        elif orient == "up":
            for i, x in enumerate((22, 30, 36, 42)):
                off = la if i % 2 == 0 else lb
                pygame.draw.rect(s, body, (x, 46+off, 5, 12), border_radius=2)
            pygame.draw.ellipse(s, body, (18, 30, 28, 20))
            for i, c in enumerate(mane):
                pygame.draw.circle(s, c, (32, 12+i*4), 5-i)
            pygame.draw.circle(s, body, (32, 20), 10)
            pygame.draw.polygon(s, body, [(24, 12), (26, 5), (30, 11)])
            pygame.draw.polygon(s, body, [(34, 11), (38, 5), (40, 12)])
        else:
            for i, x in enumerate((22, 30, 36, 42)):
                off = la if i % 2 == 0 else lb
                pygame.draw.rect(s, body, (x, 46+off, 5, 12), border_radius=2)
            pygame.draw.ellipse(s, body, (18, 30, 28, 20))
            pygame.draw.circle(s, body, (32, 20), 10)
            pygame.draw.polygon(s, gold, [(30, 11), (32, 0), (35, 11)])
            pygame.draw.polygon(s, body, [(23, 13), (25, 6), (29, 12)])
            pygame.draw.polygon(s, body, [(35, 12), (39, 6), (41, 13)])
            for i, c in enumerate(mane):
                pygame.draw.circle(s, c, (24-i*2, 18+i*3), 4)
                pygame.draw.circle(s, c, (40+i*2, 18+i*3), 4)
            pygame.draw.circle(s, (60, 50, 70), (28, 20), 2)
            pygame.draw.circle(s, (60, 50, 70), (36, 20), 2)

    @classmethod
    def build_unicorn_sheet(cls, body, mane):
        sheet = cls._tmp(BASE_FRAME * ANIM_FRAMES, BASE_FRAME * 4)
        for f in range(ANIM_FRAMES):
            down = cls._tmp(); cls._draw_unicorn(down, body, mane, "down", f)
            right = cls._tmp(); cls._draw_unicorn(right, body, mane, "right", f)
            left = pygame.transform.flip(right, True, False)
            up = cls._tmp(); cls._draw_unicorn(up, body, mane, "up", f)
            sheet.blit(down, (f * BASE_FRAME, 0))
            sheet.blit(right, (f * BASE_FRAME, BASE_FRAME))
            sheet.blit(left, (f * BASE_FRAME, BASE_FRAME * 2))
            sheet.blit(up, (f * BASE_FRAME, BASE_FRAME * 3))
        return sheet

    @classmethod
    def build_mount_sprite(cls, cat_sheet, uni_sheet, direction, frame):
        s = pygame.Surface((96, 104), pygame.SRCALPHA)
        uni = pygame.transform.smoothscale(uni_sheet.frame(frame, direction), (86, 86))
        s.blit(uni, (5, 18))
        bounce = int(math.sin(frame * 2.1) * 2)
        cat = pygame.transform.smoothscale(cat_sheet.frame(0, direction), (51, 51))
        s.blit(cat, (24, 2 + bounce))
        pygame.draw.rect(s, (180, 120, 90, 180), (30, 44+bounce, 40, 4), border_radius=2)
        return s

    @classmethod
    def generate_all(cls):
        # Protagonistas
        teko = {"fur": (246, 244, 250), "fur2": (255, 255, 255),
                "eyes": (205, 45, 70), "pattern": "solid"}
        tomas = {"fur": (122, 116, 122), "fur2": (250, 250, 250),
                 "eyes": (240, 200, 70), "pattern": "tuxedo"}
        AssetManager.put_sheet("teko", Spritesheet(
            cls.build_cat_sheet(teko["fur"], teko["fur2"], teko["eyes"], teko["pattern"])))
        AssetManager.put_sheet("tomas", Spritesheet(
            cls.build_cat_sheet(tomas["fur"], tomas["fur2"], tomas["eyes"], tomas["pattern"])))

        # Unicornios
        for uid, body, mane in [("alba", (250, 250, 255),
                                 [(255, 150, 190), (255, 220, 150), (160, 220, 255)]),
                                ("rosa", (255, 225, 235),
                                 [(170, 240, 200), (140, 220, 255), (220, 190, 255)]),
                                ("dorado", (255, 240, 200),
                                 [(255, 200, 120), (255, 160, 160), (255, 230, 180)])]:
            AssetManager.put_sheet(uid, Spritesheet(
                cls.build_unicorn_sheet(body, mane)))

        # Pétalo sakura
        petal = cls._tmp(10, 10)
        pygame.draw.ellipse(petal, (255, 175, 200), (1, 2, 8, 6))
        pygame.draw.ellipse(petal, (255, 220, 232), (2, 3, 4, 3))
        AssetManager.put_surface("petal", petal)

        # Corazón
        heart = cls._tmp(14, 12)
        pygame.draw.circle(heart, (255, 105, 160), (4, 4), 4)
        pygame.draw.circle(heart, (255, 105, 160), (10, 4), 4)
        pygame.draw.polygon(heart, (255, 105, 160), [(0, 5), (7, 12), (14, 5)])
        AssetManager.put_surface("heart", heart)

        # Cristal de energía
        crystal = cls._tmp(14, 16)
        pygame.draw.polygon(crystal, (170, 230, 255), [(7, 0), (13, 6), (7, 16), (1, 6)])
        pygame.draw.polygon(crystal, (220, 245, 255), [(7, 2), (10, 6), (7, 12)])
        AssetManager.put_surface("crystal", crystal)

        # Perro sombra (enemigo)
        for f in range(ANIM_FRAMES):
            sh = cls._tmp(48, 48)
            wob = 2 if f == 1 else 0
            pygame.draw.circle(sh, (30, 20, 45, 160), (24, 26), 20+wob)
            pygame.draw.circle(sh, (45, 30, 65, 230), (24, 24), 16-wob)
            pygame.draw.ellipse(sh, (45, 30, 65, 230), (10, 18, 28, 16))
            pygame.draw.polygon(sh, (30, 20, 45), [(12, 12), (16, 4), (20, 12)])
            pygame.draw.polygon(sh, (30, 20, 45), [(28, 12), (32, 4), (36, 12)])
            pygame.draw.circle(sh, (255, 90, 140), (18, 22), 3)
            pygame.draw.circle(sh, (255, 90, 140), (30, 22), 3)
            AssetManager.put_surface("shadow_%d" % f, sh)

        # Insecto (caza)
        insect = cls._tmp(16, 16)
        pygame.draw.ellipse(insect, (80, 200, 120), (2, 4, 12, 8))
        pygame.draw.circle(insect, (60, 180, 100), (4, 8), 3)
        pygame.draw.circle(insect, (60, 180, 100), (12, 8), 3)
        pygame.draw.line(insect, (200, 200, 255, 160), (8, 4), (2, 0), 1)
        pygame.draw.line(insect, (200, 200, 255, 160), (8, 4), (14, 0), 1)
        AssetManager.put_surface("insect", insect)

        # Tronco de árbol sakura
        trunk = cls._tmp(80, 120)
        trunk.blit(AssetManager.get_gradient(12, 80, (150, 110, 90), (90, 62, 50)), (34, 40))
        pygame.draw.line(trunk, (120, 85, 70), (40, 60), (20, 35), 6)
        pygame.draw.line(trunk, (120, 85, 70), (40, 55), (60, 30), 6)
        AssetManager.put_surface("trunk", trunk)

        # Copa sakura
        canopy = cls._tmp(170, 130)
        for x, y, r in [(85, 65, 55), (45, 80, 38), (125, 80, 38), (65, 45, 40), (105, 45, 40)]:
            pygame.draw.circle(canopy, (255, 183, 203), (x, y), r)
        for x, y in [(60, 60), (95, 40), (120, 75), (45, 85)]:
            pygame.draw.circle(canopy, (255, 246, 250), (x, y), 4)
        AssetManager.put_surface("canopy", canopy)


# =============================================================================
# INPUT MANAGER (PC + Android táctil)
# =============================================================================
class InputManager:
    def __init__(self, screen_w, screen_h):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.joystick_center = (120, screen_h - 120)
        self.joystick_radius = 80
        self.joystick_pos = (0.0, 0.0)
        self.touch_buttons = {}
        self._build_touch_buttons()
        self.touch_state = {"a": False, "b": False, "x": False, "y": False,
                            "lb": False, "rb": False, "menu": False}
        self.keys_pressed = {}
        self.touches = {}

    def _build_touch_buttons(self):
        sx, sy = self.screen_w - 130, self.screen_h - 240
        self.touch_buttons = {
            "a": (sx + 70, sy + 80, 40, "Interactuar"),
            "b": (sx, sy + 80, 40, "Atacar"),
            "x": (sx + 70, sy + 20, 40, "Montar"),
            "y": (sx + 140, sy + 80, 40, "Gacha"),
            "lb": (sx - 80, sy - 40, 32, "Switch"),
            "rb": (sx + 80, sy - 40, 32, "Menu"),
        }

    def update(self, events):
        keys = pygame.key.get_pressed()
        self.keys_pressed = keys
        self.joystick_pos = (0.0, 0.0)
        for k in self.touch_state:
            self.touch_state[k] = False

        for ev in events:
            if ev.type == pygame.FINGERDOWN:
                self._handle_touch(ev.fingerId, ev.x * self.screen_w, ev.y * self.screen_h, True)
            elif ev.type == pygame.FINGERUP:
                self.touches.pop(ev.fingerId, None)
            elif ev.type == pygame.FINGERMOTION:
                self._handle_touch(ev.fingerId, ev.x * self.screen_w, ev.y * self.screen_h, False)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if IS_MOBILE:
                    self._handle_touch(-1, ev.pos[0], ev.pos[1], True)

    def _handle_touch(self, fid, x, y, is_down):
        self.touches[fid] = (x, y)
        # Joystick
        jx, jy = self.joystick_center
        jr = self.joystick_radius
        if distance(x, y, jx, jy) < jr * 2.0:
            dx = clamp((x - jx) / jr, -1, 1)
            dy = clamp((y - jy) / jr, -1, 1)
            self.joystick_pos = (dx, dy)
        # Botones
        if is_down:
            for name, (bx, by, br, _) in self.touch_buttons.items():
                if distance(x, y, bx, by) < br * 1.3:
                    self.touch_state[name] = True

    def get_movement(self):
        keys = self.keys_pressed
        dx = dy = 0.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
        if IS_MOBILE or abs(self.joystick_pos[0]) > 0.1 or abs(self.joystick_pos[1]) > 0.1:
            if self.joystick_pos != (0, 0):
                dx = self.joystick_pos[0]
                dy = self.joystick_pos[1]
        return dx, dy

    def just_pressed(self, key):
        return self.keys_pressed.get(key, False)

    def button_pressed(self, name):
        return self.touch_state.get(name, False)

    def draw_touch_ui(self, screen):
        if not IS_MOBILE:
            return
        # Joystick base
        jx, jy = self.joystick_center
        jr = self.joystick_radius
        pygame.draw.circle(screen, (255, 255, 255, 80), (jx, jy), jr, 4)
        stick_x = int(jx + self.joystick_pos[0] * jr * 0.6)
        stick_y = int(jy + self.joystick_pos[1] * jr * 0.6)
        pygame.draw.circle(screen, (255, 255, 255, 180), (stick_x, stick_y), jr // 2)
        # Botones
        for name, (bx, by, br, label) in self.touch_buttons.items():
            pressed = self.touch_state.get(name, False)
            color = (255, 182, 193, 180) if not pressed else (255, 110, 170, 230)
            s = pygame.Surface((br*2, br*2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (br, br), br, 3)
            screen.blit(s, (bx - br, by - br))
            font = pygame.font.SysFont("verdana", 14, bold=True)
            t = font.render(label[:4], True, (255, 255, 255))
            screen.blit(t, (bx - t.get_width() // 2, by - t.get_height() // 2))


# =============================================================================
# WEATHER & DAY/NIGHT
# =============================================================================
class WeatherSystem:
    def __init__(self):
        self.type = "clear"
        self.t = 0.0
        self.change_timer = 60.0
        self.intensity = 0.0

    def update(self, dt, biome):
        self.t += dt
        self.change_timer -= dt
        if self.change_timer <= 0:
            self.change_timer = random.uniform(60, 180)
            if biome == "desierto":
                self.type = random.choice(["clear", "wind", "clear"])
            elif biome == "cristal":
                self.type = random.choice(["clear", "snow", "clear"])
            elif biome == "flotantes":
                self.type = random.choice(["clear", "wind"])
            else:
                self.type = random.choice(["clear", "rain", "clear", "clear"])
            self.intensity = random.uniform(0.5, 1.0)

    def spawn_particles(self, particles, camera):
        if self.type == "rain" and random.random() < 0.6 * self.intensity:
            x = camera.x + random.randint(0, 1024)
            y = camera.y - 20
            particles.add_weather("rain", x, y)
        elif self.type == "snow" and random.random() < 0.3 * self.intensity:
            x = camera.x + random.randint(0, 1024)
            y = camera.y - 20
            particles.add_weather("snow", x, y)
        elif self.type == "wind" and random.random() < 0.4 * self.intensity:
            x = camera.x - 20
            y = camera.y + random.randint(0, 640)
            particles.add_weather("wind", x, y)


class DayNightCycle:
    def __init__(self):
        self.time = 0.0
        self.day_duration = 600.0  # 10 minutos por día completo

    def update(self, dt):
        self.time = (self.time + dt) % self.day_duration

    def get_phase(self):
        p = self.time / self.day_duration
        if p < 0.25: return "dawn"
        if p < 0.5: return "day"
        if p < 0.75: return "dusk"
        return "night"

    def get_ambient_overlay(self):
        p = self.time / self.day_duration
        if p < 0.125:
            t = p / 0.125
            return (lerp(40, 60, t), lerp(20, 30, t), lerp(80, 70, t), lerp(180, 80, t))
        elif p < 0.25:
            t = (p - 0.125) / 0.125
            return (lerp(60, 0, t), lerp(30, 0, t), lerp(70, 0, t), lerp(80, 0, t))
        elif p < 0.5:
            return (0, 0, 0, 0)
        elif p < 0.625:
            t = (p - 0.5) / 0.125
            return (lerp(0, 80, t), lerp(0, 30, t), lerp(0, 60, t), lerp(0, 120, t))
        elif p < 0.75:
            t = (p - 0.625) / 0.125
            return (lerp(80, 20, t), lerp(30, 10, t), lerp(60, 50, t), lerp(120, 200, t))
        else:
            return (20, 10, 50, 200)


# =============================================================================
# PARTICLES
# =============================================================================
class Particle:
    def __init__(self, kind, x, y, vx, vy, life, color=None):
        self.kind = kind
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.color = color or (255, 255, 255)
        self.rot = random.uniform(0, 360)
        self.phase = random.uniform(0, math.tau)

    def update(self, dt, t):
        if self.kind == "petal":
            self.vy = min(self.vy + 30 * dt, 60)
            self.x += self.vx * dt + math.sin(t * 3 + self.phase) * 20 * dt
        elif self.kind == "heart":
            self.vy -= 40 * dt
            self.x += self.vx * dt + math.sin(t * 4 + self.phase) * 12 * dt
        elif self.kind == "rain":
            self.vy = 600
            self.x += self.vx * dt
        elif self.kind == "snow":
            self.vy = min(self.vy + 20 * dt, 80)
            self.x += math.sin(t * 2 + self.phase) * 30 * dt
        elif self.kind == "wind":
            self.vx = 400
        elif self.kind == "sparkle":
            self.vx *= (1 - 2.5 * dt)
            self.vy *= (1 - 2.5 * dt)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    @property
    def alive(self):
        return self.life > 0


class ParticleSystem:
    MAX = 600

    def __init__(self):
        self.parts = []

    def add(self, p):
        if len(self.parts) >= self.MAX:
            self.parts.pop(0)
        self.parts.append(p)

    def spawn_petal(self, x, y):
        self.add(Particle("petal", x, y, random.uniform(-10, 10), 20, random.uniform(4, 7)))

    def spawn_hearts(self, x, y, n=6):
        for _ in range(n):
            self.add(Particle("heart", x + random.uniform(-15, 15), y + random.uniform(-10, 4),
                              random.uniform(-15, 15), random.uniform(-40, -10), random.uniform(0.8, 1.5)))

    def spawn_sparkle(self, x, y, n=8, color=(255, 245, 200)):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            self.add(Particle("sparkle", x, y, math.cos(a) * 80, math.sin(a) * 80,
                              random.uniform(0.3, 0.7), color))

    def add_weather(self, kind, x, y):
        if kind == "rain":
            self.add(Particle("rain", x, y, -30, 100, 1.5, (140, 180, 220)))
        elif kind == "snow":
            self.add(Particle("snow", x, y, 0, 10, 4.0, (240, 240, 255)))
        elif kind == "wind":
            self.add(Particle("wind", x, y, 100, 0, 2.0, (220, 220, 200)))

    def update(self, dt, t):
        for p in self.parts:
            p.update(dt, t)
        self.parts = [p for p in self.parts if p.alive]

    def draw(self, screen, cam):
        petal = AssetManager.get_surface("petal")
        heart = AssetManager.get_surface("heart")
        for p in self.parts:
            sx, sy = int(p.x - cam.x), int(p.y - cam.y)
            if not (-20 < sx < 1024 + 20 and -20 < sy < 640 + 20):
                continue
            if p.kind == "petal":
                screen.blit(pygame.transform.rotate(petal, p.rot), (sx, sy))
            elif p.kind == "heart":
                screen.blit(heart, (sx, sy))
            elif p.kind == "rain":
                pygame.draw.line(screen, p.color, (sx, sy), (sx - 2, sy + 10), 1)
            elif p.kind == "snow":
                pygame.draw.circle(screen, p.color, (sx, sy), 2)
            elif p.kind == "wind":
                pygame.draw.line(screen, p.color, (sx, sy), (sx + 15, sy), 1)
            elif p.kind == "sparkle":
                r = 2 if p.life / p.max_life > 0.5 else 1
                pygame.draw.circle(screen, p.color, (sx, sy), r)


# =============================================================================
# CAMERA
# =============================================================================
class Camera:
    def __init__(self):
        self.x = self.y = 0.0
        self.target_biome = "sakura"

    def follow(self, tx, ty, dt):
        target_x = clamp(tx - 512, 0, BIOME_SIZE * 3 - 1024)
        target_y = clamp(ty - 320, 0, BIOME_SIZE * 2 - 640)
        k = 1 - math.pow(0.001, dt)
        self.x = lerp(self.x, target_x, k)
        self.y = lerp(self.y, target_y, k)

    def get_current_biome(self):
        bx = int(self.x + 512) // BIOME_SIZE
        by = int(self.y + 320) // BIOME_SIZE
        for bname, (gx, gy) in BIOME_GRID.items():
            if (gx, gy) == (bx, by):
                return bname
        return "sakura"


# =============================================================================
# BIOMES
# =============================================================================
class Biome:
    def __init__(self, name, gx, gy, ground_top, ground_bot, trees=30):
        self.name = name
        self.x = gx * BIOME_SIZE
        self.y = gy * BIOME_SIZE
        self.ground_top = ground_top
        self.ground_bot = ground_bot
        self.trees = []
        rng = random.Random(gx * 1000 + gy + 42)
        for _ in range(trees):
            self.trees.append((rng.uniform(80, BIOME_SIZE-80),
                               rng.uniform(160, BIOME_SIZE-40),
                               rng.uniform(0.8, 1.3), rng.uniform(0, 6.28)))
        self.pickups = []
        for _ in range(8):
            self.pickups.append([rng.uniform(80, BIOME_SIZE-80), rng.uniform(80, BIOME_SIZE-80)])
        self.insects = []
        for _ in range(4):
            self.insects.append({"x": rng.uniform(100, BIOME_SIZE-100),
                                  "y": rng.uniform(100, BIOME_SIZE-100),
                                  "t": rng.uniform(0, 6.28), "alive": True})

    def update(self, dt, t, particles, game):
        for i in self.insects:
            if not i["alive"]:
                continue
            i["t"] += dt
            i["x"] += math.sin(i["t"] * 1.5) * 20 * dt
            i["y"] += math.cos(i["t"] * 1.2) * 15 * dt
        if self.name == "sakura" and random.random() < 0.2:
            tx, ty, sc, ph = random.choice(self.trees)
            particles.spawn_petal(self.x + tx + random.uniform(-60, 60) * sc,
                                   self.y + ty - 90 * sc)
        kept = []
        for p in self.pickups:
            px, py = p
            if distance(game.controlled.x, game.controlled.y, self.x + px, self.y + py) < 34:
                game.gacha.add_crystals(3)
                particles.spawn_sparkle(self.x + px, self.y + py)
                game.quest.event("collect_crystal", 1)
            else:
                kept.append(p)
        self.pickups = kept
        if len(self.pickups) < 8:
            self.pickups.append([random.uniform(80, BIOME_SIZE-80), random.uniform(80, BIOME_SIZE-80)])

    def draw(self, screen, cam, t):
        bx, by = self.x - cam.x, self.y - cam.y
        if bx > 1024 or by > 640 or bx + BIOME_SIZE < 0 or by + BIOME_SIZE < 0:
            return
        grad = AssetManager.get_gradient(1024, 640, self.ground_top, self.ground_bot)
        screen.blit(grad, (max(0, int(bx)), max(0, int(by))))
        crystal = AssetManager.get_surface("crystal")
        for px, py in self.pickups:
            sx, sy = int(self.x + px - cam.x), int(self.y + py - cam.y)
            if -20 < sx < 1044 and -20 < sy < 660:
                screen.blit(crystal, (sx, int(sy + math.sin(t * 3 + px) * 3)))
        insect_img = AssetManager.get_surface("insect")
        for ins in self.insects:
            if not ins["alive"]:
                continue
            sx, sy = int(self.x + ins["x"] - cam.x), int(self.y + ins["y"] - cam.y)
            if -20 < sx < 1044 and -20 < sy < 660:
                screen.blit(insect_img, (sx, int(sy + math.sin(t * 5) * 2)))
        if self.name == "sakura":
            trunk = AssetManager.get_surface("trunk")
            canopy = AssetManager.get_surface("canopy")
            for tx, ty, sc, ph in self.trees:
                sway = math.sin(t * 1.3 + ph) * 6 * sc
                x = int(self.x + tx - cam.x - 40 * sc)
                y = int(self.y + ty - cam.y - 110 * sc)
                if x < -220 or x > 1244 or y < -220 or y > 860:
                    continue
                tr = pygame.transform.smoothscale(trunk, (int(80 * sc), int(120 * sc)))
                ca = pygame.transform.smoothscale(canopy, (int(170 * sc), int(130 * sc)))
                screen.blit(tr, (x, y))
                screen.blit(ca, (int(x - 45 * sc + sway), int(y - 75 * sc)))
        elif self.name == "cristal":
            for i, (tx, ty, sc, ph) in enumerate(self.trees[:12]):
                x = int(self.x + tx - cam.x)
                y = int(self.y + ty - cam.y)
                pulse = 0.7 + 0.3 * math.sin(t * 2 + ph)
                c1 = (int(140 * pulse), int(200 * pulse), int(255 * pulse))
                c2 = (int(180 * pulse), int(230 * pulse), int(255 * pulse))
                pygame.draw.polygon(screen, c1, [(x, y), (x - 15 * sc, y + 60 * sc),
                                                  (x + 15 * sc, y + 60 * sc)])
                pygame.draw.polygon(screen, c2, [(x, y + 10), (x - 10 * sc, y + 50 * sc),
                                                  (x + 10 * sc, y + 50 * sc)])
        elif self.name == "neon":
            for i, (tx, ty, sc, ph) in enumerate(self.trees):
                x = int(self.x + tx - cam.x)
                y = int(self.y + ty - cam.y)
                w = 40 * sc
                h = 120 * sc
                pygame.draw.rect(screen, (40, 30, 60), (x - w/2, y - h, w, h))
                for j in range(3):
                    wy = y - h + j * 30
                    pygame.draw.rect(screen, (255, 100, 200) if j % 2 == 0 else (100, 200, 255),
                                     (x - w/2 + 4, wy + 8, w - 8, 8))
        elif self.name == "flotantes":
            for i, (tx, ty, sc, ph) in enumerate(self.trees[:15]):
                x = int(self.x + tx - cam.x)
                y = int(self.y + ty - cam.y + math.sin(t + ph) * 10)
                pygame.draw.ellipse(screen, (180, 220, 200), (x - 40 * sc, y - 20 * sc, 80 * sc, 40 * sc))
                pygame.draw.ellipse(screen, (140, 200, 180), (x - 30 * sc, y - 30 * sc, 60 * sc, 30 * sc))
        elif self.name == "desierto":
            for i, (tx, ty, sc, ph) in enumerate(self.trees[:8]):
                x = int(self.x + tx - cam.x)
                y = int(self.y + ty - cam.y)
                pygame.draw.ellipse(screen, (220, 190, 140), (x - 40 * sc, y - 10 * sc, 80 * sc, 30 * sc))


# =============================================================================
# WORLD
# =============================================================================
class World:
    def __init__(self):
        self.biomes = {}
        for bname, (gx, gy) in BIOME_GRID.items():
            if bname == "sakura":
                top, bot = (180, 210, 160), (130, 170, 120)
            elif bname == "cristal":
                top, bot = (160, 180, 220), (100, 130, 180)
            elif bname == "neon":
                top, bot = (60, 40, 100), (30, 20, 60)
            elif bname == "flotantes":
                top, bot = (180, 210, 230), (140, 180, 210)
            elif bname == "desierto":
                top, bot = (235, 210, 160), (200, 170, 120)
            trees = {"sakura": 40, "cristal": 20, "neon": 25, "flotantes": 18, "desierto": 12}[bname]
            self.biomes[bname] = Biome(bname, gx, gy, top, bot, trees)

    def get_biome_at(self, x, y):
        for bname, biome in self.biomes.items():
            if biome.x <= x < biome.x + BIOME_SIZE and biome.y <= y < biome.y + BIOME_SIZE:
                return biome
        return self.biomes["sakura"]

    def update(self, dt, t, particles, game):
        current = self.get_biome_at(game.controlled.x, game.controlled.y)
        current.update(dt, t, particles, game)

    def draw(self, screen, cam, t):
        for biome in self.biomes.values():
            biome.draw(screen, cam, t)


# =============================================================================
# ENEMIES (Perros Sombra)
# =============================================================================
class ShadowDog:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.hp = 5
        self.max_hp = 5
        self.alive = True
        self.cd = 0.0
        self.frame = 0
        self.anim_t = 0.0
        self.t = random.uniform(0, 6)
        self.facing = DIR_DOWN

    def update(self, dt, player):
        if not self.alive:
            return 0
        self.cd = max(0.0, self.cd - dt)
        self.t += dt
        d = distance(self.x, self.y, player.x, player.y)
        if d < 300 and d > 30:
            self.x += (player.x - self.x) / d * 100 * dt
            self.y += (player.y - self.y) / d * 100 * dt
        elif d <= 30 and self.cd <= 0:
            self.cd = 1.2
            return 8
        self.anim_t += dt
        if self.anim_t > 0.2:
            self.anim_t = 0
            self.frame = (self.frame + 1) % ANIM_FRAMES
        return 0

    def damage(self, dmg, particles):
        self.hp -= dmg
        particles.spawn_sparkle(self.x, self.y - 10, 4, (255, 100, 150))
        if self.hp <= 0:
            self.alive = False
            particles.spawn_sparkle(self.x, self.y, 12, (255, 200, 100))

    def draw(self, screen, cam):
        if not self.alive:
            return
        sx, sy = int(self.x - cam.x) - 24, int(self.y - cam.y) - 24 + math.sin(self.t * 3) * 3
        if -60 < sx < 1084 and -60 < sy < 700:
            img = AssetManager.get_surface("shadow_%d" % self.frame)
            screen.blit(img, (sx, sy))


# =============================================================================
# PLAYER
# =============================================================================
class Player:
    def __init__(self, name, cid, x, y):
        self.name = name
        self.cid = cid
        self.x, self.y = float(x), float(y)
        self.speed = 230
        self.facing = DIR_DOWN
        self.frame = 0
        self.anim_t = 0.0
        self.moving = False
        self.mounted = None
        self.level = 1
        self.xp = 0
        self.hp = 100
        self.max_hp = 100
        self.hunger = 100
        self.sleep = 100
        self.attack_cd = 0.0
        self.attack_anim = 0.0
        self.zoomies_cd = 0.0
        self.zoomies_active = 0.0
        self.ultimate_cd = 0.0
        self.gestures = set()

    @staticmethod
    def xp_needed(level):
        return int(XP_BASE * (XP_GROWTH ** (level - 1)) + 15)

    def gain_xp(self, amount, game):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_needed(self.level):
            self.xp -= self.xp_needed(self.level)
            self.level += 1
            self.max_hp += 15
            self.hp = self.max_hp
            leveled = True
        if leveled:
            game.particles.spawn_sparkle(self.x, self.y - 40, 14, (255, 215, 130))
            game.notify("%s sube a nivel %d!" % (self.name, self.level))
        return leveled

    def set_move(self, dx, dy, dt):
        speed = self.speed * (1.6 if self.zoomies_active > 0 else 1.0)
        if dx or dy:
            ln = math.hypot(dx, dy)
            self.x = clamp(self.x + dx / ln * speed * dt, 20, BIOME_SIZE * 3 - 20)
            self.y = clamp(self.y + dy / ln * speed * dt, 20, BIOME_SIZE * 2 - 20)
            self.facing = (DIR_RIGHT if abs(dx) > abs(dy) and dx > 0 else
                           DIR_LEFT if abs(dx) > abs(dy) else
                           DIR_DOWN if dy > 0 else DIR_UP)
            self.moving = True
        else:
            self.moving = False
        if self.moving:
            self.anim_t += dt
            if self.anim_t > 0.15:
                self.anim_t = 0
                self.frame = (self.frame + 1) % ANIM_FRAMES
        else:
            self.frame = 0
        self.attack_cd = max(0.0, self.attack_cd - dt)
        self.attack_anim = max(0.0, self.attack_anim - dt)
        self.zoomies_cd = max(0.0, self.zoomies_cd - dt)
        self.zoomies_active = max(0.0, self.zoomies_active - dt)
        self.ultimate_cd = max(0.0, self.ultimate_cd - dt)

    def follow_target(self, tx, ty, dt, min_dist=80):
        d = distance(self.x, self.y, tx, ty)
        if d > min_dist:
            self.set_move((tx - self.x) / d, (ty - self.y) / d, dt)
        else:
            self.set_move(0, 0, dt)

    def attack(self, enemies, particles, game):
        if self.attack_cd > 0:
            return 0
        self.attack_cd = 0.4
        self.attack_anim = 0.25
        hits = 0
        ox = {DIR_RIGHT: 55, DIR_LEFT: -55}.get(self.facing, 0)
        oy = {DIR_DOWN: 45, DIR_UP: -45}.get(self.facing, 0)
        for enemy in enemies:
            if not enemy.alive:
                continue
            if distance(enemy.x, enemy.y, self.x + ox, self.y + oy) < 60:
                enemy.damage(2, particles)
                hits += 1
                if not enemy.alive:
                    self.gain_xp(20, game)
                    game.gacha.add_crystals(5)
                    game.quest.event("kill_shadow", 1)
        return hits

    def ultimate(self, partner, enemies, particles, game):
        if self.ultimate_cd > 0 or not partner:
            return 0
        self.ultimate_cd = 30.0
        hits = 0
        for enemy in enemies:
            if not enemy.alive:
                continue
            if distance(enemy.x, enemy.y, self.x, self.y) < 250:
                enemy.damage(8, particles)
                hits += 1
                if not enemy.alive:
                    self.gain_xp(30, game)
                    partner.gain_xp(30, game)
                    game.gacha.add_crystals(10)
        particles.spawn_sparkle(self.x, self.y, 20, (255, 110, 170))
        particles.spawn_hearts((self.x + partner.x) / 2, (self.y + partner.y) / 2, 12)
        return hits

    def draw(self, screen, cam, t):
        sheet = AssetManager.get_sheet(self.cid)
        sx, sy = int(self.x - cam.x) - 32, int(self.y - cam.y) - 56
        # Sombra
        s_shadow = pygame.Surface((32, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(s_shadow, (50, 35, 45, 80), (0, 0, 32, 10))
        screen.blit(s_shadow, (sx + 16, sy + 56))
        # Aura zoomies
        if self.zoomies_active > 0:
            pygame.draw.circle(screen, (255, 200, 100, 100), (sx + 32, sy + 32),
                               int(40 + math.sin(t * 20) * 5), 2)
        # Sprite del gato
        frame_surf = sheet.frame(self.frame, self.facing)
        if self.attack_anim > 0:
            rot = 10 * math.sin(self.attack_anim * 30)
            frame_surf = pygame.transform.rotate(frame_surf, rot)
            r = frame_surf.get_rect(center=(sx + 32, sy + 32))
            screen.blit(frame_surf, r)
        else:
            screen.blit(frame_surf, (sx, sy))
        # Barra de vida mini
        hp_w = 40
        hp_rect = pygame.Rect(sx + 12, sy - 10, hp_w, 4)
        draw_round_rect(screen, (40, 40, 40), hp_rect, 2)
        fill_w = int(hp_w * self.hp / self.max_hp)
        draw_round_rect(screen, (255, 100, 100), (hp_rect.x, hp_rect.y, fill_w, 4), 2)


# =============================================================================
# MOUNT (sprite compuesto)
# =============================================================================
class Mount:
    def __init__(self, uid, name, body_color, mane, stats, x, y):
        self.uid = uid
        self.name = name
        self.body = body_color
        self.mane = mane
        self.stats = stats
        self.x, self.y = float(x), float(y)
        self.facing = DIR_DOWN
        self.frame = 0
        self.anim_t = 0.0
        self.stamina = stats["stamina"]
        self.max_stamina = stats["stamina"]
        self.rider = None

    def update(self, dt, target=None):
        if self.rider is not None:
            return
        if target is not None:
            d = distance(self.x, self.y, target[0], target[1])
            if d > 100:
                dx, dy = (target[0] - self.x) / d, (target[1] - self.y) / d
                self.x += dx * 150 * dt
                self.y += dy * 150 * dt
                self.facing = DIR_RIGHT if abs(dx) > abs(dy) and dx > 0 else \
                              DIR_LEFT if abs(dx) > abs(dy) else \
                              DIR_DOWN if dy > 0 else DIR_UP
        self.stamina = clamp(self.stamina + 15 * dt, 0, self.max_stamina)
        self.anim_t += dt
        if self.anim_t > 0.15:
            self.anim_t = 0
            self.frame = (self.frame + 1) % ANIM_FRAMES

    def draw(self, screen, cam):
        if self.rider:
            return
        sheet = AssetManager.get_sheet(self.uid)
        sx, sy = int(self.x - cam.x) - 32, int(self.y - cam.y) - 54
        s_shadow = pygame.Surface((40, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(s_shadow, (50, 35, 45, 80), (0, 0, 40, 12))
        screen.blit(s_shadow, (sx + 12, sy + 58))
        screen.blit(sheet.frame(self.frame, self.facing), (sx, sy))

    def draw_mounted(self, rider, screen, cam, t):
        sheet_cat = AssetManager.get_sheet(rider.cid)
        sheet_uni = AssetManager.get_sheet(self.uid)
        key = (rider.cid, self.uid, self.facing, self.frame)
        surf = AssetManager.get_mount(key, lambda: ArtFactory.build_mount_sprite(
            sheet_cat, sheet_uni, self.facing, self.frame))
        sx, sy = int(self.x - cam.x) - 48, int(self.y - cam.y) - 78
        s_shadow = pygame.Surface((70, 14), pygame.SRCALPHA)
        pygame.draw.ellipse(s_shadow, (50, 35, 45, 90), (0, 0, 70, 14))
        screen.blit(s_shadow, (sx + 14, sy + 96))
        screen.blit(surf, (sx, sy))
        # Vínculo visual
        bond = 1 + 0.5 * math.sin(t * 3)
        for i in range(3):
            angle = t * 2 + i * 2.09
            px = sx + 48 + math.cos(angle) * 40
            py = sy + 50 + math.sin(angle) * 25
            pygame.draw.circle(screen, (255, 200, 230, 120), (int(px), int(py)), int(3 + bond))


# =============================================================================
# COUPLE SYSTEM (afinidad entre Teko & Tomás)
# =============================================================================
class CoupleSystem:
    def __init__(self):
        self.affection = 0
        self.cooldowns = {"talk": 0.0, "pet": 0.0, "sleep": 0.0, "purr": 0.0}
        self.story_log = []
        self.hug_timer = 0.0

    @property
    def level(self):
        lvl = 1
        for i, th in enumerate(COUPLE_THRESHOLDS):
            if self.affection >= th:
                lvl = i + 1
        return lvl

    @property
    def progress(self):
        lvl = self.level
        if lvl >= len(COUPLE_THRESHOLDS):
            return 1.0
        lo = COUPLE_THRESHOLDS[lvl - 1]
        hi = COUPLE_THRESHOLDS[lvl] if lvl < len(COUPLE_THRESHOLDS) else lo + 1
        return clamp((self.affection - lo) / max(1, hi - lo), 0, 1)

    def add_affection(self, n, game):
        before = self.level
        self.affection += n
        if self.level > before:
            game.notify("Afinidad de pareja: nivel %d!" % self.level)
            game.particles.spawn_hearts(game.controlled.x, game.controlled.y - 60, 16)
        return self.level > before

    def ready(self, k):
        return self.cooldowns.get(k, 0.0) <= 0

    def use(self, k, secs):
        self.cooldowns[k] = secs

    def tick(self, dt, game):
        for k in self.cooldowns:
            self.cooldowns[k] = max(0.0, self.cooldowns[k] - dt)
        self.hug_timer = max(0.0, self.hug_timer - dt)


# =============================================================================
# GACHA SYSTEM
# =============================================================================
class GachaSystem:
    RATES = {"N": 0.52, "R": 0.30, "SR": 0.14, "SSR": 0.04}
    PITY_SSR = 30
    PITY_SR = 10

    def __init__(self):
        self.crystals = 100
        self.history = []
        self.pity = {"ssr": 0, "sr": 0}
        self.banners = {
            "unicornios": {
                "pool": {"R": [("alba", "Alba", (250, 250, 255),
                                [(255, 150, 190), (255, 220, 150), (160, 220, 255)],
                                {"speed": 300, "stamina": 80})],
                         "SR": [("rosa", "Rosa", (255, 225, 235),
                                [(170, 240, 200), (140, 220, 255), (220, 190, 255)],
                                {"speed": 350, "stamina": 100})],
                         "SSR": [("dorado", "Dorado", (255, 240, 200),
                                  [(255, 200, 120), (255, 160, 160), (255, 230, 180)],
                                  {"speed": 400, "stamina": 150})]}
            },
            "mascotas": {
                "pool": {"R": [("mariposa", "Mariposa Lunar"), ("abeja", "Abeja Dorada")],
                         "SR": [("buho", "Búho Sabio")],
                         "SSR": [("dragon", "Dragón Kawaii")]}
            }
        }
        self.owned_unis = {}
        self.owned_mascots = set()

    def add_crystals(self, n):
        self.crystals = max(0, self.crystals + n)

    def _roll(self):
        self.pity["ssr"] += 1
        self.pity["sr"] += 1
        if self.pity["ssr"] >= self.PITY_SSR:
            rar = "SSR"
        elif self.pity["sr"] >= self.PITY_SR:
            rar = "SR"
        else:
            r, acc, rar = random.random(), 0.0, "N"
            for k in ("SSR", "SR", "R", "N"):
                acc += self.RATES[k]
                if r <= acc:
                    rar = k
                    break
        if rar == "SSR":
            self.pity["ssr"] = self.pity["sr"] = 0
        elif rar == "SR":
            self.pity["sr"] = 0
        return rar

    def pull(self, banner_name, count, game):
        cost = 10 if count == 1 else 90
        if self.crystals < cost:
            return None
        self.crystals -= cost
        banner = self.banners.get(banner_name, self.banners["unicornios"])
        results = []
        for _ in range(count):
            rar = self._roll()
            if rar == "N":
                self.add_crystals(5)
                res = {"rarity": "N", "name": "Pétalo de sakura (+5)", "type": "item"}
            else:
                pool = banner["pool"].get(rar, banner["pool"]["R"])
                item = random.choice(pool)
                if banner_name == "unicornios":
                    uid, name, body, mane, stats = item
                    new = uid not in self.owned_unis
                    if new:
                        self.owned_unis[uid] = {"name": name, "body": body, "mane": mane, "stats": stats}
                        mount = Mount(uid, name, body, mane, stats,
                                      game.controlled.x + 100, game.controlled.y)
                        game.mounts.append(mount)
                    else:
                        self.add_crystals(30)
                    res = {"rarity": rar, "name": name, "type": "unicorn", "new": new}
                else:
                    mid, name = item
                    new = mid not in self.owned_mascots
                    if new:
                        self.owned_mascots.add(mid)
                    else:
                        self.add_crystals(20)
                    res = {"rarity": rar, "name": name, "type": "mascot", "new": new}
            self.history.append(res)
            results.append(res)
        return results


# =============================================================================
# QUEST MANAGER (Timer dinámico cada 10 min)
# =============================================================================
class QuestManager:
    def __init__(self):
        self.quests = []
        self.completed = set()
        self.progress = {}
        self.refresh_timer = 0.0
        self.REFRESH_INTERVAL = 600.0  # 10 minutos
        self._generate_quests()

    def _generate_quests(self):
        templates = [
            {"id": "q_crystals", "name": "Recolector de Cristales", "type": "collect_crystal",
             "target": 5, "xp": 30, "cr": 20, "desc": "Recoge 5 cristales de energía"},
            {"id": "q_shadows", "name": "Cazador de Sombras", "type": "kill_shadow",
             "target": 3, "xp": 50, "cr": 40, "desc": "Derrota 3 perros sombra"},
            {"id": "q_explore", "name": "Explorador del Mundo", "type": "travel",
             "target": 500, "xp": 40, "cr": 30, "desc": "Viaja 500 pasos"},
            {"id": "q_affinity", "name": "Vínculo de Pareja", "type": "affinity",
             "target": 20, "xp": 60, "cr": 50, "desc": "Aumenta la afinidad 20 puntos"},
            {"id": "q_insects", "name": "Caza de Insectos", "type": "hunt_insect",
             "target": 2, "xp": 35, "cr": 25, "desc": "Caza 2 insectos"},
            {"id": "q_mount", "name": "Jinete de Unicornios", "type": "ride",
             "target": 300, "xp": 45, "cr": 35, "desc": "Recorre 300 pasos montado"},
            {"id": "q_sleep", "name": "Siesta Juntos", "type": "sleep_together",
             "target": 1, "xp": 40, "cr": 30, "desc": "Duerme acurrucado con tu pareja"},
            {"id": "q_ultimate", "name": "Ataque Definitivo", "type": "ultimate",
             "target": 1, "xp": 80, "cr": 70, "desc": "Usa el ataque definitivo de pareja"},
        ]
        chosen = random.sample(templates, min(4, len(templates)))
        self.quests = []
        for q in chosen:
            q = dict(q)
            q["current"] = 0
            q["done"] = False
            self.quests.append(q)

    def update(self, dt, game):
        self.refresh_timer += dt
        if self.refresh_timer >= self.REFRESH_INTERVAL:
            self.refresh_timer = 0
            self._generate_quests()
            game.notify("¡Nuevas misiones disponibles!")

    def event(self, etype, amount, game):
        for q in self.quests:
            if q["done"] or q["type"] != etype:
                continue
            q["current"] += amount
            if q["current"] >= q["target"]:
                q["done"] = True
                self.completed.add(q["id"])
                game.gacha.add_crystals(q["cr"])
                game.controlled.gain_xp(q["xp"], game)
                game.notify("Misión completada: %s (+%d XP)" % (q["name"], q["xp"]))


# =============================================================================
# UI MANAGER (Paneles)
# =============================================================================
class Button:
    def __init__(self, x, y, w, h, label, callback, color=(255, 183, 203)):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.callback = callback
        self.color = color
        self.enabled = True

    def draw(self, screen, font, mouse):
        hover = self.rect.collidepoint(mouse) and self.enabled
        col = self.color if self.enabled else (170, 170, 170)
        draw_round_rect(screen, (255, 210, 224) if hover else col, self.rect, 10)
        t = font.render(self.label, True, (80, 50, 70))
        screen.blit(t, (self.rect.centerx - t.get_width() // 2,
                        self.rect.centery - t.get_height() // 2))

    def handle(self, pos):
        if self.enabled and self.rect.collidepoint(pos):
            self.callback()
            return True
        return False


class Panel:
    def __init__(self, game, title):
        self.game = game
        self.title = title
        self.buttons = []
        self.rect = pygame.Rect(50, 40, 924, 560)

    def draw_base(self, screen, fb):
        draw_round_rect(screen, (255, 246, 250, 240), self.rect, 22)
        pygame.draw.rect(screen, (255, 160, 200), self.rect, 4, border_radius=22)
        t = fb.render(self.title, True, (200, 90, 130))
        screen.blit(t, (self.rect.centerx - t.get_width() // 2, self.rect.top + 12))


class GachaPanel(Panel):
    def __init__(self, game):
        super().__init__(game, "Invocación Gacha")
        self.banner = "unicornios"
        self.results = []
        self.reveal_t = 0.0
        x, y = self.rect.x + 30, self.rect.y + 470
        self.buttons = [
            Button(x, y, 180, 40, "x1 (10)", lambda: self.do_pull(1)),
            Button(x + 200, y, 190, 40, "x10 (90)", lambda: self.do_pull(10)),
            Button(x + 650, y, 160, 40, "Cerrar", self.close, (200, 200, 210)),
        ]

    def do_pull(self, n):
        res = self.game.gacha.pull(self.banner, n, self.game)
        if res:
            self.results = res
            self.reveal_t = 0.0

    def close(self):
        self.game.state = "explore"

    def update(self, dt):
        if self.results:
            self.reveal_t += dt

    def draw(self, screen, fonts):
        self.draw_base(screen, fonts["big"])
        f, fs = fonts["med"], fonts["small"]
        g = self.game.gacha
        x, y = self.rect.x + 30, self.rect.y + 60
        # Banner selector
        for i, bname in enumerate(["unicornios", "mascotas"]):
            r = pygame.Rect(x, y + i * 44, 200, 38)
            sel = bname == self.banner
            draw_round_rect(screen, (255, 200, 220) if sel else (245, 232, 238), r, 10)
            screen.blit(f.render(bname.capitalize(), True, (110, 70, 95)), (x + 12, y + i * 44 + 8))
        screen.blit(f.render("Cristales: %d" % g.crystals, True, (90, 130, 200)), (x + 250, y))
        screen.blit(fs.render("Pity SSR %d/30 | SR %d/10" % (g.pity["ssr"], g.pity["sr"]),
                              True, (140, 110, 130)), (x + 250, y + 30))
        # Reveal
        for i, r in enumerate(self.results[:10]):
            delay = i * 0.12
            prog = clamp((self.reveal_t - delay) / 0.3, 0, 1)
            if prog <= 0:
                continue
            cx = x + 50 + (i % 5) * 160
            cy = y + 120 + (i // 5) * 170
            scale = 0.4 + 0.6 * prog
            w, h = int(140 * scale), int(150 * scale)
            col = RARITY_COLORS.get(r.get("rarity", "N"), (170, 170, 170))
            draw_round_rect(screen, col, (cx - 4, cy - 4, w + 8, h + 8), 14, alpha=80)
            draw_round_rect(screen, (255, 252, 255), (cx, cy, w, h), 12)
            pygame.draw.rect(screen, col, (cx, cy, w, h), 3, border_radius=12)
            if prog >= 1:
                t = fs.render(r.get("name", "?")[:14], True, (90, 60, 80))
                screen.blit(t, (cx + w // 2 - t.get_width() // 2, cy + h // 2 - 14))
                tag = "[%s]" % r.get("rarity", "N")
                if r.get("new"):
                    tag += " NUEVO"
                t = fs.render(tag, True, col)
                screen.blit(t, (cx + w // 2 - t.get_width() // 2, cy + h // 2 + 10))
        self.draw_buttons(screen, f)

    def draw_buttons(self, screen, f):
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(screen, f, m)

    def on_click(self, pos):
        return any(b.handle(pos) for b in self.buttons)


class CouplePanel(Panel):
    def __init__(self, game):
        super().__init__(game, "Teko & Tomás - Pareja")
        x, y = self.rect.x + 30, self.rect.y + 430
        self.buttons = [
            Button(x, y, 150, 38, "Hablar", lambda: game.try_interact("talk")),
            Button(x + 165, y, 150, 38, "Caricia", lambda: game.try_interact("pet")),
            Button(x + 330, y, 150, 38, "Dormir", lambda: game.try_interact("sleep")),
            Button(x + 495, y, 150, 38, "Ronroneo", lambda: game.try_interact("purr")),
            Button(x + 700, y, 140, 38, "Cerrar", self.close, (200, 200, 210)),
        ]

    def close(self):
        self.game.state = "explore"

    def draw(self, screen, fonts):
        self.draw_base(screen, fonts["big"])
        f, fs = fonts["med"], fonts["small"]
        c = self.game.couple
        x, y = self.rect.x + 30, self.rect.y + 60
        screen.blit(f.render("Teko & Tomás: pareja homosexual de gatos enamorados",
                             True, (200, 90, 130)), (x, y))
        screen.blit(f.render("Nivel de amor: %d   Afinidad: %d" % (c.level, c.affection),
                             True, (120, 80, 100)), (x, y + 34))
        bar = pygame.Rect(x, y + 70, 500, 20)
        draw_round_rect(screen, (240, 225, 232), bar, 10)
        if c.progress > 0:
            draw_round_rect(screen, (255, 120, 170),
                            (bar.x, bar.y, int(bar.w * c.progress), bar.h), 10)
        # Stats felinos
        sy = y + 120
        for i, p in enumerate(self.game.players):
            py = sy + i * 80
            screen.blit(f.render("%s (nv%d)" % (p.name, p.level), True, (120, 80, 100)), (x, py))
            # HP
            bar = pygame.Rect(x, py + 26, 300, 12)
            draw_round_rect(screen, (240, 225, 232), bar, 6)
            draw_round_rect(screen, (255, 110, 130),
                            (bar.x, bar.y, int(bar.w * p.hp / p.max_hp), bar.h), 6)
            screen.blit(fs.render("HP %d/%d" % (int(p.hp), p.max_hp), True, (150, 90, 100)), (x + 320, py + 24))
            # Hunger
            bar = pygame.Rect(x, py + 42, 300, 10)
            draw_round_rect(screen, (240, 225, 232), bar, 5)
            draw_round_rect(screen, (255, 190, 100),
                            (bar.x, bar.y, int(bar.w * p.hunger / 100), bar.h), 5)
            screen.blit(fs.render("Hambre %d" % int(p.hunger), True, (150, 130, 80)), (x + 320, py + 40))
            # Sleep
            bar = pygame.Rect(x, py + 56, 300, 10)
            draw_round_rect(screen, (240, 225, 232), bar, 5)
            draw_round_rect(screen, (140, 180, 255),
                            (bar.x, bar.y, int(bar.w * p.sleep / 100), bar.h), 5)
            screen.blit(fs.render("Sueño %d" % int(p.sleep), True, (90, 130, 180)), (x + 320, py + 54))
        self.draw_buttons(screen, f)

    def draw_buttons(self, screen, f):
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(screen, f, m)

    def on_click(self, pos):
        return any(b.handle(pos) for b in self.buttons)


class QuestPanel(Panel):
    def __init__(self, game):
        super().__init__(game, "Misiones Dinámicas")
        self.buttons = [Button(self.rect.x + 720, self.rect.y + 480, 150, 40,
                               "Cerrar", self.close, (200, 200, 210))]

    def close(self):
        self.game.state = "explore"

    def draw(self, screen, fonts):
        self.draw_base(screen, fonts["big"])
        f, fs = fonts["med"], fonts["small"]
        x, y = self.rect.x + 30, self.rect.y + 60
        remaining = int(self.game.quest.REFRESH_INTERVAL - self.game.quest.refresh_timer)
        m, s = divmod(max(0, remaining), 60)
        screen.blit(f.render("Próxima renovación en: %02d:%02d" % (m, s), True, (120, 80, 100)), (x, y))
        for i, q in enumerate(self.game.quest.quests):
            ry = y + 50 + i * 70
            col = (140, 200, 140) if q["done"] else (200, 150, 120)
            screen.blit(f.render(q["name"], True, col), (x, ry))
            screen.blit(fs.render(q["desc"], True, (130, 110, 125)), (x + 20, ry + 26))
            prog = clamp(q["current"] / q["target"], 0, 1)
            bar = pygame.Rect(x, ry + 46, 600, 12)
            draw_round_rect(screen, (240, 225, 232), bar, 6)
            draw_round_rect(screen, col, (bar.x, bar.y, int(bar.w * prog), bar.h), 6)
            screen.blit(fs.render("%d/%d" % (min(q["current"], q["target"]), q["target"]),
                                  True, (120, 100, 120)), (x + 620, ry + 42))
        self.draw_buttons(screen, f)

    def draw_buttons(self, screen, f):
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(screen, f, m)

    def on_click(self, pos):
        return any(b.handle(pos) for b in self.buttons)


class HelpPanel(Panel):
    def __init__(self, game):
        super().__init__(game, "Ayuda / Controles")
        self.buttons = [Button(self.rect.x + 360, self.rect.y + 470, 150, 40,
                               "Cerrar", self.close, (200, 200, 210))]

    def close(self):
        self.game.state = "explore"

    def draw(self, screen, fonts):
        self.draw_base(screen, fonts["big"])
        fs = fonts["small"]
        if IS_MOBILE:
            lines = [
                "Joystick Izq: mover | A: interactuar | B: atacar",
                "X: montar | Y: gacha | LB: cambiar gato | RB: menu",
                "", "Toca los botones en pantalla para cada acción.",
                "Las misiones se renuevan cada 10 minutos.",
            ]
        else:
            lines = [
                "WASD/Flechas: mover | Q: cambiar gato | E: interactuar",
                "F: montar | ESPACIO: atacar | SHIFT: zoomies",
                "U: ataque definitivo (pareja) | B: gacha | C: pareja",
                "J: misiones | H: cazar insecto | F1: ayuda",
                "", "Las misiones se renuevan cada 10 minutos reales.",
                "El ciclo día/noche cambia el ambiente del mundo.",
            ]
        for i, ln in enumerate(lines):
            screen.blit(fs.render(ln, True, (100, 70, 90)),
                        (self.rect.x + 60, self.rect.y + 70 + i * 26))
        self.draw_buttons(screen, fonts["med"])

    def draw_buttons(self, screen, f):
        m = pygame.mouse.get_pos()
        for b in self.buttons:
            b.draw(screen, f, m)

    def on_click(self, pos):
        return any(b.handle(pos) for b in self.buttons)


class UIManager:
    def __init__(self, game):
        self.panels = {"gacha": GachaPanel(game), "couple": CouplePanel(game),
                       "quests": QuestPanel(game), "help": HelpPanel(game)}

    def update(self, dt, state):
        if state in self.panels and hasattr(self.panels[state], "update"):
            self.panels[state].update(dt)

    def draw(self, screen, fonts, state):
        if state in self.panels:
            self.panels[state].draw(screen, fonts)

    def click(self, state, pos):
        if state in self.panels:
            return self.panels[state].on_click(pos)
        return False


# =============================================================================
# GAME (bucle principal)
# =============================================================================
class Game:
    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        if IS_MOBILE:
            self.screen_w, self.screen_h = info.current_w, info.current_h
            self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), FULLSCREEN)
        else:
            self.screen_w, self.screen_h = 1024, 640
            self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), RESIZABLE)
        pygame.display.set_caption("Sakura Neko Open World - Teko & Tomás")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "explore"
        self.time = 0.0
        base = "comic sans ms, verdana, arial"
        self.fonts = {"big": pygame.font.SysFont(base, 28, bold=True),
                      "med": pygame.font.SysFont(base, 18),
                      "small": pygame.font.SysFont(base, 14)}
        ArtFactory.generate_all()
        self.input = InputManager(self.screen_w, self.screen_h)
        self.particles = ParticleSystem()
        self.camera = Camera()
        self.world = World()
        self.weather = WeatherSystem()
        self.daynight = DayNightCycle()
        self.gacha = GachaSystem()
        self.couple = CoupleSystem()
        self.quest = QuestManager()
        self.ui = UIManager(self)
        self.players = []
        # Teko y Tomás: la pareja
        self.players.append(Player("Teko", "teko", BIOME_SIZE // 2, BIOME_SIZE // 2))
        self.players.append(Player("Tomás", "tomas", BIOME_SIZE // 2 + 80, BIOME_SIZE // 2))
        self.controlled = self.players[0]
        self.partner = self.players[1]
        self.mounts = []
        self.enemies = []
        self._spawn_initial_enemies()
        self.dialogue = None
        self.notify_text = ""
        self.notify_t = 0.0
        self.sleep_anim_t = 0.0

    def _spawn_initial_enemies(self):
        # Perros sombra dispersos por biomas peligrosos
        for bname in ["cristal", "neon", "desierto"]:
            biome = self.world.biomes[bname]
            for _ in range(3):
                self.enemies.append(ShadowDog(
                    biome.x + random.uniform(200, BIOME_SIZE-200),
                    biome.y + random.uniform(200, BIOME_SIZE-200)))

    def partner_of_controlled(self):
        return self.partner if self.controlled is self.players[0] else self.players[0]

    def switch_controlled(self):
        self.controlled, self.partner = self.partner, self.controlled
        self.notify("Ahora controlas a %s" % self.controlled.name)

    def notify(self, text):
        self.notify_text = text
        self.notify_t = 3.0

    def try_interact(self, action):
        partner = self.partner_of_controlled()
        if distance(self.controlled.x, self.controlled.y, partner.x, partner.y) > 130:
            self.notify("Acércate a tu pareja para interactuar.")
            return
        c = self.couple
        if action == "talk" and c.ready("talk"):
            c.use("talk", 2.0)
            c.add_affection(3, self)
            self.particles.spawn_hearts(partner.x, partner.y - 50, 4)
            self.quest.event("affinity", 3, self)
            self.notify("%s y %s comparten palabras tiernas" % (self.controlled.name, partner.name))
        elif action == "pet" and c.ready("pet") and c.level >= 2:
            c.use("pet", 3.0)
            c.add_affection(5, self)
            self.particles.spawn_hearts((self.controlled.x + partner.x) / 2,
                                         (self.controlled.y + partner.y) / 2 - 50, 8)
            self.quest.event("affinity", 5, self)
        elif action == "sleep" and c.ready("sleep") and c.level >= 3:
            c.use("sleep", 10.0)
            self.sleep_anim_t = 2.0
            self.controlled.sleep = 100
            partner.sleep = 100
            c.add_affection(10, self)
            self.quest.event("affinity", 10, self)
            self.quest.event("sleep_together", 1, self)
            self.particles.spawn_hearts((self.controlled.x + partner.x) / 2,
                                         (self.controlled.y + partner.y) / 2 - 60, 12)
            self.notify("Ambos duermen acurrucados...")
        elif action == "purr" and c.ready("purr") and c.level >= 2:
            c.use("purr", 5.0)
            self.controlled.hp = min(self.controlled.max_hp, self.controlled.hp + 20)
            partner.hp = min(partner.max_hp, partner.hp + 20)
            c.add_affection(4, self)
            self.particles.spawn_sparkle(self.controlled.x, self.controlled.y, 6, (255, 220, 200))
            self.particles.spawn_sparkle(partner.x, partner.y, 6, (255, 220, 200))

    def try_mount(self):
        if self.controlled.mounted:
            u = self.controlled.mounted
            u.rider = None
            self.controlled.mounted = None
            self.controlled.y = u.y + 34
            return
        for m in self.mounts:
            if distance(m.x, m.y, self.controlled.x, self.controlled.y) < 80:
                self.controlled.mounted = m
                m.rider = self.controlled
                self.notify("Montando a %s" % m.name)
                return
        self.notify("No hay unicornio cerca para montar")

    def try_hunt_insect(self):
        current_biome = self.world.get_biome_at(self.controlled.x, self.controlled.y)
        for ins in current_biome.insects:
            if not ins["alive"]:
                continue
            wx, wy = current_biome.x + ins["x"], current_biome.y + ins["y"]
            if distance(wx, wy, self.controlled.x, self.controlled.y) < 50:
                ins["alive"] = False
                self.controlled.hunger = min(100, self.controlled.hunger + 30)
                self.particles.spawn_sparkle(wx, wy, 8, (200, 255, 180))
                self.quest.event("hunt_insect", 1, self)
                self.notify("¡Insecto cazado! Hambre recuperada")
                return
        self.notify("No hay insectos cerca")

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 1 / 30)
            self.time += dt
            self._events()
            self._update(dt)
            self._draw()
            pygame.display.flip()
        pygame.quit()

    def _events(self):
        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    if self.state != "explore":
                        self.state = "explore"
                    else:
                        self.running = False
                elif self.state == "explore":
                    self._keys(ev.key)
            elif ev.type == pygame.VIDEORESIZE:
                self.screen_w, self.screen_h = ev.w, ev.h
                self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), RESIZABLE)
                self.input = InputManager(self.screen_w, self.screen_h)
        self.input.update(events)

    def _keys(self, key):
        if key == pygame.K_q:
            self.switch_controlled()
        elif key == pygame.K_e:
            self.try_interact("talk")
        elif key == pygame.K_r:
            self.try_interact("pet")
        elif key == pygame.K_t:
            self.try_interact("sleep")
        elif key == pygame.K_y:
            self.try_interact("purr")
        elif key == pygame.K_f:
            self.try_mount()
        elif key == pygame.K_SPACE:
            biome = self.world.get_biome_at(self.controlled.x, self.controlled.y)
            self.controlled.attack(self.enemies, self.particles, self)
        elif key == pygame.K_LSHIFT:
            if self.controlled.zoomies_cd <= 0:
                self.controlled.zoomies_active = 2.0
                self.controlled.zoomies_cd = 8.0
        elif key == pygame.K_u:
            partner = self.partner_of_controlled()
            if self.controlled.ultimate(partner, self.enemies, self.particles, self):
                self.quest.event("ultimate", 1, self)
        elif key == pygame.K_h:
            self.try_hunt_insect()
        elif key == pygame.K_b:
            self.state = "gacha"
        elif key == pygame.K_c:
            self.state = "couple"
        elif key == pygame.K_j:
            self.state = "quests"
        elif key == pygame.K_F1:
            self.state = "help"

    def _update(self, dt):
        self.daynight.update(dt)
        self.weather.update(dt, self.camera.get_current_biome())
        self.couple.tick(dt, self)
        self.quest.update(dt, self)
        self.notify_t = max(0.0, self.notify_t - dt)
        self.ui.update(dt, self.state)

        if self.state != "explore":
            return

        if self.sleep_anim_t > 0:
            self.sleep_anim_t -= dt
            return

        dx, dy = self.input.get_movement()

        # Táctiles
        if self.input.button_pressed("lb"):
            self.switch_controlled()
        if self.input.button_pressed("a"):
            self.try_interact("talk")
        if self.input.button_pressed("b"):
            biome = self.world.get_biome_at(self.controlled.x, self.controlled.y)
            self.controlled.attack(self.enemies, self.particles, self)
        if self.input.button_pressed("x"):
            self.try_mount()
        if self.input.button_pressed("y"):
            self.state = "gacha"
        if self.input.button_pressed("rb"):
            self.state = "couple"

        # Movimiento
        prev_x, prev_y = self.controlled.x, self.controlled.y
        if self.controlled.mounted:
            u = self.controlled.mounted
            if dx or dy:
                ln = math.hypot(dx, dy)
                spd = u.stats["speed"]
                u.x = clamp(u.x + dx / ln * spd * dt, 20, BIOME_SIZE * 3 - 20)
                u.y = clamp(u.y + dy / ln * spd * dt, 20, BIOME_SIZE * 2 - 20)
                u.facing = DIR_RIGHT if abs(dx) > abs(dy) and dx > 0 else \
                           DIR_LEFT if abs(dx) > abs(dy) else \
                           DIR_DOWN if dy > 0 else DIR_UP
                u.anim_t += dt
                if u.anim_t > 0.14:
                    u.anim_t = 0
                    u.frame = (u.frame + 1) % ANIM_FRAMES
                self.controlled.x, self.controlled.y = u.x, u.y - 12
                self.controlled.facing = u.facing
                moved = distance(prev_x, prev_y, self.controlled.x, self.controlled.y)
                self.quest.event("ride", moved, self)
                self.quest.event("travel", moved, self)
        else:
            self.controlled.set_move(dx, dy, dt)
            moved = distance(prev_x, prev_y, self.controlled.x, self.controlled.y)
            if moved > 0:
                self.quest.event("travel", moved, self)

        # Partner sigue
        self.partner.follow_target(self.controlled.x, self.controlled.y, dt)

        # Enemigos
        for enemy in self.enemies:
            dmg = enemy.update(dt, self.controlled)
            if dmg:
                self.controlled.hp = max(0, self.controlled.hp - dmg)
                if self.controlled.hp <= 0:
                    self.controlled.hp = self.controlled.max_hp // 2
                    self.notify("¡Te desmayaste! Recuperas algo de vida.")

        # Monturas sin jinete siguen
        for m in self.mounts:
            if m.rider is None:
                m.update(dt, (self.controlled.x, self.controlled.y))

        # Respawn enemigos
        alive_enemies = [e for e in self.enemies if e.alive]
        if len(alive_enemies) < 6 and random.random() < 0.005:
            biome = self.world.biomes[random.choice(["cristal", "neon", "desierto"])]
            self.enemies.append(ShadowDog(
                biome.x + random.uniform(200, BIOME_SIZE-200),
                biome.y + random.uniform(200, BIOME_SIZE-200)))

        # Regen hambre/sueño
        for p in self.players:
            p.hunger = max(0, p.hunger - 0.5 * dt)
            p.sleep = max(0, p.sleep - 0.3 * dt)
            if p.hunger < 30:
                p.hp = max(0, p.hp - 1 * dt)
            p.hp = min(p.max_hp, p.hp + 1 * dt)

        # Bioma y clima
        self.world.update(dt, self.time, self.particles, self)
        self.weather.spawn_particles(self.particles, self.camera)
        self.camera.follow(self.controlled.x, self.controlled.y, dt)
        self.particles.update(dt, self.time)

    def _draw(self):
        self.screen.fill((20, 20, 30))
        self.world.draw(self.screen, self.camera, self.time)

        # Enemigos
        for e in self.enemies:
            e.draw(self.screen, self.camera)

        # Monturas sin jinete
        for m in self.mounts:
            m.draw(self.screen, self.camera)

        # Entidades ordenadas por Y
        drawables = []
        for p in self.players:
            if p.mounted:
                drawables.append((p.mounted.y, lambda p=p: p.mounted.draw_mounted(
                    p, self.screen, self.camera, self.time)))
            else:
                drawables.append((p.y, lambda p=p: p.draw(self.screen, self.camera, self.time)))
        drawables.sort(key=lambda d: d[0])
        for _, fn in drawables:
            fn()

        # Partículas
        self.particles.draw(self.screen, self.camera)

        # Overlay día/noche
        ambient = self.daynight.get_ambient_overlay()
        if ambient[3] > 0:
            ov = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            ov.fill(ambient)
            self.screen.blit(ov, (0, 0))

        # Dormir juntos
        if self.sleep_anim_t > 0:
            zzz_font = pygame.font.SysFont("verdana", 40, bold=True)
            t1 = zzz_font.render("Z", True, (255, 255, 255))
            t2 = zzz_font.render("z", True, (200, 200, 255))
            t3 = zzz_font.render("z", True, (150, 150, 200))
            off = int((2.0 - self.sleep_anim_t) * 30)
            self.screen.blit(t1, (int(self.controlled.x - self.camera.x + 20),
                                   int(self.controlled.y - self.camera.y - 60 - off)))
            self.screen.blit(t2, (int(self.controlled.x - self.camera.x + 40),
                                   int(self.controlled.y - self.camera.y - 80 - off * 1.2)))
            self.screen.blit(t3, (int(self.controlled.x - self.camera.x + 55),
                                   int(self.controlled.y - self.camera.y - 95 - off * 1.4)))

        # HUD
        self._draw_hud()

        # Diálogo
        if self.dialogue:
            self._draw_dialogue()

        # Notificación
        if self.notify_t > 0:
            t = self.fonts["med"].render(self.notify_text, True, (255, 240, 200))
            draw_round_rect(self.screen, (60, 40, 60),
                            (self.screen_w // 2 - t.get_width() // 2 - 12, 60,
                             t.get_width() + 24, 34), 10, alpha=200)
            self.screen.blit(t, (self.screen_w // 2 - t.get_width() // 2, 66))

        # UI panel activa
        self.ui.draw(self.screen, self.fonts, self.state)

        # Controles táctiles
        self.input.draw_touch_ui(self.screen)

    def _draw_hud(self):
        # Cristal counter
        draw_round_rect(self.screen, (255, 246, 250), (8, 8, 180, 40), 12, alpha=210)
        self.screen.blit(AssetManager.get_surface("crystal"), (16, 14))
        t = self.fonts["med"].render("%d" % self.gacha.crystals, True, (90, 130, 200))
        self.screen.blit(t, (36, 18))
        # Bioma actual
        biome_name = self.camera.get_current_biome()
        t = self.fonts["small"].render(biome_name.capitalize(), True, (120, 80, 100))
        draw_round_rect(self.screen, (255, 246, 250),
                        (self.screen_w - 160, 8, 152, 26), 10, alpha=210)
        self.screen.blit(t, (self.screen_w - 150, 14))
        # Fase día/noche
        phase = self.daynight.get_phase()
        t = self.fonts["small"].render(phase.capitalize(), True, (140, 120, 160))
        self.screen.blit(t, (self.screen_w - 150, 40))
        # Afinidad mini
        draw_round_rect(self.screen, (255, 246, 250), (8, 54, 200, 30), 10, alpha=210)
        self.screen.blit(AssetManager.get_surface("heart"), (14, 58))
        bar = pygame.Rect(34, 62, 150, 10)
        draw_round_rect(self.screen, (240, 225, 232), bar, 5)
        draw_round_rect(self.screen, (255, 120, 170),
                        (bar.x, bar.y, int(bar.w * self.couple.progress), bar.h), 5)
        t = self.fonts["small"].render("Nv %d" % self.couple.level, True, (200, 90, 130))
        self.screen.blit(t, (36, 72))
        # Stats del jugador activo
        p = self.controlled
        draw_round_rect(self.screen, (255, 246, 250), (8, self.screen_h - 120, 220, 112), 12, alpha=210)
        t = self.fonts["med"].render("%s (nv%d)" % (p.name, p.level), True, (120, 80, 100))
        self.screen.blit(t, (16, self.screen_h - 112))
        # HP
        bar = pygame.Rect(16, self.screen_h - 90, 200, 10)
        draw_round_rect(self.screen, (240, 225, 232), bar, 5)
        draw_round_rect(self.screen, (255, 110, 130),
                        (bar.x, bar.y, int(bar.w * p.hp / p.max_hp), bar.h), 5)
        # Hunger
        bar = pygame.Rect(16, self.screen_h - 74, 200, 10)
        draw_round_rect(self.screen, (240, 225, 232), bar, 5)
        draw_round_rect(self.screen, (255, 190, 100),
                        (bar.x, bar.y, int(bar.w * p.hunger / 100), bar.h), 5)
        # Sleep
        bar = pygame.Rect(16, self.screen_h - 58, 200, 10)
        draw_round_rect(self.screen, (240, 225, 232), bar, 5)
        draw_round_rect(self.screen, (140, 180, 255),
                        (bar.x, bar.y, int(bar.w * p.sleep / 100), bar.h), 5)
        # XP
        bar = pygame.Rect(16, self.screen_h - 42, 200, 10)
        draw_round_rect(self.screen, (240, 225, 232), bar, 5)
        need = p.xp_needed(p.level)
        draw_round_rect(self.screen, (140, 200, 255),
                        (bar.x, bar.y, int(bar.w * p.xp / need), bar.h), 5)
        t = self.fonts["small"].render("XP %d/%d" % (p.xp, need), True, (120, 100, 130))
        self.screen.blit(t, (16, self.screen_h - 26))
        # Hints
        hint = "Q: cambiar | E: hablar | F: montar | B: gacha | C: pareja | J: misiones"
        if IS_MOBILE:
            hint = "Toca los botones laterales para interactuar"
        t = self.fonts["small"].render(hint, True, (255, 255, 255, 220))
        self.screen.blit(t, (self.screen_w // 2 - t.get_width() // 2, self.screen_h - 22))

    def _draw_dialogue(self):
        rect = pygame.Rect(60, self.screen_h - 116, self.screen_w - 120, 82)
        draw_round_rect(self.screen, (255, 246, 250), rect, 16, alpha=238)
        pygame.draw.rect(self.screen, (255, 150, 190), rect, 3, border_radius=16)


# =============================================================================
# PUNTO DE ENTRADA OBLIGATORIO
# =============================================================================
if __name__ == '__main__': Game().run()
