#!/usr/bin/env python3
"""Chronolocation & Shadow Math Engine for CTF OSINT.

Calculates astronomical solar position (azimuth, elevation), shadow ratios,
and solves inverse problems (determining time of day, date, or latitude from
shadow length and direction).

Zero external dependencies: uses pure Python standard library (math, datetime, json).

Formulas & Principles:
- Shadow Ratio: R = L_shadow / H_object = cot(alpha) = 1 / tan(alpha)
- Object Height: H = L_shadow / cot(alpha) = L_shadow * tan(alpha)
- Shadow Bearing: Azimuth_shadow = (Azimuth_sun + 180) % 360
- Solar Noon: Shortest shadow of the day (alpha is maximal, sun due South or North)
  At solar noon: Zenith = |Latitude - Declination|
  If shadow points North: Latitude = Declination + Zenith
  If shadow points South: Latitude = Declination - Zenith

Usage:
    # 1. Calculate sun & shadow position for given location and UTC timestamp:
    python3 -I chronolocation.py calc --lat 48.8584 --lon 2.2945 --time "2026-06-21T12:00:00Z"

    # 2. Compute solar elevation from measured object and shadow lengths:
    python3 -I chronolocation.py shadow --height 10.5 --shadow 15.2

    # 3. Find candidate times of day matching observed shadow ratio:
    python3 -I chronolocation.py solve-time --lat 40.7128 --lon -74.0060 --date 2026-04-15 --ratio 1.42

    # 4. Estimate latitude from shortest shadow (solar noon):
    python3 -I chronolocation.py noon-lat --date 2026-05-10 --ratio 0.55 --shadow-dir north

    # 5. Run built-in self-test verification:
    python3 -I chronolocation.py --test
"""
import argparse
from datetime import datetime, timezone
import json
import math
import sys


# ---------------------------------------------------------------------------
# Astronomical Solar Position Algorithms (NOAA / Meeus standard equations)
# ---------------------------------------------------------------------------

def to_julian_date(dt_utc):
    """Convert UTC datetime object to Julian Date."""
    year = dt_utc.year
    month = dt_utc.month
    day = dt_utc.day
    hour = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0 + dt_utc.microsecond / 3600000000.0

    if month <= 2:
        year -= 1
        month += 12

    a = math.floor(year / 100.0)
    b = 2 - a + math.floor(a / 4.0)

    jd = (math.floor(365.25 * (year + 4716)) +
          math.floor(30.6001 * (month + 1)) +
          day + (hour / 24.0) + b - 1524.5)
    return jd


