#!/usr/bin/env python3
"""
Neon Viper 2.0 - Supercharged Cyberpunk Arcade Snake
Built with Pygame.

Features:
- Silky-Smooth Sub-Grid Gliding: Decoupled 60 FPS rendering with continuous
  sub-cell interpolation (no discrete tile hopping!).
- Tapered Neon Viper Body: Sleek organic snake geometry, directional animated
  eyes, and dynamic flickering forked tongue.
- Power-Up Arsenal:
  * 🍎 Ruby Apple: Core nourishment (+10 pts, grows 1).
  * ⭐ Golden Star: Timed high-value bonus (+40 pts, grows 2, spark fireworks).
  * ⚡ Turbo Blitz: 2x score multiplier + supersonic speed for 6 seconds.
  * ❄️ Chrono Freeze: 45% time-dilation slow-motion field for 6 seconds.
  * 👻 Ghost Phase: Spectral phase shift allowing safe passage through your
    own coils for 5 seconds.
- Dash / Boost Engine: Hold SPACE or LSHIFT to ignite neon thrusters and boost.
- Combo Chain System: Eat in quick succession to stack multipliers up to 5x!
- Shockwaves & Floating Text: Expanding grid ripple rings and arcade score popups.
- 5 Cyberpunk Themes: Cycle on the fly (T key) between Cyber Neon, Synthwave '84,
  Matrix Code, Arctic Frost, and Solar Inferno.
- Dual Game Modes: Classic Wall Collision vs. Portal Wrap (toggle with TAB).
- Pure-Python Audio Synthesizer: 16-bit PCM procedural WAV sound engine
  requiring zero external libraries like NumPy.
- Comprehensive High Score & Stats Tracking: Stored locally in JSON.
"""

import argparse
import io
import json
import math
import os
import random
import struct
import sys
import time
import wave
from collections import deque

import pygame

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
WINDOW_WIDTH = 840
WINDOW_HEIGHT = 700
HUD_HEIGHT = 80
CELL_SIZE = 25

GRID_COLS = 30
GRID_ROWS = 22
GRID_OFFSET_X = (WINDOW_WIDTH - (GRID_COLS * CELL_SIZE)) // 2
GRID_OFFSET_Y = HUD_HEIGHT + 10

TARGET_FPS = 60
BASE_TICK_RATE = 7.5     # Base grid movements per second
MAX_TICK_RATE = 22.0     # Maximum natural speed cap

HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), "snake_high_score.json")

# ==============================================================================
# THEMES & COLOR PALETTES
# ==============================================================================
THEMES = [
    {
        "name": "CYBER NEON",
        "bg": (10, 14, 26),
        "grid_bg": (16, 23, 40),
        "grid_line": (26, 38, 62),
        "border": (59, 130, 246),
        "border_glow": (37, 99, 235),
        "snake_head": (16, 215, 140),
        "snake_tail": (6, 182, 212),
        "accent": (168, 85, 247),
        "hud_bg": (15, 23, 42),
    },
    {
        "name": "SYNTHWAVE '84",
        "bg": (18, 10, 32),
        "grid_bg": (28, 16, 48),
        "grid_line": (52, 26, 84),
        "border": (244, 63, 94),
        "border_glow": (219, 39, 119),
        "snake_head": (244, 63, 94),
        "snake_tail": (249, 115, 22),
        "accent": (234, 179, 8),
        "hud_bg": (30, 15, 50),
    },
    {
        "name": "MATRIX CODE",
        "bg": (6, 16, 8),
        "grid_bg": (10, 26, 14),
        "grid_line": (18, 44, 24),
        "border": (34, 197, 94),
        "border_glow": (22, 163, 74),
        "snake_head": (74, 222, 128),
        "snake_tail": (21, 128, 61),
        "accent": (134, 239, 172),
        "hud_bg": (8, 24, 12),
    },
    {
        "name": "ARCTIC FROST",
        "bg": (8, 18, 32),
        "grid_bg": (14, 28, 50),
        "grid_line": (24, 46, 80),
        "border": (56, 189, 248),
        "border_glow": (14, 165, 233),
        "snake_head": (125, 211, 252),
        "snake_tail": (224, 242, 254),
        "accent": (147, 197, 253),
        "hud_bg": (12, 24, 44),
    },
    {
        "name": "SOLAR INFERNO",
        "bg": (20, 10, 10),
        "grid_bg": (34, 16, 16),
        "grid_line": (58, 26, 26),
        "border": (239, 68, 68),
        "border_glow": (220, 38, 38),
        "snake_head": (251, 146, 60),
        "snake_tail": (239, 68, 68),
        "accent": (251, 191, 36),
        "hud_bg": (30, 14, 14),
    },
]

# Universal Item & Effect Colors
COLOR_APPLE = (239, 68, 68)
COLOR_APPLE_GLOW = (248, 113, 113)

COLOR_GOLD = (245, 158, 11)
COLOR_GOLD_GLOW = (251, 191, 36)

COLOR_TURBO = (6, 182, 212)
COLOR_TURBO_GLOW = (34, 211, 238)

COLOR_FREEZE = (56, 189, 248)
COLOR_FREEZE_GLOW = (186, 230, 253)

COLOR_GHOST = (168, 85, 247)
COLOR_GHOST_GLOW = (216, 180, 254)

COLOR_TEXT_PRIMARY = (248, 250, 252)
COLOR_TEXT_MUTED = (148, 163, 184)
COLOR_SNAKE_EYE = (255, 255, 255)
COLOR_SNAKE_PUPIL = (15, 23, 42)


