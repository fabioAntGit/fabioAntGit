"""Regenerates the open-source section of the README: a folder of tabs, one per
upstream repo where USER has merged pull requests. The card cycles through the
tabs on its own (READMEs can't run JS, so the tabs can't be clicked), showing
merged PRs, commits, issues opened, files and lines for each repo.
Runs daily in .github/workflows/open-source.yml.

    python scripts/oss.py
"""
import base64
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime

from kit import (ACCENT, ANIM, CARD, INK, RED, ROOT, Svg, clamp_lines, f_grain, f_ink, f_shadow, f_stamp, heading,
                 star, text_width, torn_rect, wrap)

USER = 'fabioAntGit'
README = os.path.join(ROOT, 'README.md')
START, END = '<!-- OSS:START -->', '<!-- OSS:END -->'
MAX_TABS = 5
SLIDE = 5  # seconds each tab stays up


def get(url, raw=False):
    req = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json', 'User-Agent': USER})
    token = os.environ.get('GITHUB_TOKEN')
    if token and url.startswith('https://api.github.com'):
        req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=30) as r:
        return (r.read(), r.headers.get('Content-Type')) if raw else json.load(r)


def search(q):
    return get('https://api.github.com/search/issues?per_page=100&q=' + urllib.parse.quote(q))


def fetch():
    """Repos with at least one merged PR by USER, with per-repo totals."""
    repos = {}
    for it in search(f'author:{USER} type:pr is:merged -user:{USER}')['items']:
        full = it['repository_url'].split('/repos/', 1)[1]
        pr = get(f'https://api.github.com/repos/{full}/pulls/{it["number"]}')
        repos.setdefault(full, []).append({
            'number': it['number'],
            'title': it['title'],
            'merged_at': pr['merged_at'],
            'commits': pr.get('commits', 0),
        })
    out = []
    for full, prs in repos.items():
        meta = get(f'https://api.github.com/repos/{full}')
        avatar, ctype = get(meta['owner']['avatar_url'] + '&s=64', raw=True)
        prs.sort(key=lambda p: p['merged_at'], reverse=True)
        out.append({
            'full': full,
            'owner': meta['owner']['login'],
            'name': meta['name'],
            'stars': meta['stargazers_count'],
            'description': meta.get('description') or '',
            'avatar': f'data:{ctype or "image/png"};base64,' + base64.b64encode(avatar).decode(),
            'issues': search(f'repo:{full} author:{USER} type:issue')['total_count'],
            'prs': prs,
            'merged': len(prs),
            'commits': sum(p['commits'] for p in prs),
            'since': min(p['merged_at'] for p in prs),
        })
    out.sort(key=lambda r: (-r['merged'], -r['stars']))
    return out


def fmt_num(n):
    return f'{n / 1000:.1f}k' if n >= 10000 else f'{n:,}'


def fmt_month(iso):
    return datetime.strptime(iso[:10], '%Y-%m-%d').strftime('%b %Y').upper()


# --------------------------------------------------------------------------- the card

W = 1000
TAB_Y, TAB_H = 14, 46
PX, PY, PW, PH = 22, TAB_Y + TAB_H - 4, 956, 338
H = PY + PH + 34


def tab_shape(x, w, y=TAB_Y, h=TAB_H + 6):
    return (f'M{x:.1f} {y + h} L{x + 7:.1f} {y + 8} Q{x + 9:.1f} {y} {x + 18:.1f} {y} L{x + w - 18:.1f} {y} '
            f'Q{x + w - 9:.1f} {y} {x + w - 7:.1f} {y + 8} L{x + w:.1f} {y + h} Z')


