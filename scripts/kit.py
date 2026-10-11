"""Shared toolkit for the profile SVGs.

Everything here mirrors fabioportfolio.com: the same fonts (embedded as
subsets, so the SVGs render identically everywhere), the same palette and the
same paper / ink / torn-edge SVG filters.
"""
import base64
import io
import os
import urllib.request
from functools import lru_cache
from xml.sax.saxutils import escape

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, 'assets')
CACHE = os.path.join(ROOT, 'scripts', '.cache')

INK = '#141210'
PAPER = '#d9d6cf'
CARD = '#f7f4ec'
CREAM = '#f3e9dc'
ACCENT = '#3450c4'
RED = '#d94e34'
DARK = '#0d0c11'

FONTS = {
    'display': ('inter-tight', 900),
    'body': ('archivo', 400),
    'semi': ('archivo', 600),
    'hand': ('caveat', 600),
    'hand-md': ('caveat', 500),
    'mono': ('ibm-plex-mono', 400),
    'mono-md': ('ibm-plex-mono', 500),
}


# --------------------------------------------------------------------------- fonts

def font_path(key):
    family, weight = FONTS[key]
    path = os.path.join(CACHE, f'{family}-{weight}.woff2')
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        url = f'https://cdn.jsdelivr.net/fontsource/fonts/{family}@latest/latin-{weight}-normal.woff2'
        urllib.request.urlretrieve(url, path)
    return path


@lru_cache(None)
def _metrics(key):
    font = TTFont(font_path(key))
    return font.getBestCmap(), font['hmtx'], font['head'].unitsPerEm


def text_width(text, key, size, tracking=0.0):
    cmap, hmtx, upm = _metrics(key)
    fallback = cmap[ord('?')]
    units = sum(hmtx[cmap.get(ord(c), fallback)][0] for c in text)
    return units * size / upm + tracking * size * len(text)


def wrap(text, key, size, width, tracking=0.0):
    lines, cur = [], ''
    for word in text.split():
        trial = f'{cur} {word}'.strip()
        if cur and text_width(trial, key, size, tracking) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def clamp_lines(lines, n, key, size, width):
    """Keep at most n lines, ending the last one with an ellipsis if cut."""
    if len(lines) <= n:
        return lines
    last = lines[n - 1]
    while last and text_width(last + '…', key, size) > width:
        last = last.rsplit(' ', 1)[0] if ' ' in last else last[:-1]
    return lines[:n - 1] + [last.rstrip(',.;:') + '…']


def font_face(key, chars):
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = ['kern', 'calt', 'liga']
    opts.name_IDs = []
    opts.hinting = False
    font = TTFont(font_path(key), recalcTimestamp=False)  # stable output, no daily diff noise
    sub = subset.Subsetter(opts)
    sub.populate(text=''.join(sorted(chars)))
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = 'woff2'
    font.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'fa-{key}';src:url(data:font/woff2;base64,{b64}) format('woff2')}}"


# --------------------------------------------------------------------------- canvas

