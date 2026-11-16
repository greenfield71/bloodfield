#!/usr/bin/env python3
"""OpenStreetMap Overpass QL Query Builder and Spatial Data Mining Tool.

Used in CTF OSINT challenges to locate landmarks and infrastructure features
(telecom towers, chimneys, railway junctions, power substations, bridges, water towers)
using geographic bounding boxes, radius searches, or Nominatim geocoding.

Usage:
    python3 -I overpass_query.py geocode "Mackay, Idaho"
    python3 -I overpass_query.py reverse --lat 43.9135 --lon -113.6133
    python3 -I overpass_query.py around --lat 44.81 --lon 20.46 --radius 5000 --tags "man_made=chimney"
    python3 -I overpass_query.py bbox --south 44.80 --west 20.40 --north 44.85 --east 20.50 --tags "man_made=tower"
    python3 -I overpass_query.py preset chimney_telecom --lat 44.81 --lon 20.46 --radius 10000
    python3 -I overpass_query.py query "node[\"man_made\"=\"water_tower\"](44.8,20.4,44.9,20.5); out body;"
    python3 -I overpass_query.py --test

Deps:
    Python standard library (urllib, json, math, re).
    Optional: requests (used if installed, graceful fallback to urllib).
"""
import argparse
import json
import math
import re
import sys
import urllib.parse
import urllib.request

USER_AGENT = "ctf-osint-overpass/1.0 (CTF challenge solver research)"
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"


# ---------------------------------------------------------------------------
# Geodesic Math Helpers
# ---------------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    """Compute great-circle distance between two points in meters."""
    r = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def bounding_box_from_point(lat, lon, radius_m):
    """Calculate an approximate lat/lon bounding box (south, west, north, east) around a point."""
    lat_delta = radius_m / 111139.0
    lon_delta = radius_m / (111139.0 * math.cos(math.radians(lat)))
    return (lat - lat_delta, lon - lon_delta, lat + lat_delta, lon + lon_delta)


# ---------------------------------------------------------------------------
# HTTP Client Helper
# ---------------------------------------------------------------------------

