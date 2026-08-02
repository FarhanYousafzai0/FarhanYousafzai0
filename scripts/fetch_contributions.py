#!/usr/bin/env python3
"""Fetch a public GitHub contribution calendar and calculate profile stats."""

import datetime as dt
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
USERNAME = os.environ.get("GH_PROFILE_USER", "FarhanYousafzai0")


def read_calendar():
    url = f"https://github.com/users/{USERNAME}/contributions"
    response = requests.get(url, headers={"User-Agent": "animated-profile-readme"}, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        tooltip = soup.find("tool-tip", attrs={"for": cell.get("id")})
        label = tooltip.get_text(" ", strip=True) if tooltip else ""
        match = re.match(r"([\d,]+) contribution", label, flags=re.I)
        count = int(match.group(1).replace(",", "")) if match else 0
        days.append({"date": cell["data-date"], "count": count})
    days.sort(key=lambda item: item["date"])
    if not days:
        raise RuntimeError("GitHub returned no contribution cells")
    return days


def streaks(days):
    current = 0
    index = len(days) - 1
    if days[index]["count"] == 0:
        index -= 1
    while index >= 0 and days[index]["count"] > 0:
        current += 1
        index -= 1

    longest = run = 0
    for day in days:
        run = run + 1 if day["count"] else 0
        longest = max(longest, run)
    return current, longest


def build_payload(days):
    current, longest = streaks(days)
    best = max(days, key=lambda item: item["count"])
    active = sum(day["count"] > 0 for day in days)
    return {
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": sum(day["count"] for day in days),
        "active_days": active,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best,
        "days": days,
    }


def main():
    payload = build_payload(read_calendar())
    output = ROOT / "data" / "contributions.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {output}: {payload['total_contributions']} contributions, "
        f"current streak {payload['current_streak']}, longest streak {payload['longest_streak']}"
    )


if __name__ == "__main__":
    main()