# ==============================================================================
# PURE-PYTHON PROCEDURAL SOUND SYNTHESIZER
# ==============================================================================
class SoundManager:
    """Generates and plays 16-bit PCM retro-arcade audio via standard library."""

    def __init__(self):
        self.enabled = False
        self.muted = False
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self._create_synthesized_sounds()
            self.enabled = True
        except Exception:
            self.enabled = False

    def _synthesize_wav(self, freq_start, freq_end, duration, volume=0.25, wave_type="sine", decay_rate=3.5, sample_rate=22050):
        """Builds in-memory 16-bit mono PCM WAV bytes without NumPy."""
        n_samples = max(1, int(sample_rate * duration))
        frames = bytearray()
        phase = 0.0
        for i in range(n_samples):
            t = i / n_samples
            cur_freq = freq_start + (freq_end - freq_start) * t
            phase += 2.0 * math.pi * cur_freq / sample_rate
            decay = math.exp(-decay_rate * t)

            if wave_type == "sine":
                val = math.sin(phase)
            elif wave_type == "triangle":
                val = 2.0 * abs(2.0 * ((phase / (2.0 * math.pi)) % 1.0) - 1.0) - 1.0
            elif wave_type == "square":
                val = 0.7 if (phase % (2.0 * math.pi)) < math.pi else -0.7
            elif wave_type == "noise":
                val = random.uniform(-1.0, 1.0)
            else:
                val = math.sin(phase)

            sample = int(32767.0 * volume * decay * val)
            sample = max(-32768, min(32767, sample))
            frames += struct.pack("<h", sample)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(frames)
        buf.seek(0)
        return pygame.mixer.Sound(buf)

    def _create_synthesized_sounds(self):
        try:
            # Food & Powerup SFX
            self.sounds["eat"] = self._synthesize_wav(460, 920, 0.08, volume=0.22, wave_type="sine")
            self.sounds["golden"] = self._synthesize_wav(700, 1400, 0.16, volume=0.26, wave_type="triangle")
            self.sounds["turbo"] = self._synthesize_wav(350, 1050, 0.18, volume=0.25, wave_type="square")
            self.sounds["freeze"] = self._synthesize_wav(880, 440, 0.22, volume=0.24, wave_type="sine")
            self.sounds["ghost"] = self._synthesize_wav(520, 780, 0.25, volume=0.22, wave_type="triangle")
            self.sounds["dash"] = self._synthesize_wav(600, 200, 0.12, volume=0.18, wave_type="noise")
            self.sounds["gameover"] = self._synthesize_wav(360, 80, 0.45, volume=0.32, wave_type="triangle", decay_rate=2.0)
            self.sounds["click"] = self._synthesize_wav(750, 850, 0.03, volume=0.15, wave_type="sine")
            self.sounds["spawn"] = self._synthesize_wav(800, 1200, 0.10, volume=0.16, wave_type="sine")

            # Combo musical scale arpeggios (C5, D5, E5, G5, A5, C6)
            combo_freqs = [523, 587, 659, 784, 880, 1046]
            for idx, freq in enumerate(combo_freqs, start=1):
                self.sounds[f"combo_{idx}"] = self._synthesize_wav(
                    freq, freq * 1.25, 0.10, volume=0.25, wave_type="triangle"
                )
        except Exception:
            self.enabled = False

    def play(self, sound_name):
        if self.enabled and not self.muted and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception:
                pass

    def play_combo(self, streak):
        level = min(6, max(1, streak))
        self.play(f"combo_{level}")

    def toggle_mute(self):
        self.muted = not self.muted
        return not self.muted


# ==============================================================================
# VISUAL EFFECTS (PARTICLES, SHOCKWAVES, FLOATING TEXT)
# ==============================================================================
class Particle:
    def __init__(self, x, y, vx, vy, color, size, lifetime, shrink=True, shape="circle"):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.initial_size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.shrink = shrink
        self.shape = shape

    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.lifetime -= dt
        if self.shrink:
            progress = max(0.0, self.lifetime / self.max_lifetime)
            self.size = self.initial_size * progress

    @property
    def is_alive(self):
        return self.lifetime > 0 and self.size > 0.4

    def draw(self, surface):
        if self.size < 0.8:
            return
        if self.shape == "circle":
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))
        elif self.shape == "diamond":
            s = int(self.size)
            pts = [(self.x, self.y - s), (self.x + s, self.y), (self.x, self.y + s), (self.x - s, self.y)]
            pygame.draw.polygon(surface, self.color, pts)


class Shockwave:
    def __init__(self, x, y, color, max_radius=90.0, duration=0.45):
        self.x = x
        self.y = y
        self.color = color
        self.max_radius = max_radius
        self.duration = duration
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt

    @property
    def is_alive(self):
        return self.elapsed < self.duration

    def draw(self, surface):
        progress = self.elapsed / self.duration
        radius = int(self.max_radius * math.sqrt(progress))
        alpha = int(220 * (1.0 - progress))
        if radius > 1 and alpha > 0:
            surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            ring_color = (*self.color[:3], alpha)
            pygame.draw.circle(surf, ring_color, (radius + 2, radius + 2), radius, width=2)
            surface.blit(surf, (int(self.x - radius - 2), int(self.y - radius - 2)))


class FloatingText:
    def __init__(self, text, x, y, color, font, duration=1.0, rise_speed=32.0):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.font = font
        self.duration = duration
        self.elapsed = 0.0
        self.rise_speed = rise_speed

    def update(self, dt):
        self.elapsed += dt
        self.y -= self.rise_speed * dt

    @property
    def is_alive(self):
        return self.elapsed < self.duration

    def draw(self, surface):
        progress = self.elapsed / self.duration
        alpha = max(0, min(255, int(255 * (1.0 - progress**1.5))))
        rendered = self.font.render(self.text, True, self.color)
        rendered.set_alpha(alpha)
        rect = rendered.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rendered, rect)


class FXManager:
    def __init__(self):
        self.particles = []
        self.shockwaves = []
        self.floating_texts = []

    def spawn_burst(self, x, y, color, count=24, speed_range=(1.5, 5.0), size_range=(2.5, 5.0), shape="circle"):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(*speed_range)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(*size_range)
            lifetime = random.uniform(0.35, 0.75)
            self.particles.append(Particle(x, y, vx, vy, color, size, lifetime, shape=shape))

    def spawn_sparkle(self, x, y, color, shape="circle"):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.4, 1.4)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed - 0.4
        size = random.uniform(2.0, 3.8)
        lifetime = random.uniform(0.4, 0.7)
        self.particles.append(Particle(x, y, vx, vy, color, size, lifetime, shape=shape))

    def spawn_thruster(self, x, y, vx, vy, color):
        jitter_angle = math.atan2(vy, vx) + random.uniform(-0.35, 0.35)
        speed = random.uniform(1.8, 3.6)
        p_vx = math.cos(jitter_angle) * speed
        p_vy = math.sin(jitter_angle) * speed
        size = random.uniform(2.5, 4.2)
        lifetime = random.uniform(0.2, 0.4)
        self.particles.append(Particle(x, y, p_vx, p_vy, color, size, lifetime))

    def spawn_shockwave(self, x, y, color, max_radius=85.0):
        self.shockwaves.append(Shockwave(x, y, color, max_radius=max_radius))

    def add_floating_text(self, text, x, y, color, font):
        self.floating_texts.append(FloatingText(text, x, y, color, font))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive]

        for s in self.shockwaves:
            s.update(dt)
        self.shockwaves = [s for s in self.shockwaves if s.is_alive]

        for t in self.floating_texts:
            t.update(dt)
        self.floating_texts = [t for t in self.floating_texts if t.is_alive]

    def draw(self, surface):
        for s in self.shockwaves:
            s.draw(surface)
        for p in self.particles:
            p.draw(surface)
        for t in self.floating_texts:
            t.draw(surface)