def _http_request(url, data=None, headers=None, timeout=30):
    """Perform HTTP GET or POST using requests if available, else urllib."""
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)

    try:
        import requests
        if data is not None:
            if isinstance(data, dict):
                resp = requests.post(url, data=data, headers=hdrs, timeout=timeout)
            else:
                resp = requests.post(url, data=data.encode("utf-8"), headers=hdrs, timeout=timeout)
        else:
            resp = requests.get(url, headers=hdrs, timeout=timeout)
        return resp.status_code, resp.text
    except ImportError:
        pass

    encoded_data = None
    if data is not None:
        if isinstance(data, dict):
            encoded_data = urllib.parse.urlencode(data).encode("utf-8")
        elif isinstance(data, str):
            encoded_data = data.encode("utf-8")
        else:
            encoded_data = data

    req = urllib.request.Request(url, data=encoded_data, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return 0, str(e)


# ---------------------------------------------------------------------------
# Overpass QL Generator & Parser
# ---------------------------------------------------------------------------

def parse_tag_spec(tag_str):
    """Parse tag expression into Overpass filter string.
    
    Supports:
      "key=val"     -> ["key"="val"]
      "key!=val"    -> ["key"!="val"]
      "key~val_rx"  -> ["key"~"val_rx"]
      "key"         -> ["key"]
      "!key"        -> [!"key"]
    """
    tag_str = tag_str.strip()
    if not tag_str:
        return ""
    if tag_str.startswith("[") and tag_str.endswith("]"):
        return tag_str

    if "!=" in tag_str:
        k, v = tag_str.split("!=", 1)
        return f'["{k.strip()}"!="{v.strip()}"]'
    elif "~" in tag_str:
        k, v = tag_str.split("~", 1)
        return f'["{k.strip()}"~"{v.strip()}"]'
    elif "=" in tag_str:
        k, v = tag_str.split("=", 1)
        return f'["{k.strip()}"="{v.strip()}"]'
    elif tag_str.startswith("!"):
        return f'[!"{tag_str[1:].strip()}"]'
    else:
        return f'["{tag_str}"]'


def build_overpass_ql(tag_filters, bbox=None, around=None, area_name=None,
                      element_types=("node", "way", "relation"),
                      timeout=35, output_format="json", max_count=500):
    """Generate syntactically valid Overpass QL script.
    
    Args:
        tag_filters: list of tag strings or a single string.
        bbox: tuple (south, west, north, east)
        around: tuple (radius_m, lat, lon)
        area_name: name of administrative area to restrict search
        element_types: sequence of 'node', 'way', 'relation'
        timeout: query timeout in seconds
        output_format: 'json' or 'xml'
        max_count: maximum number of elements
    """
    if isinstance(tag_filters, str):
        tag_filters = [tag_filters]

    tag_clause = "".join(parse_tag_spec(t) for t in tag_filters if t)

    geo_filter = ""
    prefix_area = ""
    if area_name:
        clean_area = area_name.replace('"', '\\"')
        prefix_area = f'area["name"="{clean_area}"]->.searchArea;\n'
        geo_filter = "(area.searchArea)"
    elif around:
        radius_m, lat, lon = around
        geo_filter = f"(around:{radius_m},{lat},{lon})"
    elif bbox:
        s, w, n, e = bbox
        geo_filter = f"({s},{w},{n},{e})"

    query_parts = []
    query_parts.append(f"[out:{output_format}][timeout:{timeout}];")
    if prefix_area:
        query_parts.append(prefix_area)

    subqueries = []
    for elem in element_types:
        subqueries.append(f"  {elem}{tag_clause}{geo_filter};")

    query_parts.append("(")
    query_parts.append("\n".join(subqueries))
    query_parts.append(");")
    query_parts.append(f"out center tags {max_count};")
    return "\n".join(query_parts)


def execute_overpass_ql(ql_query, endpoint=None):
    """Execute Overpass QL code against public Overpass endpoints."""
    endpoints = [endpoint] if endpoint else OVERPASS_ENDPOINTS
    last_err = None

    for ep in endpoints:
        code, body = _http_request(ep, data={"data": ql_query}, timeout=45)
        if code == 200:
            try:
                data = json.loads(body)
                return data
            except json.JSONDecodeError as err:
                last_err = f"JSON decode error from {ep}: {err}"
        else:
            last_err = f"HTTP {code} from {ep}: {body[:200]}"

    raise RuntimeError(f"Overpass query failed across endpoints: {last_err}")


def extract_elements(overpass_json, center_lat=None, center_lon=None):
    """Normalize nodes/ways/relations from Overpass JSON into flat record list."""
    elements = overpass_json.get("elements", [])
    results = []

    for el in elements:
        el_type = el.get("type", "node")
        el_id = el.get("id")
        tags = el.get("tags", {})

        # Coordinates: node has lat/lon directly; ways/relations have center
        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None and "center" in el:
            lat = el["center"].get("lat")
            lon = el["center"].get("lon")

        dist = None
        if lat is not None and lon is not None and center_lat is not None and center_lon is not None:
            dist = round(haversine(center_lat, center_lon, lat, lon), 1)

        name = tags.get("name") or tags.get("description") or tags.get("ref") or f"{el_type}/{el_id}"
        osm_url = f"https://www.openstreetmap.org/{el_type}/{el_id}"
        gmaps_url = f"https://www.google.com/maps?q={lat},{lon}" if lat is not None else ""

        results.append({
            "type": el_type,
            "id": el_id,
            "name": name,
            "lat": lat,
            "lon": lon,
            "distance_m": dist,
            "tags": tags,
            "osm_url": osm_url,
            "gmaps_url": gmaps_url,
        })

    if center_lat is not None and center_lon is not None:
        results.sort(key=lambda x: (x["distance_m"] if x["distance_m"] is not None else float("inf")))

    return results


def elements_to_geojson(elements):
    """Convert parsed elements list to GeoJSON FeatureCollection."""
    features = []
    for el in elements:
        if el.get("lat") is None or el.get("lon") is None:
            continue
        feat = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [el["lon"], el["lat"]]
            },
            "properties": {
                "id": el["id"],
                "osm_type": el["type"],
                "name": el["name"],
                "distance_m": el.get("distance_m"),
                "osm_url": el.get("osm_url"),
                "gmaps_url": el.get("gmaps_url"),
                "tags": el.get("tags", {})
            }
        }
        features.append(feat)

    return {
        "type": "FeatureCollection",
        "features": features
    }


# ---------------------------------------------------------------------------
# Nominatim Geocoding
# ---------------------------------------------------------------------------