def panel(s, r):
    """Everything inside the folder for one repo."""
    x0, x1 = PX + 40, PX + PW - 40
    g = s.text(x0, PY + 46, r['owner'].upper() + ' /', 'mono', 12, tracking=.16, attrs='opacity=".7"')
    g += f'<g filter="url(#ink)">{s.text(x0 - 3, PY + 104, r["name"], "display", 62, tracking=-.04)}</g>'
    stars = f'{fmt_num(r["stars"])} STARS'
    sw = text_width(stars, 'mono-md', 12, .1)
    g += star(x1 - sw - 14, PY + 41, 7.5, INK)
    g += s.text(x1, PY + 46, stars, 'mono-md', 12, tracking=.1, anchor='end')
    desc = clamp_lines(wrap(r['description'], 'body', 14.5, 560), 1, 'body', 14.5, 560)
    if desc:
        g += s.text(x0, PY + 136, desc[0], 'body', 14.5, attrs='opacity=".72"')

    # merged stamp
    label = 'MERGED'
    stw = text_width(label, 'mono-md', 17, .2) + 30
    sx, sy = x1 - stw - 10, PY + 100
    g += (f'<g transform="rotate(-7 {sx + stw / 2:.1f} {sy})"><g filter="url(#stamp)">'
          f'<rect x="{sx:.1f}" y="{sy - 21}" width="{stw:.1f}" height="40" rx="3" fill="none" stroke="{RED}" '
          f'stroke-width="3"/>' + s.text(sx + 15, sy + 6, label, 'mono-md', 17, fill=RED, tracking=.2) + '</g></g>')

    g += (f'<line x1="{x0}" y1="{PY + 160}" x2="{x1}" y2="{PY + 160}" stroke="{INK}" stroke-opacity=".28" '
          f'stroke-dasharray="3 6" stroke-linecap="round"/>')

    # the numbers
    stats = [(r['merged'], 'PRS MERGED'), (r['commits'], 'COMMITS'), (r['issues'], 'ISSUES OPENED')]
    col = (x1 - x0) / len(stats)
    nums = ''
    for i, (n, lab) in enumerate(stats):
        cx = x0 + i * col
        nums += s.text(cx - 2, PY + 234, fmt_num(n), 'display', 64, tracking=-.03)
        g += s.text(cx, PY + 258, lab, 'mono', 11, tracking=.16, attrs='opacity=".7"')
    g += f'<g filter="url(#ink)">{nums}</g>'

    # footer line: first merge and the latest PR
    by = PY + 300
    g += s.text(x0, by + 5, [('FIRST MERGE', f'fill="{ACCENT}"'), (f'  ·  {fmt_month(r["since"])}', '')], 'mono-md',
                12, tracking=.14)
    latest = r['prs'][0]
    note = clamp_lines([f'latest: {latest["title"]} #{latest["number"]}'], 1, 'hand-md', 24, 520)[0]
    g += s.text(x1, by + 7, note, 'hand-md', 24, fill=ACCENT, anchor='end')
    return g