# ==============================================================================
# SNAKE LOGIC & SUB-GRID INTERPOLATED RENDERING
# ==============================================================================
class Snake:
    DIRECTIONS = {
        "UP": (0, -1),
        "DOWN": (0, 1),
        "LEFT": (-1, 0),
        "RIGHT": (1, 0),
    }
    OPPOSITES = {
        "UP": "DOWN",
        "DOWN": "UP",
        "LEFT": "RIGHT",
        "RIGHT": "LEFT",
    }

    def __init__(self):
        self.reset()

    def reset(self):
        start_x = GRID_COLS // 2
        start_y = GRID_ROWS // 2
        self.body = [
            (start_x, start_y),
            (start_x - 1, start_y),
            (start_x - 2, start_y),
        ]
        self.prev_body = list(self.body)
        self.direction = "RIGHT"
        self.input_queue = deque(maxlen=2)
        self.grow_pending = 0
        self.tongue_timer = 0.0

    def enqueue_direction(self, new_dir):
        last_dir = self.input_queue[-1] if self.input_queue else self.direction
        if new_dir != last_dir and new_dir != self.OPPOSITES[last_dir]:
            self.input_queue.append(new_dir)

    def move(self, is_portal=False, is_ghost=False):
        """Advances the snake by one grid tile.

        Returns: (new_head, grew, collision_self, out_of_bounds)
        """
        if self.input_queue:
            self.direction = self.input_queue.popleft()

        # Save previous snapshot for sub-cell rendering interpolation
        self.prev_body = list(self.body)

        dx, dy = self.DIRECTIONS[self.direction]
        head_x, head_y = self.body[0]
        nx, ny = head_x + dx, head_y + dy

        out_of_bounds = False
        if is_portal:
            nx = nx % GRID_COLS
            ny = ny % GRID_ROWS
        else:
            if nx < 0 or nx >= GRID_COLS or ny < 0 or ny >= GRID_ROWS:
                out_of_bounds = True

        new_head = (nx, ny)

        # Self-collision check (ignored if ghost phase power-up is active)
        collision_self = False
        if not is_ghost and new_head in self.body[:-1]:
            collision_self = True

        self.body.insert(0, new_head)

        if self.grow_pending > 0:
            self.grow_pending -= 1
            grew = True
        else:
            self.body.pop()
            grew = False

        return new_head, grew, collision_self, out_of_bounds

    def grow(self, amount=1):
        self.grow_pending += amount

    def get_interpolated_positions(self, alpha):
        """Calculates sub-grid float positions for continuous fluid movement."""
        positions = []
        num_segments = len(self.body)

        for i in range(num_segments):
            curr_pos = self.body[i]

            if i == 0:
                prev_pos = self.prev_body[0] if self.prev_body else curr_pos
            else:
                # Segment i was previously where segment (i-1) was
                if i < len(self.prev_body):
                    prev_pos = self.prev_body[i]
                    target_pos = self.prev_body[i - 1]
                else:
                    prev_pos = curr_pos
                    target_pos = curr_pos

                # Interpolate from prev_pos toward target_pos
                dist_x = target_pos[0] - prev_pos[0]
                dist_y = target_pos[1] - prev_pos[1]
                # If wrapped across boundary, snap
                if abs(dist_x) > 1 or abs(dist_y) > 1:
                    positions.append((float(curr_pos[0]), float(curr_pos[1])))
                else:
                    ix = prev_pos[0] + dist_x * alpha
                    iy = prev_pos[1] + dist_y * alpha
                    positions.append((ix, iy))
                continue

            # Head interpolation
            dist_x = curr_pos[0] - prev_pos[0]
            dist_y = curr_pos[1] - prev_pos[1]
            if abs(dist_x) > 1 or abs(dist_y) > 1:
                positions.append((float(curr_pos[0]), float(curr_pos[1])))
            else:
                ix = prev_pos[0] + dist_x * alpha
                iy = prev_pos[1] + dist_y * alpha
                positions.append((ix, iy))

        return positions

    def draw(self, surface, grid_x, grid_y, cell_size, alpha, theme, is_ghost=False, is_turbo=False):
        num_segments = len(self.body)
        interp_positions = self.get_interpolated_positions(alpha)

        # 1. Render Ghost / Ethereal Aura or Headlight Glow
        if interp_positions:
            head_x, head_y = interp_positions[0]
            head_px = grid_x + head_x * cell_size + cell_size / 2
            head_py = grid_y + head_y * cell_size + cell_size / 2

            glow_color = COLOR_GHOST_GLOW if is_ghost else (COLOR_TURBO_GLOW if is_turbo else theme["snake_head"])
            glow_radius = int(cell_size * 1.8)
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_color[:3], 40), (glow_radius, glow_radius), glow_radius)
            surface.blit(glow_surf, (int(head_px - glow_radius), int(head_py - glow_radius)))

        # 2. Draw Segments (tail to head so head sits on top)
        for i in reversed(range(num_segments)):
            gx, gy = interp_positions[i]
            px = grid_x + gx * cell_size + cell_size / 2
            py = grid_y + gy * cell_size + cell_size / 2

            t = i / max(1, num_segments - 1)

            if is_ghost:
                base_color = COLOR_GHOST
                alpha_val = 140
            else:
                r = int(theme["snake_head"][0] * (1 - t) + theme["snake_tail"][0] * t)
                g = int(theme["snake_head"][1] * (1 - t) + theme["snake_tail"][1] * t)
                b = int(theme["snake_head"][2] * (1 - t) + theme["snake_tail"][2] * t)
                base_color = (r, g, b)
                alpha_val = 255

            # Taper body slightly towards tail
            segment_radius = (cell_size / 2) * (0.88 - 0.22 * t)

            if is_ghost:
                seg_surf = pygame.Surface((int(cell_size * 1.5), int(cell_size * 1.5)), pygame.SRCALPHA)
                center = int(cell_size * 0.75)
                pygame.draw.circle(seg_surf, (*base_color, alpha_val), (center, center), int(segment_radius))
                surface.blit(seg_surf, (int(px - center), int(py - center)))
            else:
                pygame.draw.circle(surface, base_color, (int(px), int(py)), int(segment_radius))
                # Inner highlight shine
                if segment_radius > 4:
                    pygame.draw.circle(
                        surface,
                        (min(255, base_color[0] + 50), min(255, base_color[1] + 50), min(255, base_color[2] + 50)),
                        (int(px - segment_radius * 0.25), int(py - segment_radius * 0.25)),
                        int(segment_radius * 0.35),
                    )

            # Draw Connecting bridges between consecutive segments for continuous fluid snake
            if i < num_segments - 1:
                next_x, next_y = interp_positions[i + 1]
                n_px = grid_x + next_x * cell_size + cell_size / 2
                n_py = grid_y + next_y * cell_size + cell_size / 2
                if math.hypot(n_px - px, n_py - py) < cell_size * 1.8:
                    line_width = max(2, int(segment_radius * 1.5))
                    if is_ghost:
                        bridge_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                        pygame.draw.line(bridge_surf, (*base_color, alpha_val), (px, py), (n_px, n_py), line_width)
                        surface.blit(bridge_surf, (0, 0))
                    else:
                        pygame.draw.line(surface, base_color, (px, py), (n_px, n_py), line_width)

            # Head eyes and tongue
            if i == 0:
                self._draw_head_details(surface, px, py, cell_size)

    def _draw_head_details(self, surface, hx, hy, cell_size):
        dx, dy = self.DIRECTIONS[self.direction]
        perp_x, perp_y = -dy, dx

        eye_radius = cell_size * 0.17
        pupil_radius = cell_size * 0.08
        dist_forward = cell_size * 0.22
        dist_side = cell_size * 0.27

        left_eye = (hx + dx * dist_forward + perp_x * dist_side, hy + dy * dist_forward + perp_y * dist_side)
        right_eye = (hx + dx * dist_forward - perp_x * dist_side, hy + dy * dist_forward - perp_y * dist_side)

        # 1. Animated Flicking Tongue
        tongue_cycle = (time.time() * 2.2) % 2.0
        if tongue_cycle < 0.45:
            tongue_extend = (math.sin(tongue_cycle / 0.45 * math.pi)) * (cell_size * 0.55)
            tip_x = hx + dx * (cell_size * 0.42 + tongue_extend)
            tip_y = hy + dy * (cell_size * 0.42 + tongue_extend)
            base_x = hx + dx * (cell_size * 0.35)
            base_y = hy + dy * (cell_size * 0.35)

            fork_len = cell_size * 0.16
            f1_x = tip_x + dx * fork_len + perp_x * (fork_len * 0.8)
            f1_y = tip_y + dy * fork_len + perp_y * (fork_len * 0.8)
            f2_x = tip_x + dx * fork_len - perp_x * (fork_len * 0.8)
            f2_y = tip_y + dy * fork_len - perp_y * (fork_len * 0.8)

            pygame.draw.line(surface, (244, 63, 94), (base_x, base_y), (tip_x, tip_y), 2)
            pygame.draw.line(surface, (244, 63, 94), (tip_x, tip_y), (f1_x, f1_y), 2)
            pygame.draw.line(surface, (244, 63, 94), (tip_x, tip_y), (f2_x, f2_y), 2)

        # 2. Glowing Eyes & Tracking Pupils
        for eye in (left_eye, right_eye):
            pygame.draw.circle(surface, COLOR_SNAKE_EYE, (int(eye[0]), int(eye[1])), int(eye_radius))
            pupil_pos = (
                eye[0] + dx * (eye_radius * 0.4),
                eye[1] + dy * (eye_radius * 0.4),
            )
            pygame.draw.circle(surface, COLOR_SNAKE_PUPIL, (int(pupil_pos[0]), int(pupil_pos[1])), int(pupil_radius))