def solar_position(lat, lon, dt_utc):
    """Compute solar elevation, solar azimuth, declination, and equation of time.

    Args:
        lat: Latitude in decimal degrees (-90 to +90)
        lon: Longitude in decimal degrees (-180 to +180)
        dt_utc: datetime object in UTC timezone

    Returns:
        dict with:
          elevation_deg: Solar elevation angle above horizon (degrees)
          zenith_deg: Solar zenith angle from vertical (degrees)
          azimuth_deg: Solar azimuth angle clockwise from North (0=N, 90=E, 180=S, 270=W)
          shadow_ratio: Ratio of shadow length to object height (cot(elevation))
          shadow_azimuth_deg: Bearing in which shadow is cast (opposite sun)
          declination_deg: Solar declination angle
          eq_time_min: Equation of time in minutes
          solar_noon_utc: Approximate UTC time of solar noon
    """
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt_utc.astimezone(timezone.utc)

    jd = to_julian_date(dt_utc)
    t = (jd - 2451545.0) / 36525.0  # Julian centuries since J2000.0

    # Geometric mean longitude of sun (degrees)
    l0 = (280.46646 + t * (36000.76983 + 0.0003032 * t)) % 360.0

    # Geometric mean anomaly of sun (degrees)
    m = (357.52911 + t * (35999.05029 - 0.0001537 * t)) % 360.0
    m_rad = math.radians(m)

    # Eccentricity of earth orbit
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)

    # Sun equation of center (degrees)
    c = (math.sin(m_rad) * (1.914602 - t * (0.004817 + 0.000014 * t)) +
         math.sin(2.0 * m_rad) * (0.019993 - 0.000101 * t) +
         math.sin(3.0 * m_rad) * 0.000289)

    # Sun true longitude & true anomaly
    sun_true_lon = l0 + c
    f = m + c

    # Sun apparent longitude
    omega = 125.04 - 1934.136 * t
    lambda_deg = sun_true_lon - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    lambda_rad = math.radians(lambda_deg)

    # Mean obliquity of ecliptic (degrees)
    eps0 = 23.439291 - 0.013004167 * t - 0.0000001639 * t * t + 0.0000005036 * t * t * t
    eps = eps0 + 0.00256 * math.cos(math.radians(omega))
    eps_rad = math.radians(eps)

    # Solar declination (degrees)
    sin_delta = math.sin(eps_rad) * math.sin(lambda_rad)
    delta_rad = math.asin(sin_delta)
    delta_deg = math.degrees(delta_rad)

    # Equation of time (minutes)
    y = math.tan(eps_rad / 2.0) ** 2
    l0_rad = math.radians(l0)
    eot = 4.0 * math.degrees(
        y * math.sin(2.0 * l0_rad) -
        2.0 * e * math.sin(m_rad) +
        4.0 * e * y * math.sin(m_rad) * math.cos(2.0 * l0_rad) -
        0.5 * (y ** 2) * math.sin(4.0 * l0_rad) -
        1.25 * (e ** 2) * math.sin(2.0 * m_rad)
    )

    # True solar time (minutes from midnight)
    utc_hours = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0
    time_offset = eot + 4.0 * lon
    true_solar_time = (utc_hours * 60.0 + time_offset) % 1440.0

    # Solar hour angle (degrees)
    # Hour angle is 0 at true solar noon, negative before noon, positive after noon
    if (true_solar_time / 4.0) < 0:
        hour_angle = (true_solar_time / 4.0) + 180.0
    else:
        hour_angle = (true_solar_time / 4.0) - 180.0
    ha_rad = math.radians(hour_angle)

    # Solar zenith angle
    lat_rad = math.radians(lat)
    cos_zenith = (math.sin(lat_rad) * math.sin(delta_rad) +
                  math.cos(lat_rad) * math.cos(delta_rad) * math.cos(ha_rad))
    cos_zenith = max(-1.0, min(1.0, cos_zenith))
    zenith_rad = math.acos(cos_zenith)
    zenith_deg = math.degrees(zenith_rad)

    # Solar elevation angle
    elevation_deg = 90.0 - zenith_deg

    # Atmospheric refraction correction (apparent elevation)
    if elevation_deg > 85.0:
        refraction = 0.0
    elif elevation_deg > 5.0:
        te = math.tan(math.radians(elevation_deg))
        refraction = (58.1 / te - 0.07 / (te ** 3) + 0.000086 / (te ** 5)) / 3600.0
    elif elevation_deg > -0.575:
        refraction = (1735.0 + elevation_deg * (-518.2 + elevation_deg * (103.4 + elevation_deg * (-12.79 + elevation_deg * 0.711)))) / 3600.0
    else:
        refraction = -20.774 / math.tan(math.radians(elevation_deg)) / 3600.0
    apparent_elevation = elevation_deg + refraction

    # Solar azimuth angle (degrees from North)
    sin_zenith = math.sin(zenith_rad)
    if abs(sin_zenith) > 1e-6:
        cos_azimuth = ((math.sin(lat_rad) * math.cos(zenith_rad) - math.sin(delta_rad)) /
                       (math.cos(lat_rad) * sin_zenith))
        cos_azimuth = max(-1.0, min(1.0, cos_azimuth))
        azimuth_deg = math.degrees(math.acos(cos_azimuth))
        if hour_angle > 0:
            azimuth_deg = (azimuth_deg + 180.0) % 360.0
        else:
            azimuth_deg = (540.0 - azimuth_deg) % 360.0
    else:
        azimuth_deg = 180.0 if lat >= 0 else 0.0

    # Shadow calculations
    if apparent_elevation > 0.05:
        shadow_ratio = 1.0 / math.tan(math.radians(apparent_elevation))
    else:
        shadow_ratio = None  # Sun is below horizon; no distinct direct shadow

    shadow_azimuth = (azimuth_deg + 180.0) % 360.0

    # Solar noon calculation (when true_solar_time = 720 minutes)
    solar_noon_minutes_utc = 720.0 - (4.0 * lon) - eot
    noon_h = int(solar_noon_minutes_utc // 60) % 24
    noon_m = int(solar_noon_minutes_utc % 60)
    noon_s = int((solar_noon_minutes_utc * 60) % 60)
    solar_noon_str = f"{noon_h:02d}:{noon_m:02d}:{noon_s:02d} UTC"

    return {
        "elevation_deg": round(apparent_elevation, 3),
        "true_elevation_deg": round(elevation_deg, 3),
        "zenith_deg": round(zenith_deg, 3),
        "azimuth_deg": round(azimuth_deg, 2),
        "shadow_ratio": round(shadow_ratio, 4) if shadow_ratio is not None else None,
        "shadow_azimuth_deg": round(shadow_azimuth, 2),
        "declination_deg": round(delta_deg, 3),
        "eq_time_min": round(eot, 2),
        "solar_noon_utc": solar_noon_str,
    }


# ---------------------------------------------------------------------------
# Shadow Geometry Helpers
# ---------------------------------------------------------------------------

def elevation_from_shadow(height, shadow_length):
    """Compute sun elevation angle alpha = arctan(height / shadow_length)."""
    if shadow_length <= 0 or height <= 0:
        raise ValueError("Height and shadow length must be positive numbers.")
    alpha_rad = math.atan(height / shadow_length)
    alpha_deg = math.degrees(alpha_rad)
    ratio = shadow_length / height
    return {
        "elevation_deg": round(alpha_deg, 3),
        "zenith_deg": round(90.0 - alpha_deg, 3),
        "shadow_ratio": round(ratio, 4),
    }


def shadow_from_elevation(height, elevation_deg):
    """Compute shadow length from height and solar elevation angle."""
    if elevation_deg <= 0:
        return None
    alpha_rad = math.radians(elevation_deg)
    return height / math.tan(alpha_rad)


# ---------------------------------------------------------------------------
# Inverse Solvers for CTF OSINT
# ---------------------------------------------------------------------------

def solve_times_for_shadow_ratio(lat, lon, date_str, target_ratio, tol=0.08):
    """Find candidate UTC times on a given date matching an observed shadow ratio.

    Args:
        lat: Latitude
        lon: Longitude
        date_str: 'YYYY-MM-DD'
        target_ratio: Observed ratio = shadow_len / object_height
        tol: Tolerance margin on ratio

    Returns:
        List of matching candidate times with solar azimuth and shadow bearing.
    """
    year, month, day = (int(x) for x in date_str.split("-"))
    candidates = []

    # Sweep every minute of the target day
    prev_diff = None
    for minute_idx in range(1440):
        hour = minute_idx // 60
        minute = minute_idx % 60
        dt = datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
        pos = solar_position(lat, lon, dt)
        cur_ratio = pos["shadow_ratio"]

        if cur_ratio is None:
            continue

        diff = cur_ratio - target_ratio
        if abs(diff) <= tol:
            candidates.append({
                "time_utc": f"{hour:02d}:{minute:02d} UTC",
                "shadow_ratio": cur_ratio,
                "elevation_deg": pos["elevation_deg"],
                "sun_azimuth": pos["azimuth_deg"],
                "shadow_bearing": pos["shadow_azimuth_deg"],
            })

    # Cluster candidates into morning and afternoon intervals
    clustered = []
    if candidates:
        current_cluster = [candidates[0]]
        for c in candidates[1:]:
            prev_m = int(current_cluster[-1]["time_utc"][:2]) * 60 + int(current_cluster[-1]["time_utc"][3:5])
            cur_m = int(c["time_utc"][:2]) * 60 + int(c["time_utc"][3:5])
            if cur_m - prev_m <= 3:
                current_cluster.append(c)
            else:
                best = min(current_cluster, key=lambda x: abs(x["shadow_ratio"] - target_ratio))
                clustered.append(best)
                current_cluster = [c]
        if current_cluster:
            best = min(current_cluster, key=lambda x: abs(x["shadow_ratio"] - target_ratio))
            clustered.append(best)

    return clustered


def estimate_latitude_from_solar_noon(date_str, shadow_ratio, shadow_points_to="north"):
    """Estimate latitude given the shortest shadow ratio of the day (Solar Noon).

    At solar noon, Zenith = |Latitude - Declination|.
    Since tan(elevation) = 1 / shadow_ratio, elevation = arctan(1 / shadow_ratio),
    zenith = 90 - elevation.
    If shadow points North: Latitude = Declination + Zenith
    If shadow points South: Latitude = Declination - Zenith
    """
    year, month, day = (int(x) for x in date_str.split("-"))
    dt_noon = datetime(year, month, day, 12, 0, tzinfo=timezone.utc)

    # Approximate declination for the day
    jd = to_julian_date(dt_noon)
    t = (jd - 2451545.0) / 36525.0
    l0 = (280.46646 + t * (36000.76983 + 0.0003032 * t)) % 360.0
    m = (357.52911 + t * (35999.05029 - 0.0001537 * t)) % 360.0
    m_rad = math.radians(m)
    c = math.sin(m_rad) * 1.914602 + math.sin(2 * m_rad) * 0.019993
    lambda_rad = math.radians(l0 + c)
    eps_rad = math.radians(23.439291)
    declination = math.degrees(math.asin(math.sin(eps_rad) * math.sin(lambda_rad)))

    elevation = math.degrees(math.atan(1.0 / shadow_ratio))
    zenith = 90.0 - elevation

    direction = shadow_points_to.lower()
    if "north" in direction:
        lat = declination + zenith
    elif "south" in direction:
        lat = declination - zenith
    else:
        raise ValueError("shadow_points_to must be 'north' or 'south'")

    return {
        "estimated_latitude": round(lat, 3),
        "solar_elevation_at_noon": round(elevation, 3),
        "zenith_angle": round(zenith, 3),
        "solar_declination": round(declination, 3),
        "note": "Exact latitude assuming snapshot taken at local solar noon."
    }


# ---------------------------------------------------------------------------
# Self-Test Suite
# ---------------------------------------------------------------------------

def _self_test():
    """Verify astronomical calculations against published NOAA reference benchmarks."""
    print("[*] Running chronolocation.py self-test suite...")

    # Reference Benchmark 1: Summer Solstice in Greenwich (London)
    # 2026-06-21 12:00 UTC at 51.4769° N, 0.0005° W
    # Known: Declination ~ +23.44°, elevation ~ 61.9° - 62.0°
    dt1 = datetime(2026, 6, 21, 12, 0, tzinfo=timezone.utc)
    res1 = solar_position(51.4769, -0.0005, dt1)
    assert 61.0 < res1["elevation_deg"] < 63.0, f"Benchmark 1 elevation fail: {res1}"
    assert 23.0 < res1["declination_deg"] < 24.0, f"Benchmark 1 declination fail: {res1}"
    assert 170.0 < res1["azimuth_deg"] < 190.0, f"Benchmark 1 azimuth fail: {res1}"
    assert 0.50 < res1["shadow_ratio"] < 0.60, f"Benchmark 1 shadow ratio fail: {res1}"
    print(f"  [+] Greenwich Summer Solstice: Elevation={res1['elevation_deg']}°, Azimuth={res1['azimuth_deg']}° [OK]")

    # Reference Benchmark 2: Tokyo, Equinox
    # 2026-03-20 03:00 UTC (12:00 JST) at 35.6762° N, 139.6503° E
    # Declination ~ 0°, Elevation ~ 90 - 35.67 = 54.3°
    dt2 = datetime(2026, 3, 20, 2, 45, tzinfo=timezone.utc)
    res2 = solar_position(35.6762, 139.6503, dt2)
    assert 52.0 < res2["elevation_deg"] < 56.0, f"Benchmark 2 Tokyo fail: {res2}"
    print(f"  [+] Tokyo Equinox Solar Noon: Elevation={res2['elevation_deg']}°, Ratio={res2['shadow_ratio']} [OK]")

    # Reference Benchmark 3: Shadow geometry functions
    # 10m pole casts 10m shadow -> 45 deg elevation, ratio = 1.0
    sh_res = elevation_from_shadow(10.0, 10.0)
    assert abs(sh_res["elevation_deg"] - 45.0) < 1e-4
    assert abs(sh_res["shadow_ratio"] - 1.0) < 1e-4

    # 10m pole casts 17.32m shadow -> ~30 deg elevation, ratio ~ 1.732
    sh_res2 = elevation_from_shadow(10.0, 17.3205)
    assert abs(sh_res2["elevation_deg"] - 30.0) < 0.05
    print("  [+] Direct shadow-to-elevation conversions [OK]")

    # Reference Benchmark 4: Inverse time solver
    # In Greenwich on June 21, find when ratio is ~1.0 (elevation 45 deg)
    matches = solve_times_for_shadow_ratio(51.4769, -0.0005, "2026-06-21", 1.0)
    assert len(matches) == 2, f"Expected 2 matches (morning & afternoon), got: {matches}"
    # Morning shadow points W/NW (~310-330 deg), afternoon points E/NE (~30-50 deg)
    m_morning, m_afternoon = matches[0], matches[1]
    assert "08:" in m_morning["time_utc"] or "09:" in m_morning["time_utc"]
    assert "14:" in m_afternoon["time_utc"] or "15:" in m_afternoon["time_utc"]
    print(f"  [+] Inverse time-of-day solver (Morning: {m_morning['time_utc']}, Afternoon: {m_afternoon['time_utc']}) [OK]")

    # Reference Benchmark 5: Solar noon latitude estimation
    # On 2026-06-21, at Paris (48.85° N), solar noon ratio is ~0.587 (elevation ~64.5°)
    noon_est = estimate_latitude_from_solar_noon("2026-06-21", 0.477, "north")
    assert 48.0 < noon_est["estimated_latitude"] < 50.0, f"Noon latitude estimate failed: {noon_est}"
    print(f"  [+] Noon latitude estimator: est={noon_est['estimated_latitude']}° [OK]")

    print("[+] All chronolocation self-tests PASSED successfully!")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Chronolocation & Astronomical Shadow Math Engine")
    parser.add_argument("--test", action="store_true", help="Run self-test verification suite")
    subparsers = parser.add_subparsers(dest="subcommand")

    # calc
    p_calc = subparsers.add_parser("calc", help="Calculate solar position & shadow characteristics")
    p_calc.add_argument("--lat", type=float, required=True, help="Latitude (-90 to +90)")
    p_calc.add_argument("--lon", type=float, required=True, help="Longitude (-180 to +180)")
    p_calc.add_argument("--time", type=str, required=True, help="ISO-8601 UTC timestamp (e.g. 2026-06-21T12:00:00Z)")

    # shadow
    p_sh = subparsers.add_parser("shadow", help="Compute elevation & ratio from measured height and shadow")
    p_sh.add_argument("--height", type=float, required=True, help="Object height in meters/pixels")
    p_sh.add_argument("--shadow", type=float, required=True, help="Shadow length in meters/pixels")

    # solve-time
    p_sol = subparsers.add_parser("solve-time", help="Find candidate times of day matching shadow ratio")
    p_sol.add_argument("--lat", type=float, required=True, help="Latitude")
    p_sol.add_argument("--lon", type=float, required=True, help="Longitude")
    p_sol.add_argument("--date", type=str, required=True, help="Date YYYY-MM-DD")
    p_sol.add_argument("--ratio", type=float, required=True, help="Observed shadow ratio (shadow / height)")
    p_sol.add_argument("--tol", type=float, default=0.08, help="Tolerance margin (default: 0.08)")

    # noon-lat
    p_noon = subparsers.add_parser("noon-lat", help="Estimate latitude from solar noon shortest shadow")
    p_noon.add_argument("--date", type=str, required=True, help="Date YYYY-MM-DD")
    p_noon.add_argument("--ratio", type=float, required=True, help="Shortest shadow ratio at solar noon")
    p_noon.add_argument("--shadow-dir", choices=["north", "south"], default="north", help="Direction shadow points")

    args = parser.parse_args()

    if args.test:
        _self_test()
        sys.exit(0)

    if not args.subcommand:
        parser.print_help()
        sys.exit(1)

    if args.subcommand == "calc":
        iso_str = args.time.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso_str)
        res = solar_position(args.lat, args.lon, dt)
        print(json.dumps(res, indent=2))

    elif args.subcommand == "shadow":
        res = elevation_from_shadow(args.height, args.shadow)
        print(json.dumps(res, indent=2))

    elif args.subcommand == "solve-time":
        res = solve_times_for_shadow_ratio(args.lat, args.lon, args.date, args.ratio, tol=args.tol)
        print(f"[*] Candidate Times for Ratio {args.ratio} on {args.date} at ({args.lat}, {args.lon}):")
        print(json.dumps(res, indent=2))

    elif args.subcommand == "noon-lat":
        res = estimate_latitude_from_solar_noon(args.date, args.ratio, args.shadow_dir)
        print(f"[*] Estimated Latitude for Solar Noon on {args.date}:")
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
