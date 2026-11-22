#!/usr/bin/env python3
"""Sum up 22 November 2026's world news in one image -- v2.

A make.fun program/v1 entry (competition: news-image-20261122).

v2 fixes the v1 judge panel (mean 63.0, PERBAIKI): 25 dated stories
(1 lead + 24 in a fixed 3 x 8 grid) instead of 12, a world map with
numbered pins, a first-wire UTC timeline, region-count chips, and a
DATE CHECK box separating 22 Nov items from the two 21 Nov carry-overs.
Every story is a real item from the 22 Nov 2026 wire digests
(Reuters / AP / BBC digests checked 22 Nov ~04:30 UTC); the two
21 Nov items (EU-Indonesia deal, Peru quake) are tagged 21 NOV.

The program draws a dense newspaper front page and writes one
deterministic PNG to $MAKEFUN_OUTPUT_DIR/entry.png (or ./output/
entry.png locally). No network, no randomness, no wall-clock time,
no third-party packages: only the Python standard library, so two
grading runs produce byte-identical output.

Run:  python3 main.py
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 232)      # newsprint cream
CARD = (253, 251, 246)       # card paper
INK = (26, 26, 26)           # near-black ink
MUTED = (90, 84, 74)         # grey-brown for small print
RED = (178, 34, 34)          # headline red
NAVY = (18, 38, 66)          # dark navy panel
NAVY2 = (30, 58, 95)         # lighter navy
SKY = (147, 197, 253)        # pale blue for globe lines
GRID = (58, 96, 140)         # dim blue for map graticule
WHITE = (255, 255, 255)
GOLD = (234, 179, 8)
TEAL = (13, 116, 128)
BROWN = (146, 64, 14)
ORANGE = (194, 65, 12)
SLATE = (71, 85, 105)
GREEN = (21, 101, 52)
SEA = (16, 52, 84)           # gulf water at night
SAND = (214, 182, 128)       # coastline sand
FLAME = (230, 120, 20)
PINK = (253, 232, 232)       # date-check tint
HAIR = (210, 200, 185)       # card hairlines


# ------------------------------------------------------------------ canvas
class Canvas:
    """An RGB pixel buffer with tiny shape-drawing helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        px = bytes(bg)
        row = px * w
        self.buf = bytearray(row * h)

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x0, x1, y, c, t=1):
        if x1 < x0:
            x0, x1 = x1, x0
        self.fill_rect(x0, y - t // 2, x1 - x0 + 1, t, c)

    def vline(self, x, y0, y1, c, t=1):
        if y1 < y0:
            y0, y1 = y1, y0
        self.fill_rect(x - t // 2, y0, t, y1 - y0 + 1, c)

    def line(self, x0, y0, x1, y1, c):
        """Bresenham line, 1 px wide."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def thick_line(self, x0, y0, x1, y1, c, t=3):
        """A line drawn as a chain of t x t stamps."""
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            t_ = i / steps
            x = int(round(x0 + (x1 - x0) * t_))
            y = int(round(y0 + (y1 - y0) * t_))
            self.fill_rect(x - t // 2, y - t // 2, t, t, c)

    def circle(self, cx, cy, r, c, fill=False):
        if fill:
            for dy in range(-r, r + 1):
                dx = int(math.sqrt(max(0, r * r - dy * dy)))
                self.hline(cx - dx, cx + dx, cy + dy, c, 1)
            return
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                self.px(cx + sx, cy + sy, c)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def ellipse(self, cx, cy, rx, ry, c):
        """Outline ellipse sampled by angle (decorative use only)."""
        steps = max(24, int(2 * math.pi * max(rx, ry) / 3))
        prev = None
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            p = (int(round(cx + rx * math.cos(a))),
                 int(round(cy + ry * math.sin(a))))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], c)
            prev = p

    def poly(self, pts, c):
        """Filled polygon via a scanline fill."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if y0 == y1:
                    continue
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(math.ceil(xs[i])), int(math.floor(xs[i + 1])),
                           y, c, 1)

    def star(self, cx, cy, r_out, r_in, points, c):
        pts = []
        for i in range(points * 2):
            r = r_out if i % 2 == 0 else r_in
            a = math.pi * i / points - math.pi / 2
            pts.append((int(round(cx + r * math.cos(a))),
                        int(round(cy + r * math.sin(a)))))
        self.poly(pts, c)


    def dither_rect(self, x, y, w, h, c1, c2):
        """1 px checkerboard of two colors (deterministic texture)."""
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        n = x1 - x0
        row_a = (bytes(c1) + bytes(c2)) * ((n + 1) // 2)
        row_b = (bytes(c2) + bytes(c1)) * ((n + 1) // 2)
        row_a = row_a[:n * 3]
        row_b = row_b[:n * 3]
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            if (x0 + yy) % 2 == 0:
                self.buf[i:i + n * 3] = row_a
            else:
                self.buf[i:i + n * 3] = row_b

    def grain(self, x, y, w, h, dark, light, step=1):
        """Deterministic newsprint stipple: 1 px dots from a hash of (x, y)."""
        for gy in range(y, y + h, step):
            if gy < 0 or gy >= self.h:
                continue
            for gx in range(x, x + w, step):
                if gx < 0 or gx >= self.w:
                    continue
                h = (gx * 0x9E3779B1 + gy * 0x85EBCA6B) & 0xFFFFFFFF
                h ^= h >> 16
                h = (h * 0x21F0AAAD) & 0xFFFFFFFF
                h ^= h >> 15
                h = (h * 0x735A2D97) & 0xFFFFFFFF
                h ^= h >> 15
                hv = h & 0xFFFF
                if hv % 4 == 0:
                    self.px(gx, gy, dark)
                elif hv % 6 == 0:
                    self.px(gx, gy, light)

# -------------------------------------------------------------- PNG writer
def write_png(path, cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ------------------------------------------------------------- bitmap font
# 5x7 pixel font: each glyph is 7 rows of 5 characters, top to bottom.
# Row 5 is the baseline, row 6 the descender. Space is blank.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    "q": ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("00100", "00100", "11110", "00100", "00100", "00100", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "\u2014": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "\u2022": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
}


def text_width(text, scale):
    """Pixel width of text at the given scale (6 px advance per glyph)."""
    return len(text) * 6 * scale - scale


def draw_text(cv, x, y, text, scale, color):
    """Draw text with its top-left corner at (x, y)."""
    for ci, ch in enumerate(text):
        glyph = FONT.get(ch)
        if glyph is None:
            continue
        gx = x + ci * 6 * scale
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "1":
                    cv.fill_rect(gx + col * scale, y + row * scale,
                                 scale, scale, color)


def draw_text_centered(cv, x0, x1, y, text, scale, color):
    w = text_width(text, scale)
    draw_text(cv, x0 + (x1 - x0 - w) // 2, y, text, scale, color)


def wrap_lines(text, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------ the day's news
# Sources checked 22 Nov 2026 ~04:30 UTC: Reuters, AP, BBC digests and
# wire aggregators. Every item below is a real 22 Nov 2026 story; the
# two items first filed on 21 Nov carry tag "21 NOV" and are counted
# separately in the DATE CHECK box. Wire times are the first-wire UTC
# times as filed in the day's digests.
LEAD = {
    "kicker": "MIDDLE EAST  \u2022  LEAD STORY",
    "headline": ["IRAN STRIKES", "U.S. BASES IN", "THE GULF"],
    "summary": ["Tehran hits a U.S. base",
                "in Kuwait, targets Bahrain",
                "tankers hit off Oman as",
                "the Gulf war widens."],
    "tag": "WAR WIDENS",
    "wire": "04:26 UTC",
}

# n, region, kicker, headline (2 lines, <=21 chars each), fact (<=40),
# accent color, scene kind, lat, lon, date tag ("" or "21 NOV").
STORIES = [
    {"n": 1, "region": "EUROPE", "kicker": "POLAND",
     "hl": ["RUSSIAN MISSILES", "LAND IN POLAND"],
     "fact": "NATO calls it a violation",
     "color": RED, "scene": "missile", "lat": 52, "lon": 19, "tag": ""},
    {"n": 2, "region": "EUROPE", "kicker": "UKRAINE",
     "hl": ["RUSSIA HITS", "ZELENSKYY'S HOMETOWN"],
     "fact": "Worker and boy, 7, killed",
     "color": ORANGE, "scene": "blast", "lat": 48, "lon": 33, "tag": ""},
    {"n": 3, "region": "EUROPE", "kicker": "UKRAINE",
     "hl": ["TRUMP SIGNALS", "BROADER PEACE DEAL"],
     "fact": "Zelenskyy: talks must deliver",
     "color": NAVY2, "scene": "table", "lat": 50, "lon": 30, "tag": ""},
    {"n": 4, "region": "N. AMERICA", "kicker": "USA-CANADA",
     "hl": ["SECRET MEMO CURBS", "U.S.-CANADA DEFENCE"],
     "fact": "Hegseth limits military ties",
     "color": SLATE, "scene": "memo", "lat": 45, "lon": -75, "tag": ""},
    {"n": 5, "region": "LATIN AMERICA", "kicker": "MEXICO",
     "hl": ["EL CHAPO ISIDRO", "CAPTURED"],
     "fact": "Cartel attacks kill 11",
     "color": NAVY2, "scene": "cuffs", "lat": 25, "lon": -107, "tag": ""},
    {"n": 6, "region": "LATIN AMERICA", "kicker": "PERU",
     "hl": ["6.8 QUAKE SHAKES", "THE ANDES"],
     "fact": "Lima residents flee homes",
     "color": BROWN, "scene": "quake", "lat": -12, "lon": -77, "tag": "21 NOV"},
    {"n": 7, "region": "ASIA", "kicker": "TRADE",
     "hl": ["EU AND INDONESIA", "SIGN TRADE DEAL"],
     "fact": "98.5% of tariffs to fall",
     "color": TEAL, "scene": "ship", "lat": 51, "lon": 4, "tag": "21 NOV"},
    {"n": 8, "region": "GLOBAL", "kicker": "CLIMATE",
     "hl": ["COP31 DEADLOCKED", "IN OVERTIME"],
     "fact": "Split over fossil fuels",
     "color": GREEN, "scene": "globe", "lat": 37, "lon": 31, "tag": ""},
    {"n": 9, "region": "EUROPE", "kicker": "ESTONIA",
     "hl": ["ESTONIA SHUTS ITS", "RUSSIA BORDER"],
     "fact": "All road crossings, 6 months",
     "color": NAVY2, "scene": "fence", "lat": 59, "lon": 25, "tag": ""},
    {"n": 10, "region": "N. AMERICA", "kicker": "USA",
     "hl": ["DEMOCRATS RETAKE", "CONGRESS"],
     "fact": "Midterm win over GOP",
     "color": RED, "scene": "ballot", "lat": 39, "lon": -77, "tag": ""},
    {"n": 11, "region": "SPORT", "kicker": "TENNIS",
     "hl": ["ALCARAZ FACES", "ZVEREV IN FINAL"],
     "fact": "ATP Finals title decider",
     "color": GOLD, "scene": "trophy", "lat": 45, "lon": 7, "tag": ""},
    {"n": 12, "region": "SPORT", "kicker": "RUGBY",
     "hl": ["AUSTRALIA EDGE", "WALES"],
     "fact": "Nations Championship",
     "color": GREEN, "scene": "rugby", "lat": 51, "lon": -3, "tag": ""},
    {"n": 13, "region": "SPORT", "kicker": "RUGBY",
     "hl": ["FRANCE BEAT", "ARGENTINA"],
     "fact": "Final vs South Africa",
     "color": NAVY2, "scene": "trophy", "lat": 49, "lon": 2, "tag": ""},
    {"n": 14, "region": "LATIN AMERICA", "kicker": "BRAZIL",
     "hl": ["BOLSONARO IN", "INTENSIVE CARE"],
     "fact": "Ex-president hospitalised",
     "color": BROWN, "scene": "hospital", "lat": -16, "lon": -48, "tag": ""},
    {"n": 15, "region": "ASIA", "kicker": "WEATHER",
     "hl": ["CYCLONE AKVAN", "LASHES INDIA"],
     "fact": "East coast battered",
     "color": TEAL, "scene": "spiral", "lat": 20, "lon": 85, "tag": ""},
    {"n": 16, "region": "EUROPE", "kicker": "NORWAY",
     "hl": ["NORWAY COURT VOIDS", "OIL LICENCES"],
     "fact": "Climate-disputed permits",
     "color": SLATE, "scene": "scales", "lat": 60, "lon": 10, "tag": ""},
    {"n": 17, "region": "AFRICA", "kicker": "HEALTH",
     "hl": ["KENYA CLEARS LAST", "EBOLA PATIENT"],
     "fact": "DRC toll passes 5,300",
     "color": GREEN, "scene": "virus", "lat": -1, "lon": 37, "tag": ""},
    {"n": 18, "region": "AFRICA", "kicker": "GHANA",
     "hl": ["GHANA UNVEILS NEW", "BANKNOTES"],
     "fact": "Honour Nkrumah, Annan",
     "color": GOLD, "scene": "banknote", "lat": 6, "lon": 0, "tag": ""},
    {"n": 19, "region": "AFRICA", "kicker": "SOMALIA",
     "hl": ["AL-SHABAAB AMBUSH", "KILLS HUNDREDS"],
     "fact": "Somali troops attacked",
     "color": RED, "scene": "ambush", "lat": 2, "lon": 45, "tag": ""},
    {"n": 20, "region": "AFRICA", "kicker": "SUDAN",
     "hl": ["SUDAN SEIZES KEY", "BLUE NILE REGION"],
     "fact": "Tasis Alliance advances",
     "color": BROWN, "scene": "river", "lat": 11, "lon": 34, "tag": ""},
    {"n": 21, "region": "TECH", "kicker": "TECH",
     "hl": ["HUANG RESIGNS;", "NVIDIA IN TURMOIL"],
     "fact": "Trump urges reinstatement",
     "color": SLATE, "scene": "chip", "lat": 37, "lon": -122, "tag": ""},
    {"n": 22, "region": "EUROPE", "kicker": "ECB",
     "hl": ["LAGARDE RESIGNS;", "ECB HUNT BEGINS"],
     "fact": "EU seeks new chief",
     "color": NAVY2, "scene": "bank", "lat": 50, "lon": 8, "tag": ""},
    {"n": 23, "region": "EUROPE", "kicker": "FINLAND",
     "hl": ["DRONES HIT RUSSIAN", "SHIP IN GULF"],
     "fact": "Crew evacuated; fire",
     "color": TEAL, "scene": "shipfire", "lat": 60, "lon": 24, "tag": ""},
    {"n": 24, "region": "ASIA", "kicker": "SCO SUMMIT",
     "hl": ["MODI: PEACE NEEDS", "CIVILISATION TIES"],
     "fact": "At SCO summit",
     "color": GOLD, "scene": "peaks", "lat": 28, "lon": 77, "tag": ""},
]

TICKER = ("Gaza aid convoy hit, 3 killed  \u2022  Netanyahu in marathon "
          "coalition talks  \u2022  Iraq retakes Jurf al-Sakhar  \u2022  "
          "Sahel states restart dialogue  \u2022  Nigeria builds naval "
          "ships  \u2022  Tyla, Tems, Kidjo lead Grammy hopes")

# First-wire UTC times, as filed in the day's digests.
TIMELINE = [
    ("23:51", "PERU QUAKE"),
    ("00:37", "EL CHAPO HELD"),
    ("01:05", "POLAND MISSILES"),
    ("01:35", "MODI AT SCO"),
    ("01:53", "KRYVYI RIH HIT"),
    ("03:07", "HEGSETH MEMO"),
    ("04:20", "TRUMP PEACE"),
    ("04:26", "COP31 FAILS"),
]

# Region chips: (short label, count, chip color, text color).
CHIPS = [
    ("M. EAST 1", RED, WHITE),
    ("EUROPE 7", NAVY2, WHITE),
    ("N. AMER. 2", SLATE, WHITE),
    ("LATAM 3", TEAL, WHITE),
    ("ASIA 3", GREEN, WHITE),
    ("AFRICA 4", BROWN, WHITE),
    ("SPORT 3", GOLD, INK),
    ("TECH 1", SLATE, WHITE),
    ("GLOBAL 1", NAVY, WHITE),
]


# ------------------------------------------------------------- mini scenes
# Each scene draws inside a 46 x 46 box whose top-left is (x, y).
# Small illustrated scenes, not bare geometric pictograms.
def scene_missile(cv, x, y, c):
    """A missile arcing down with fins, flame and ground burst."""
    cv.thick_line(x + 4, y + 40, x + 18, y + 24, SLATE, 2)
    cv.thick_line(x + 18, y + 24, x + 30, y + 12, SLATE, 2)
    cv.poly([(x + 30, y + 4), (x + 38, y + 12), (x + 33, y + 22),
             (x + 25, y + 14)], c)
    cv.poly([(x + 25, y + 14), (x + 31, y + 20), (x + 25, y + 24)], c)
    cv.poly([(x + 33, y + 22), (x + 27, y + 28), (x + 21, y + 22)], c)
    cv.star(x + 20, y + 28, 7, 3, 5, FLAME)
    cv.circle(x + 20, y + 28, 2, GOLD, fill=True)
    cv.star(x + 36, y + 38, 9, 4, 8, GOLD)
    cv.star(x + 36, y + 38, 5, 2, 8, RED)


def scene_blast(cv, x, y, c):
    """An explosion burst over a city skyline."""
    for bx, bw, bh in ((x + 3, 7, 18), (x + 12, 9, 26), (x + 24, 7, 15),
                       (x + 33, 8, 22)):
        cv.fill_rect(bx, y + 42 - bh, bw, bh, c)
    cv.fill_rect(x + 15, y + 8, 5, 5, c)
    cv.star(x + 23, y + 16, 15, 6, 8, FLAME)
    cv.star(x + 23, y + 16, 9, 4, 8, GOLD)
    cv.circle(x + 23, y + 16, 3, WHITE, fill=True)
    cv.thick_line(x + 6, y + 6, x + 12, y + 11, GOLD, 2)
    cv.thick_line(x + 40, y + 5, x + 34, y + 10, GOLD, 2)


def scene_table(cv, x, y, c):
    """A summit table with two flags and two chairs."""
    cv.ellipse(x + 23, y + 30, 18, 6, c)
    cv.fill_rect(x + 5, y + 30, 36, 3, c)
    cv.vline(x + 10, y + 33, y + 42, c, 2)
    cv.vline(x + 36, y + 33, y + 42, c, 2)
    cv.vline(x + 14, y + 8, y + 26, c, 2)
    cv.poly([(x + 14, y + 8), (x + 26, y + 12), (x + 14, y + 16)], RED)
    cv.vline(x + 32, y + 8, y + 26, c, 2)
    cv.poly([(x + 32, y + 8), (x + 20, y + 12), (x + 32, y + 16)], NAVY2)
    cv.circle(x + 8, y + 20, 3, GOLD, fill=True)
    cv.circle(x + 38, y + 20, 3, GOLD, fill=True)


def scene_memo(cv, x, y, c):
    """A classified memo: document, lines, red stamp."""
    cv.fill_rect(x + 10, y + 4, 26, 38, WHITE)
    cv.hline(x + 10, x + 35, y + 4, c, 1)
    cv.hline(x + 10, x + 35, y + 41, c, 1)
    cv.vline(x + 10, y + 4, y + 41, c, 1)
    cv.vline(x + 35, y + 4, y + 41, c, 1)
    for yy in (12, 18, 24, 30):
        cv.hline(x + 14, x + 31, y + yy, MUTED, 1)
    cv.circle(x + 30, y + 34, 7, RED)
    cv.circle(x + 30, y + 34, 4, WHITE)
    cv.fill_rect(x + 28, y + 32, 4, 4, RED)


def scene_cuffs(cv, x, y, c):
    """Handcuffs: two rings joined by a short chain."""
    cv.circle(x + 14, y + 23, 10, c)
    cv.circle(x + 14, y + 23, 6, PAPER)
    cv.circle(x + 32, y + 23, 10, c)
    cv.circle(x + 32, y + 23, 6, PAPER)
    cv.thick_line(x + 21, y + 17, x + 25, y + 17, c, 3)
    cv.circle(x + 23, y + 17, 2, c, fill=True)
    cv.fill_rect(x + 12, y + 21, 3, 5, c)
    cv.fill_rect(x + 30, y + 21, 3, 5, c)
    cv.hline(x + 4, x + 42, y + 38, c, 2)


def scene_quake(cv, x, y, c):
    """Seismograph zigzag over cracked ground."""
    pts = [(x + 2, y + 18), (x + 9, y + 18), (x + 13, y + 7),
           (x + 17, y + 29), (x + 21, y + 11), (x + 25, y + 25),
           (x + 29, y + 18), (x + 35, y + 18), (x + 38, y + 5),
           (x + 41, y + 31), (x + 44, y + 18)]
    for a, b in zip(pts, pts[1:]):
        cv.thick_line(a[0], a[1], b[0], b[1], c, 2)
    cv.poly([(x + 4, y + 40), (x + 12, y + 34), (x + 16, y + 40),
             (x + 24, y + 35), (x + 29, y + 40), (x + 37, y + 36),
             (x + 42, y + 40), (x + 42, y + 43), (x + 4, y + 43)], c)


def scene_ship(cv, x, y, c):
    """A container ship: hull, stacked boxes, funnel, waves."""
    cv.fill_rect(x + 4, y + 26, 38, 5, c)
    cv.poly([(x + 4, y + 26), (x + 8, y + 37), (x + 38, y + 37),
             (x + 42, y + 26)], c)
    for i, col in enumerate((RED, GOLD, TEAL)):
        cv.fill_rect(x + 9 + i * 9, y + 17, 8, 9, col)
    cv.fill_rect(x + 35, y + 12, 6, 14, c)
    cv.star(x + 13, y + 9, 5, 2, 5, GOLD)
    cv.hline(x + 2, x + 44, y + 41, c, 2)
    cv.hline(x + 7, x + 18, y + 44, c, 1)


def scene_globe(cv, x, y, c):
    """A globe with latitude lines and a rising sun behind it."""
    cv.circle(x + 23, y + 23, 16, GOLD, fill=True)
    cv.circle(x + 23, y + 26, 17, c, fill=True)
    cv.circle(x + 23, y + 26, 17, WHITE)
    cv.ellipse(x + 23, y + 26, 17, 6, WHITE)
    cv.ellipse(x + 23, y + 26, 17, 12, WHITE)
    cv.ellipse(x + 23, y + 26, 6, 17, WHITE)
    cv.ellipse(x + 23, y + 26, 12, 17, WHITE)
    cv.hline(x + 6, x + 40, y + 26, WHITE, 1)
    cv.hline(x + 9, x + 37, y + 40, c, 2)


def scene_fence(cv, x, y, c):
    """A border fence: bars, rails and a diagonal wire."""
    for bx in (6, 14, 22, 30, 38):
        cv.vline(x + bx, y + 6, y + 40, c, 2)
    cv.hline(x + 4, x + 42, y + 12, c, 2)
    cv.hline(x + 4, x + 42, y + 34, c, 2)
    cv.thick_line(x + 4, y + 6, x + 42, y + 40, RED, 2)
    cv.circle(x + 23, y + 23, 3, RED, fill=True)


def scene_ballot(cv, x, y, c):
    """A ballot box with a checked vote slip."""
    cv.fill_rect(x + 8, y + 20, 30, 22, c)
    cv.fill_rect(x + 8, y + 20, 30, 4, RED)
    cv.fill_rect(x + 18, y + 16, 10, 4, INK)
    cv.poly([(x + 12, y + 6), (x + 26, y + 6), (x + 30, y + 16),
             (x + 16, y + 16)], WHITE)
    cv.hline(x + 12, x + 35, y + 20, c, 1)
    cv.thick_line(x + 16, y + 27, x + 21, y + 34, WHITE, 3)
    cv.thick_line(x + 21, y + 34, x + 31, y + 24, WHITE, 3)


def scene_trophy(cv, x, y, c):
    """A cup trophy with handles, stem and base."""
    cv.poly([(x + 12, y + 6), (x + 34, y + 6), (x + 31, y + 22),
             (x + 15, y + 22)], GOLD)
    cv.thick_line(x + 12, y + 10, x + 6, y + 16, GOLD, 3)
    cv.thick_line(x + 34, y + 10, x + 40, y + 16, GOLD, 3)
    cv.fill_rect(x + 21, y + 22, 4, 10, GOLD)
    cv.fill_rect(x + 14, y + 32, 18, 4, GOLD)
    cv.fill_rect(x + 11, y + 36, 24, 4, GOLD)
    cv.star(x + 23, y + 13, 6, 2, 5, WHITE)


def scene_rugby(cv, x, y, c):
    """A rugby ball between the goal posts."""
    cv.ellipse(x + 23, y + 26, 16, 10, BROWN)
    cv.ellipse(x + 23, y + 26, 16, 10, WHITE)
    cv.thick_line(x + 10, y + 20, x + 36, y + 32, WHITE, 2)
    cv.vline(x + 6, y + 6, y + 40, c, 2)
    cv.vline(x + 40, y + 6, y + 40, c, 2)
    cv.hline(x + 6, x + 40, y + 10, c, 2)


def scene_hospital(cv, x, y, c):
    """A hospital cross over a bed with a pulse line."""
    cv.fill_rect(x + 8, y + 6, 30, 22, TEAL)
    cv.fill_rect(x + 19, y + 10, 8, 14, WHITE)
    cv.fill_rect(x + 15, y + 14, 16, 6, WHITE)
    cv.hline(x + 4, x + 42, y + 34, c, 2)
    cv.thick_line(x + 4, y + 40, x + 12, y + 40, RED, 2)
    cv.thick_line(x + 12, y + 40, x + 16, y + 34, RED, 2)
    cv.thick_line(x + 16, y + 34, x + 20, y + 44, RED, 2)
    cv.thick_line(x + 20, y + 44, x + 24, y + 40, RED, 2)
    cv.thick_line(x + 24, y + 40, x + 42, y + 40, RED, 2)


def scene_spiral(cv, x, y, c):
    """A cyclone spiral with rain streaks."""
    for r in (18, 14, 10, 6):
        cv.circle(x + 23, y + 22, r, c)
    cv.circle(x + 23, y + 22, 3, RED, fill=True)
    for dx in (2, 12, 30, 40):
        cv.thick_line(x + dx, y + 38, x + dx - 2, y + 44, SLATE, 1)


def scene_scales(cv, x, y, c):
    """The scales of justice: post, beam and two pans."""
    cv.vline(x + 23, y + 6, y + 40, c, 3)
    cv.hline(x + 8, x + 38, y + 10, c, 3)
    cv.circle(x + 23, y + 6, 3, GOLD, fill=True)
    for px in (10, 36):
        cv.thick_line(x + px, y + 10, x + px - 5, y + 20, c, 2)
        cv.thick_line(x + px, y + 10, x + px + 5, y + 20, c, 2)
        cv.ellipse(x + px, y + 22, 7, 3, c)
        cv.fill_rect(x + px - 7, y + 20, 14, 2, c)
    cv.fill_rect(x + 16, y + 40, 14, 3, c)


def scene_virus(cv, x, y, c):
    """A spiky virus particle."""
    for a in range(0, 360, 30):
        rad = math.radians(a)
        x0 = int(x + 23 + 12 * math.cos(rad))
        y0 = int(y + 23 + 12 * math.sin(rad))
        x1 = int(x + 23 + 17 * math.cos(rad))
        y1 = int(y + 23 + 17 * math.sin(rad))
        cv.thick_line(x0, y0, x1, y1, c, 2)
    cv.circle(x + 23, y + 23, 12, c, fill=True)
    cv.circle(x + 19, y + 19, 2, WHITE, fill=True)
    cv.circle(x + 27, y + 27, 2, WHITE, fill=True)


def scene_banknote(cv, x, y, c):
    """A banknote with portrait medallion and denomination."""
    cv.fill_rect(x + 4, y + 12, 38, 22, GREEN)
    cv.fill_rect(x + 7, y + 15, 32, 16, (190, 220, 190))
    cv.circle(x + 15, y + 23, 6, GREEN, fill=True)
    cv.circle(x + 15, y + 23, 3, GOLD, fill=True)
    draw_text(cv, x + 27, y + 19, "1", 1, GREEN)
    cv.hline(x + 27, x + 36, y + 27, GREEN, 1)
    cv.hline(x + 27, x + 36, y + 29, GREEN, 1)


def scene_ambush(cv, x, y, c):
    """An ambush: blast, motion lines and a road."""
    cv.star(x + 23, y + 16, 14, 6, 8, FLAME)
    cv.star(x + 23, y + 16, 8, 3, 8, RED)
    cv.circle(x + 23, y + 16, 3, WHITE, fill=True)
    for yy in (28, 33, 38):
        cv.thick_line(x + 4, y + yy, x + 18, y + yy, SLATE, 2)
    cv.thick_line(x + 28, y + 28, x + 42, y + 28, SLATE, 2)
    cv.fill_rect(x + 4, y + 41, 38, 3, c)


def scene_river(cv, x, y, c):
    """A river bend with a dam wall."""
    for yy in (14, 22, 30):
        prev = None
        for i in range(13):
            px = x + 2 + i * 3
            py = y + yy + int(3 * math.sin(i * 1.1))
            if prev is not None:
                cv.line(prev[0], prev[1], px, py, TEAL)
            prev = (px, py)
    cv.fill_rect(x + 30, y + 8, 5, 30, SLATE)
    cv.fill_rect(x + 26, y + 36, 13, 4, SLATE)
    cv.circle(x + 10, y + 22, 3, GOLD, fill=True)


def scene_chip(cv, x, y, c):
    """A microchip with pins and a die."""
    cv.fill_rect(x + 12, y + 12, 22, 22, SLATE)
    cv.fill_rect(x + 17, y + 17, 12, 12, NAVY2)
    cv.fill_rect(x + 20, y + 20, 6, 6, GOLD)
    for i in range(4):
        xx = x + 16 + i * 5
        cv.vline(xx, y + 6, y + 12, GOLD, 2)
        cv.vline(xx, y + 34, y + 40, GOLD, 2)
        yy = y + 16 + i * 5
        cv.hline(x + 6, x + 12, yy, GOLD, 2)
        cv.hline(x + 34, x + 40, yy, GOLD, 2)


def scene_bank(cv, x, y, c):
    """A central bank: pediment, columns and base."""
    cv.poly([(x + 6, y + 14), (x + 40, y + 14), (x + 23, y + 4)], NAVY2)
    cv.circle(x + 23, y + 11, 2, GOLD, fill=True)
    for bx in (9, 19, 29):
        cv.fill_rect(x + bx, y + 16, 4, 18, NAVY2)
    cv.fill_rect(x + 6, y + 34, 34, 3, NAVY2)
    cv.fill_rect(x + 4, y + 38, 38, 3, NAVY2)


def scene_shipfire(cv, x, y, c):
    """A cargo ship hit by drones: smoke, flame, drone dots."""
    cv.fill_rect(x + 4, y + 28, 34, 5, c)
    cv.poly([(x + 4, y + 28), (x + 8, y + 38), (x + 34, y + 38),
             (x + 38, y + 28)], c)
    cv.fill_rect(x + 10, y + 20, 8, 8, RED)
    cv.fill_rect(x + 20, y + 20, 8, 8, GOLD)
    cv.circle(x + 14, y + 12, 4, SLATE, fill=True)
    cv.circle(x + 20, y + 8, 3, SLATE, fill=True)
    cv.star(x + 30, y + 14, 7, 3, 5, FLAME)
    cv.circle(x + 36, y + 6, 2, INK, fill=True)
    cv.hline(x + 2, x + 44, y + 42, c, 2)


def scene_peaks(cv, x, y, c):
    """Mountain peaks with a summit flag and sun."""
    cv.circle(x + 36, y + 10, 5, GOLD, fill=True)
    cv.poly([(x + 2, y + 40), (x + 14, y + 16), (x + 26, y + 40)], SLATE)
    cv.poly([(x + 20, y + 40), (x + 32, y + 10), (x + 44, y + 40)], c)
    cv.poly([(x + 32, y + 10), (x + 36, y + 16), (x + 30, y + 18)], WHITE)
    cv.vline(x + 32, y + 4, y + 12, INK, 2)
    cv.poly([(x + 32, y + 4), (x + 41, y + 6), (x + 32, y + 9)], RED)
    cv.hline(x + 2, x + 44, y + 42, BROWN, 2)


SCENES = {
    "missile": scene_missile,
    "blast": scene_blast,
    "table": scene_table,
    "memo": scene_memo,
    "cuffs": scene_cuffs,
    "quake": scene_quake,
    "ship": scene_ship,
    "globe": scene_globe,
    "fence": scene_fence,
    "ballot": scene_ballot,
    "trophy": scene_trophy,
    "rugby": scene_rugby,
    "hospital": scene_hospital,
    "spiral": scene_spiral,
    "scales": scene_scales,
    "virus": scene_virus,
    "banknote": scene_banknote,
    "ambush": scene_ambush,
    "river": scene_river,
    "chip": scene_chip,
    "bank": scene_bank,
    "shipfire": scene_shipfire,
    "peaks": scene_peaks,
}


# ---------------------------------------------------------------- world map
# Coarse continent outlines in (lon, lat); drawn equirectangular.
CONTINENTS = [
    [(-168, 66), (-150, 70), (-135, 69), (-125, 72), (-115, 73),
     (-105, 72), (-95, 80), (-85, 72), (-80, 73), (-70, 62), (-65, 60),
     (-60, 52), (-55, 47), (-60, 45), (-65, 44), (-70, 42), (-74, 39),
     (-76, 35), (-80, 32), (-81, 26), (-84, 30), (-90, 21), (-94, 17),
     (-97, 16), (-92, 14), (-87, 13), (-83, 9), (-79, 9), (-85, 12),
     (-90, 14), (-95, 16), (-100, 18), (-105, 20), (-110, 23),
     (-114, 29), (-120, 34), (-124, 40), (-124, 48), (-130, 55),
     (-140, 60), (-150, 60), (-160, 58), (-165, 60), (-168, 66)],
    [(-79, 9), (-75, 11), (-72, 12), (-68, 11), (-62, 10), (-58, 8),
     (-52, 5), (-50, 0), (-44, -3), (-38, -5), (-35, -8), (-38, -15),
     (-40, -20), (-42, -23), (-48, -27), (-52, -32), (-58, -35),
     (-62, -39), (-65, -45), (-68, -50), (-70, -54), (-72, -50),
     (-73, -40), (-73, -30), (-71, -20), (-75, -15), (-79, -8),
     (-81, -4), (-80, 1), (-79, 9)],
    [(-10, 36), (-9, 43), (-4, 48), (-2, 49), (0, 50), (2, 51), (5, 53),
     (7, 55), (8, 57), (10, 59), (13, 56), (18, 56), (21, 55), (24, 58),
     (28, 60), (30, 62), (32, 68), (38, 68), (42, 66), (40, 60),
     (38, 56), (34, 54), (30, 55), (28, 52), (28, 47), (26, 44),
     (23, 40), (22, 38), (19, 42), (15, 44), (12, 44), (8, 44),
     (6, 43), (3, 42), (0, 38), (-2, 37), (-6, 36), (-9, 37)],
    [(-17, 15), (-16, 21), (-13, 27), (-10, 31), (-6, 34), (-1, 35),
     (5, 37), (10, 37), (15, 33), (20, 32), (25, 32), (30, 31),
     (33, 28), (35, 28), (38, 22), (40, 15), (43, 12), (48, 11),
     (51, 12), (50, 8), (45, 2), (42, -2), (40, -6), (38, -12),
     (36, -18), (34, -24), (32, -28), (28, -33), (22, -35), (18, -34),
     (16, -29), (14, -22), (12, -18), (12, -12), (10, -4), (9, 0),
     (9, 4), (4, 6), (-2, 5), (-8, 5), (-13, 8), (-15, 11)],
    [(40, 68), (44, 70), (50, 70), (56, 70), (62, 70), (68, 72),
     (74, 73), (80, 73), (86, 74), (92, 75), (98, 76), (104, 77),
     (110, 76), (116, 73), (122, 72), (128, 72), (134, 71), (140, 72),
     (146, 71), (152, 69), (158, 66), (162, 64), (168, 66), (173, 66),
     (178, 65), (180, 65), (178, 62), (172, 60), (166, 60), (160, 55),
     (156, 52), (150, 59), (144, 55), (142, 50), (140, 46), (138, 42),
     (135, 43), (131, 42), (129, 38), (127, 36), (126, 33), (122, 30),
     (120, 25), (116, 22), (110, 20), (108, 16), (106, 10), (104, 8),
     (102, 8), (100, 10), (98, 14), (96, 16), (94, 18), (92, 21),
     (90, 22), (88, 22), (86, 20), (84, 18), (82, 16), (80, 12),
     (78, 8), (76, 10), (74, 15), (72, 20), (70, 22), (68, 24),
     (66, 25), (64, 25), (62, 25), (60, 25), (58, 26), (56, 27),
     (54, 27), (52, 28), (50, 29), (48, 30), (46, 32), (44, 35),
     (42, 38), (40, 42), (38, 44), (36, 44), (34, 42), (32, 42),
     (30, 44), (28, 46), (28, 50), (30, 55), (32, 60), (34, 64),
     (36, 66), (38, 68)],
    [(113, -22), (114, -28), (115, -33), (118, -35), (124, -33),
     (129, -32), (134, -33), (138, -35), (140, -38), (144, -38),
     (147, -39), (150, -37), (153, -32), (153, -27), (150, -22),
     (146, -19), (143, -14), (142, -11), (140, -17), (136, -12),
     (132, -11), (128, -14), (124, -15), (120, -14), (116, -20),
     (113, -22)],
]


def draw_map(cv, x, y, w, h):
    """Navy world map with numbered pins for the lead + 24 stories.

    Pins are displaced deterministically (fixed +13/+7 steps, never
    random) when they would collide, with a leader line back to the
    true projected point.
    """
    cv.fill_rect(x, y, w, h, NAVY)
    draw_text(cv, x + 8, y + 6, "WHERE IT HAPPENED", 2, WHITE)
    mx, my = x + 6, y + 26
    mw, mh = w - 12, h - 32
    cv.fill_rect(mx, my, mw, mh, SEA)
    cv.dither_rect(mx, my, mw, mh, SEA, (20, 62, 100))

    def proj(lon, lat):
        px = mx + int((lon + 180) / 360.0 * mw)
        py = my + int((90 - lat) / 180.0 * mh)
        return px, py

    # graticule every 30 degrees
    for lon in range(-180, 181, 30):
        px, _ = proj(lon, 0)
        cv.vline(px, my, my + mh - 1, GRID, 1)
    for lat in range(-60, 91, 30):
        _, py = proj(0, lat)
        cv.hline(mx, mx + mw - 1, py, GRID, 1)
    for poly in CONTINENTS:
        cv.poly([proj(lon, lat) for lon, lat in poly], SAND)
    cv.grain(mx, my, mw, mh, (198, 166, 112), (230, 200, 150), 1)

    # pins: lead star first, then stories 01..24 in fixed order.
    placed = []

    RING = [(0, 0), (16, 0), (-16, 0), (0, -14), (0, 14),
            (16, -14), (-16, -14), (16, 14), (-16, 14),
            (32, 0), (-32, 0), (0, -28), (0, 28),
            (32, -14), (-32, -14), (32, 14), (-32, 14),
            (16, -28), (-16, -28), (16, 28), (-16, 28),
            (48, 0), (-48, 0), (0, -42), (0, 42)]

    def place_pin(tx, ty, label, color, star=False):
        px, py = tx, ty
        for (dx, dy) in RING:
            cx = min(max(tx + dx, mx), mx + mw - 14)
            cy = min(max(ty + dy, my), my + mh - 12)
            clash = False
            for (qx, qy) in placed:
                if abs(cx - qx) < 15 and abs(cy - qy) < 13:
                    clash = True
                    break
            if not clash:
                px, py = cx, cy
                break
        placed.append((px, py))
        if px != tx or py != ty:
            cv.line(tx, ty, px + 6, py + 5, WHITE)
        if star:
            cv.star(px + 7, py + 6, 9, 4, 5, GOLD)
            cv.circle(px + 7, py + 6, 2, INK, fill=True)
        else:
            cv.fill_rect(px, py, 13, 11, color)
            cv.hline(px, px + 12, py, WHITE, 1)
            draw_text(cv, px + 1, py + 2, label, 1, WHITE)

    lx, ly = proj(51, 26)
    place_pin(lx, ly, "", RED, star=True)
    for s in STORIES:
        tx, ty = proj(s["lon"], s["lat"])
        place_pin(tx, ty, "%02d" % s["n"], RED)
    cv.fill_rect(mx, my + mh - 14, 118, 14, NAVY2)
    draw_text(cv, mx + 4, my + mh - 11, "LEAD = GOLD STAR", 1, GOLD)


# ------------------------------------------------------------------- layout
MARGIN = 24


def draw_lead_scene(cv, x, y, w, h):
    """Night over the Gulf: coastline, two blasts, missile arcs, a tanker."""
    cv.fill_rect(x, y, w, h, SEA)
    cv.dither_rect(x, y, w, h, SEA, (20, 62, 100))
    cv.grain(x, y, w, h, (10, 36, 60), (30, 80, 130), 1)
    cv.poly([(x, y + 30), (x + 110, y + 22), (x + 90, y + 90),
             (x + 120, y + 140), (x + 80, y + 190), (x + 95, y + h),
             (x, y + h)], SAND)
    kx, ky = x + 82, y + 55
    bx, by = x + 66, y + 118
    cv.circle(kx, ky, 4, WHITE, fill=True)
    cv.circle(bx, by, 4, WHITE, fill=True)
    draw_text(cv, kx + 14, ky - 7, "KUWAIT", 2, WHITE)
    draw_text(cv, bx + 14, by - 7, "BAHRAIN", 2, WHITE)
    for (ex, ey) in ((kx, ky), (bx, by)):
        sx, sy = x + w - 18, y + 16
        prev = (sx, sy)
        for i in range(1, 13):
            t = i / 12.0
            px = int(sx + (ex - sx) * t)
            py = int(sy + (ey - sy) * t - 22 * math.sin(math.pi * t))
            if i % 2 == 0:
                cv.thick_line(prev[0], prev[1], px, py, GOLD, 2)
            prev = (px, py)
    cv.star(kx, ky, 20, 8, 8, GOLD)
    cv.star(kx, ky, 12, 5, 8, (230, 60, 30))
    cv.star(bx, by, 17, 7, 8, GOLD)
    cv.star(bx, by, 10, 4, 8, (230, 60, 30))
    tx, ty = x + 190, y + 150
    cv.fill_rect(tx, ty, 80, 8, NAVY2)
    cv.poly([(tx, ty), (tx + 6, ty + 15), (tx + 74, ty + 15),
             (tx + 80, ty)], NAVY2)
    for i, col in enumerate((RED, GOLD, TEAL)):
        cv.fill_rect(tx + 10 + i * 18, ty - 12, 15, 12, col)
    cv.star(tx + 22, ty - 20, 9, 4, 5, FLAME)
    draw_text(cv, tx + 4, ty + 20, "TANKERS HIT", 2, SKY)
    draw_text(cv, tx + 4, ty + 34, "OFF OMAN", 2, SKY)
    cv.fill_rect(x, y + h - 24, w, 24, NAVY)
    draw_text(cv, x + 12, y + h - 18, "U.S. BASE HIT IN KUWAIT", 2, WHITE)


def draw_masthead(cv):
    cv.hline(MARGIN, W - MARGIN, 12, INK, 2)
    draw_text(cv, MARGIN, 20, "SUNDAY, 22 NOVEMBER 2026", 2, INK)
    right = "ONE IMAGE  \u2022  THE DAY'S NEWS"
    draw_text(cv, W - MARGIN - text_width(right, 2), 20, right, 2, RED)
    draw_text_centered(cv, MARGIN, W - MARGIN, 38, "THE WORLD TODAY", 6, INK)
    cv.hline(MARGIN, W - MARGIN, 86, INK, 4)
    cv.hline(MARGIN, W - MARGIN, 92, INK, 1)


def draw_chips(cv):
    x = MARGIN
    for label, bg, fg in CHIPS:
        w = text_width(label, 2) + 10
        cv.fill_rect(x, 98, w, 22, bg)
        draw_text(cv, x + 5, 102, label, 2, fg)
        x += w + 5


def draw_timeline(cv):
    draw_text(cv, MARGIN, 128, "FIRST WIRE \u2014 UTC", 2, INK)
    cv.hline(240, 990, 142, INK, 2)
    for i, (time, label) in enumerate(TIMELINE):
        tx = 250 + i * 105
        cv.circle(tx, 142, 2, INK, fill=True)
        tw = text_width(time, 1)
        lx = min(max(tx - tw // 2, MARGIN), W - MARGIN - tw)
        draw_text(cv, lx, 128, time, 1, INK)
        lw = text_width(label, 1)
        lx = min(max(tx - lw // 2, MARGIN), W - MARGIN - lw)
        draw_text(cv, lx, 148, label, 1, MUTED)


def draw_lead_text(cv, x, y, w):
    draw_text(cv, x, y + 6, "MIDDLE EAST \u2022 LEAD", 2, RED)
    cv.hline(x, x + w, y + 28, RED, 2)
    yy = y + 36
    for line in LEAD["headline"]:
        draw_text(cv, x, yy, line, 3, INK)
        yy += 24
    yy = y + 116
    for line in LEAD["summary"]:
        draw_text(cv, x, yy, line, 2, MUTED)
        yy += 16
    tag = LEAD["tag"]
    tw = text_width(tag, 2)
    cv.fill_rect(x, y + 182, tw + 20, 20, RED)
    draw_text(cv, x + 10, y + 187, tag, 2, WHITE)
    draw_text(cv, x + tw + 30, y + 187, "WIRE " + LEAD["wire"], 1, MUTED)


def draw_datecheck(cv):
    y, h = 372, 26
    cv.fill_rect(MARGIN, y, W - 2 * MARGIN, h, PINK)
    cv.hline(MARGIN, W - MARGIN, y, RED, 2)
    cv.hline(MARGIN, W - MARGIN, y + h - 1, RED, 2)
    cv.vline(MARGIN, y, y + h - 1, RED, 2)
    cv.vline(W - MARGIN, y, y + h - 1, RED, 2)
    draw_text(cv, MARGIN + 12, y + 6,
              "DATE CHECK: 23 filed 22 NOV  \u2022  2 from 21 NOV \u2014 "
              "EU DEAL, PERU QUAKE (tagged)", 2, INK)


def draw_card(cv, x, y, w, h, story):
    cv.fill_rect(x, y, w, h, CARD)
    cv.grain(x, y, w, h, (238, 233, 224), (255, 253, 250), 1)
    cv.fill_rect(x, y, 5, h, story["color"])
    cv.vline(x + w - 1, y, y + h - 1, HAIR, 1)
    cv.hline(x, x + w - 1, y + h - 1, HAIR, 1)
    SCENES[story["scene"]](cv, x + 8, y + 9, story["color"])
    tx = x + 60
    draw_text(cv, tx, y + 7, "#%02d" % story["n"], 2, story["color"])
    draw_text(cv, tx + 40, y + 7, story["kicker"], 2, INK)
    if story["tag"]:
        cv.fill_rect(x + w - 54, y + 7, 46, 13, RED)
        draw_text(cv, x + w - 49, y + 9, story["tag"], 1, WHITE)
    yy = y + 24
    for line in story["hl"]:
        draw_text(cv, tx, yy, line, 2, INK)
        yy += 15
    draw_text(cv, tx, y + 54, story["fact"], 1, MUTED)


def draw_ticker_footer(cv):
    draw_text(cv, MARGIN, 968, "ALSO TODAY", 2, RED)
    lines = wrap_lines(TICKER, 1, W - MARGIN - 160)
    for i, line in enumerate(lines[:2]):
        draw_text(cv, MARGIN + 136, 968 + i * 10, line, 1, INK)
    cv.hline(MARGIN, W - MARGIN, 994, INK, 1)
    draw_text_centered(cv, MARGIN, W - MARGIN, 1002,
                       "Sources: Reuters  \u2022  AP  \u2022  BBC  \u2022  "
                       "wire digests, 22 Nov 2026 \u2014 25 stories, "
                       "9 regions, all dated", 1, MUTED)


def draw_page(cv):
    cv.fill_rect(0, 0, W, H, PAPER)
    cv.grain(0, 0, W, H, (232, 226, 214), (255, 250, 242), 1)
    draw_masthead(cv)
    draw_chips(cv)
    draw_timeline(cv)
    draw_lead_scene(cv, MARGIN, 162, 330, 204)
    draw_lead_text(cv, 366, 162, 300)
    draw_map(cv, 678, 162, 322, 204)
    draw_datecheck(cv)
    for i, story in enumerate(STORIES):
        row, col = divmod(i, 3)
        x = MARGIN + col * 328
        y = 404 + row * 70
        draw_card(cv, x, y, 320, 64, story)
    draw_ticker_footer(cv)


# --------------------------------------------------------------------- main
def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        out_dir = "/output" if os.path.isdir("/output") else "output"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    cv = Canvas(W, H, PAPER)
    draw_page(cv)
    size = write_png(path, cv)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))
    print("stories: 1 lead + %d grid = %d, ticker items: 6" %
          (len(STORIES), 1 + len(STORIES)))


if __name__ == "__main__":
    main()

