# FlatsCheck 🎣

**Go/no-go fishing conditions dashboard for Texas Gulf Coast flats fishing.**

Target species: **Redfish (red drum)** and **Speckled Trout (spotted seatrout)**

Locations covered: Laguna Madre · Port Aransas / Aransas Pass · Rockport / Aransas Bay · Baffin Bay

---

## What It Does

Pulls live data from two free APIs (no keys required) and scores the next 7 days on a 0–10 scale for flats fishing conditions:

| Score | Label | Meaning |
|-------|-------|---------|
| 9–12 | ✅ GO | Prime conditions — get on the water |
| 5–8 | ⚠️ MAYBE | Fishable — pick your spots |
| 0–4 | ❌ NO | Skip it |

**Scoring breakdown (12 pts total):**

| Factor | Max Pts | Logic |
|--------|---------|-------|
| Wind speed | 3 | <10mph=3, 10–15=2, 15–20=1, >20=0 |
| Tidal movement | 2 | Significant range=2, moderate=1, dead neap=0 |
| Low tide timing | 2 | Low tide 6–10am=2 (prime wading window), near=1 |
| Temperature | 2 | 65–85°F=2 (both species active), 55–92°F=1, extreme=0 |
| Rain | 1 | Dry=1, rain=0 |
| 🌕 Solunar | 2 | New/Full moon=2, First/Last quarter=1, Crescent=0 |

**Solunar theory:** Based on John Alden Knight's 1926 research. New and full moons create the strongest combined gravitational pull from the sun and moon, producing "major periods" of intense fish feeding activity. Quarter moons produce moderate activity. Crescent phases are weakest.

---

## How to Run

### One command:
```bash
cd ~/Documents/Ai\ projects/Personal/flatscheck
./run.sh
```
This fetches fresh data, starts a local server, and opens the dashboard in your browser.

### Manual (two steps):
```bash
# 1. Fetch conditions
python3 fetch_conditions.py

# 2. Serve and open
python3 -m http.server 8080
open http://localhost:8080/dashboard.html
```

**Requirements:** Python 3.x (standard library only — no pip installs needed)

---

## Files

| File | Purpose |
|------|---------|
| `fetch_conditions.py` | Fetches NOAA tides + Open-Meteo weather, scores each day, writes `conditions.json` |
| `dashboard.html` | Single-file web dashboard that reads `conditions.json` |
| `conditions.json` | Generated data file (gitignored) |
| `run.sh` | One-shot launcher |
| `README.md` | This file |

---

## Data Sources

- **Tides:** [NOAA Tides & Currents API](https://tidesandcurrents.noaa.gov/api-helper/url-generator.html) — Station `8775241` (Port Aransas, TX). Free, no auth.
- **Weather:** [Open-Meteo](https://open-meteo.com/) — Free, no auth. Coordinates: 27.8336°N, 97.0641°W

---

## Customizing

### Add more tide stations
NOAA station IDs for other TX Gulf Coast spots:
- Rockport: `8774770`
- Corpus Christi: `8775870`
- South Padre Island: `8779749`
- Galveston: `8771450`

Change `NOAA_STATION` at the top of `fetch_conditions.py`.

### Adjust scoring weights
Find the `score_day()` function in `fetch_conditions.py`. Each factor returns points — edit the thresholds and point values directly.

**Redfish vs. trout tuning notes:**
- Redfish tolerate more wind and colder water than trout
- Speckled trout fishing shuts down hard below 55°F — they go deep
- Both species feed aggressively on moving tides, especially falling tides
- Morning low tides (6–10am) are the best window for wading shallow flats

### Refresh data
Just re-run `python3 fetch_conditions.py` — it overwrites `conditions.json` and refreshes the dashboard on next reload.

### Schedule daily refresh (optional)
Add to crontab to run every morning at 5am:
```
0 5 * * * cd ~/Documents/Ai\ projects/Personal/flatscheck && python3 fetch_conditions.py
```

---

## Notes

- The TX Gulf Coast is **micro-tidal** (~0.5–2.0 ft range), so tidal movement is scored relative to local norms — not compared to East Coast tides
- NOAA tide data is from Port Aransas station; conditions vary across the coast (especially Baffin Bay, which is more isolated)
- If either API is unavailable, the script falls back to sample/simulated data and labels it clearly in the dashboard

---

*Built overnight by Claude Code. Ship it.*
