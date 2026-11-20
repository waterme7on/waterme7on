#!/usr/bin/env python3
"""Generate a minimal monochrome GitHub stats strip (light + dark SVGs).

Data comes from the GitHub GraphQL API. No third-party services are involved.
"""

import json
import os
import urllib.request

LOGIN = os.environ.get("PROFILE_LOGIN", "waterme7on")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
OUT_DIR = os.environ.get(
    "OUT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "profile"),
)

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
    }
    repositories(first: 100, ownerAffiliations: [OWNER], isFork: false, privacy: PUBLIC) {
      totalCount
      nodes { stargazerCount }
    }
  }
}
"""


def fetch():
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN (or GH_TOKEN) is required")
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-stats",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise SystemExit(payload["errors"])
    user = payload["data"]["user"]
    return {
        "stars": sum(node["stargazerCount"] for node in user["repositories"]["nodes"]),
        "commits": user["contributionsCollection"]["totalCommitContributions"],
        "prs": user["contributionsCollection"]["totalPullRequestContributions"],
        "repos": user["repositories"]["totalCount"],
    }


def render(stats, dark):
    if dark:
        value, label, rule, foot = "#e6edf3", "#8b949e", "#30363d", "#6e7681"
    else:
        value, label, rule, foot = "#1f2328", "#6f7780", "#d0d7de", "#8b949e"

    cells = [
        (f"{stats['stars']:,}", "STARS"),
        (f"{stats['commits']:,}", "COMMITS"),
        (f"{stats['prs']:,}", "PULL REQUESTS"),
        (f"{stats['repos']:,}", "REPOSITORIES"),
    ]
    width, column = 720, 180
    centers = [column * i + column / 2 for i in range(4)]
    dividers = [column * i for i in (1, 2, 3)]
    aria = (
        f"GitHub stats: {stats['stars']} stars, {stats['commits']} commits, "
        f"{stats['prs']} pull requests, {stats['repos']} repositories"
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="124" '
        f'viewBox="0 0 {width} 124" role="img" aria-label="{aria}">',
        '<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    ]
    for x in dividers:
        parts.append(f'<line x1="{x}" y1="20" x2="{x}" y2="84" stroke="{rule}" stroke-width="1"/>')
    for (val, lab), cx in zip(cells, centers):
        parts.append(
            f'<text x="{cx}" y="54" text-anchor="middle" font-size="34" fill="{value}">{val}</text>'
        )
        parts.append(
            f'<text x="{cx}" y="78" text-anchor="middle" font-size="11" '
            f'letter-spacing="2.5" fill="{label}">{lab}</text>'
        )
    parts.append(
        f'<text x="20" y="112" font-size="11" fill="{foot}">commits &amp; pull requests: last 365 days</text>'
    )
    parts.append("</g></svg>\n")
    return "".join(parts)


def main():
    stats = fetch()
    os.makedirs(OUT_DIR, exist_ok=True)
    for dark, name in ((False, "stats-light.svg"), (True, "stats-dark.svg")):
        with open(os.path.join(OUT_DIR, name), "w", encoding="utf-8") as handle:
            handle.write(render(stats, dark))
    print("stats:", stats)


if __name__ == "__main__":
    main()
