#!/usr/bin/env python3
"""
FlatsCheck — TX Gulf Coast Flats Fishing Conditions Fetcher
Targets: Redfish (red drum) and Speckled Trout (spotted seatrout)
Locations: Laguna Madre, Port Aransas / Aransas Pass, Rockport, Baffin Bay
NOAA Station: Port Aransas (8775241)
"""

import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
import math

# ── Constants ────────────────────────────────────────────────────────────────

NOAA_STATION = "8775241"  # Port Aransas
LAT = 27.8336
LON = -97.0641
TIMEZONE = "America/Chicago"

# ── API Fetchers ─────────────────────────────────────────────────────────────

def fetch_noaa_tides():
    """Fetch 7 days of hourly tide predictions from NOAA."""
    today = datetime.now().strftime("%Y%m%d")
    url = (
        f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
        f"?begin_date={today}&range=168&station={NOAA_STATION}"
        f"&product=predictions&datum=MLLW&time_zone=lst_ldt"
        f"&interval=h&units=english&application=flatscheck&format=json"
    )
    print(f"  Fetching NOAA tides from {url[:80]}...")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if "predictions" in data:
                print(f"  ✓ Got {len(data['predictions'])} hourly tide predictions")
                return data["predictions"]
            else:
                print(f"  ✗ NOAA returned unexpected data: {list(data.keys())}")
                return None
    except Exception as e:
        print(f"  ✗ NOAA API error: {e} — using sample tide data")
        return None


def fetch_weather():
    """Fetch 7-day daily forecast from Open-Meteo."""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        f"&daily=wind_speed_10m_max,wind_direction_10m_dominant,"
        f"temperature_2m_max,precipitation_sum,sunrise,sunset"
        f"&temperature_unit=fahrenheit&wind_speed_unit=mph"
        f"&precipitation_unit=inch&timezone={TIMEZONE}&forecast_days=7"
    )
    print(f"  Fetching Open-Meteo weather...")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if "daily" in data:
                print(f"  ✓ Got {len(data['daily']['time'])} days of weather")
                return data["daily"]
            else:
                print(f"  ✗ Open-Meteo returned unexpected data")
                return None
    except Exception as e:
        print(f"  ✗ Open-Meteo error: {e} — using sample weather data")
        return None


# ── Sample / Fallback Data ───────────────────────────────────────────────────

