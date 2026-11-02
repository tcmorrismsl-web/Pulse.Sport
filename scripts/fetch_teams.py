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

# College lists are limited to one division: FBS for football (ESPN group 80),
# Division I for men's basketball (group 50). ESPN publishes group membership per season.
DIVISION = {
    "ncaaf": ("football", "college-football", 80, (115, 150)),
    "ncaam": ("basketball", "mens-college-basketball", 50, (330, 380)),
}

def division_ids(lg):
    sport, league, group, (lo, hi) = DIVISION[lg]
    y = time.gmtime().tm_year
    # Basketball seasons are named for the year they end (2026-27 is "2027").
    years = [y + 1, y] if sport == "basketball" else [y, y - 1]
    for season in years:
        for kind in (2, 3):
            url = (f"https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}"
                   f"/seasons/{season}/types/{kind}/groups/{group}/teams?limit=1000")
            try:
                j = get(url)
                ids = set()
                for item in j.get("items") or []:
                    ref = item.get("$ref", "")
                    part = ref.split("/teams/")[-1].split("?")[0].strip("/")
                    if part.isdigit():
                        ids.add(part)
                print(f"  {lg} division list {season}/{kind}: {len(ids)} teams")
                if lo <= len(ids) <= hi:
                    return ids
            except Exception as e:
                print(f"  {url}: {e}", file=sys.stderr)
    return None

os.makedirs("teams", exist_ok=True)
failed = []
for lg, (path, grp) in LEAGUES.items():
    teams, url = teams_for(path, grp)
    if lg in DIVISION and teams:
        keep = division_ids(lg)
        lo, hi = DIVISION[lg][3]
        if keep:
            teams = [t for t in teams if t["id"] in keep]
        elif not (lo <= len(teams) <= hi):
            # Couldn't confirm the division and the list is clearly mixed: keep last week's file.
            print(f"{lg}: division filter unavailable, keeping the previous list", file=sys.stderr)
            continue
    print(f"{lg}: {len(teams)} teams from {url}")
    if not teams:
        failed.append(lg)
        continue
    with open(f"teams/{lg}.json", "w") as f:
        json.dump({"league": lg, "updated": time.strftime("%Y-%m-%d"), "teams": teams}, f, separators=(",", ":"))
if len(failed) == len(LEAGUES):
    sys.exit("no team lists fetched")
