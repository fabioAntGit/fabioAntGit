"""Builds the static SVGs of the profile README (hero, buttons, project cards,
headings, footer). Run from the repo root:  python scripts/build.py
"""
import base64
import io
import os

from PIL import Image

from kit import (ACCENT, ANIM, CARD, CARD_EDGE, COMPASS, CREAM, DARK, GITHUB_ICON, INK, PAPER, RED, ROOT,
                 TAPE_EDGE, Svg, arrow_ne, delays, f_grain, f_ink, f_paper, f_pen, f_shadow, f_stamp,
                 heading, poly, text_width, torn_rect, wrap)

IMAGES = os.path.join(ROOT, 'scripts', 'images')

PROJECTS = [
    {
        'slug': 'attesta',
        'name': 'Attesta',
        'blurb': 'Trained a small ML model, generated a zero-knowledge proof of its prediction, and verified that '
                 'proof on-chain, enabling trustless AI inference without revealing the model or the input.',
        'stack': 'Python · PyTorch · EZKL · Solidity',
        'cover': ('attesta_logo.png', 1.0, None),
        'tilt': -1.4,
    },
    {
        'slug': 'politutor',
        'name': 'PoliTutor',
        'blurb': 'Full-stack AI tutoring platform with a RAG pipeline built from scratch: chunking, embeddings, '
                 'reranking, short/long-term memory and multi-layer guardrails. Benchmarked embedding models, '
                 'rerankers and chunking strategies for retrieval quality.',
        'stack': 'Python · React/Vite · FastAPI · MongoDB · Redis · ChromaDB',
        'cover': ('poli_tutor_question.webp', 1.15, None),
        'tilt': 1.2,
    },
    {
        'slug': 'chair-cv',
        'name': 'Chair Computer Vision',
        'blurb': 'Trained and benchmarked three YOLO architectures (YOLOv8n/m, YOLO11s) to detect chairs and their '
                 'components for automated furniture assembly checks. Diagnosed weaknesses via confusion matrices '
                 'and PR/F1 curves, then iterated on the dataset.',
        'stack': 'YOLO · Roboflow · Google Colab · Streamlit · Python',
        'cover': ('yolo_screenshot.webp', 1.55, None),
        'tilt': 0.9,
    },
    {
        'slug': 'levelestate',
        'name': 'LevelEstate',
        'blurb': 'Real-estate web and mobile platform engineered end-to-end: requirements, architecture, data model, '
                 'API contracts, web & Android apps, listings, internal chat, agent rankings and a points-based '
                 'reward system.',
        'stack': '.NET (C#) · Angular · Kotlin · SQL Server',
        'cover': ('levelestate_screenshot.webp', 0.9, '#ffffff'),
        'tilt': -1.1,
    },
]


# --------------------------------------------------------------------------- images

