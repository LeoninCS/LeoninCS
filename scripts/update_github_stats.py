#!/usr/bin/env python3

import json
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
    <svg x="{x}" y="{y}" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      {icon_path(name)}
    </svg>"""


def render_row(icon, label, value, scope, y, shaded):
    fill = "#111820" if shaded else "#0d1117"
    return f"""
  <rect x="30" y="{y}" width="580" height="43" rx="7" fill="{fill}"/>
  {svg_icon(icon, 46, y + 10)}
  <text x="82" y="{y + 27}" class="metric">{escape(label)}</text>
  <text x="430" y="{y + 27}" class="value">{escape(format_number(value))}</text>
  <text x="535" y="{y + 27}" class="scope" text-anchor="middle">{escape(scope)}</text>"""


def build_svg(totals):
    stats = [
        ("star", "Total Stars Earned", totals["stars"], "Owned repos"),
        ("commit", "Total Commits", totals["commits"], "Public"),
        ("pr", "Total Pull Requests", totals["pull_requests"], "Authored"),
        ("issue", "Total Issues", totals["issues"], "Authored"),
        ("repo", "Repositories", totals["repositories"], "Owned"),
    ]

    rows_markup = "\n".join(
        render_row(*stat, y=102 + index * 48, shaded=index % 2 == 0)
        for index, stat in enumerate(stats)
    )

    return f"""<svg width="640" height="380" viewBox="0 0 640 380" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">{escape(USERNAME)}'s GitHub Stats</title>
  <desc id="desc">GitHub profile statistics for {escape(USERNAME)}.</desc>
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="18" flood-color="#000000" flood-opacity="0.28"/>
    </filter>
    <linearGradient id="accent" x1="30" y1="28" x2="610" y2="28" gradientUnits="userSpaceOnUse">
      <stop stop-color="#4ade80"/>
      <stop offset="0.52" stop-color="#22d3ee"/>
      <stop offset="1" stop-color="#f4b36b"/>
    </linearGradient>
  </defs>
  <style>
    .card {{ fill: #0d1117; }}
    .title {{ fill: #f3f4f6; font: 800 25px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .subtitle {{ fill: #7d8590; font: 600 13px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .head {{ fill: #7d8590; font: 800 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; letter-spacing: 0.8px; }}
    .metric {{ fill: #c9d1d9; font: 750 16px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .value {{ fill: #e5e7eb; font: 850 18px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .scope {{ fill: #8b949e; font: 700 12px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  </style>
  <rect x="10" y="10" width="620" height="360" rx="10" class="card" filter="url(#shadow)"/>
  <rect x="30" y="28" width="580" height="4" rx="2" fill="url(#accent)"/>
  <text x="32" y="63" class="title">{escape(USERNAME)}'s GitHub Stats</text>
  <text x="32" y="84" class="subtitle">Lifetime public activity snapshot</text>
  <text x="82" y="100" class="head">METRIC</text>
  <text x="430" y="100" class="head">TOTAL</text>
  <text x="535" y="100" class="head" text-anchor="middle">SCOPE</text>
  {rows_markup}
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

    pattern = r"<!-- STATS:START -->.*?<!-- STATS:END -->"
    if re.search(pattern, readme, flags=re.DOTALL) is None:
        raise RuntimeError("Stats markers were not found in README.md.")

    updated = re.sub(
        pattern,
        build_stats_block(),
        readme,
        flags=re.DOTALL,
    )

    with open(README_PATH, "w", encoding="utf-8") as file:
        file.write(updated)


def main():
    totals = get_totals()
    write_svg(build_svg(totals))
    update_readme()


if __name__ == "__main__":
    main()