# ==============================================================================
# FOOD & POWER-UP MANAGER
# ==============================================================================
class ItemType:
    APPLE = "APPLE"
    GOLDEN = "GOLDEN"
    TURBO = "TURBO"
    FREEZE = "FREEZE"
    GHOST = "GHOST"


class PowerUpManager:
    def __init__(self):
        self.apple_pos = None
        self.special_pos = None
        self.special_type = None
        self.special_timer = 0.0
        self.special_max_time = 8.0

        self.apples_eaten_count = 0

        # Active power-up durations on the snake
        self.active_turbo = 0.0
        self.active_freeze = 0.0
        self.active_ghost = 0.0

    def spawn_apple(self, occupied):
        available = [
            (x, y)
            for x in range(GRID_COLS)
            for y in range(GRID_ROWS)
            if (x, y) not in occupied and (x, y) != self.special_pos
        ]
        self.apple_pos = random.choice(available) if available else (0, 0)

    def maybe_spawn_special(self, occupied):
        """Spawns an exciting special power-up every 4 apples if none active."""
        if self.special_pos is None and self.apples_eaten_count > 0 and (self.apples_eaten_count % 4 == 0):
            available = [
                (x, y)
                for x in range(GRID_COLS)
                for y in range(GRID_ROWS)
                if (x, y) not in occupied and (x, y) != self.apple_pos
            ]
            if available:
                self.special_pos = random.choice(available)
                self.special_timer = self.special_max_time

                # Weighted random selection of power-up
                choices = [
                    (ItemType.GOLDEN, 0.35),
                    (ItemType.TURBO, 0.25),
                    (ItemType.FREEZE, 0.20),
                    (ItemType.GHOST, 0.20),
                ]
                r = random.random()
                cumulative = 0.0
                for item, weight in choices:
                    cumulative += weight
                    if r <= cumulative:
                        self.special_type = item
                        break
                return True
        return False

    def update(self, dt):
        # Countdown active item on ground
        if self.special_pos is not None:
            self.special_timer -= dt
            if self.special_timer <= 0:
                self.special_pos = None
                self.special_type = None

        # Countdown active status effects
        if self.active_turbo > 0:
            self.active_turbo = max(0.0, self.active_turbo - dt)
        if self.active_freeze > 0:
            self.active_freeze = max(0.0, self.active_freeze - dt)
        if self.active_ghost > 0:
            self.active_ghost = max(0.0, self.active_ghost - dt)

    def draw(self, surface, grid_x, grid_y, cell_size, fx):
        now = time.time()

        # 1. Pulsing Ruby Apple
        if self.apple_pos:
            ax, ay = self.apple_pos
            px = grid_x + ax * cell_size + cell_size / 2
            py = grid_y + ay * cell_size + cell_size / 2

            pulse = 1.0 + 0.12 * math.sin(now * 6.5)
            radius = (cell_size / 2) * 0.76 * pulse

            # Apple Glow
            glow_surf = pygame.Surface((int(cell_size * 2), int(cell_size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*COLOR_APPLE_GLOW, 50), (int(cell_size), int(cell_size)), int(radius * 1.5))
            surface.blit(glow_surf, (int(px - cell_size), int(py - cell_size)))

            # Apple Body
            pygame.draw.circle(surface, COLOR_APPLE, (int(px), int(py + 1)), int(radius))
            # Specular shine
            pygame.draw.circle(
                surface,
                (255, 155, 175),
                (int(px - radius * 0.35), int(py - radius * 0.3)),
                int(radius * 0.3),
            )
            # Leaf
            pygame.draw.ellipse(surface, (34, 197, 94), (int(px - 1), int(py - radius - 4), 6, 4))

        # 2. Special Item (Star, Turbo, Freeze, Ghost)
        if self.special_pos and self.special_type:
            sx, sy = self.special_pos
            px = grid_x + sx * cell_size + cell_size / 2
            py = grid_y + sy * cell_size + cell_size / 2

            if self.special_type == ItemType.GOLDEN:
                color, glow, char = COLOR_GOLD, COLOR_GOLD_GLOW, "★"
            elif self.special_type == ItemType.TURBO:
                color, glow, char = COLOR_TURBO, COLOR_TURBO_GLOW, "⚡"
            elif self.special_type == ItemType.FREEZE:
                color, glow, char = COLOR_FREEZE, COLOR_FREEZE_GLOW, "❄"
            else:  # GHOST
                color, glow, char = COLOR_GHOST, COLOR_GHOST_GLOW, "👻"

            # Ambient sparkle
            if random.random() < 0.3:
                fx.spawn_sparkle(px + random.uniform(-6, 6), py + random.uniform(-6, 6), glow)

            pulse = 1.0 + 0.16 * math.sin(now * 9.0)
            radius = (cell_size / 2) * 0.82 * pulse

            glow_surf = pygame.Surface((int(cell_size * 2.2), int(cell_size * 2.2)), pygame.SRCALPHA)
            c = int(cell_size * 1.1)
            pygame.draw.circle(glow_surf, (*glow, 70), (c, c), int(radius * 1.6))
            surface.blit(glow_surf, (int(px - c), int(py - c)))

            pygame.draw.circle(surface, color, (int(px), int(py)), int(radius))
            pygame.draw.circle(
                surface,
                (255, 255, 255),
                (int(px - radius * 0.3), int(py - radius * 0.3)),
                int(radius * 0.32),
            )

            # Circular Countdown Ring
            ratio = max(0.0, self.special_timer / self.special_max_time)
            ring_rect = pygame.Rect(
                px - radius - 4,
                py - radius - 4,
                (radius + 4) * 2,
                (radius + 4) * 2,
            )
            start_angle = -math.pi / 2
            end_angle = start_angle + ratio * (2 * math.pi)
            if ratio > 0.05:
                pygame.draw.arc(surface, glow, ring_rect, start_angle, end_angle, 2)


# ==============================================================================
# MAIN GAME CONTROLLER
# ==============================================================================
class Game:
    STATE_START = "START"
    STATE_PLAYING = "PLAYING"
    STATE_PAUSED = "PAUSED"
    STATE_GAME_OVER = "GAME_OVER"

    MODE_CLASSIC = "CLASSIC"
    MODE_PORTAL = "PORTAL"

    def __init__(self, headless=False):
        self.headless = headless
        pygame.init()
        pygame.display.set_caption("Neon Viper 2.0 - Supercharged Cyberpunk Snake")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_title = pygame.font.Font(None, 56)
        self.font_large = pygame.font.Font(None, 40)
        self.font_medium = pygame.font.Font(None, 27)
        self.font_small = pygame.font.Font(None, 20)
        self.font_bold = pygame.font.Font(None, 32)

        self.audio = SoundManager()
        self.fx = FXManager()
        self.snake = Snake()
        self.items = PowerUpManager()

        # Theme & Game Mode
        self.theme_index = 0
        self.theme = THEMES[self.theme_index]
        self.game_mode = self.MODE_CLASSIC

        # Gameplay tracking
        self.state = self.STATE_START
        self.score = 0
        self.high_score_data = self._load_high_scores()
        self.high_score = self.high_score_data.get("high_score", 0)
        self.is_new_high = False
        self.level = 1

        # Timing & movement
        self.move_timer = 0.0
        self.screen_shake = 0.0
        self.is_dashing = False

        # Combo system
        self.combo_streak = 0
        self.combo_timer = 0.0
        self.max_combo_window = 3.8
        self.highest_combo_run = 0

        # Stats for end screen
        self.total_apples_run = 0
        self.total_powerups_run = 0
        self.start_play_time = 0.0
        self.survival_seconds = 0.0

        # Initial food spawn
        self.items.spawn_apple(self.snake.body)

    def _load_high_scores(self):
        if os.path.exists(HIGH_SCORE_FILE):
            try:
                with open(HIGH_SCORE_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {"high_score": 0}
        return {"high_score": 0}

    def _save_high_scores(self):
        try:
            self.high_score_data["high_score"] = self.high_score
            with open(HIGH_SCORE_FILE, "w") as f:
                json.dump(self.high_score_data, f, indent=2)
        except Exception:
            pass

    def cycle_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEMES)
        self.theme = THEMES[self.theme_index]
        self.audio.play("click")
        self.fx.add_floating_text(
            f"Theme: {self.theme['name']}",
            WINDOW_WIDTH // 2,
            HUD_HEIGHT + 30,
            self.theme["accent"],
            self.font_medium,
        )

    def toggle_game_mode(self):
        if self.game_mode == self.MODE_CLASSIC:
            self.game_mode = self.MODE_PORTAL
        else:
            self.game_mode = self.MODE_CLASSIC
        self.audio.play("click")

    def restart_game(self):
        self.snake.reset()
        self.items = PowerUpManager()
        self.items.spawn_apple(self.snake.body)
        self.fx = FXManager()

        self.score = 0
        self.level = 1
        self.move_timer = 0.0
        self.screen_shake = 0.0
        self.is_new_high = False
        self.is_dashing = False

        self.combo_streak = 0
        self.combo_timer = 0.0
        self.highest_combo_run = 0
        self.total_apples_run = 0
        self.total_powerups_run = 0
        self.start_play_time = time.time()
        self.survival_seconds = 0.0

        self.state = self.STATE_PLAYING
        self.audio.play("spawn")

    def get_current_tick_interval(self):
        # Base progression with score
        speed = BASE_TICK_RATE + (self.score // 35) * 0.7
        speed = min(speed, MAX_TICK_RATE)

        # Modifiers: Turbo, Freeze, Dash
        if self.items.active_turbo > 0:
            speed *= 1.35
        if self.items.active_freeze > 0:
            speed *= 0.55
        if self.is_dashing:
            speed *= 1.55

        return 1.0 / max(3.0, speed)

    def cleanup_and_exit(self):
        try:
            if pygame.mixer.get_init():
                pygame.mixer.stop()
                pygame.mixer.quit()
        except Exception:
            pass
        try:
            pygame.display.quit()
        except Exception:
            pass
        try:
            pygame.quit()
        except Exception:
            pass
        sys.exit(0)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                # Immediate Quit via Q from any state
                if event.key == pygame.K_q:
                    return False

                # ESC Key Handling:
                # - In PLAYING: pauses game and reveals Quit / Resume menu
                # - In PAUSED, START, or GAME_OVER: cleanly quits the application
                if event.key == pygame.K_ESCAPE:
                    if self.state == self.STATE_PLAYING:
                        self.state = self.STATE_PAUSED
                    else:
                        return False

                # Global hotkeys
                if event.key == pygame.K_t:
                    self.cycle_theme()
                elif event.key == pygame.K_m:
                    sound_on = self.audio.toggle_mute()
                    msg = "Sound: ON" if sound_on else "Sound: OFF"
                    self.fx.add_floating_text(
                        msg, WINDOW_WIDTH // 2, HUD_HEIGHT + 30, COLOR_TEXT_PRIMARY, self.font_medium
                    )
                elif event.key == pygame.K_TAB:
                    if self.state in (self.STATE_START, self.STATE_PAUSED):
                        self.toggle_game_mode()

                # State-specific controls
                if self.state == self.STATE_START:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        self.restart_game()

                elif self.state == self.STATE_PLAYING:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.snake.enqueue_direction("UP")
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.snake.enqueue_direction("DOWN")
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        self.snake.enqueue_direction("LEFT")
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.snake.enqueue_direction("RIGHT")
                    elif event.key == pygame.K_p:
                        self.state = self.STATE_PAUSED

                elif self.state == self.STATE_PAUSED:
                    if event.key in (pygame.K_p, pygame.K_SPACE, pygame.K_RETURN):
                        self.state = self.STATE_PLAYING

                elif self.state == self.STATE_GAME_OVER:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                        self.restart_game()

        # Continuous Dash key check (Space or Left Shift)
        keys = pygame.key.get_pressed()
        self.is_dashing = (self.state == self.STATE_PLAYING) and (keys[pygame.K_LSHIFT] or keys[pygame.K_SPACE])

        return True

    def trigger_game_over(self):
        self.state = self.STATE_GAME_OVER
        self.screen_shake = 18.0
        self.survival_seconds = time.time() - self.start_play_time
        self.audio.play("gameover")

        # Shatter snake into colorful particle sparks
        for segment in self.snake.body:
            px = GRID_OFFSET_X + segment[0] * CELL_SIZE + CELL_SIZE / 2
            py = GRID_OFFSET_Y + segment[1] * CELL_SIZE + CELL_SIZE / 2
            self.fx.spawn_burst(px, py, self.theme["snake_head"], count=8, speed_range=(2.0, 7.0))

        if self.score > self.high_score:
            self.high_score = self.score
            self.is_new_high = True
            self._save_high_scores()

    def update(self, dt):
        self.fx.update(dt)

        if self.screen_shake > 0:
            self.screen_shake = max(0.0, self.screen_shake - dt * 32.0)

        if self.state != self.STATE_PLAYING:
            return

        self.items.update(dt)

        # Decay combo timer
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo_streak = 0

        # Thruster particle emission when dashing or turbo boosted
        if self.is_dashing or self.items.active_turbo > 0:
            head_x, head_y = self.snake.body[0]
            px = GRID_OFFSET_X + head_x * CELL_SIZE + CELL_SIZE / 2
            py = GRID_OFFSET_Y + head_y * CELL_SIZE + CELL_SIZE / 2
            dx, dy = self.snake.DIRECTIONS[self.snake.direction]
            thruster_color = COLOR_TURBO_GLOW if self.items.active_turbo > 0 else self.theme["snake_tail"]
            self.fx.spawn_thruster(px, py, -dx, -dy, thruster_color)

        # Decoupled Sub-Grid Movement
        tick_interval = self.get_current_tick_interval()
        self.move_timer += dt

        is_portal = (self.game_mode == self.MODE_PORTAL)
        is_ghost = (self.items.active_ghost > 0)

        while self.move_timer >= tick_interval:
            self.move_timer -= tick_interval
            new_head, grew, self_hit, oob = self.snake.move(is_portal=is_portal, is_ghost=is_ghost)

            if self_hit or oob:
                self.trigger_game_over()
                return

            head_pos = self.snake.body[0]
            px = GRID_OFFSET_X + head_pos[0] * CELL_SIZE + CELL_SIZE / 2
            py = GRID_OFFSET_Y + head_pos[1] * CELL_SIZE + CELL_SIZE / 2

            # 1. Normal Apple Consumed
            if head_pos == self.items.apple_pos:
                self.total_apples_run += 1
                self.items.apples_eaten_count += 1
                self.snake.grow(1)

                # Combo calculation
                self.combo_streak += 1
                self.combo_timer = max(1.8, self.max_combo_window - self.combo_streak * 0.15)
                if self.combo_streak > self.highest_combo_run:
                    self.highest_combo_run = self.combo_streak

                # Multipliers: base combo multiplier + turbo doubling
                combo_mult = 1.0 + (self.combo_streak - 1) * 0.5
                if self.items.active_turbo > 0:
                    combo_mult *= 2.0

                earned = int(10 * combo_mult)
                self.score += earned
                self.level = 1 + (self.score // 45)

                self.audio.play_combo(self.combo_streak)
                self.fx.spawn_burst(px, py, COLOR_APPLE_GLOW, count=30)
                self.fx.spawn_shockwave(px, py, COLOR_APPLE_GLOW, max_radius=80.0)

                # Floating score & combo text
                if self.combo_streak > 1:
                    label = f"+{earned} (x{combo_mult:.1f} COMBO!)"
                    col = COLOR_GOLD_GLOW if self.combo_streak < 4 else (244, 63, 94)
                else:
                    label = f"+{earned}"
                    col = COLOR_APPLE_GLOW
                self.fx.add_floating_text(label, px, py - 10, col, self.font_bold)

                # Respawn Apple & Check Special
                self.items.spawn_apple(self.snake.body)
                if self.items.maybe_spawn_special(self.snake.body):
                    self.audio.play("spawn")

            # 2. Special Power-Up Consumed
            elif head_pos == self.items.special_pos and self.items.special_type:
                self.total_powerups_run += 1
                item_type = self.items.special_type

                if item_type == ItemType.GOLDEN:
                    self.score += 40
                    self.snake.grow(2)
                    self.audio.play("golden")
                    self.fx.spawn_burst(px, py, COLOR_GOLD_GLOW, count=45, speed_range=(3.0, 8.5), shape="diamond")
                    self.fx.spawn_shockwave(px, py, COLOR_GOLD_GLOW, max_radius=110.0)
                    self.fx.add_floating_text("+40 GOLDEN STAR!", px, py - 12, COLOR_GOLD_GLOW, self.font_bold)

                elif item_type == ItemType.TURBO:
                    self.score += 20
                    self.items.active_turbo = 6.0
                    self.audio.play("turbo")
                    self.fx.spawn_burst(px, py, COLOR_TURBO_GLOW, count=35, speed_range=(3.0, 7.0))
                    self.fx.spawn_shockwave(px, py, COLOR_TURBO_GLOW, max_radius=95.0)
                    self.fx.add_floating_text("TURBO BLITZ 2x!", px, py - 12, COLOR_TURBO_GLOW, self.font_bold)

                elif item_type == ItemType.FREEZE:
                    self.score += 20
                    self.items.active_freeze = 6.0
                    self.audio.play("freeze")
                    self.fx.spawn_burst(px, py, COLOR_FREEZE_GLOW, count=35, speed_range=(2.5, 6.0))
                    self.fx.spawn_shockwave(px, py, COLOR_FREEZE_GLOW, max_radius=95.0)
                    self.fx.add_floating_text("CHRONO SLOW!", px, py - 12, COLOR_FREEZE_GLOW, self.font_bold)

                elif item_type == ItemType.GHOST:
                    self.score += 20
                    self.items.active_ghost = 5.0
                    self.audio.play("ghost")
                    self.fx.spawn_burst(px, py, COLOR_GHOST_GLOW, count=35, speed_range=(2.5, 6.0))
                    self.fx.spawn_shockwave(px, py, COLOR_GHOST_GLOW, max_radius=95.0)
                    self.fx.add_floating_text("GHOST PHASE!", px, py - 12, COLOR_GHOST_GLOW, self.font_bold)

                self.items.special_pos = None
                self.items.special_type = None

    def draw_grid_and_board(self, surface):
        grid_w = GRID_COLS * CELL_SIZE
        grid_h = GRID_ROWS * CELL_SIZE
        board_rect = pygame.Rect(GRID_OFFSET_X, GRID_OFFSET_Y, grid_w, grid_h)

        # Board background
        pygame.draw.rect(surface, self.theme["grid_bg"], board_rect, border_radius=8)

        # Subtle cyber grid lines
        for col in range(1, GRID_COLS):
            x = GRID_OFFSET_X + col * CELL_SIZE
            pygame.draw.line(surface, self.theme["grid_line"], (x, GRID_OFFSET_Y), (x, GRID_OFFSET_Y + grid_h))
        for row in range(1, GRID_ROWS):
            y = GRID_OFFSET_Y + row * CELL_SIZE
            pygame.draw.line(surface, self.theme["grid_line"], (GRID_OFFSET_X, y), (GRID_OFFSET_X + grid_w, y))

        # Glowing Neon Border
        border_color = COLOR_GHOST if self.items.active_ghost > 0 else (
            COLOR_FREEZE if self.items.active_freeze > 0 else self.theme["border"]
        )
        pygame.draw.rect(surface, border_color, board_rect, width=2, border_radius=8)

        # Portal Mode visual accents on corners
        if self.game_mode == self.MODE_PORTAL:
            corner_len = 16
            corners = [
                (GRID_OFFSET_X, GRID_OFFSET_Y),
                (GRID_OFFSET_X + grid_w, GRID_OFFSET_Y),
                (GRID_OFFSET_X, GRID_OFFSET_Y + grid_h),
                (GRID_OFFSET_X + grid_w, GRID_OFFSET_Y + grid_h),
            ]
            for cx, cy in corners:
                pygame.draw.circle(surface, COLOR_TURBO_GLOW, (cx, cy), 4)

    def draw_hud(self, surface):
        hud_w = GRID_COLS * CELL_SIZE
        hud_rect = pygame.Rect(GRID_OFFSET_X, 12, hud_w, HUD_HEIGHT - 16)
        pygame.draw.rect(surface, self.theme["hud_bg"], hud_rect, border_radius=8)
        pygame.draw.rect(surface, self.theme["grid_line"], hud_rect, width=1, border_radius=8)

        # 1. Score & High Score
        lbl_score = self.font_small.render("SCORE", True, COLOR_TEXT_MUTED)
        val_score = self.font_large.render(f"{self.score:04d}", True, COLOR_TEXT_PRIMARY)
        surface.blit(lbl_score, (GRID_OFFSET_X + 18, 18))
        surface.blit(val_score, (GRID_OFFSET_X + 18, 34))

        best = max(self.score, self.high_score)
        lbl_best = self.font_small.render("BEST", True, COLOR_TEXT_MUTED)
        val_best = self.font_large.render(f"{best:04d}", True, self.theme["accent"])
        surface.blit(lbl_best, (GRID_OFFSET_X + 125, 18))
        surface.blit(val_best, (GRID_OFFSET_X + 125, 34))

        # 2. Combo Streak Bar
        lbl_combo = self.font_small.render("COMBO METER", True, COLOR_TEXT_MUTED)
        surface.blit(lbl_combo, (GRID_OFFSET_X + 230, 18))
        bar_w = 110
        bar_h = 8
        bar_x = GRID_OFFSET_X + 230
        bar_y = 48
        pygame.draw.rect(surface, (30, 41, 59), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        if self.combo_timer > 0:
            ratio = max(0.0, min(1.0, self.combo_timer / self.max_combo_window))
            bar_color = COLOR_GOLD if self.combo_streak < 4 else (244, 63, 94)
            fill_w = max(4, int(bar_w * ratio))
            pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_w, bar_h), border_radius=4)
            streak_txt = self.font_bold.render(f"x{self.combo_streak}", True, bar_color)
            surface.blit(streak_txt, (bar_x + bar_w + 8, bar_y - 8))

        # 3. Active Power-Up Badges
        badge_x = GRID_OFFSET_X + 410
        active_badges = []
        if self.items.active_turbo > 0:
            active_badges.append(("TURBO", f"{self.items.active_turbo:.1f}s", COLOR_TURBO_GLOW))
        if self.items.active_freeze > 0:
            active_badges.append(("FREEZE", f"{self.items.active_freeze:.1f}s", COLOR_FREEZE_GLOW))
        if self.items.active_ghost > 0:
            active_badges.append(("GHOST", f"{self.items.active_ghost:.1f}s", COLOR_GHOST_GLOW))

        for idx, (b_name, b_time, b_col) in enumerate(active_badges):
            bx = badge_x + idx * 80
            pygame.draw.rect(surface, (20, 25, 40), (bx, 20, 74, 38), border_radius=6)
            pygame.draw.rect(surface, b_col, (bx, 20, 74, 38), width=1, border_radius=6)
            b_txt = self.font_small.render(b_name, True, b_col)
            t_txt = self.font_small.render(b_time, True, COLOR_TEXT_PRIMARY)
            surface.blit(b_txt, (bx + 8, 23))
            surface.blit(t_txt, (bx + 8, 38))

        # 4. Mode & Hints
        mode_str = f"MODE: {self.game_mode}"
        mode_col = COLOR_TURBO_GLOW if self.game_mode == self.MODE_PORTAL else self.theme["snake_head"]
        mode_txt = self.font_small.render(mode_str, True, mode_col)
        surface.blit(mode_txt, (GRID_OFFSET_X + hud_w - 180, 20))

        hint_txt = self.font_small.render("P / ESC: Pause  •  Q: Quit  •  T: Theme  •  Space: Boost", True, COLOR_TEXT_MUTED)
        surface.blit(hint_txt, (GRID_OFFSET_X + hud_w - 295, 40))

    def draw_overlays(self, surface):
        center_x = WINDOW_WIDTH // 2
        center_y = GRID_OFFSET_Y + (GRID_ROWS * CELL_SIZE) // 2

        if self.state == self.STATE_START:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*self.theme["bg"], 215))
            surface.blit(overlay, (0, 0))

            title = self.font_title.render("NEON VIPER 2.0", True, self.theme["snake_head"])
            subtitle = self.font_medium.render("Supercharged Cyber Arcade Snake", True, self.theme["snake_tail"])
            start_hint = self.font_large.render("Press SPACE or ENTER to Play", True, COLOR_TEXT_PRIMARY)

            mode_info = self.font_medium.render(f"Mode: {self.game_mode} (Press TAB to Toggle)", True, COLOR_TURBO_GLOW)
            theme_info = self.font_small.render(f"Theme: {self.theme['name']} (Press T to Cycle)", True, self.theme["accent"])
            keys_info = self.font_small.render("WASD / Arrows to Slither  •  Hold SHIFT/SPACE to Boost  •  P: Pause  •  ESC: Quit", True, COLOR_TEXT_MUTED)

            surface.blit(title, title.get_rect(center=(center_x, center_y - 85)))
            surface.blit(subtitle, subtitle.get_rect(center=(center_x, center_y - 42)))
            surface.blit(start_hint, start_hint.get_rect(center=(center_x, center_y + 15)))
            surface.blit(mode_info, mode_info.get_rect(center=(center_x, center_y + 55)))
            surface.blit(theme_info, theme_info.get_rect(center=(center_x, center_y + 85)))
            surface.blit(keys_info, keys_info.get_rect(center=(center_x, center_y + 120)))

        elif self.state == self.STATE_PAUSED:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*self.theme["bg"], 190))
            surface.blit(overlay, (0, 0))

            pause_title = self.font_title.render("GAME PAUSED", True, self.theme["border"])
            pause_resume = self.font_large.render("Press SPACE or P to Resume", True, COLOR_TEXT_PRIMARY)
            pause_quit = self.font_medium.render("Press ESC or Q to Quit Game", True, COLOR_APPLE_GLOW)
            mode_hint = self.font_small.render(
                f"Mode: {self.game_mode} (Press TAB to Toggle)  •  Theme: {self.theme['name']} (Press T)",
                True,
                COLOR_TEXT_MUTED,
            )

            surface.blit(pause_title, pause_title.get_rect(center=(center_x, center_y - 50)))
            surface.blit(pause_resume, pause_resume.get_rect(center=(center_x, center_y)))
            surface.blit(pause_quit, pause_quit.get_rect(center=(center_x, center_y + 40)))
            surface.blit(mode_hint, mode_hint.get_rect(center=(center_x, center_y + 80)))

        elif self.state == self.STATE_GAME_OVER:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*self.theme["bg"], 220))
            surface.blit(overlay, (0, 0))

            go_title = self.font_title.render("GAME OVER", True, COLOR_APPLE)
            surface.blit(go_title, go_title.get_rect(center=(center_x, center_y - 110)))

            if self.is_new_high:
                high_msg = self.font_large.render("★ NEW HIGH SCORE! ★", True, COLOR_GOLD_GLOW)
                surface.blit(high_msg, high_msg.get_rect(center=(center_x, center_y - 65)))
            else:
                score_msg = self.font_large.render(f"Final Score: {self.score}", True, COLOR_TEXT_PRIMARY)
                surface.blit(score_msg, score_msg.get_rect(center=(center_x, center_y - 65)))

            # Stats Breakdown Box
            stats_box = pygame.Rect(center_x - 170, center_y - 35, 340, 95)
            pygame.draw.rect(surface, (20, 25, 42), stats_box, border_radius=8)
            pygame.draw.rect(surface, (40, 55, 80), stats_box, width=1, border_radius=8)

            s_apples = self.font_small.render(f"Apples Harvested: {self.total_apples_run}", True, COLOR_APPLE_GLOW)
            s_power = self.font_small.render(f"Power-Ups Grabbed: {self.total_powerups_run}", True, COLOR_TURBO_GLOW)
            s_combo = self.font_small.render(f"Peak Combo Streak: x{self.highest_combo_run}", True, COLOR_GOLD_GLOW)
            s_surv = self.font_small.render(f"Time Survived: {self.survival_seconds:.1f}s", True, COLOR_TEXT_MUTED)

            surface.blit(s_apples, (center_x - 150, center_y - 25))
            surface.blit(s_power, (center_x - 150, center_y - 5))
            surface.blit(s_combo, (center_x - 150, center_y + 15))
            surface.blit(s_surv, (center_x - 150, center_y + 35))

            restart_hint = self.font_medium.render("Press SPACE or R to Play Again", True, self.theme["snake_head"])
            quit_hint = self.font_small.render("Press ESC to Quit", True, COLOR_TEXT_MUTED)

            surface.blit(restart_hint, restart_hint.get_rect(center=(center_x, center_y + 90)))
            surface.blit(quit_hint, quit_hint.get_rect(center=(center_x, center_y + 125)))

    def render(self):
        render_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        render_surf.fill(self.theme["bg"])

        # Calculate sub-cell movement progress alpha (0.0 to 1.0)
        tick_interval = self.get_current_tick_interval()
        alpha = min(1.0, max(0.0, self.move_timer / tick_interval))

        # Draw main layers
        self.draw_hud(render_surf)
        self.draw_grid_and_board(render_surf)

        self.items.draw(render_surf, GRID_OFFSET_X, GRID_OFFSET_Y, CELL_SIZE, self.fx)

        is_ghost = (self.items.active_ghost > 0)
        is_turbo = (self.items.active_turbo > 0 or self.is_dashing)
        self.snake.draw(
            render_surf,
            GRID_OFFSET_X,
            GRID_OFFSET_Y,
            CELL_SIZE,
            alpha,
            self.theme,
            is_ghost=is_ghost,
            is_turbo=is_turbo,
        )

        self.fx.draw(render_surf)
        self.draw_overlays(render_surf)

        # Screen Shake
        offset_x = 0
        offset_y = 0
        if self.screen_shake > 0:
            offset_x = random.uniform(-self.screen_shake, self.screen_shake)
            offset_y = random.uniform(-self.screen_shake, self.screen_shake)

        self.screen.fill(self.theme["bg"])
        self.screen.blit(render_surf, (int(offset_x), int(offset_y)))
        pygame.display.flip()

    def run(self, max_frames=None):
        running = True
        frame_count = 0

        while running:
            dt = self.clock.tick(TARGET_FPS) / 1000.0
            dt = min(dt, 0.1)

            if not self.handle_events():
                break

            self.update(dt)
            self.render()

            frame_count += 1
            if max_frames and frame_count >= max_frames:
                break

        if not self.headless:
            self.cleanup_and_exit()
        else:
            pygame.quit()


# ==============================================================================
# ENTRY POINT & VERIFICATION HARNESS
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Neon Viper 2.0 Snake Game")
    parser.add_argument(
        "--test-headless",
        action="store_true",
        help="Run 60 frames headlessly with simulated moves and power-ups for verification",
    )
    args = parser.parse_args()

    if args.test_headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        game = Game(headless=True)
        game.restart_game()

        # Simulate movement ticks
        for direction in ["RIGHT", "DOWN", "LEFT", "UP"]:
            game.snake.enqueue_direction(direction)
            for _ in range(15):
                game.update(1.0 / 60.0)
                game.render()

        # Test power-ups activation
        game.items.active_turbo = 3.0
        game.items.active_freeze = 3.0
        game.items.active_ghost = 3.0
        game.cycle_theme()
        game.toggle_game_mode()
        game.update(1.0 / 60.0)
        game.render()

        print("Headless verification test completed successfully!")
        sys.exit(0)
    else:
        game = Game()
        game.run()
        sys.exit(0)


if __name__ == "__main__":
    main()