def geocode(query):
    """Geocode search string into candidate coordinates and bounding boxes."""
    params = urllib.parse.urlencode({
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": 5,
    })
    url = f"{NOMINATIM_SEARCH}?{params}"
    code, body = _http_request(url)
    if code != 200:
        raise RuntimeError(f"Nominatim geocode failed with HTTP {code}: {body[:200]}")
    data = json.loads(body)
    results = []
    for item in data:
        bbox = item.get("boundingbox", [])
        # Nominatim format: [south, north, west, east]
        s, n, w, e = (float(x) for x in bbox) if len(bbox) == 4 else (None, None, None, None)
        results.append({
            "display_name": item.get("display_name"),
            "lat": float(item.get("lat")),
            "lon": float(item.get("lon")),
            "osm_type": item.get("osm_type"),
            "osm_id": item.get("osm_id"),
            "bbox_snwe": (s, n, w, e),
            "bbox_swne": (s, w, n, e),
            "category": item.get("category"),
            "type": item.get("type"),
        })
    return results


def reverse_geocode(lat, lon):
    """Reverse geocode coordinates into structured address."""
    params = urllib.parse.urlencode({
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "addressdetails": 1,
    })
    url = f"{NOMINATIM_REVERSE}?{params}"
    code, body = _http_request(url)
    if code != 200:
        raise RuntimeError(f"Nominatim reverse geocode failed with HTTP {code}: {body[:200]}")
    return json.loads(body)


# ---------------------------------------------------------------------------
# Common CTF OSINT Presets
# ---------------------------------------------------------------------------

PRESETS = {
    "chimney_telecom": {
        "description": "Industrial chimneys, telecom masts and cell towers",
        "tags": ["man_made~chimney|tower|mast", "tower:type~communication|cellular|telecommunication"],
    },
    "railway_substation": {
        "description": "Power substations and transformers near industrial railways",
        "tags": ["power=substation"],
    },
    "water_tower": {
        "description": "Elevated water towers and reservoirs",
        "tags": ["man_made=water_tower"],
    },
    "church_spire": {
        "description": "Historic churches, cathedrals and bell towers",
        "tags": ["amenity=place_of_worship", "building=church"],
    },
    "helipad_hospital": {
        "description": "Hospital emergency helipads or aerodromes",
        "tags": ["aeroway=helipad"],
    },
    "wind_turbine": {
        "description": "Wind generators and turbines",
        "tags": ["generator:source=wind"],
    },
    "bridge_railway": {
        "description": "Railway bridges crossing rivers or highways",
        "tags": ["bridge=yes", "railway=rail"],
    },
    "sports_circuit": {
        "description": "Motorsport racetracks, circuits or motocross courses",
        "tags": ["sport=motor", "leisure=track"],
    },
}


# ---------------------------------------------------------------------------
# Formatting Output
# ---------------------------------------------------------------------------