class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.defs, self.css, self.body = [], [], []
        self.used = {}

    def text(self, x, y, content, key, size, fill=INK, tracking=0.0, anchor='start', attrs=''):
        """content is a string or a list of (string, tspan-attrs) segments."""
        segments = [(content, '')] if isinstance(content, str) else content
        inner = ''
        for seg, seg_attrs in segments:
            self.used.setdefault(key, set()).update(seg)
            inner += f'<tspan {seg_attrs}>{escape(seg)}</tspan>' if seg_attrs else escape(seg)
        ls = f' letter-spacing="{tracking * size:.2f}"' if tracking else ''
        anchor_attr = f' text-anchor="{anchor}"' if anchor != 'start' else ''
        return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="fa-{key}" font-size="{size}"'
                f' fill="{fill}"{ls}{anchor_attr} {attrs}>{inner}</text>')

    def add(self, *parts):
        self.body.extend(parts)

    def render(self):
        faces = ''.join(font_face(k, chars) for k, chars in sorted(self.used.items()))
        css = ''.join(self.css) + REDUCED_MOTION
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img" aria-label="{escape(self.title)}">'
                f'<title>{escape(self.title)}</title>'
                f'<style>{faces}{css}</style>'
                f'<defs>{"".join(self.defs)}</defs>'
                f'{"".join(self.body)}</svg>')

    def save(self, name):
        path = os.path.join(ASSETS, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = self.render()
        with open(path, 'w', encoding='utf8', newline='\n') as f:
            f.write(data)
        print(f'  {name:<34} {len(data) / 1024:7.1f} KB')


REDUCED_MOTION = '@media (prefers-reduced-motion:reduce){*{animation:none!important}}'

# Shared keyframes. Elements only declare their *start* state inside the
# keyframes, so with motion disabled everything simply shows its final state.
ANIM = """
@keyframes rise{from{opacity:0;transform:translateY(18px)}}
@keyframes fade{from{opacity:0}}
@keyframes draw{from{stroke-dashoffset:100}}
@keyframes grow{from{transform:scaleX(0)}}
@keyframes stamp{0%{opacity:0;transform:scale(1.9)}60%{opacity:1;transform:scale(.94)}100%{transform:scale(1)}}
@keyframes wiggle{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(8deg)}}
.rise{animation:rise .9s cubic-bezier(.22,1,.36,1) both}
.fade{animation:fade .8s ease both}
.draw{stroke-dasharray:100;animation:draw 1.6s cubic-bezier(.65,0,.35,1) both}
.grow{transform-box:fill-box;transform-origin:left center;animation:grow 1s cubic-bezier(.22,1,.36,1) both}
.stamp{transform-box:fill-box;transform-origin:center;animation:stamp .55s cubic-bezier(.3,1.4,.5,1) both}
.wiggle{transform-box:fill-box;transform-origin:center;animation:wiggle 5s ease-in-out infinite}
"""


def delays(*pairs):
    return ''.join(f'.d{i}{{animation-delay:{d}s}}' for i, d in pairs)


# --------------------------------------------------------------------------- filters

def f_paper(fid='paper', seed=4, scale=9, freq=0.035, shadow=(4, 8, 7, 0.32)):
    """Torn edges (feDisplacementMap) plus a soft drop shadow."""
    dx, dy, sd, op = shadow
    return (f'<filter id="{fid}" x="-6%" y="-8%" width="112%" height="120%" color-interpolation-filters="sRGB">'
            f'<feTurbulence type="fractalNoise" baseFrequency="{freq}" numOctaves="3" seed="{seed}" result="n"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="n" scale="{scale}" xChannelSelector="R" yChannelSelector="G"/>'
            f'<feDropShadow dx="{dx}" dy="{dy}" stdDeviation="{sd}" flood-color="#000" flood-opacity="{op}"/>'
            f'</filter>')


def f_grain(fid='grain', alpha=0.17, freq=0.9, seed=1):
    """Paper grain, same recipe as the site's grain overlay."""
    return (f'<filter id="{fid}" x="0" y="0" width="100%" height="100%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="{freq}" numOctaves="2" seed="{seed}" stitchTiles="stitch"/>'
            f'<feColorMatrix values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 {alpha} 0"/>'
            f'</filter>')


def f_ink(fid='ink', blur=3, color=INK):
    """The site's inkBleed: thresholded blur eaten by noise."""
    return (f'<filter id="{fid}" x="-10%" y="-20%" width="120%" height="140%" color-interpolation-filters="sRGB">'
            f'<feGaussianBlur in="SourceAlpha" stdDeviation="{blur}" result="b"/>'
            f'<feComponentTransfer in="b" result="t"><feFuncA type="table" tableValues="0 0 0 .3 1 1 1"/></feComponentTransfer>'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="5" result="n"/>'
            f'<feColorMatrix in="n" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .9 .55" result="g"/>'
            f'<feComposite in="t" in2="g" operator="in" result="ink"/>'
            f'<feFlood flood-color="{color}" result="c"/>'
            f'<feComposite in="c" in2="ink" operator="in"/>'
            f'</filter>')


def f_soft(fid='soft'):
    """The site's inkSoft, keeps the source colour."""
    return (f'<filter id="{fid}" x="-10%" y="-20%" width="120%" height="140%" color-interpolation-filters="sRGB">'
            f'<feGaussianBlur in="SourceGraphic" stdDeviation="1.1" result="b"/>'
            f'<feComponentTransfer in="b" result="t"><feFuncA type="table" tableValues="0 0 .35 1 1"/></feComponentTransfer>'
            f'<feTurbulence type="fractalNoise" baseFrequency="1.1" numOctaves="2" seed="8" result="n"/>'
            f'<feColorMatrix in="n" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 .7 .7" result="g"/>'
            f'<feComposite in="t" in2="g" operator="in"/>'
            f'</filter>')


def f_pen(fid='pen', scale=3, seed=2):
    """Slightly wobbly, grainy stroke, like the site's chalk filter."""
    return (f'<filter id="{fid}" x="-10%" y="-10%" width="120%" height="120%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.12" numOctaves="3" seed="{seed}" result="n"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="n" scale="{scale}" xChannelSelector="R" yChannelSelector="G" result="d"/>'
            f'<feTurbulence type="fractalNoise" baseFrequency="1.2" numOctaves="1" seed="9" result="g"/>'
            f'<feColorMatrix in="g" type="matrix" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 1.6 -.35" result="m"/>'
            f'<feComposite in="d" in2="m" operator="in"/>'
            f'</filter>')


def f_stamp(fid='stamp', seed=3):
    """Rubber-stamp ink: patchy coverage plus a rough outline."""
    return (f'<filter id="{fid}" x="-10%" y="-20%" width="120%" height="140%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.08" numOctaves="2" seed="{seed}" result="w"/>'
            f'<feDisplacementMap in="SourceGraphic" in2="w" scale="2.5" xChannelSelector="R" yChannelSelector="G" result="d"/>'
            f'<feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="2" seed="{seed + 4}" result="g"/>'
            f'<feColorMatrix in="g" type="matrix" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 3 -.62" result="m"/>'
            f'<feComposite in="d" in2="m" operator="in"/>'
            f'</filter>')


def f_shadow(fid='shadow', dx=4, dy=7, sd=6, op=0.3):
    return (f'<filter id="{fid}" x="-10%" y="-10%" width="125%" height="130%">'
            f'<feDropShadow dx="{dx}" dy="{dy}" stdDeviation="{sd}" flood-color="#000" flood-opacity="{op}"/>'
            f'</filter>')


# --------------------------------------------------------------------------- shapes

# clip-path polygons lifted from the site's CSS (percentages).
CARD_EDGE = [(1, 2), (18, 0), (34, 2), (52, 0), (70, 1.5), (86, 0), (99, 2), (100, 20), (98.5, 38),
             (100, 55), (99, 72), (100, 88), (98, 100), (80, 98.5), (62, 100), (45, 98), (28, 100),
             (12, 98.5), (0, 100), (1, 84), (0, 66), (1.5, 48), (0, 30), (1, 14)]
TAPE_EDGE = [(0, 3), (7, 0), (22, 2), (38, 0), (55, 3), (72, 0), (88, 2), (100, 0), (99, 22), (100, 48),
             (98, 70), (100, 100), (84, 97), (66, 100), (48, 97), (30, 100), (14, 98), (0, 100), (2, 76),
             (0, 52), (2, 26)]


def poly(points, x, y, w, h):
    """Map a percentage polygon onto a box."""
    return ' '.join(f'{x + px * w / 100:.1f},{y + py * h / 100:.1f}' for px, py in points)


def torn_rect(x, y, w, h, step=46, depth=4, seed=1):
    """Hand-torn rectangle whose tear depth is in pixels, not percent, so it
    looks the same on tiny and huge sheets."""
    import random
    rnd = random.Random(seed)
    pts = []

    def run(x0, y0, x1, y1, nx, ny):
        n = max(2, int(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / step))
        for i in range(n):
            t = i / n
            d = rnd.uniform(0, depth)
            pts.append((x0 + (x1 - x0) * t + nx * d, y0 + (y1 - y0) * t + ny * d))

    run(x, y, x + w, y, 0, 1)
    run(x + w, y, x + w, y + h, -1, 0)
    run(x + w, y + h, x, y + h, 0, -1)
    run(x, y + h, x, y, 1, 0)
    return ' '.join(f'{px:.1f},{py:.1f}' for px, py in pts)


def arrow_ne(x, y, s=10, color=CREAM, width=1.8):
    """↗ drawn as a path (the fonts don't ship the glyph)."""
    return (f'<path d="M{x:.1f} {y + s:.1f} L{x + s:.1f} {y:.1f} M{x + s * .3:.1f} {y:.1f} L{x + s:.1f} {y:.1f} '
            f'L{x + s:.1f} {y + s * .7:.1f}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def star(cx, cy, r, fill=INK):
    import math
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(f'{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}')
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


GITHUB_ICON = ('M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235'
               '-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 '
               '1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305'
               '.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 '
               '.405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625'
               '-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 '
               '12c0-6.63-5.37-12-12-12z')

# The site's compass doodle (100x100 box).
COMPASS = [
    'M50 4 C 52 26, 54 34, 57 46 C 66 40, 76 34, 94 26 C 78 38, 68 46, 60 52 C 68 62, 76 74, 88 92 C 72 78, 62 68, '
    '54 60 C 48 70, 42 82, 32 96 C 40 78, 45 68, 48 58 C 34 56, 22 54, 4 50 C 24 48, 36 48, 47 48 C 48 34, 49 22, 50 4',
    'M50 8 C 51 28, 53 36, 56 47 C 65 41, 74 36, 90 28',
    'M46 50 C 32 52, 20 53, 7 51',
]


# --------------------------------------------------------------------------- section headings

def heading(name, title, hint, dark):
    """Big Caveat section title + mono hint, in a light and a dark variant."""
    ink = CREAM if dark else INK
    s = Svg(1000, 132, title)
    s.defs.append(f_soft('soft'))
    s.css.append(ANIM + delays((1, 0.15), (2, 0.5)))
    # long titles shrink so they never run into the hint on the right
    room = 994 - (text_width(hint, 'mono-md', 12, 0.14) + 28) - 36
    size = min(82, round(82 * room / text_width(title, 'hand', 82)))
    tw = text_width(title, 'hand', size)
    s.add(f'<g filter="url(#soft)" class="rise">{s.text(6, 86, title, "hand", size, fill=ink)}</g>')
    # hand-drawn underline that writes itself in
    x0, x1 = 10, 10 + tw * 0.92
    s.add(f'<path class="draw d1" pathLength="100" d="M{x0} 108 C {x0 + tw * .3:.0f} 100, {x0 + tw * .6:.0f} 112, '
          f'{x1:.0f} 101 C {x1 + 8:.0f} 99, {x1 + 10:.0f} 104, {x1 - 6:.0f} 108" fill="none" stroke="{ACCENT}" '
          f'stroke-width="5" stroke-linecap="round"/>')
    hw = text_width(hint, 'mono-md', 12, 0.14)
    s.add(f'<rect x="{994 - hw - 28:.1f}" y="62" width="{hw + 28:.1f}" height="30" rx="4" fill="{ink}" '
          f'fill-opacity=".08" class="fade d2"/>')
    s.add(s.text(994 - 14, 82, hint, 'mono-md', 12, fill=ink, tracking=0.14, anchor='end',
                 attrs='opacity=".75" class="fade d2"'))
    s.save(f'{name}-{"dark" if dark else "light"}.svg')
