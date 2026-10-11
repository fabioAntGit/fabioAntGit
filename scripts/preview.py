"""Renders README.md through GitHub's own markdown API into preview.html
(light + dark side by side), so the layout can be checked before pushing.

    python scripts/preview.py && python -m http.server 8000
"""
import json
import os
import re
import urllib.request

from kit import ROOT

CSS = 'https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.8.1/github-markdown-{}.min.css'

with open(os.path.join(ROOT, 'README.md'), encoding='utf8') as f:
    md = f.read()
req = urllib.request.Request('https://api.github.com/markdown', method='POST',
                             data=json.dumps({'text': md, 'mode': 'markdown'}).encode(),
                             headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'preview'})
with urllib.request.urlopen(req) as r:
    html = r.read().decode()


def page(theme):
    body = html
    if theme == 'dark':  # what <picture> resolves to on GitHub's dark theme
        def to_dark(m):
            dark = re.search(r'srcset="([^"]+)"', m.group(0)).group(1)
            return re.sub(r'<img([^>]*?)src="[^"]+"', rf'<img\1src="{dark}"', m.group(0))
        body = re.sub(r'<picture>.*?</picture>', to_dark, body, flags=re.S)
    bg = '#0d1117' if theme == 'dark' else '#ffffff'
    return (f'<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="{CSS.format(theme)}">'
            f'<style>body{{margin:0;background:{bg}}}.markdown-body{{box-sizing:border-box;max-width:918px;'
            f'margin:24px auto;padding:24px;border:1px solid {"#30363d" if theme == "dark" else "#d1d9e0"};'
            f'border-radius:6px}}</style><article class="markdown-body">{body}</article>')


for theme in ('light', 'dark'):
    with open(os.path.join(ROOT, f'preview-{theme}.html'), 'w', encoding='utf8') as f:
        f.write(page(theme))
print('wrote preview-light.html and preview-dark.html')