def format_summary_table(elements, max_display=20):
    """Format human-readable CLI table of discovered OSINT elements."""
    lines = []
    lines.append(f"{'#':<3} | {'Type':<8} | {'Name/ID':<30} | {'Lat':<10} | {'Lon':<10} | {'Dist(m)':<8} | Key Tags")
    lines.append("-" * 95)
    for idx, el in enumerate(elements[:max_display], 1):
        name = (el["name"][:28] + "..") if len(el["name"]) > 30 else el["name"]
        lat = f"{el['lat']:.5f}" if el['lat'] is not None else "N/A"
        lon = f"{el['lon']:.5f}" if el['lon'] is not None else "N/A"
        dist = str(el['distance_m']) if el['distance_m'] is not None else "-"
        key_tags = ", ".join(f"{k}={v}" for k, v in list(el["tags"].items())[:3] if k not in ("name", "source"))
        lines.append(f"{idx:<3} | {el['type']:<8} | {name:<30} | {lat:<10} | {lon:<10} | {dist:<8} | {key_tags}")
    if len(elements) > max_display:
        lines.append(f"... and {len(elements) - max_display} more items.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-Test Suite
# ---------------------------------------------------------------------------

def _self_test():
    """Verify Overpass QL generator, math calculations, and parsers offline."""
    print("[*] Running overpass_query.py self-test suite...")

    # 1. Haversine distance test (Eiffel Tower to Arc de Triomphe approx 1.6-1.7 km)
    # Eiffel Tower: 48.8584, 2.2945; Arc de Triomphe: 48.8738, 2.2950
    dist = haversine(48.8584, 2.2945, 48.8738, 2.2950)
    assert 1600 < dist < 1800, f"Haversine calculation unexpected: {dist}"
    print(f"  [+] Haversine distance accuracy: {dist:.1f} m [OK]")

    # 2. Tag filter parser test
    assert parse_tag_spec("man_made=tower") == '["man_made"="tower"]'
    assert parse_tag_spec("power!=line") == '["power"!="line"]'
    assert parse_tag_spec("tower:type~communication") == '["tower:type"~"communication"]'
    assert parse_tag_spec("!historic") == '[!"historic"]'
    assert parse_tag_spec('["amenity"="hospital"]') == '["amenity"="hospital"]'
    print("  [+] Tag parser expressions [OK]")

    # 3. Overpass QL script builder test (around and bbox)
    ql_around = build_overpass_ql(["man_made=chimney", "height>50"], around=(1000, 44.81, 20.46))
    assert "[out:json][timeout:35];" in ql_around
    assert 'node["man_made"="chimney"]["height>50"](around:1000,44.81,20.46);' in ql_around
    assert 'way["man_made"="chimney"]["height>50"](around:1000,44.81,20.46);' in ql_around
    assert 'relation["man_made"="chimney"]["height>50"](around:1000,44.81,20.46);' in ql_around
    print("  [+] Around query generator [OK]")

    ql_bbox = build_overpass_ql(["power=substation"], bbox=(44.0, 20.0, 44.5, 20.5))
    assert "(44.0,20.0,44.5,20.5)" in ql_bbox
    print("  [+] Bounding box query generator [OK]")

    ql_area = build_overpass_ql(["railway=industrial"], area_name="Berlin")
    assert 'area["name"="Berlin"]->.searchArea;' in ql_area
    assert "(area.searchArea)" in ql_area
    print("  [+] Area query generator [OK]")

    # 4. JSON result parsing & normalization test
    mock_overpass = {
        "elements": [
            {
                "type": "node",
                "id": 101,
                "lat": 44.8120,
                "lon": 20.4610,
                "tags": {"man_made": "chimney", "name": "Factory Chimney A"}
            },
            {
                "type": "way",
                "id": 202,
                "center": {"lat": 44.8150, "lon": 20.4650},
                "tags": {"man_made": "tower", "tower:type": "communication"}
            }
        ]
    }
    extracted = extract_elements(mock_overpass, center_lat=44.8100, center_lon=20.4600)
    assert len(extracted) == 2
    assert extracted[0]["id"] == 101
    assert extracted[0]["name"] == "Factory Chimney A"
    assert extracted[0]["distance_m"] is not None
    assert extracted[1]["lat"] == 44.8150
    assert "https://www.openstreetmap.org/way/202" == extracted[1]["osm_url"]
    print("  [+] Elements extraction and distance sorting [OK]")

    # 5. GeoJSON conversion test
    geojson = elements_to_geojson(extracted)
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) == 2
    assert geojson["features"][0]["geometry"]["coordinates"] == [20.4610, 44.8120]
    print("  [+] GeoJSON conversion [OK]")

    # 6. Presets dictionary check
    for p_name, p_data in PRESETS.items():
        assert "tags" in p_data and len(p_data["tags"]) > 0
        ql = build_overpass_ql(p_data["tags"], around=(500, 0, 0))
        assert "out center" in ql
    print("  [+] Presets integrity [OK]")

    print("[+] All overpass_query self-tests PASSED successfully!")


