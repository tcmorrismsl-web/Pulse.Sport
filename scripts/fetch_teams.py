"""Fetch every team for each Pulse league from ESPN and save teams/<league>.json.

Runs in GitHub Actions (server side), because ESPN's team-list endpoint can't be
called from a web page. The app reads these files for its "Add teams" picker.
"""
import json, os, sys, time, urllib.request

LEAGUES = {
    "nfl":   ("football/nfl", ""),
    "ncaaf": ("football/college-football", "groups=80"),
    "mlb":   ("baseball/mlb", ""),
    "nba":   ("basketball/nba", ""),
    "wnba":  ("basketball/wnba", ""),
    "ncaam": ("basketball/mens-college-basketball", "groups=50"),
    "nhl":   ("hockey/nhl", ""),
    "mls":   ("soccer/usa.1", ""),
    "epl":   ("soccer/eng.1", ""),
    "ucl":   ("soccer/uefa.champions", ""),
}

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Pulse team list)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def teams_for(path, grp):
    base = f"https://site.api.espn.com/apis/site/v2/sports/{path}/teams"
    tries = ([f"{base}?{grp}&limit=1000"] if grp else []) + [f"{base}?limit=1000", base]
    for url in tries:
        try:
            j = get(url)
            raw = ((j.get("sports") or [{}])[0].get("leagues") or [{}])[0].get("teams") or []
            out = []
            for x in raw:
                t = x.get("team") or {}
                if not t.get("id"):
                    continue
                logos = t.get("logos") or []
                out.append({
                    "id": str(t["id"]),
                    "name": t.get("shortDisplayName") or t.get("displayName") or t.get("name") or "",
                    "full": t.get("displayName") or "",
                    "abbr": t.get("abbreviation") or "",
                    "logo": logos[0].get("href", "") if logos else "",
                })
            if out:
                return sorted(out, key=lambda t: t["name"].lower()), url
        except Exception as e:  # try the next query shape
            print(f"  {url}: {e}", file=sys.stderr)
    return [], None

os.makedirs("teams", exist_ok=True)
failed = []
for lg, (path, grp) in LEAGUES.items():
    teams, url = teams_for(path, grp)
    print(f"{lg}: {len(teams)} teams from {url}")
    if not teams:
        failed.append(lg)
        continue
    with open(f"teams/{lg}.json", "w") as f:
        json.dump({"league": lg, "updated": time.strftime("%Y-%m-%d"), "teams": teams}, f, separators=(",", ":"))
if len(failed) == len(LEAGUES):
    sys.exit("no team lists fetched")
