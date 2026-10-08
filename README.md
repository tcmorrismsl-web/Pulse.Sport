# Pulse.Sport

Pulse rates every game across 14 leagues on a 0–100 excitement scale. It answers one question: is this game fun to watch right now?

The whole app is one file, `index.html`. It pulls live scoreboards from ESPN's public scoreboard feed when the page loads and refreshes them while it's open. There's no build step, server or API key.

## Leagues

NFL, NCAAF, MLB, NBA, WNBA, NCAAM, NHL, MLS, Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League.

## Hosting on GitHub Pages

1. Push this repo to GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, set Source to **Deploy from a branch**. Pick `main` and `/ (root)`, then click Save.
4. After a minute or two, the site is at `https://<your-username>.github.io/Pulse.Sport/`.

On an iPhone, open that link in Safari, tap Share, then **Add to Home Screen** to get an app-style icon.

The empty `.nojekyll` file tells GitHub Pages to serve the files as they are.

## How the excitement number works

- **Core:** how close the score is, compared with a normal margin in that sport, multiplied by how late in the game it is.
- **Scoring pace:** the core is then scaled by how much scoring there has been against the league's norm. A 0–0 match lands in the 40s; a 3–3 match lands in the 90s.
- **Boosts:**
  - Comebacks: how far the margin has moved over the last 15% of the game.
  - Lead changes, which fade over the next few minutes.
  - Upsets, weighted by the betting line, or by ranking gap when there's no line.
  - Overtime, and crunch time in a one-score game.
  - Stakes, which come from the hype score.
  - Right now: the live situation. Baseball uses runners, outs, the count and whether the tying or winning run is on base or at the plate. Football uses red zone, 4th down and the two-minute drill when the team with the ball is within one score. Soccer uses red cards.
  - Fresh scores: a score jolts the number, more for a go-ahead or tying score, then fades over about five minutes.
- **Hype anchor:** every game starts at its pregame hype score, built from rankings, rivalry and how close the line is. Over the first third of the game, live play takes over from that number.
- **Zones:**
  - 0–40, blue: quiet
  - 40–60, green: competitive
  - 60–80, orange: heating up
  - 80–100, red: must-watch

  Scores above 70 are compressed, so anything over 90 is rare.

## Where to tune it

All of these are in the `<script>` section of `index.html`:

- `LEAGUES`: the settings for each league:
  - `tm`: a normal final margin
  - `pace`: typical combined score
  - `one`: what counts as a one-score game
  - period lengths
- `RIVALS`: rivalry pairs, listed by ESPN team abbreviation.
- `hypeScore()`: the pregame hype formula.
- `rate()`: the live excitement formula and its boosts.
- `moment()`: the live-situation boosts (runners, red zone, 4th down and so on).
- `jolt()`: how much a fresh score adds and how fast it fades.
- `compress()`: the curve that compresses scores at the top.

## Notes

- If ESPN can't be reached (for example, inside a sandboxed preview), the app shows labeled sample games instead.
- Score history used for comebacks and lead changes comes from period-by-period scores, plus snapshots the page saves in your browser while it's open.