def sample_weather(num_days=7):
    """Fallback weather data if Open-Meteo is unavailable."""
    base = datetime.now()
    days = [(base + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]
    sample_winds   = [8, 14, 22, 10, 6, 18, 12]
    sample_dirs    = [120, 145, 170, 110, 95, 160, 135]
    sample_temps   = [72, 68, 65, 75, 78, 63, 70]
    sample_rain    = [0.0, 0.0, 0.1, 0.0, 0.0, 0.2, 0.0]
    sample_sunrise = [f"{d}T07:12" for d in days]
    sample_sunset  = [f"{d}T18:45" for d in days]
    return {
        "time": days,
        "wind_speed_10m_max": sample_winds[:num_days],
        "wind_direction_10m_dominant": sample_dirs[:num_days],
        "temperature_2m_max": sample_temps[:num_days],
        "precipitation_sum": sample_rain[:num_days],
        "sunrise": sample_sunrise,
        "sunset":  sample_sunset,
        "_is_sample": True,
    }


def sample_tides():
    """Generate plausible sample hourly tide data for 7 days (168 hrs)."""
    base = datetime.now().replace(minute=0, second=0, microsecond=0)
    predictions = []
    # Simulate a mixed semi-diurnal pattern typical of TX Gulf Coast
    # (one dominant cycle ~24.8 hrs, muted second cycle)
    for h in range(168):
        t = base + timedelta(hours=h)
        # Primary: 12.4-hr cycle; secondary: 24.8-hr cycle (weaker on TX coast)
        v = (
            1.2 * math.sin(2 * math.pi * h / 12.4 + 0.5)
            + 0.4 * math.sin(2 * math.pi * h / 24.8 + 1.0)
        )
        predictions.append({
            "t": t.strftime("%Y-%m-%d %H:%M"),
            "v": f"{v:.3f}",
        })
    return predictions


# ── Solunar Calculations ─────────────────────────────────────────────────────

def moon_phase(date_obj):
    """
    Calculate moon phase for a given date.
    Returns (phase_days, phase_name, emoji).
    phase_days: 0-29.5 (days elapsed since last new moon)

    Based on John Alden Knight's Solunar Theory (1926):
    - New moon & full moon = strongest gravitational pull = peak feeding activity
    - Quarter moons = moderate solunar activity
    - In-between = weak periods

    Reference epoch: January 6, 2000 18:14 UTC (confirmed new moon)
    Synodic period: 29.530588853 days
    """
    epoch = datetime(2000, 1, 6, 18, 14, 0)
    synodic = 29.530588853
    diff = (date_obj - epoch).total_seconds() / 86400
    phase_days = diff % synodic
    if phase_days < 0:
        phase_days += synodic

    # Phase name and emoji
    if phase_days < 1.85:
        name, emoji = "New Moon", "🌑"
    elif phase_days < 7.38:
        name, emoji = "Waxing Crescent", "🌒"
    elif phase_days < 11.08:
        name, emoji = "First Quarter", "🌓"
    elif phase_days < 14.77:
        name, emoji = "Waxing Gibbous", "🌔"
    elif phase_days < 16.61:
        name, emoji = "Full Moon", "🌕"
    elif phase_days < 22.15:
        name, emoji = "Waning Gibbous", "🌖"
    elif phase_days < 25.84:
        name, emoji = "Last Quarter", "🌗"
    else:
        name, emoji = "Waning Crescent", "🌘"

    return phase_days, name, emoji


def score_solunar(phase_days):
    """
    Score solunar activity for DAYTIME flats fishing (0–2 pts).

    Key insight: full moon = bright nights = fish feed all night on lit water
    → arrive at dawn already full → slow daytime bite.
    New moon = dark nights = fish couldn't feed overnight → hungry at first light
    → aggressive daytime bite on the flats.

    Windows:
      New moon  (days 0–4 or 26.5–29.5):  2 pts  — dark nights, hungry fish at dawn
      Crescent + Quarter (days 4–11 or 19–26.5): 1 pt — partial nights, moderate bite
      Gibbous + Full (days 11–19):         0 pts  — bright moon nights, fish fed overnight
    """
    # New moon window (dark nights — best for daytime fishing)
    if phase_days <= 4.0 or phase_days >= 26.5:
        return 2, "New moon — dark nights, fish arrive hungry at daybreak"
    # Gibbous and full moon (bright nights — fish fed overnight, slow daytime bite)
    elif 11.0 <= phase_days <= 19.0:
        return 0, "Bright moon — fish fed overnight, expect slow morning bite"
    # Crescent and quarter phases (in between)
    else:
        return 1, "Quarter/crescent — partial moon nights, moderate daytime bite"


# ── Tide Analysis ────────────────────────────────────────────────────────────

def analyze_tides_for_day(hourly_predictions, date_str):
    """
    Extract tide highs/lows for a given date and compute scoring factors.
    Returns dict with: highs, lows, tidal_range, moving_water_pts,
                       low_tide_timing_pts, best_low_time
    """
    day_data = [p for p in hourly_predictions if p["t"].startswith(date_str)]
    if not day_data:
        return {
            "highs": [], "lows": [], "tidal_range": 0,
            "moving_water_pts": 1, "low_tide_timing_pts": 1,
            "best_low_time": "N/A",
        }

    values = [float(p["v"]) for p in day_data]
    times  = [p["t"] for p in day_data]

    # Find local highs and lows
    highs, lows = [], []
    for i in range(1, len(values) - 1):
        if values[i] > values[i-1] and values[i] > values[i+1]:
            highs.append({"time": times[i], "height": round(values[i], 2)})
        elif values[i] < values[i-1] and values[i] < values[i+1]:
            lows.append({"time": times[i], "height": round(values[i], 2)})

    tidal_range = max(values) - min(values) if values else 0

    # Moving water score: significant tidal range is good for redfish/trout
    # TX Gulf Coast tides are micro-tidal (~1-2 ft), so calibrate accordingly
    if tidal_range >= 1.2:
        moving_water_pts = 2
    elif tidal_range >= 0.5:
        moving_water_pts = 1
    else:
        moving_water_pts = 0  # Dead neap, stagnant water

    # Low tide timing: best for wading flats is low around 6am–10am
    # Fish stack on edges and are more accessible / feeding aggressively
    best_low_time = "N/A"
    low_timing_pts = 0
    for low in lows:
        try:
            hour = int(low["time"].split(" ")[1].split(":")[0])
            if 6 <= hour <= 10:
                low_timing_pts = 2
                best_low_time = low["time"].split(" ")[1]
                break
            elif 10 < hour <= 13 or 4 <= hour < 6:
                low_timing_pts = 1
                if best_low_time == "N/A":
                    best_low_time = low["time"].split(" ")[1]
        except Exception:
            pass

    if best_low_time == "N/A" and lows:
        best_low_time = lows[0]["time"].split(" ")[1]

    return {
        "highs": highs,
        "lows": lows,
        "tidal_range": round(tidal_range, 2),
        "moving_water_pts": moving_water_pts,
        "low_tide_timing_pts": low_timing_pts,
        "best_low_time": best_low_time,
    }


# ── Wind Direction Label ──────────────────────────────────────────────────────

def wind_dir_label(degrees):
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
    idx = round(degrees / 22.5) % 16
    return dirs[idx]


# ── Scoring Engine ────────────────────────────────────────────────────────────

def score_day(wind_mph, wind_deg, tide_data, temp_f, rain_in, date_obj):
    """
    Score a day 0–12 for redfish and speckled trout flats fishing.

    Breakdown (max 12 pts):
      Wind          0–3 pts
      Tidal range   0–2 pts
      Low tide time 0–2 pts
      Temperature   0–2 pts
      Rain          0–1 pt
      Solunar       0–2 pts  ← moon phase / feeding activity
    """
    breakdown = {}

    # Wind (0–3 pts) — redfish tolerate moderate wind better than trout
    if wind_mph < 10:
        wind_pts = 3
        wind_note = "Calm — perfect sight-fishing"
    elif wind_mph < 15:
        wind_pts = 2
        wind_note = "Light — good casting lanes"
    elif wind_mph < 20:
        wind_pts = 1
        wind_note = "Moderate — manageable"
    else:
        wind_pts = 0
        wind_note = "Too windy — water choppy, visibility poor"
    breakdown["wind"] = {"pts": wind_pts, "note": wind_note}

    # Tidal movement (0–2 pts)
    moving_pts = tide_data["moving_water_pts"]
    if moving_pts == 2:
        tide_note = "Good tidal movement — baitfish pushed, fish active"
    elif moving_pts == 1:
        tide_note = "Moderate movement"
    else:
        tide_note = "Dead water — fish sluggish"
    breakdown["tides"] = {"pts": moving_pts, "note": tide_note}

    # Low tide timing (0–2 pts)
    low_pts = tide_data["low_tide_timing_pts"]
    best_low = tide_data["best_low_time"]
    if low_pts == 2:
        lt_note = f"Low tide at {best_low} — prime morning flat access"
    elif low_pts == 1:
        lt_note = f"Low tide at {best_low} — decent timing"
    else:
        lt_note = f"Low tide at {best_low} — off-peak timing"
    breakdown["low_tide_timing"] = {"pts": low_pts, "note": lt_note}

    # Temperature (0–2 pts)
    # Redfish: active 55–90°F; Speckled trout: 60–85°F optimal
    if 65 <= temp_f <= 85:
        temp_pts = 2
        temp_note = "Ideal — both species active"
    elif 55 <= temp_f < 65 or 85 < temp_f <= 92:
        temp_pts = 1
        temp_note = "Acceptable — fish may be slower"
    elif temp_f < 55:
        temp_pts = 0
        temp_note = "Cold — trout lethargic, fish deep structure"
    else:
        temp_pts = 0
        temp_note = "Too hot — fish in deeper, cooler water"
    breakdown["temperature"] = {"pts": temp_pts, "note": temp_note}

    # Rain (0–1 pt)
    if rain_in == 0:
        rain_pts = 1
        rain_note = "No rain — clear skies"
    elif rain_in < 0.1:
        rain_pts = 1
        rain_note = "Trace rain — minimal impact"
    else:
        rain_pts = 0
        rain_note = "Rain — reduced visibility, harder wade"
    breakdown["rain"] = {"pts": rain_pts, "note": rain_note}

    # Solunar (0–2 pts) — moon phase feeding activity
    phase_days, phase_name, phase_emoji = moon_phase(date_obj)
    solunar_pts, solunar_note = score_solunar(phase_days)
    breakdown["solunar"] = {
        "pts": solunar_pts,
        "note": solunar_note,
        "phase": phase_name,
        "emoji": phase_emoji,
        "phase_days": round(phase_days, 1),
    }

    total = wind_pts + moving_pts + low_pts + temp_pts + rain_pts + solunar_pts

    # Thresholds scaled for 12-pt max
    if total >= 9:
        label = "GO"
        verdict = "Prime day — get on the water"
    elif total >= 5:
        label = "MAYBE"
        verdict = "Fishable — pick your spots carefully"
    else:
        label = "NO"
        verdict = "Skip it — conditions are against you"

    return {
        "score": total,
        "label": label,
        "verdict": verdict,
        "breakdown": breakdown,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n🎣 FlatsCheck — TX Gulf Coast Conditions Fetcher")
    print("   Target species: Redfish (red drum) · Speckled Trout (spotted seatrout)")
    print("=" * 62)

    today = datetime.now()

    # Fetch data
    print("\n[1/2] Fetching tide data (NOAA)...")
    tide_predictions = fetch_noaa_tides()
    if not tide_predictions:
        print("  → Using sample tide data (NOAA unavailable)")
        tide_predictions = sample_tides()
        tide_source = "sample"
    else:
        tide_source = "NOAA"

    print("\n[2/2] Fetching weather data (Open-Meteo)...")
    weather = fetch_weather()
    if not weather:
        print("  → Using sample weather data (Open-Meteo unavailable)")
        weather = sample_weather()
        weather_source = "sample"
    else:
        weather_source = "Open-Meteo"
        weather["_is_sample"] = False

    # Build 7-day forecast
    print("\n[3/3] Scoring days...")
    days = []

    for i in range(7):
        date_obj = today + timedelta(days=i)
        date_str = date_obj.strftime("%Y-%m-%d")
        day_name = date_obj.strftime("%A")

        # Weather for this day
        try:
            idx = weather["time"].index(date_str)
        except ValueError:
            idx = i  # fallback to positional

        wind_mph  = weather["wind_speed_10m_max"][idx]
        wind_deg  = weather["wind_direction_10m_dominant"][idx]
        temp_f    = weather["temperature_2m_max"][idx]
        rain_in   = weather["precipitation_sum"][idx]
        sunrise   = weather["sunrise"][idx].split("T")[1] if "T" in str(weather["sunrise"][idx]) else weather["sunrise"][idx]
        sunset    = weather["sunset"][idx].split("T")[1] if "T" in str(weather["sunset"][idx]) else weather["sunset"][idx]

        # Tide analysis
        tide_data = analyze_tides_for_day(tide_predictions, date_str)

        # Score (now includes solunar)
        result = score_day(wind_mph, wind_deg, tide_data, temp_f, rain_in, date_obj)

        solunar = result["breakdown"]["solunar"]
        day_record = {
            "date": date_str,
            "day": day_name,
            "score": result["score"],
            "label": result["label"],
            "verdict": result["verdict"],
            "breakdown": result["breakdown"],
            "wind": {
                "speed_mph": round(wind_mph, 1),
                "direction_deg": wind_deg,
                "direction_label": wind_dir_label(wind_deg),
            },
            "tides": {
                "highs": tide_data["highs"],
                "lows": tide_data["lows"],
                "tidal_range_ft": tide_data["tidal_range"],
                "best_low_time": tide_data["best_low_time"],
            },
            "temperature_f": round(temp_f, 1),
            "rain_in": round(rain_in, 2),
            "sunrise": sunrise,
            "sunset": sunset,
        }

        label_icon = {"GO": "✅", "MAYBE": "⚠️", "NO": "❌"}.get(result["label"], "?")
        print(f"  {date_str} ({day_name[:3]}): {label_icon} {result['label']:5s} "
              f"[{result['score']}/12] — wind {wind_mph:.0f}mph, "
              f"{temp_f:.0f}°F, rain {rain_in:.2f}\" "
              f"{solunar['emoji']} {solunar['phase']}")

        days.append(day_record)

    # Build output
    output = {
        "generated_at": today.strftime("%Y-%m-%d %H:%M"),
        "station": {
            "noaa_id": NOAA_STATION,
            "name": "Port Aransas, TX",
            "lat": LAT,
            "lon": LON,
        },
        "sources": {
            "tides": tide_source,
            "weather": weather_source,
        },
        "target_species": ["Redfish (red drum)", "Speckled Trout (spotted seatrout)"],
        "locations": [
            {
                "name": "Laguna Madre",
                "notes": "Shallow hypersaline lagoon — prime redfish habitat. "
                         "Ultra-clear water means wind matters enormously. "
                         "Best on calm mornings on the flats. Watch for tailing reds.",
            },
            {
                "name": "Port Aransas / Aransas Pass",
                "notes": "Jetties + grass flats. Great trout habitat in the back bays. "
                         "Tidal current through the pass creates feeding lanes. "
                         "Best on moving tides. The NOAA data is from this station.",
            },
            {
                "name": "Rockport / Aransas Bay",
                "notes": "Classic Texas flats — grass beds, shell pads, shallow bays. "
                         "Excellent for wading. Speckled trout love the grass edges. "
                         "Redfish stack in potholes at low tide.",
            },
            {
                "name": "Baffin Bay",
                "notes": "Remote and wild — legendary big trout country. "
                         "Rocky shorelines and clear water. Sensitive to cold fronts; "
                         "trout go deep below 55°F. Best in fall and spring.",
            },
        ],
        "scoring_guide": {
            "12": "Perfect — book it, call in sick",
            "9-11": "GO — prime conditions",
            "5-8": "MAYBE — pick your spots",
            "0-4": "NO — conditions are against you",
        },
        "days": days,
    }

    with open("conditions.json", "w") as f:
        json.dump(output, f, indent=2)

    print("\n✓ conditions.json written")

    best = max(days, key=lambda d: d["score"])
    print(f"\n🏆 Best day: {best['date']} ({best['day']}) — "
          f"Score {best['score']}/12 [{best['label']}]")
    print(f"   {best['verdict']}")
    print("\nOpen dashboard.html in your browser to view the full forecast.\n")


if __name__ == "__main__":
    main()