def cover_data(filename, scale, bg, w, h):
    """Pre-render a cover exactly like the site's thumbnail (object-fit:cover +
    scale, or contain on a solid background) and return a JPEG data URI."""
    im = Image.open(os.path.join(IMAGES, filename)).convert('RGBA')
    out = Image.new('RGB', (w, h), bg or DARK)
    if bg:  # contain
        r = min(w / im.width, h / im.height) * scale
        fit = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        out.paste(fit, ((w - fit.width) // 2, (h - fit.height) // 2), fit)
    else:  # cover, then zoom
        r = max(w / im.width, h / im.height) * scale
        fit = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        out.paste(fit, ((w - fit.width) // 2, (h - fit.height) // 2), fit)
    return jpeg_uri(out)


def jpeg_uri(im, quality=80):
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


# --------------------------------------------------------------------------- hero

def hero():
    W, H = 1000, 560
    s = Svg(W, H, 'Fábio Antunes — AI / Software Engineer. Looking for real problems to solve along the way '
                  'to my Master\'s in AI.')
    s.defs += [f_paper('paper'), f_grain('grain'), f_ink('ink', blur=2.2), f_shadow('shadow', 3, 6, 5, .28),
               f_pen('pen', scale=2.5), f_grain('tapegrain', alpha=.35, seed=7)]
    s.css.append(ANIM + delays((1, .1), (2, .35), (3, .7), (4, 1.0), (5, 1.25), (6, 1.5), (7, 1.9), (8, 2.3)))

    # the sheet of paper
    s.add(f'<polygon points="{torn_rect(18, 16, 964, 512, seed=3)}" fill="{PAPER}" filter="url(#paper)"/>')

    s.add(s.text(66, 70, 'PORTUGAL','mono', 12, tracking=.22, attrs='opacity=".85" class="fade d1"'))

    # the name, in bleeding ink
    size = 146
    s.add('<g filter="url(#ink)"><g class="rise d2">'
          + s.text(56, 222, 'Fábio', 'display', size, tracking=-.06)
          + s.text(56, 342, 'Antunes', 'display', size, tracking=-.06)
          + '</g></g>')

    # compass doodle tucked next to "Fábio"
    fw = 56 + 0 + text_width('Fábio', 'display', size, -.06)
    s.add(f'<g transform="translate({fw + 26:.0f} 104) scale(.78)"><g class="wiggle"><g class="fade d4">'
          + ''.join(f'<path d="{d}" fill="none" stroke="{ACCENT}" stroke-width="2.4" stroke-linecap="round" '
                    f'stroke-linejoin="round"/>' for d in COMPASS)
          + '</g></g></g>')

    # polaroid with the halftone portrait, scribbled on in blue pen
    portrait = Image.open(os.path.join(IMAGES, 'portrait.webp')).convert('RGB').resize((480, 480), Image.LANCZOS)
    px, py, pw = 712, 62, 236
    s.add(f'<g transform="rotate(4 {px + 125} {py + 150})" class="rise d3">'
          f'<rect x="{px}" y="{py}" width="264" height="306" fill="{CARD}" filter="url(#shadow)"/>'
          f'<clipPath id="photo"><rect x="{px + 14}" y="{py + 14}" width="{pw}" height="{pw}"/></clipPath>'
          f'<image href="{jpeg_uri(portrait, 72)}" x="{px + 14}" y="{py + 14}" width="{pw}" height="{pw}" '
          f'clip-path="url(#photo)" preserveAspectRatio="xMidYMid slice"/>'
          f'<g transform="translate({px + 14} {py + 14}) scale({pw / 100})" fill="none" stroke="{ACCENT}" '
          f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" filter="url(#pen)">'
          + ''.join(f'<path class="draw d{5 + i // 3}" pathLength="100" d="{d}"/>' for i, d in enumerate([
              'M10 72 C -6 76, -6 98, 10 100 C 28 102, 32 82, 20 74 C 16 71, 11 72, 8 76', 'M0 88 L 28 82',
              'M80 32 C 70 36, 72 54, 84 52 C 96 50, 98 34, 88 30 C 82 28, 76 32, 76 38', 'M68 46 L 98 32',
              'M14 10 C 22 6, 30 14, 24 20 C 18 26, 10 20, 14 14', 'M8 24 C 16 18, 26 16, 34 20',
              'M18 12 L 30 8']))
          + '</g>'
          + s.text(px + 132, py + 290, 'hello, world!', 'hand-md', 30, anchor='middle')
          + '</g>')
    # a strip of blue tape holding it
    tx, ty = px + 82, py - 18
    s.add(f'<g transform="rotate(-7 {tx + 50} {ty + 18})" class="fade d4">'
          f'<clipPath id="tape"><polygon points="{poly(TAPE_EDGE, tx, ty, 104, 34)}"/></clipPath>'
          f'<g clip-path="url(#tape)" opacity=".74"><rect x="{tx}" y="{ty}" width="104" height="34" fill="{ACCENT}"/>'
          f'<rect x="{tx}" y="{ty}" width="104" height="34" filter="url(#tapegrain)"/></g></g>')

    # ink rule, role, tagline
    s.add(f'<rect x="66" y="392" width="868" height="1.5" fill="{INK}" fill-opacity=".35" class="grow d4"/>')
    s.add(s.text(62, 458, 'AI / Software Engineer', 'hand-md', 50, fill=ACCENT, attrs='class="rise d5"'))
    s.add(s.text(66, 494, 'Looking for real problems to solve along the way to my Master\'s in AI.', 'body', 16,
                 attrs='opacity=".92" class="rise d6"'))

    # done / next
    rows = [('DONE', 'BSC INFORMATICS ENGINEERING, P.PORTO'),
            ('NEXT', 'MASTER\'S IN AI')]
    for i, (label, value) in enumerate(rows):
        y = 452 + i * 26
        s.add(s.text(934, y, [(label, f'fill="{ACCENT}"'), ('  —  ' + value, '')], 'mono-md', 11, tracking=.14,
                     anchor='end', attrs=f'class="fade d{6 + i // 2}"'))

    # grain over everything (inset so it never leaks past the torn edge)
    s.add('<rect x="30" y="28" width="940" height="488" filter="url(#grain)"/>')
    s.save('hero.svg')


# --------------------------------------------------------------------------- buttons

def button(name, label, tilt):
    size, tracking = 14, .14
    tw = text_width(label, 'mono-md', size, tracking)
    bw, bh = round(tw + 36 * 2 + 22), 54
    W, H = bw + 24, bh + 26
    s = Svg(W, H, label.title())
    s.defs += [f_shadow('shadow', 3, 5, 4, .32), f_grain('grain', alpha=.4, seed=7)]
    x, y = 10, 9
    s.add(f'<g transform="rotate({tilt} {W / 2} {H / 2})"><g filter="url(#shadow)">'
          f'<clipPath id="c"><polygon points="{poly(TAPE_EDGE, x, y, bw, bh)}"/></clipPath>'
          f'<g clip-path="url(#c)"><rect x="{x}" y="{y}" width="{bw}" height="{bh}" fill="{ACCENT}"/>'
          f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" filter="url(#grain)"/></g></g>'
          + s.text(x + 36, y + bh / 2 + 5, label, 'mono-md', size, fill=CREAM, tracking=tracking)
          + arrow_ne(x + 36 + tw + 12, y + bh / 2 - 6, 10)
          + '</g>')
    s.save(f'btn-{name}.svg')


# --------------------------------------------------------------------------- project cards

CARD_W = 420
PAD = 14
THUMB_H = round((CARD_W - 2 * PAD) * 3 / 4)
BLURB = ('body', 15, 1.5)
STACK = ('mono', 12, 1.55)


def card_layout(p):
    inner = CARD_W - 2 * PAD - 8
    blurb = wrap(p['blurb'], BLURB[0], BLURB[1], inner)
    stack = wrap(p['stack'], STACK[0], STACK[1], inner, .02)
    return blurb, stack


def card(p, height):
    W, H = CARD_W + 50, height + 50
    x, y = 25, 18
    s = Svg(W, H, f'{p["name"]} — {p["blurb"]}')
    s.defs += [f_shadow('shadow', 6, 10, 8, .33), f_grain('grain', alpha=.12, seed=5)]
    s.css.append(ANIM)
    edge = poly(CARD_EDGE, x, y, CARD_W, height)
    cover = cover_data(p['cover'][0], p['cover'][1], p['cover'][2], (CARD_W - 2 * PAD) * 2, THUMB_H * 2)
    blurb, stack = card_layout(p)
    bx = x + PAD + 4
    ty = y + PAD + THUMB_H + 38
    body = s.text(bx, ty, p['name'], 'semi', 21)
    body += (f'<g transform="translate({x + CARD_W - PAD - 30} {ty - 18}) scale(.95)" opacity=".65">'
             f'<path d="{GITHUB_ICON}" fill="{INK}"/></g>')
    ly = ty + 32
    for line in blurb:
        body += s.text(bx, ly, line, *BLURB[:2], attrs='opacity=".88"')
        ly += BLURB[1] * BLURB[2]
    ly += 12
    for line in stack:
        body += s.text(bx, ly, line, *STACK[:2], tracking=.02, attrs='opacity=".72"')
        ly += STACK[1] * STACK[2]
    s.add(f'<g transform="rotate({p["tilt"]} {W / 2} {H / 2})" class="rise"><g filter="url(#shadow)">'
          f'<clipPath id="edge"><polygon points="{edge}"/></clipPath>'
          f'<g clip-path="url(#edge)">'
          f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{height}" fill="{CARD}"/>'
          f'<image href="{cover}" x="{x + PAD}" y="{y + PAD}" width="{CARD_W - 2 * PAD}" height="{THUMB_H}" '
          f'preserveAspectRatio="xMidYMid slice"/>'
          f'{body}'
          f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{height}" filter="url(#grain)"/>'
          f'</g></g></g>')
    s.save(f'card-{p["slug"]}.svg')


def cards():
    heights = []
    for p in PROJECTS:
        blurb, stack = card_layout(p)
        heights.append(PAD + THUMB_H + 38 + 32 + len(blurb) * BLURB[1] * BLURB[2] + 12
                       + len(stack) * STACK[1] * STACK[2] + 12)
    height = round(max(heights))
    for p in PROJECTS:
        card(p, height)


def avow():
    """Wide 'now building' card with a chalk sketch of how Avow works."""
    W, H = 1000, 372
    x, y, cw, ch = 22, 22, 952, 318
    s = Svg(W, H, 'Avow (in progress) — a multi-agent system that answers questions about public companies from '
                  'SEC filings, with a verifier agent that checks every number against official XBRL data and '
                  'cites its source, so no figure is ever made up.')
    s.defs += [f_shadow('shadow', 6, 10, 8, .33), f_grain('grain', alpha=.12, seed=5), f_ink('ink', blur=1.4),
               f_pen('chalk', scale=2.5), f_stamp('stamp')]
    s.css.append(ANIM + delays((1, .3), (2, .6), (3, .9), (4, 1.2), (5, 1.5), (6, 1.8), (7, 2.3)))

    # left: text
    tx = x + 34
    left = s.text(tx, y + 50, 'COMING SOON', 'mono-md', 12, fill=ACCENT, tracking=.16)
    left += f'<g filter="url(#ink)">{s.text(tx - 4, y + 128, "Avow", "display", 84, tracking=-.05)}</g>'
    blurb = ('A multi-agent system that answers questions about public companies from SEC filings, with a '
             'verifier agent that checks every number against official XBRL data and cites its source, so no '
             'figure is ever made up.')
    ly = y + 170
    for line in wrap(blurb, 'body', 15.5, 396):
        left += s.text(tx, ly, line, 'body', 15.5, attrs='opacity=".88"')
        ly += 23.5
    left += s.text(tx, ly + 14, 'MULTI-AGENT · SEC FILINGS · XBRL · CITATIONS', 'mono', 11.5, tracking=.06,
                   attrs='opacity=".72"')

    # right: dark panel with a chalk sketch of the loop
    dx, dy, dw, dh = x + 470, y + 16, cw - 470 - 16, ch - 32
    chalk = f'fill="none" stroke="{CREAM}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"'
    bw, bh = 166, 76
    cols = (dx + dw * .26, dx + dw * .74)
    rows = (dy + dh * .3, dy + dh * .72)

    def node(c, r, title, sub, d):
        cx, cy = cols[c], rows[r]
        return (f'<g class="fade d{d}"><rect x="{cx - bw / 2:.1f}" y="{cy - bh / 2:.1f}" width="{bw}" height="{bh}" '
                f'rx="7" {chalk} filter="url(#chalk)"/>'
                + s.text(cx, cy - 2, title, 'hand', 28, fill=CREAM, anchor='middle')
                + s.text(cx, cy + 23, sub, 'hand-md', 18, fill=CREAM, anchor='middle', attrs='opacity=".72"')
                + '</g>')

    def arrow(x0, y0, x1, y1, d):
        import math
        a = math.atan2(y1 - y0, x1 - x0)
        h1 = (x1 - 12 * math.cos(a - .45), y1 - 12 * math.sin(a - .45))
        h2 = (x1 - 12 * math.cos(a + .45), y1 - 12 * math.sin(a + .45))
        mx, my = (x0 + x1) / 2 + (y1 - y0) * .08, (y0 + y1) / 2 - (x1 - x0) * .08
        return (f'<path class="draw d{d}" pathLength="100" d="M{x0:.1f} {y0:.1f} Q{mx:.1f} {my:.1f} {x1:.1f} '
                f'{y1:.1f} M{h1[0]:.1f} {h1[1]:.1f} L{x1:.1f} {y1:.1f} L{h2[0]:.1f} {h2[1]:.1f}" {chalk} '
                f'filter="url(#chalk)"/>')

    gap = 9
    right = f'<rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" fill="{DARK}"/>'
    right += node(0, 0, 'a question', 'about a company', 1)
    right += node(1, 0, 'agents', 'read SEC filings', 2)
    right += node(1, 1, 'verifier', 'checks vs XBRL', 3)
    right += node(0, 1, 'answer', 'every number cited', 4)
    right += arrow(cols[0] + bw / 2 + gap, rows[0], cols[1] - bw / 2 - gap, rows[0], 2)
    right += arrow(cols[1], rows[0] + bh / 2 + gap, cols[1], rows[1] - bh / 2 - gap, 3)
    right += arrow(cols[1] - bw / 2 - gap, rows[1], cols[0] + bw / 2 + gap, rows[1], 4)
    # a tick on the final answer
    tx0, ty0 = cols[0] - bw / 2 + 4, rows[1] - bh / 2 - 6
    right += (f'<path class="draw d5" pathLength="100" d="M{tx0:.1f} {ty0:.1f} l8 9 l17 -21" fill="none" '
              f'stroke="{CREAM}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" '
              f'filter="url(#chalk)"/>')

    # stamp, next to the title
    stamp_w = text_width('IN PROGRESS', 'mono-md', 15, .18) + 26
    sx, sy = tx + text_width('Avow', 'display', 84, -.05) + 34, y + 100
    stamp = (f'<g transform="rotate(-8 {sx + stamp_w / 2:.1f} {sy})"><g class="stamp d6"><g filter="url(#stamp)">'
             f'<rect x="{sx:.1f}" y="{sy - 19}" width="{stamp_w:.1f}" height="36" rx="3" fill="none" stroke="{RED}" '
             f'stroke-width="3"/>'
             + s.text(sx + 13, sy + 5, 'IN PROGRESS', 'mono-md', 15, fill=RED, tracking=.18)
             + '</g></g></g>')

    edge = torn_rect(x, y, cw, ch, step=60, depth=5, seed=8)
    s.add(f'<g transform="rotate(-.5 {W / 2} {H / 2})" class="rise"><g filter="url(#shadow)">'
          f'<clipPath id="edge"><polygon points="{edge}"/></clipPath><g clip-path="url(#edge)">'
          f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" fill="{CARD}"/>{left}{right}'
          f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" filter="url(#grain)"/></g></g>{stamp}</g>')
    s.save('card-avow.svg')


# --------------------------------------------------------------------------- footer

RIBBON = ('M -200 680 C -120 620, -50 560, -20 480 C 10 400, 100 460, 40 560 C -20 660, 180 620, 220 280 '
          'C 260 -60, 60 40, 140 380 C 220 720, 420 680, 520 540 C 620 400, 440 220, 560 140 C 680 60, 720 280, '
          '600 360 C 480 440, 640 580, 740 480 C 840 380, 720 120, 880 40 C 1040 -40, 980 260, 920 420 '
          'C 860 580, 1080 660, 1140 460 C 1200 260, 1060 200, 1120 100 C 1180 0, 1300 80, 1240 280 '
          'C 1180 480, 1340 580, 1420 420 C 1500 260, 1380 180, 1480 80 C 1580 -20, 1720 60, 1780 240')


def squash(d, sx, sy, dx, dy):
    """Scale an absolute M/C path non-uniformly while keeping the stroke round."""
    out, nums = [], []
    for tok in d.replace(',', ' ').split():
        if tok.isalpha():
            out.append(tok)
        else:
            nums.append(float(tok))
            if len(nums) == 2:
                out.append(f'{nums[0] * sx + dx:.1f} {nums[1] * sy + dy:.1f}')
                nums = []
    return ' '.join(out)


def footer():
    W, H = 1000, 210
    s = Svg(W, H, 'Thanks for scrolling — fabioportfolio.com')
    s.defs += [f_shadow('shadow', 3, 5, 4, .3), f_grain('grain', alpha=.14, seed=7)]
    s.css.append(ANIM + '.ribbon{stroke-dasharray:100;animation:draw 3.2s cubic-bezier(.65,0,.35,1) both}'
                 + delays((1, 1.2), (2, 1.6)))
    s.add(f'<path class="ribbon" pathLength="100" d="{squash(RIBBON, .5, .23, 105, 20)}" fill="none" '
          f'stroke="{ACCENT}" stroke-width="15" stroke-linecap="round" stroke-linejoin="round"/>')
    # a scrap of paper taped over the ribbon: readable on light and dark themes
    label, url = 'thanks for scrolling', 'FABIOPORTFOLIO.COM'
    uw = text_width(url, 'mono-md', 11, .22)
    bw, bh = max(text_width(label, 'hand', 36), uw + 22) + 64, 84
    bx, by = W / 2 - bw / 2, 62
    s.add(f'<g transform="rotate(-2.5 {W / 2} {by + bh / 2})" class="rise d1"><g filter="url(#shadow)">'
          f'<clipPath id="c"><polygon points="{poly(TAPE_EDGE, bx, by, bw, bh)}"/></clipPath>'
          f'<g clip-path="url(#c)"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{CARD}"/>'
          f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" filter="url(#grain)"/></g></g>'
          + s.text(W / 2, by + 42, label, 'hand', 36, anchor='middle')
          + s.text(W / 2 - 11, by + 66, url, 'mono-md', 11, fill=ACCENT, tracking=.22, anchor='middle')
          + arrow_ne(W / 2 + uw / 2 - 5, by + 57, 8, ACCENT, 1.6)
          + '</g>')
    s.save('footer.svg')


if __name__ == '__main__':
    print('building assets/')
    hero()
    for name, label, tilt in [('email', 'SEND EMAIL', -2), ('linkedin', 'LINKEDIN', 1.5), ('site', 'PORTFOLIO', -1.2)]:
        button(name, label, tilt)
    for dark in (False, True):
        heading('h-projects', 'Projects', 'SELECTED WORK · 05', dark)
    avow()
    cards()
    footer()
