#!/usr/bin/env python3
"""Generate Farhan's self-contained animated ASCII wordmark SVG."""

import argparse
import html
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TEXT = os.environ.get("WORDMARK_TEXT", "FY")
COLS = int(os.environ.get("WORDMARK_COLS", "50"))
CELL_W = 9
CELL_H = 15.5
WIDTH = 486
HEIGHT = 387
TITLE_H = 28
PAD_X = 18
RAMP = " .:-=+*#%@"


def find_font():
    override = os.environ.get("WORDMARK_FONT")
    candidates = [
        override,
        r"C:\Windows\Fonts\arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return "DejaVuSans-Bold.ttf"


def ascii_rows():
    font = ImageFont.truetype(find_font(), 260)
    probe = Image.new("L", (900, 420), 0)
    draw = ImageDraw.Draw(probe)
    box = draw.textbbox((0, 0), TEXT, font=font)
    x = (probe.width - (box[2] - box[0])) // 2 - box[0]
    y = (probe.height - (box[3] - box[1])) // 2 - box[1]
    draw.text((x, y), TEXT, fill=255, font=font, stroke_width=2)
    crop = probe.getbbox()
    mark = probe.crop(crop)
    rows = max(12, round(COLS * (mark.height / mark.width) * (CELL_W / CELL_H)))
    mark = mark.resize((COLS, rows), Image.Resampling.LANCZOS)
    result = []
    for row in range(rows):
        chars = []
        for col in range(COLS):
            value = mark.getpixel((col, row))
            index = round((value / 255) * (len(RAMP) - 1))
            chars.append(RAMP[index])
        result.append("".join(chars).rstrip())
    return result


def text_group(rows, color, dx=0, dy=0, opacity=1):
    top = TITLE_H + 52 + dy
    lines = [f'<g fill="{color}" opacity="{opacity}" transform="translate({dx} 0)">']
    for row_index, row in enumerate(rows):
        if not row.strip():
            continue
        y = top + row_index * CELL_H
        lines.append(
            f'<text x="{PAD_X}" y="{y:.1f}" font-size="{CELL_H * 0.93:.1f}" '
            f'textLength="{COLS * CELL_W}" lengthAdjust="spacing" xml:space="preserve">'
            f'{html.escape(row)}</text>'
        )
    lines.append("</g>")
    return "".join(lines)


def build_svg(mode):
    rows = ascii_rows()
    animation = "" if mode == "static" else "animation:rock 5s ease-in-out 1.6s infinite;"
    clip_width = COLS * CELL_W
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<style>@keyframes rock{0%,100%{transform:skewY(-1deg) scaleX(.98)}'
        '50%{transform:skewY(1deg) scaleX(1.02)}}'
        f'#mark{{transform-box:fill-box;transform-origin:center;{animation}}}'
        '@media(prefers-reduced-motion:reduce){#mark{animation:none}}</style>',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/>'
        '</linearGradient><clipPath id="reveal">',
        f'<rect x="{PAD_X}" y="{TITLE_H}" height="{HEIGHT - TITLE_H}" '
        f'width="{clip_width if mode == "static" else 0}">',
    ]
    if mode != "static":
        parts.append(
            f'<animate attributeName="width" from="0" to="{clip_width}" dur="1.6s" fill="freeze"/>'
        )
    parts.extend([
        '</rect></clipPath></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" rx="12" fill="url(#bg)"/>',
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" '
        'fill="none" stroke="#30363d"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{WIDTH}" y2="{TITLE_H}" stroke="#30363d"/>',
    ])
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD_X + index * 15}" cy="14" r="4.5" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2}" y="18" fill="#7d8590" font-size="11.5" text-anchor="middle">'
        'farhan@github: ~$ ./wordmark.sh --3d</text>'
    )
    parts.append('<g id="mark" clip-path="url(#reveal)">')
    parts.append(text_group(rows, "#0e4429", 12, 12, .55))
    parts.append(text_group(rows, "#1f6feb", 7, 7, .45))
    parts.append(text_group(rows, "#c9d1d9"))
    parts.append('</g></svg>')
    return "".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("rock", "static"), default="rock")
    parser.add_argument("--out", default=str(ROOT / "wordmark.svg"))
    args = parser.parse_args()
    svg = build_svg(args.mode)
    Path(args.out).write_text(svg, encoding="utf-8")
    print(f"wrote {args.out} ({len(svg)} bytes, {WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
