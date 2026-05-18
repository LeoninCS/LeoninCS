#!/usr/bin/env python3

import json
import math
import os
import re
import urllib.parse
import urllib.request
from html import escape


USERNAME = os.environ.get("GITHUB_USERNAME", "LeoninCS")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
README_PATH = "README.md"
SVG_PATH = "assets/github-stats.svg"


def request_json(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "LeoninCS-readme-stats",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def get_repositories():
    repos = []
    page = 1
    while True:
        params = urllib.parse.urlencode(
            {
                "type": "owner",
                "sort": "full_name",
                "per_page": 100,
                "page": page,
            }
        )
        batch = request_json(f"https://api.github.com/users/{USERNAME}/repos?{params}")
        if not batch:
            break

        repos.extend(repo for repo in batch if not repo.get("fork"))
        page += 1

    return repos


def search_count(endpoint, query):
    params = urllib.parse.urlencode({"q": query, "per_page": 1})
    data = request_json(f"https://api.github.com/search/{endpoint}?{params}")
    return data["total_count"]


def get_totals():
    repos = get_repositories()
    return {
        "stars": sum(repo["stargazers_count"] for repo in repos),
        "commits": search_count("commits", f"author:{USERNAME}"),
        "pull_requests": search_count("issues", f"author:{USERNAME} type:pr"),
        "issues": search_count("issues", f"author:{USERNAME} type:issue"),
        "repositories": len(repos),
    }


def format_number(value):
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M".replace(".0M", "M")
    if value >= 1_000:
        return f"{value / 1_000:.1f}k".replace(".0k", "k")
    return str(value)


def score_grade(totals):
    score = (
        min(totals["stars"] / 500, 1) * 35
        + min(totals["commits"] / 2_000, 1) * 35
        + min(totals["pull_requests"] / 100, 1) * 20
        + min(totals["repositories"] / 30, 1) * 10
    )
    if score >= 85:
        return "A+"
    if score >= 70:
        return "A"
    if score >= 55:
        return "B+"
    if score >= 40:
        return "B"
    if score >= 25:
        return "C+"
    return "C"


def grade_progress(grade):
    return {
        "A+": 0.94,
        "A": 0.86,
        "B+": 0.76,
        "B": 0.66,
        "C+": 0.52,
        "C": 0.38,
    }[grade]


def icon_path(name):
    icons = {
        "star": '<path d="M12 2.5l2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.3l-5.8 3.1 1.1-6.5-4.7-4.6 6.5-.9L12 2.5z"/>',
        "commit": '<path d="M7.4 7.4a6.5 6.5 0 1 0 9.2 0"/><path d="M12 3v5"/><path d="M9.5 5.5L12 8l2.5-2.5"/>',
        "pr": '<circle cx="6" cy="5" r="2"/><circle cx="6" cy="19" r="2"/><circle cx="18" cy="5" r="2"/><path d="M6 7v10"/><path d="M8 5h4a6 6 0 0 1 6 6v6"/>',
        "issue": '<circle cx="12" cy="12" r="9"/><path d="M12 7v6"/><circle cx="12" cy="17" r="1"/>',
        "repo": '<path d="M7 3h10a2 2 0 0 1 2 2v16l-3-2-3 2-3-2-3 2V5a2 2 0 0 1 2-2z"/><path d="M9.5 7.5h5"/>',
    }
    return icons[name]


def svg_icon(name, x, y):
    return f"""
    <svg x="{x}" y="{y}" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
      {icon_path(name)}
    </svg>"""


def render_stat(icon, label, value, y):
    return f"""
  {svg_icon(icon, 32, y - 16)}
  <text x="68" y="{y}" class="label">{escape(label)}</text>
  <text x="330" y="{y}" class="value">{escape(format_number(value))}</text>"""


def build_svg(totals):
    grade = score_grade(totals)
    progress = grade_progress(grade)
    radius = 52
    circumference = 2 * math.pi * radius
    dash = circumference * progress
    gap = circumference - dash

    stats = [
        ("star", "Total Stars Earned:", totals["stars"], 86),
        ("commit", "Total Commits:", totals["commits"], 124),
        ("pr", "Total PRs:", totals["pull_requests"], 162),
        ("issue", "Total Issues:", totals["issues"], 200),
        ("repo", "Repositories:", totals["repositories"], 238),
    ]

    stats_markup = "\n".join(render_stat(*stat) for stat in stats)

    return f"""<svg width="640" height="290" viewBox="0 0 640 290" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">{escape(USERNAME)}'s GitHub Stats</title>
  <desc id="desc">GitHub profile statistics for {escape(USERNAME)}.</desc>
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="18" flood-color="#000000" flood-opacity="0.28"/>
    </filter>
    <linearGradient id="ring" x1="468" y1="118" x2="582" y2="232" gradientUnits="userSpaceOnUse">
      <stop stop-color="#4ade80"/>
      <stop offset="1" stop-color="#f4b36b"/>
    </linearGradient>
  </defs>
  <style>
    .card {{ fill: #0d1117; }}
    .title {{ fill: #d1d5db; font: 700 24px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .label {{ fill: #9ca3af; font: 700 17px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .value {{ fill: #a1a1aa; font: 800 18px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .grade {{ fill: #d6a56d; font: 900 34px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  </style>
  <rect x="10" y="10" width="620" height="270" rx="8" class="card" filter="url(#shadow)"/>
  <text x="32" y="58" class="title">{escape(USERNAME)}'s GitHub Stats</text>
  {stats_markup}
  <circle cx="525" cy="168" r="{radius}" stroke="#30363d" stroke-width="9"/>
  <circle cx="525" cy="168" r="{radius}" stroke="url(#ring)" stroke-width="9" stroke-linecap="round" stroke-dasharray="{dash:.2f} {gap:.2f}" transform="rotate(-90 525 168)"/>
  <text x="525" y="180" text-anchor="middle" class="grade">{escape(grade)}</text>
</svg>
"""


def build_stats_block():
    return "\n".join(
        [
            "<!-- STATS:START -->",
            '<picture>',
            '  <img src="./assets/github-stats.svg" alt="LeoninCS GitHub stats" />',
            '</picture>',
            "<!-- STATS:END -->",
        ]
    )


def write_svg(svg):
    os.makedirs(os.path.dirname(SVG_PATH), exist_ok=True)
    with open(SVG_PATH, "w", encoding="utf-8") as file:
        file.write(svg)


def update_readme():
    with open(README_PATH, "r", encoding="utf-8") as file:
        readme = file.read()

    updated = re.sub(
        r"<!-- STATS:START -->.*?<!-- STATS:END -->",
        build_stats_block(),
        readme,
        flags=re.DOTALL,
    )
    if updated == readme:
        raise RuntimeError("Stats markers were not found in README.md.")

    with open(README_PATH, "w", encoding="utf-8") as file:
        file.write(updated)


def main():
    totals = get_totals()
    write_svg(build_svg(totals))
    update_readme()


if __name__ == "__main__":
    main()