def card(repos):
    repos = repos[:MAX_TABS]
    n = len(repos)
    alt = 'Open-source contributions. ' + ' '.join(
        f'{r["full"]}: {r["merged"]} merged PR{"s" if r["merged"] != 1 else ""}, {r["commits"]} commits, '
        f'{r["issues"]} issues opened.'
        for r in repos)
    s = Svg(W, H, alt)
    s.defs += [f_shadow('shadow', 5, 9, 8, .3), f_grain('grain', alpha=.12, seed=5), f_ink('ink', blur=1.6),
               f_stamp('stamp'), '<filter id="mono"><feColorMatrix type="saturate" values="0"/></filter>']

    period = SLIDE * n
    on = 100 / n
    s.css.append(ANIM)
    if n > 1:
        s.css.append(
            f'@keyframes slide{{0%{{opacity:0;transform:translateY(8px)}}2%{{opacity:1;transform:none}}'
            f'{on - 2:.2f}%{{opacity:1;transform:none}}{on:.2f}%{{opacity:0}}100%{{opacity:0}}}}'
            f'@keyframes tab{{0%,{on - 1:.2f}%{{opacity:1}}{on:.2f}%,100%{{opacity:0}}}}'
            f'@keyframes progress{{0%{{transform:scaleX(0)}}{on:.2f}%,100%{{transform:scaleX(1)}}}}'
            f'.slide,.tab,.progress{{animation-duration:{period}s;animation-iteration-count:infinite;'
            f'animation-timing-function:linear}}'
            f'.slide{{animation-name:slide}}.tab{{animation-name:tab}}'
            f'.progress{{animation-name:progress;transform-box:fill-box;transform-origin:left center}}'
            + ''.join(f'.i{i}{{animation-delay:{(i * SLIDE - period) if i else 0}s}}' for i in range(n))
            # without motion only the first tab shows
            + ''.join(f'.i{i}.slide,.i{i}.tab{{opacity:0}}' for i in range(1, n)))

    # tabs, sized to their labels
    tabs, x = [], PX + 18
    for r in repos:
        label = r['full']
        w = 22 + 26 + text_width(label, 'mono-md', 12.5, .04) + 24
        if x + w > PX + PW - 10:
            label = r['name']
            w = 22 + 26 + text_width(label, 'mono-md', 12.5, .04) + 24
        tabs.append((x, w, label))
        x += w - 4

    base = ''
    for (tx, tw, _), r in zip(tabs, repos):
        base += f'<path d="{tab_shape(tx, tw)}" fill="#e4dfd5"/>'
    edge = torn_rect(PX, PY, PW, PH, step=60, depth=4, seed=21)
    base += f'<polygon points="{edge}" fill="{CARD}"/>'
    s.add(f'<g filter="url(#shadow)" class="rise">{base}</g>')

    def tab_label(tx, tw, label, r, active):
        op = '' if active else ' opacity=".55"'
        return (f'<g{op}><clipPath id="av{tx:.0f}{int(active)}"><rect x="{tx + 22}" y="{TAB_Y + 12}" width="22" '
                f'height="22" rx="4"/></clipPath><image href="{r["avatar"]}" x="{tx + 22}" y="{TAB_Y + 12}" '
                f'width="22" height="22" clip-path="url(#av{tx:.0f}{int(active)})" filter="url(#mono)"/>'
                + s.text(tx + 52, TAB_Y + 28, label, 'mono-md', 12.5, tracking=.04) + '</g>')

    for i, ((tx, tw, label), r) in enumerate(zip(tabs, repos)):
        s.add(tab_label(tx, tw, label, r, False))
        # the active tab's top edge fills up while its panel is showing
        bar = f'x="{tx + 16:.1f}" y="{TAB_Y + 1}" width="{tw - 32:.1f}" height="3" rx="1.5" fill="{ACCENT}"'
        progress = f'<rect class="progress i{i}" {bar}/>' if n > 1 else f'<rect {bar}/>'
        cls = f' class="tab i{i}"' if n > 1 else ''
        s.add(f'<g{cls}><path d="{tab_shape(tx, tw, h=TAB_H + 8)}" fill="{CARD}"/>'
              f'{tab_label(tx, tw, label, r, True)}{progress}</g>')

    for i, r in enumerate(repos):
        cls = f' class="slide i{i}"' if n > 1 else ''
        s.add(f'<g{cls}>{panel(s, r)}</g>')

    # grain only where there is paper
    s.add('<clipPath id="paper">' + ''.join(f'<path d="{tab_shape(tx + 4, tw - 8, y=TAB_Y + 3)}"/>' for tx, tw, _ in tabs)
          + f'<rect x="{PX + 6}" y="{PY + 4}" width="{PW - 12}" height="{PH - 10}"/></clipPath>')
    s.add(f'<rect x="{PX}" y="{TAB_Y}" width="{PW}" height="{PY + PH - TAB_Y}" filter="url(#grain)" '
          f'clip-path="url(#paper)"/>')
    s.save('oss.svg')
    return alt


def main():
    repos = fetch()
    print('building assets/')
    merged = sum(r['merged'] for r in repos)
    commits = sum(r['commits'] for r in repos)
    hint = (f'{merged} PR{"S" if merged != 1 else ""} MERGED · {commits} COMMITS · '
            f'{len(repos)} REPO{"S" if len(repos) != 1 else ""}')
    for dark in (False, True):
        heading('h-oss', 'Open Source Contributions', hint, dark)

    if repos:
        alt = card(repos)
        href = (f'https://github.com/{repos[0]["full"]}/pulls?q=is%3Apr+is%3Amerged+author%3A{USER}'
                if len(repos) == 1 else
                f'https://github.com/search?q=author%3A{USER}+is%3Apr+is%3Amerged+-user%3A{USER}&type=pullrequests')
        body = f'<a href="{href}"><img src="assets/oss.svg" width="100%" alt="{alt}"></a>'
    else:
        body = '<sub>first merged pull requests on the way</sub>'
    with open(README, encoding='utf8') as f:
        readme = f.read()
    readme = re.sub(re.escape(START) + '.*?' + re.escape(END), lambda _: f'{START}\n{body}\n{END}', readme,
                    flags=re.S)
    with open(README, 'w', encoding='utf8', newline='\n') as f:
        f.write(readme)
    print(f'README: {len(repos)} repos, {merged} merged pull requests')


if __name__ == '__main__':
    main()
