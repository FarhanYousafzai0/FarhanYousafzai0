#!/usr/bin/env python3
"""Convert the prepared portrait into a row-by-row animated ASCII SVG."""

import html
import os
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "source-prepped.png"
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "farhan-ascii.svg"
STATIC = bool(os.environ.get("STATIC"))

COLS, ROWS = 100, 53
CELL_W, CELL_H = 8, 15
PAD, TITLE_H, STATUS_H = 20, 30, 30
WIDTH = COLS * CELL_W + PAD * 2
HEIGHT = TITLE_H + ROWS * CELL_H + STATUS_H + PAD
RAMP = " .`:-=+*cs#%@"


def sample_rows():
    image = Image.open(SOURCE).convert("L")
    image = image.filter(ImageFilter.UnsharpMask(radius=1.5, percent=110, threshold=3))
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = image.resize((COLS, ROWS), Image.Resampling.LANCZOS)
    rows = []
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            light = (image.getpixel((x, y)) / 255) ** 1.18
            if light >= .80:
                chars.append(" ")
            else:
                index = round((1 - light) * (len(RAMP) - 1))
                chars.append(RAMP[max(0, min(index, len(RAMP) - 1))])
        rows.append("".join(chars))
    return rows


def build_svg():
    art_width = COLS * CELL_W
    art_height = ROWS * CELL_H
    top = TITLE_H + PAD * .35
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/>'
        '</linearGradient></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="12" fill="url(#bg)"/>',
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" '
        'fill="none" stroke="#30363d"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{WIDTH}" y2="{TITLE_H}" stroke="#30363d"/>',
    ]
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + index * 16}" cy="15" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">'
        'farhan@github: ~$ ./portrait.sh</text>'
    )

    for row_index, row in enumerate(sample_rows()):
        y = top + row_index * CELL_H + CELL_H * .74
        row_y = top + row_index * CELL_H
        delay = row_index * .11
        rendered = (
            f'<text x="{PAD}" y="{y:.1f}" fill="#c9d1d9" font-size="{CELL_H * .86:.1f}" '
            f'textLength="{art_width}" lengthAdjust="spacing" xml:space="preserve">'
            f'{html.escape(row)}</text>'
        )
        if STATIC:
            parts.append(rendered)
            continue
        parts.append(
            f'<clipPath id="row{row_index}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
            f'<animate attributeName="width" from="0" to="{art_width}" begin="{delay:.2f}s" '
            'dur=".11s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(f'<g clip-path="url(#row{row_index})">{rendered}</g>')
        parts.append(
            f'<rect y="{row_y + 1:.1f}" width="{CELL_W}" height="{CELL_H - 2}" fill="#c9d1d9" opacity="0">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD + art_width}" begin="{delay:.2f}s" '
            'dur=".11s" fill="freeze"/>'
            f'<set attributeName="opacity" to=".85" begin="{delay:.2f}s"/>'
            f'<set attributeName="opacity" to="0" begin="{delay + .11:.2f}s"/></rect>'
        )

    line_y = TITLE_H + art_height + PAD * .35
    status_y = line_y + 19
    parts.extend([
        f'<line x1="0" y1="{line_y:.1f}" x2="{WIDTH}" y2="{line_y:.1f}" stroke="#30363d"/>',
        f'<text x="{PAD}" y="{status_y:.1f}" fill="#7d8590" font-size="13">'
        'farhan@github:~$ whoami <tspan fill="#c9d1d9">Muhammad Farhan</tspan></text>',
        f'<rect x="{PAD + 338}" y="{status_y - 12:.1f}" width="8" height="14" fill="#c9d1d9">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.51;1" '
        'dur="1s" repeatCount="indefinite"/></rect>',
        '</svg>',
    ])
    return "".join(parts)


OUTPUT.write_text(build_svg(), encoding="utf-8")
print(f"wrote {OUTPUT} ({WIDTH}x{HEIGHT})")
