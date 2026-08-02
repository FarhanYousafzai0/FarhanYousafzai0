#!/usr/bin/env python3
"""Render contribution JSON as a terminal-themed animated heatmap SVG."""

import datetime as dt
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "contrib-heatmap.svg"
COLORS = ("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0")
CELL, GAP, STEP = 12, 3, 15
PAD, LABEL_W, TITLE_H, MONTH_H = 22, 30, 30, 20


def intensity(count):
    for level, ceiling in enumerate((0, 5, 15, 30, 50)):
        if count <= ceiling:
            return level
    return 5


def make_columns(days):
    columns = []
    column = [None] * ((dt.date.fromisoformat(days[0]["date"]).weekday() + 1) % 7)
    for day in days:
        column.append(day)
        if len(column) == 7:
            columns.append(column)
            column = []
    if column:
        columns.append(column + [None] * (7 - len(column)))
    return columns


def render(data):
    columns = make_columns(data["days"])
    grid_width = len(columns) * STEP
    grid_height = 7 * STEP
    width = PAD + LABEL_W + grid_width + PAD
    height = TITLE_H + MONTH_H + grid_height + 110
    grid_x, grid_y = PAD + LABEL_W, TITLE_H + MONTH_H
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        '<style>@keyframes enter{from{opacity:0;transform:translateY(-6px)}'
        'to{opacity:1;transform:translateY(0)}}.day{opacity:0;animation:enter .42s ease-out both}'
        '@media(prefers-reduced-motion:reduce){.day{opacity:1;animation:none}}</style>',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#0d1420"/><stop offset="1" stop-color="#0a0e14"/>'
        '</linearGradient></defs>',
        f'<rect width="{width}" height="{height}" rx="12" fill="url(#bg)"/>',
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" '
        'fill="none" stroke="#1f6feb" stroke-opacity=".55"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{width}" y2="{TITLE_H}" stroke="#1f6feb" stroke-opacity=".35"/>',
    ]
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        parts.append(f'<circle cx="{PAD + index * 16}" cy="15" r="5" fill="{color}"/>')
    parts.append(
        f'<text x="{width / 2}" y="19" fill="#7d8590" font-size="12" text-anchor="middle">'
        'farhan@github: ~/contributions --graph</text>'
    )

    seen_months = set()
    for column_index, column in enumerate(columns):
        real_days = [day for day in column if day]
        if real_days:
            date = dt.date.fromisoformat(real_days[0]["date"])
            key = (date.year, date.month)
            if date.day <= 7 and key not in seen_months:
                seen_months.add(key)
                parts.append(
                    f'<text x="{grid_x + column_index * STEP}" y="44" fill="#7d8590" '
                    f'font-size="10">{date.strftime("%b")}</text>'
                )
        for row_index, day in enumerate(column):
            if not day:
                continue
            x, y = grid_x + column_index * STEP, grid_y + row_index * STEP
            delay = column_index * .018 + row_index * .045
            count = day["count"]
            label = html.escape(f"{day['date']}: {count} contribution{'s' if count != 1 else ''}")
            parts.append(
                f'<rect class="day" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{COLORS[intensity(count)]}" style="animation-delay:{delay:.3f}s">'
                f'<title>{label}</title></rect>'
            )

    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        parts.append(
            f'<text x="{PAD}" y="{grid_y + row * STEP + 9}" fill="#7d8590" font-size="9">{label}</text>'
        )

    divider = grid_y + grid_height + 34
    parts.append(f'<line x1="0" y1="{divider}" x2="{width}" y2="{divider}" stroke="#1f6feb" stroke-opacity=".25"/>')
    stats_y = divider + 26
    parts.append(
        f'<text x="{PAD}" y="{stats_y}" font-size="13" fill="#39d353" font-weight="700">'
        f'{data["total_contributions"]:,}<tspan fill="#7d8590" font-weight="400"> contributions in the last year</tspan></text>'
    )
    parts.append(
        f'<text x="{width - PAD}" y="{stats_y}" font-size="12" fill="#7d8590" text-anchor="end">'
        f'{data["range"]["start"]} → {data["range"]["end"]}</text>'
    )
    parts.append(
        f'<text x="{PAD}" y="{stats_y + 25}" font-size="13" fill="#7d8590">current streak '
        f'<tspan fill="#22d3ee" font-weight="700">{data["current_streak"]} days</tspan> · longest '
        f'<tspan fill="#22d3ee" font-weight="700">{data["longest_streak"]} days</tspan></text>'
    )
    parts.append(
        f'<text x="{width - PAD}" y="{stats_y + 25}" font-size="12" fill="#7d8590" text-anchor="end">best day '
        f'<tspan fill="#f2cc60" font-weight="700">{data["best_day"]["count"]}</tspan> on '
        f'{data["best_day"]["date"]}</text></svg>'
    )
    return "".join(parts)


payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
svg = render(payload)
OUTPUT.write_text(svg, encoding="utf-8")
print(f"wrote {OUTPUT} ({len(svg)} bytes)")