# ---------------------------------------------------------------------------
# Main CLI Interface
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="OpenStreetMap Overpass QL & Geocoding OSINT Tool")
    parser.add_argument("--test", action="store_true", help="Run comprehensive unit tests")
    subparsers = parser.add_subparsers(dest="subcommand")

    # geocode
    p_geo = subparsers.add_parser("geocode", help="Geocode query string using Nominatim")
    p_geo.add_argument("query", help="Place name, street or landmark")

    # reverse
    p_rev = subparsers.add_parser("reverse", help="Reverse geocode lat/lon coordinates")
    p_rev.add_argument("--lat", type=float, required=True, help="Latitude")
    p_rev.add_argument("--lon", type=float, required=True, help="Longitude")

    # around
    p_ar = subparsers.add_parser("around", help="Search OSM objects within radius of coordinates")
    p_ar.add_argument("--lat", type=float, required=True, help="Center latitude")
    p_ar.add_argument("--lon", type=float, required=True, help="Center longitude")
    p_ar.add_argument("--radius", type=int, default=3000, help="Search radius in meters (default: 3000)")
    p_ar.add_argument("--tags", nargs="+", required=True, help="Tag filters (e.g. man_made=tower)")
    p_ar.add_argument("--json", action="store_true", help="Output full JSON instead of table")
    p_ar.add_argument("--geojson", help="Save output to GeoJSON file path")

    # bbox
    p_bb = subparsers.add_parser("bbox", help="Search OSM objects in bounding box")
    p_bb.add_argument("--south", type=float, required=True)
    p_bb.add_argument("--west", type=float, required=True)
    p_bb.add_argument("--north", type=float, required=True)
    p_bb.add_argument("--east", type=float, required=True)
    p_bb.add_argument("--tags", nargs="+", required=True, help="Tag filters")
    p_bb.add_argument("--json", action="store_true", help="Output JSON")
    p_bb.add_argument("--geojson", help="Save output to GeoJSON file path")

    # preset
    p_pre = subparsers.add_parser("preset", help="Run CTF-tailored infrastructure presets")
    p_pre.add_argument("preset_name", choices=list(PRESETS.keys()), help="Name of preset")
    p_pre.add_argument("--lat", type=float, required=True, help="Center latitude")
    p_pre.add_argument("--lon", type=float, required=True, help="Center longitude")
    p_pre.add_argument("--radius", type=int, default=5000, help="Radius in meters")
    p_pre.add_argument("--geojson", help="Save output to GeoJSON file path")

    # raw query
    p_raw = subparsers.add_parser("query", help="Execute raw Overpass QL code")
    p_raw.add_argument("ql", help="Overpass QL string")

    args = parser.parse_args()

    if args.test:
        _self_test()
        sys.exit(0)

    if not args.subcommand:
        parser.print_help()
        sys.exit(1)

    if args.subcommand == "geocode":
        res = geocode(args.query)
        print(json.dumps(res, indent=2))

    elif args.subcommand == "reverse":
        res = reverse_geocode(args.lat, args.lon)
        print(json.dumps(res, indent=2))

    elif args.subcommand == "around":
        ql = build_overpass_ql(args.tags, around=(args.radius, args.lat, args.lon))
        print(f"[*] Executing Overpass Query:\n{ql}\n")
        data = execute_overpass_ql(ql)
        elements = extract_elements(data, center_lat=args.lat, center_lon=args.lon)
        if args.json:
            print(json.dumps(elements, indent=2))
        else:
            print(format_summary_table(elements))
        if args.geojson:
            gj = elements_to_geojson(elements)
            with open(args.geojson, "w", encoding="utf-8") as f:
                json.dump(gj, f, indent=2)
            print(f"[+] Saved GeoJSON with {len(elements)} items to {args.geojson}")

    elif args.subcommand == "bbox":
        bbox = (args.south, args.west, args.north, args.east)
        ql = build_overpass_ql(args.tags, bbox=bbox)
        print(f"[*] Executing Overpass Query:\n{ql}\n")
        data = execute_overpass_ql(ql)
        center_lat = (args.south + args.north) / 2.0
        center_lon = (args.west + args.east) / 2.0
        elements = extract_elements(data, center_lat=center_lat, center_lon=center_lon)
        if args.json:
            print(json.dumps(elements, indent=2))
        else:
            print(format_summary_table(elements))
        if args.geojson:
            gj = elements_to_geojson(elements)
            with open(args.geojson, "w", encoding="utf-8") as f:
                json.dump(gj, f, indent=2)
            print(f"[+] Saved GeoJSON with {len(elements)} items to {args.geojson}")

    elif args.subcommand == "preset":
        p = PRESETS[args.preset_name]
        print(f"[*] Running preset: {args.preset_name} ({p['description']})")
        ql = build_overpass_ql(p["tags"], around=(args.radius, args.lat, args.lon))
        data = execute_overpass_ql(ql)
        elements = extract_elements(data, center_lat=args.lat, center_lon=args.lon)
        print(format_summary_table(elements))
        if args.geojson:
            gj = elements_to_geojson(elements)
            with open(args.geojson, "w", encoding="utf-8") as f:
                json.dump(gj, f, indent=2)
            print(f"[+] Saved GeoJSON with {len(elements)} items to {args.geojson}")

    elif args.subcommand == "query":
        data = execute_overpass_ql(args.ql)
        elements = extract_elements(data)
        print(format_summary_table(elements))


if __name__ == "__main__":
    main()
