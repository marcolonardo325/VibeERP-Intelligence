"""
London Underground ÔÇô Real-Time Live Map Server
ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
ÔÇó Uses TfL Unified API directly (no Azure/Fabric dependency)
ÔÇó Nearest-neighbor station ordering per line (eliminates zig-zag)
ÔÇó Direction-aware interpolation (trains move forward along lines)
ÔÇó Background refresh every 10s, frontend polls every 1s
ÔÇó /api/arrivals/<naptanId> for TfL-style arrivals board
ÔÇó /api/maintenance for ERP asset maintenance dataset
ÔÇó /api/work-order for D365 F&O email via Graph API (optional)
"""

import hashlib
import json
import math
import os
import random
import re
import threading
import time
from datetime import datetime, timezone, timedelta

import requests as http_requests
from flask import Flask, jsonify, send_file, request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ÔöÇÔöÇ Config ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
ASSETS_FILE    = os.path.join(BASE_DIR, "vehicle_assets.json")
HTML_FILE      = os.path.join(BASE_DIR, "live_map.html")

TFL_API_BASE   = "https://api.tfl.gov.uk"
TFL_APP_KEY    = os.getenv("TFL_APP_KEY", "")
REFRESH_S      = 10
INTERSTATION_S = 120

# Graph API ÔÇô optional, for work-order emails
GRAPH_TENANT_ID     = os.getenv("GRAPH_TENANT_ID", "")
GRAPH_CLIENT_ID     = os.getenv("GRAPH_CLIENT_ID", "")
GRAPH_CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "")
GRAPH_SENDER_EMAIL  = os.getenv("GRAPH_SENDER_EMAIL", "")

LINE_COLORS = {
    "Bakerloo":           "#B36305",
    "Central":            "#E32017",
    "Circle":             "#FFD300",
    "District":           "#00782A",
    "Hammersmith & City": "#F3A9BB",
    "Jubilee":            "#A0A5A9",
    "Metropolitan":       "#9B0056",
    "Northern":           "#000000",
    "Piccadilly":         "#003688",
    "Victoria":           "#0098D4",
    "Waterloo & City":    "#95CDBA",
}

LINE_SLUGS = {
    "Bakerloo":           "bakerloo",
    "Central":            "central",
    "Circle":             "circle",
    "District":           "district",
    "Hammersmith & City": "hammersmith-city",
    "Jubilee":            "jubilee",
    "Metropolitan":       "metropolitan",
    "Northern":           "northern",
    "Piccadilly":         "piccadilly",
    "Victoria":           "victoria",
    "Waterloo & City":    "waterloo-city",
}

TRAIN_MODELS = {
    "Bakerloo":           {"model": "1972 Stock",  "manufacturer": "Metro-Cammell"},
    "Central":            {"model": "1992 Stock",  "manufacturer": "ABB / BREL"},
    "Circle":             {"model": "S7 Stock",    "manufacturer": "Bombardier"},
    "District":           {"model": "S7 Stock",    "manufacturer": "Bombardier"},
    "Hammersmith & City": {"model": "S7 Stock",    "manufacturer": "Bombardier"},
    "Jubilee":            {"model": "1996 Stock",  "manufacturer": "Alstom"},
    "Metropolitan":       {"model": "S8 Stock",    "manufacturer": "Bombardier"},
    "Northern":           {"model": "1995 Stock",  "manufacturer": "Alstom"},
    "Piccadilly":         {"model": "1973 Stock",  "manufacturer": "Metro-Cammell"},
    "Victoria":           {"model": "2009 Stock",  "manufacturer": "Bombardier"},
    "Waterloo & City":    {"model": "1992 Stock",  "manufacturer": "ABB / BREL"},
}

# ── Globals ──────────────────────────────────────────────────────────────────
app = Flask(__name__)

cached_tracks       = {}      # lineName -> [[lat,lon],...]  (station-based, for interpolation)
cached_tracks_geo   = {}      # GeoJSON FeatureCollection    (real geometry, for map rendering)
line_track_coords   = {}      # lineName -> [[lon,lat],...] merged track coords (for snapping)
cached_stations     = []
station_lookup      = {}
line_stations_ord   = {}
station_index       = {}

data_lock = threading.Lock()
live_data = {"trains": [], "fetch_epoch": 0, "count": 0}
maintenance_data = {}


# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
# TfL API helper
# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
def tfl_get(path, params=None):
    """Call TfL Unified API.  Adds app_key if configured."""
    p = dict(params or {})
    if TFL_APP_KEY:
        p["app_key"] = TFL_APP_KEY
    r = http_requests.get(f"{TFL_API_BASE}{path}", params=p, timeout=30)
    r.raise_for_status()
    return r.json()


# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
# Nearest-Neighbour Station Ordering
# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
def _geo_dist(a, b):
    return math.sqrt((a["lat"] - b["lat"])**2 + (a["lon"] - b["lon"])**2)


def order_stations_nn(stations):
    if len(stations) <= 2:
        return list(stations)

    best_d, best_pair = 0, (0, 1)
    for i in range(len(stations)):
        for j in range(i + 1, len(stations)):
            d = _geo_dist(stations[i], stations[j])
            if d > best_d:
                best_d, best_pair = d, (i, j)

    remaining = list(stations)
    current = remaining.pop(best_pair[0])
    ordered = [current]

    while remaining:
        nearest = min(remaining, key=lambda s: _geo_dist(s, current))
        ordered.append(nearest)
        remaining.remove(nearest)
        current = nearest
    return ordered


# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
# Static Data  (stations + tracks via TfL API)
# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
def load_static_data():
    global cached_tracks, cached_tracks_geo, cached_stations, station_lookup
    global line_stations_ord, station_index

    print("\U0001f4cd Loading stations from TfL API \u2026")
    all_stations = {}

    for line_name, slug in LINE_SLUGS.items():
        try:
            stops = tfl_get(f"/Line/{slug}/StopPoints")
            stns = []
            for s in stops:
                lat, lon = s.get("lat"), s.get("lon")
                if lat and lon:
                    nap = s["naptanId"]
                    if nap in all_stations:
                        if line_name not in all_stations[nap].get("lines", []):
                            all_stations[nap].setdefault("lines", []).append(line_name)
                        stn = all_stations[nap]
                    else:
                        stn = {
                            "naptanId": nap,
                            "StationName": s.get("commonName", ""),
                            "lat": lat,
                            "lon": lon,
                            "lines": [line_name],
                        }
                        all_stations[nap] = stn
                    stns.append(stn)

            ordered = order_stations_nn(stns)
            line_stations_ord[line_name] = ordered
            center = [[s["lat"], s["lon"]] for s in ordered]
            cached_tracks[line_name] = center

            for i, s in enumerate(ordered):
                station_index[(line_name, s["naptanId"])] = i

        except Exception as e:
            print(f"   \u26a1 {line_name}: {e}")

    cached_stations = list(all_stations.values())
    station_lookup = all_stations

    total_pts = sum(len(v) for v in cached_tracks.values())
    print(f"   \u2713 {len(cached_stations)} stations | "
          f"{len(cached_tracks)} lines | {total_pts} track points (NN ordered)")

    # ── Fetch real track geometry from TfL Route/Sequence API ──
    print("\U0001f6e4  Loading route geometry \u2026")

    def _catmull_rom_smooth(coords, subdivisions=4):
        """Centripetal Catmull-Rom spline for smoother track curves."""
        if len(coords) < 3:
            return coords
        pts = [coords[0]] + coords + [coords[-1]]  # ghost endpoints
        out = []
        for i in range(1, len(pts) - 2):
            p0, p1, p2, p3 = pts[i-1], pts[i], pts[i+1], pts[i+2]
            for t_idx in range(subdivisions):
                t = t_idx / subdivisions
                t2, t3 = t*t, t*t*t
                x = 0.5*((-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3
                         +(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2
                         +(-p0[0]+p2[0])*t + 2*p1[0])
                y = 0.5*((-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3
                         +(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2
                         +(-p0[1]+p2[1])*t + 2*p1[1])
                out.append([round(x, 6), round(y, 6)])
        out.append(coords[-1])
        return out

    def _seg_length(coords):
        """Geographic length of a segment (sum of Euclidean deltas)."""
        d = 0
        for i in range(1, len(coords)):
            dx = coords[i][0] - coords[i-1][0]
            dy = coords[i][1] - coords[i-1][1]
            d += (dx*dx + dy*dy) ** 0.5
        return d

    MIN_SEGMENT_PTS = 10          # drop stray stubs (< 10 raw points)
    MIN_SEGMENT_LEN = 0.05        # ~5.5 km at London latitude

    # Real London Tube map: number of unique route geometries per line.
    # TfL returns every (western branch × eastern branch) combination,
    # creating many duplicate/subset segments.  We keep only the N longest
    # after de-duplicating exact (start,end) pairs.
    EXPECTED_BRANCHES = {
        "Bakerloo":           1,   # Elephant & Castle → Harrow & Wealdstone
        "Central":            2,   # West Ruislip → Epping | Woodford
        "Circle":             1,   # Hammersmith loop → Edgware Road
        "District":           3,   # Ealing Bwy / Richmond / Wimbledon → Upminster
        "Hammersmith & City": 1,   # Hammersmith → Barking
        "Jubilee":            1,   # Stanmore → Stratford
        "Metropolitan":       4,   # Chesham / Amersham / Watford / Uxbridge → Aldgate
        "Northern":           4,   # Morden → High Barnet / Edgware / Mill Hill East + Battersea extension
        "Piccadilly":         3,   # Uxbridge / Heathrow T5 / T4 → Cockfosters
        "Victoria":           1,   # Brixton → Walthamstow Central
        "Waterloo & City":    1,   # Waterloo → Bank
    }

    def _pt_dist(a, b):
        return ((a[0]-b[0])**2 + (a[1]-b[1])**2) ** 0.5

    def _merge_line_segments(all_segs, max_branches):
        """Remove duplicate and subset segments, keep only unique branches.
        Step 1: dedup by (start,end) pair — keep longest for each pair.
        Step 2: keep the top N longest (matching the real tube map branch count).
        """
        if len(all_segs) <= 1:
            return all_segs

        EP_TOL = 0.002   # ~220m — same endpoint

        # Step 1: Dedup by (start, end) pair
        groups = {}
        for seg in all_segs:
            sk, ek = tuple(seg[0]), tuple(seg[-1])
            matched_key = None
            for key in groups:
                ks, ke = key
                if _pt_dist(sk, ks) < EP_TOL and _pt_dist(ek, ke) < EP_TOL:
                    matched_key = key
                    break
            if matched_key:
                if len(seg) > len(groups[matched_key]):
                    groups[matched_key] = seg
            else:
                groups[(sk, ek)] = seg
        deduped = list(groups.values())

        # Step 2: Keep only the N longest segments (real tube map branches)
        deduped.sort(key=len, reverse=True)
        return deduped[:max_branches]

    features = []
    geo_pts = 0
    skipped = 0
    merged_away = 0
    for line_name, slug in LINE_SLUGS.items():
        color = LINE_COLORS.get(line_name, "#999")
        is_short_line = slug == "waterloo-city"   # only 2 stations
        try:
            seq = tfl_get(f"/Line/{slug}/Route/Sequence/outbound")
            # Collect all raw segments for this line
            raw_segs = []
            for ls_raw in seq.get("lineStrings", []):
                parsed = json.loads(ls_raw) if isinstance(ls_raw, str) else ls_raw
                # TfL wraps coordinates: [[[lon,lat],[lon,lat],...]] — unwrap
                if (parsed and isinstance(parsed[0], list)
                        and len(parsed[0]) > 0
                        and isinstance(parsed[0][0], list)):
                    sub_paths = parsed          # list of coord arrays
                else:
                    sub_paths = [parsed]         # already flat
                for coords in sub_paths:
                    if len(coords) >= 2:
                        raw_segs.append(coords)

            # Merge: remove duplicates & subsets, keep unique branches
            before = len(raw_segs)
            max_br = EXPECTED_BRANCHES.get(line_name, 1)
            merged = _merge_line_segments(raw_segs, max_br)
            removed = before - len(merged)
            merged_away += removed
            if removed:
                print(f"      {line_name}: {before} → {len(merged)} segments"
                      f" ({removed} removed)")

            for coords in merged:
                # Filter out short stray stubs (exempt Waterloo & City)
                if not is_short_line:
                    if len(coords) < MIN_SEGMENT_PTS or _seg_length(coords) < MIN_SEGMENT_LEN:
                        skipped += 1
                        continue
                # Smooth with Catmull-Rom spline
                smooth = _catmull_rom_smooth(coords, subdivisions=8)
                features.append({
                    "type": "Feature",
                    "properties": {"lineName": line_name, "color": color},
                    "geometry": {"type": "LineString", "coordinates": smooth},
                })
                geo_pts += len(smooth)
        except Exception as e:
            print(f"   \u26a1 Route {line_name}: {e}")

    cached_tracks_geo = {"type": "FeatureCollection", "features": features}
    print(f"   \u2713 {len(features)} route segments | {geo_pts} geometry points"
          f" (merged {merged_away} dupes/subsets, skipped {skipped} stubs)")

    # ── Build per-line merged coordinate list for train snapping ──
    global line_track_coords
    line_track_coords = {}
    for feat in features:
        ln = feat["properties"]["lineName"]
        line_track_coords.setdefault(ln, []).extend(feat["geometry"]["coordinates"])


# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
# Live Trains  (TfL Arrivals API)
# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
PLACEHOLDER_VIDS = {"000", "", "0"}


def fetch_live_trains():
    all_slugs = ",".join(LINE_SLUGS.values())
    arrivals = tfl_get(f"/Line/{all_slugs}/Arrivals")

    # Keep nearest arrival (smallest timeToStation) per vehicle.
    # Some lines (e.g. Northern) return vehicleId="000" for every record.
    # For those, use naptanId+towards as the dedup key so each
    # station/direction pair becomes a separate train on the map.
    by_key = {}
    for a in arrivals:
        vid = a.get("vehicleId", "")
        line = a.get("lineName", "")
        if vid in PLACEHOLDER_VIDS:
            key = f"_syn_{line}_{a.get('naptanId','')}_{a.get('towards','')}"
        else:
            key = f"{line}_{vid}"
        tts = a.get("timeToStation", 9999)
        if key not in by_key or tts < by_key[key].get("timeToStation", 9999):
            by_key[key] = a
            by_key[key]["_resolved_vid"] = key

    trains = []
    for a in by_key.values():
        nap = a.get("naptanId", "")
        stn = station_lookup.get(nap, {})
        vid = a.get("vehicleId", "")
        line = a.get("lineName", "")
        # trainKey must be unique across all lines (vehicleIds collide cross-line)
        train_key = a.get("_resolved_vid", f"{line}_{vid}")
        trains.append({
            "vehicleId": vid,
            "trainKey":  train_key,
            "lineName":  line,
            "naptanId":  nap,
            "stationName": a.get("stationName", ""),
            "direction": a.get("direction", ""),
            "towards":   a.get("towards", ""),
            "timeToStation": a.get("timeToStation", 0),
            "destinationName": a.get("destinationName", ""),
            "timestamp": a.get("timestamp", ""),
            "stationLat": stn.get("lat", 0),
            "stationLon": stn.get("lon", 0),
        })
    return trains


# ═══════════════════════════════════════════════════════════════════════════════
# Snap to Track  (project point onto nearest track segment)
# ═══════════════════════════════════════════════════════════════════════════════
def snap_to_track_line(lon, lat, line_name):
    """Snap a (lon, lat) point to the closest position on the track geometry."""
    coords = line_track_coords.get(line_name)
    if not coords or len(coords) < 2:
        return lon, lat
    best_d2 = float('inf')
    best_pt = (lon, lat)
    for i in range(len(coords) - 1):
        ax, ay = coords[i]
        bx, by = coords[i + 1]
        dx, dy = bx - ax, by - ay
        len2 = dx * dx + dy * dy
        if len2 < 1e-14:
            continue
        t = max(0.0, min(1.0, ((lon - ax) * dx + (lat - ay) * dy) / len2))
        px, py = ax + t * dx, ay + t * dy
        d2 = (lon - px) ** 2 + (lat - py) ** 2
        if d2 < best_d2:
            best_d2 = d2
            best_pt = (px, py)
    return best_pt


# ═══════════════════════════════════════════════════════════════════════════════
# Position Interpolation  (direction-aware)
# ═══════════════════════════════════════════════════════════════════════════════
_prev_emit = {}   # trainKey -> (lon, lat, naptanId)  — forward-only cache

def interpolate_trains(raw, elapsed_s):
    global _prev_emit
    out = []
    active_keys = set()
    for t in raw:
        line   = t["lineName"]
        naptan = t["naptanId"]
        tts    = max(0, t["timeToStation"] - elapsed_s)
        target_lat, target_lon = t["stationLat"], t["stationLon"]

        idx     = station_index.get((line, naptan))
        ordered = line_stations_ord.get(line, [])
        n       = len(ordered)

        if idx is None or n < 2 or tts <= 0:
            lat, lon = target_lat, target_lon
        else:
            towards = (t.get("towards") or "").lower()
            towards_idx = None
            for i, s in enumerate(ordered):
                sn = s.get("StationName", "").lower()
                if towards and (towards in sn or sn.startswith(towards)):
                    towards_idx = i
                    break

            if towards_idx is not None:
                prev_idx = idx - 1 if towards_idx >= idx else idx + 1
            else:
                mid = n // 2
                if t.get("direction") == "inbound":
                    prev_idx = idx - 1 if idx < mid else idx + 1
                else:
                    prev_idx = idx + 1 if idx < mid else idx - 1

            prev_idx = max(0, min(prev_idx, n - 1))
            if prev_idx == idx:
                prev_idx = max(0, idx - 1)

            prev   = ordered[prev_idx]
            target = ordered[idx]
            progress = max(0.0, min(1.0, 1 - tts / INTERSTATION_S))
            lat = prev["lat"] + (target["lat"] - prev["lat"]) * progress
            lon = prev["lon"] + (target["lon"] - prev["lon"]) * progress

        # ── Compute bearing for directional flow ──
        bearing = 0
        if idx is not None and n >= 2:
            if idx == 0:
                a_s, b_s = ordered[0], ordered[1]
            elif idx >= n - 1:
                a_s, b_s = ordered[n - 2], ordered[n - 1]
            else:
                a_s, b_s = ordered[idx - 1], ordered[idx + 1]
            d_lat = b_s["lat"] - a_s["lat"]
            d_lon = b_s["lon"] - a_s["lon"]
            bearing = math.degrees(math.atan2(d_lon, d_lat)) % 360
            # Inbound trains travel in the opposite direction
            if t.get("direction") == "inbound":
                bearing = (bearing + 180) % 360

        # ── Snap position onto track geometry ──
        snapped_lon, snapped_lat = snap_to_track_line(lon, lat, line)

        # ── Forward-only: prevent backward jumps between polls ──
        train_key = t.get("trainKey", t["vehicleId"])
        active_keys.add(train_key)
        prev = _prev_emit.get(train_key)
        if prev is not None:
            p_lon, p_lat, p_nap = prev
            if p_nap == naptan:  # same destination → must not move further away
                old_d2 = (p_lon - target_lon) ** 2 + (p_lat - target_lat) ** 2
                new_d2 = (snapped_lon - target_lon) ** 2 + (snapped_lat - target_lat) ** 2
                if new_d2 > old_d2 + 1e-10:
                    snapped_lon, snapped_lat = p_lon, p_lat
        _prev_emit[train_key] = (snapped_lon, snapped_lat, naptan)

        out.append({
            "vehicleId": t["vehicleId"], "trainKey": train_key,
            "lineName": line,
            "stationName": t["stationName"],
            "direction": t.get("direction", ""),
            "towards": t.get("towards", ""),
            "timeToStation": round(tts),
            "lat": round(snapped_lat, 6), "lon": round(snapped_lon, 6),
            "bearing": round(bearing, 1),
        })

    # Clean departed trains from cache
    for k in list(_prev_emit):
        if k not in active_keys:
            del _prev_emit[k]
    return out


# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
# ERP Asset Maintenance  (deterministic, seeded by vehicleId)
# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
def _seed(vid):
    return int(hashlib.md5(vid.encode()).hexdigest()[:8], 16)


def generate_maintenance_dataset(trains):
    global maintenance_data

    if os.path.exists(ASSETS_FILE):
        with open(ASSETS_FILE, encoding="utf-8") as f:
            maintenance_data = json.load(f)
        if {t["vehicleId"] for t in trains}.issubset(maintenance_data.keys()):
            print(f"   Ô£à {len(maintenance_data)} asset records loaded")
            return

    seen  = set()
    today = datetime(2026, 4, 16)

    for t in trains:
        vid = t["vehicleId"]
        if vid in seen:
            continue
        seen.add(vid)
        rng  = random.Random(_seed(vid))
        line = t["lineName"]
        info = TRAIN_MODELS.get(line, {"model": "Unknown", "manufacturer": "Unknown"})

        mileage = rng.randint(180_000, 1_400_000)
        daily   = rng.randint(180, 420)
        cond    = rng.randint(42, 99)
        wheel   = rng.randint(5, 78)
        svc_ago = rng.randint(3, 180)
        svc_in  = rng.randint(-10, 120)
        open_wo = rng.randint(0, 5)
        crit    = 1 if cond < 55 else (rng.choice([0, 0, 0, 1]) if cond < 70 else 0)

        def comp(thr=75):
            v = rng.randint(30, 100)
            return ("Good" if v >= thr else
                    "Fair" if v >= 55 else
                    "Needs Attention" if v >= 40 else "Critical")

        maintenance_data[vid] = {
            "vehicleId": vid, "lineName": line, "assetType": "Rolling Stock",
            "manufacturer": info["manufacturer"], "model": info["model"],
            "yearManufactured": rng.randint(2005, 2022),
            "totalMileageKm": mileage, "dailyAvgKm": daily,
            "runningHours": round(mileage / (daily * 365 / rng.uniform(8, 14)), 1),
            "overallConditionPct": cond,
            "lastServiceDate": (today - timedelta(days=svc_ago)).strftime("%Y-%m-%d"),
            "nextServiceDue":  (today + timedelta(days=svc_in)).strftime("%Y-%m-%d"),
            "daysUntilService": svc_in,
            "serviceStatus": ("Overdue" if svc_in < 0 else
                              "Due Soon" if svc_in < 14 else "On Schedule"),
            "brakeCondition": comp(70), "doorSystemStatus": comp(80),
            "hvacStatus": rng.choice(["Normal", "Normal", "Normal", "Reduced", "Offline"]),
            "tractionMotor": comp(72), "wheelWearPct": wheel, "bogieCondition": comp(75),
            "openWorkOrders": open_wo, "criticalAlerts": crit,
            "pendingParts": rng.randint(0, 3),
            "lastInspectionDate": (today - timedelta(days=rng.randint(1, 60))).strftime("%Y-%m-%d"),
            "lineColor": LINE_COLORS.get(line, "#999"),
        }

    with open(ASSETS_FILE, "w", encoding="utf-8") as f:
        json.dump(maintenance_data, f, indent=2)
    print(f"   Ô£à Generated {len(maintenance_data)} asset records")


# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
# Background Refresh
# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
class TrainRefresher(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)

    def run(self):
        global live_data
        while True:
            try:
                raw = fetch_live_trains()
                with data_lock:
                    live_data = {
                        "trains": raw,
                        "fetch_epoch": time.time(),
                        "count": len(raw),
                    }
            except Exception as e:
                print(f"ÔÜá TfL refresh: {e}")
            time.sleep(REFRESH_S)


# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
# Graph API Helper  (plain HTTP ÔÇô no Azure SDK required)
# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
def get_graph_token():
    if not all([GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET]):
        return None
    r = http_requests.post(
        f"https://login.microsoftonline.com/{GRAPH_TENANT_ID}/oauth2/v2.0/token",
        data={
            "grant_type":    "client_credentials",
            "client_id":     GRAPH_CLIENT_ID,
            "client_secret": GRAPH_CLIENT_SECRET,
            "scope":         "https://graph.microsoft.com/.default",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
# Flask Routes
# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
@app.route("/")
def index():
    return send_file(HTML_FILE)


@app.route("/api/tracks")
def api_tracks():
    return jsonify(cached_tracks_geo)


@app.route("/api/stations")
def api_stations():
    return jsonify(cached_stations)


@app.route("/api/colors")
def api_colors():
    return jsonify(LINE_COLORS)


@app.route("/api/trains")
def api_trains():
    with data_lock:
        snap = live_data.copy()
    elapsed = time.time() - snap["fetch_epoch"] if snap["fetch_epoch"] else 0
    trains  = interpolate_trains(snap["trains"], elapsed)
    # Per-line counts
    line_counts = {}
    for t in trains:
        line_counts[t["lineName"]] = line_counts.get(t["lineName"], 0) + 1
    return jsonify({
        "trains": trains, "count": len(trains),
        "lineCounts": line_counts,
        "fetchAge": round(elapsed, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/api/line-status")
def api_line_status():
    """Return TfL service status for all tube lines."""
    try:
        all_slugs = ",".join(LINE_SLUGS.values())
        data = tfl_get(f"/Line/{all_slugs}/Status")
        result = []
        for line in data:
            name = line.get("name", "")
            statuses = line.get("lineStatuses", [])
            severity = statuses[0].get("statusSeverity", 0) if statuses else 0
            desc = statuses[0].get("statusSeverityDescription", "Unknown") if statuses else "Unknown"
            reason = statuses[0].get("reason", "") if statuses else ""
            result.append({
                "lineName": name,
                "severity": severity,
                "status": desc,
                "reason": reason,
            })
        return jsonify(result)
    except Exception as e:
        return jsonify([]), 500


@app.route("/api/arrivals/<station_id>")
def api_arrivals(station_id):
    if not re.match(r'^[A-Za-z0-9]+$', station_id):
        return jsonify([]), 400
    try:
        arrivals = tfl_get(f"/StopPoint/{station_id}/Arrivals")
        result = []
        for a in arrivals:
            result.append({
                "vehicleId":   a.get("vehicleId", ""),
                "lineName":    a.get("lineName", ""),
                "towards":     a.get("towards", ""),
                "direction":   a.get("direction", ""),
                "timeToStation": a.get("timeToStation", 0),
                "platformName":  a.get("platformName", ""),
                "destinationName": a.get("destinationName", ""),
            })
        result.sort(key=lambda x: (x["lineName"], x["timeToStation"]))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/maintenance")
def api_maintenance():
    return jsonify(maintenance_data)


@app.route("/api/maintenance/<vid>")
def api_maintenance_detail(vid):
    a = maintenance_data.get(vid)
    return jsonify(a) if a else (jsonify({"error": "not found"}), 404)


@app.route("/api/fleet-health")
def api_fleet_health():
    assets = list(maintenance_data.values())
    if not assets:
        return jsonify({})
    conds = [a["overallConditionPct"] for a in assets]
    return jsonify({
        "totalVehicles":   len(assets),
        "avgCondition":    round(sum(conds) / len(conds), 1),
        "critical":        sum(1 for a in assets if a["overallConditionPct"] < 55),
        "needsAttention":  sum(1 for a in assets if 55 <= a["overallConditionPct"] < 70),
        "good":            sum(1 for a in assets if a["overallConditionPct"] >= 70),
        "overdueService":  sum(1 for a in assets if a["serviceStatus"] == "Overdue"),
        "dueSoon":         sum(1 for a in assets if a["serviceStatus"] == "Due Soon"),
        "totalWorkOrders": sum(a["openWorkOrders"] for a in assets),
        "totalAlerts":     sum(a["criticalAlerts"] for a in assets),
    })


# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
# Work Order  +  Email (Graph API)
# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
def build_work_order_email(wo_number, asset):
    cond = asset["overallConditionPct"]
    cond_color = "#00e676" if cond >= 70 else ("#ffab00" if cond >= 55 else "#ff1744")
    svc_color  = ("#00e676" if asset["serviceStatus"] == "On Schedule" else
                  "#ffab00" if asset["serviceStatus"] == "Due Soon" else "#ff1744")

    def sc(s):
        if s in ("Good", "Normal", "On Schedule"):
            return "#00e676"
        if s in ("Fair", "Reduced", "Due Soon"):
            return "#ffab00"
        return "#ff1744"

    components = [
        ("Brakes", asset["brakeCondition"]),
        ("Door System", asset["doorSystemStatus"]),
        ("HVAC", asset["hvacStatus"]),
        ("Traction Motor", asset["tractionMotor"]),
        ("Bogie", asset["bogieCondition"]),
    ]
    comp_rows = ""
    for name, status in components:
        c = sc(status)
        comp_rows += (
            f'<tr><td style="padding:8px 12px;border-bottom:1px solid #2a2a4a;'
            f'color:#ccc">{name}</td><td style="padding:8px 12px;text-align:center">'
            f'<span style="background:{c}22;color:{c};padding:3px 10px;'
            f'border-radius:10px;font-size:12px;font-weight:600">{status}</span>'
            f'</td></tr>'
        )

    line_color = asset.get("lineColor", "#0098D4")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return (
        f'<div style="font-family:\'Segoe UI\',Arial,sans-serif;max-width:640px;'
        f'margin:0 auto;background:#0a0a1a;color:#e0e0e0">'
        f'<div style="background:linear-gradient(135deg,#0a0a1a,#1a1a3e);'
        f'padding:24px 32px;border-bottom:3px solid {line_color}">'
        f'<table width="100%"><tr>'
        f'<td><span style="font-size:22px;font-weight:700;letter-spacing:.5px">'
        f'D365 F&amp;O &ndash; Work Order</span></td>'
        f'<td style="text-align:right"><span style="background:#E32017;color:#fff;'
        f'padding:4px 12px;border-radius:12px;font-size:11px;font-weight:700">'
        f'MAINTENANCE</span></td></tr></table>'
        f'<div style="margin-top:8px;font-size:13px;color:#888">{now_str}</div></div>'
        f'<div style="padding:24px 32px">'
        f'<table width="100%" style="margin-bottom:20px"><tr>'
        f'<td style="background:{line_color};color:#fff;padding:10px 16px;'
        f'border-radius:8px;font-weight:700;font-size:18px;text-align:center;'
        f'width:180px">{wo_number}</td>'
        f'<td style="padding-left:16px">'
        f'<div style="font-size:16px;font-weight:700">Train {asset["vehicleId"]}</div>'
        f'<div style="font-size:13px;color:#888">{asset["lineName"]} Line &middot; '
        f'{asset["model"]} &middot; {asset["manufacturer"]}</div></td></tr></table>'
        f'<div style="background:#111;border-radius:8px;padding:16px;margin-bottom:20px">'
        f'<div style="font-size:11px;color:#888;text-transform:uppercase;'
        f'letter-spacing:1px;margin-bottom:12px">Asset Summary</div>'
        f'<table width="100%" style="border-collapse:collapse">'
        f'<tr><td style="padding:6px 12px;color:#888;width:40%">Overall Condition</td>'
        f'<td style="padding:6px 12px;font-weight:700;color:{cond_color}">{cond}%</td></tr>'
        f'<tr><td style="padding:6px 12px;color:#888">Service Status</td>'
        f'<td style="padding:6px 12px;font-weight:700;color:{svc_color}">'
        f'{asset["serviceStatus"]}</td></tr>'
        f'<tr><td style="padding:6px 12px;color:#888">Total Mileage</td>'
        f'<td style="padding:6px 12px">{asset["totalMileageKm"]:,} km</td></tr>'
        f'<tr><td style="padding:6px 12px;color:#888">Daily Average</td>'
        f'<td style="padding:6px 12px">{asset["dailyAvgKm"]} km</td></tr>'
        f'<tr><td style="padding:6px 12px;color:#888">Year Manufactured</td>'
        f'<td style="padding:6px 12px">{asset["yearManufactured"]}</td></tr>'
        f'<tr><td style="padding:6px 12px;color:#888">Last Service</td>'
        f'<td style="padding:6px 12px">{asset["lastServiceDate"]}</td></tr>'
        f'<tr><td style="padding:6px 12px;color:#888">Next Service Due</td>'
        f'<td style="padding:6px 12px;font-weight:700;color:{svc_color}">'
        f'{asset["nextServiceDue"]}</td></tr>'
        f'<tr><td style="padding:6px 12px;color:#888">Wheel Wear</td>'
        f'<td style="padding:6px 12px">{asset["wheelWearPct"]}%</td></tr>'
        f'</table></div>'
        f'<div style="background:#111;border-radius:8px;padding:16px;margin-bottom:20px">'
        f'<div style="font-size:11px;color:#888;text-transform:uppercase;'
        f'letter-spacing:1px;margin-bottom:12px">Component Status</div>'
        f'<table width="100%" style="border-collapse:collapse">'
        f'<tr style="background:rgba(255,255,255,.05)">'
        f'<th style="padding:8px 12px;text-align:left;color:#888;font-size:11px">Component</th>'
        f'<th style="padding:8px 12px;text-align:center;color:#888;font-size:11px">Status</th></tr>'
        f'{comp_rows}</table></div>'
        f'<div style="background:#111;border-radius:8px;padding:16px;margin-bottom:20px">'
        f'<div style="font-size:11px;color:#888;text-transform:uppercase;'
        f'letter-spacing:1px;margin-bottom:12px">Action Required</div>'
        f'<table width="100%" style="border-collapse:collapse">'
        f'<tr><td style="padding:6px 12px;color:#888">Open Work Orders</td>'
        f'<td style="padding:6px 12px;font-weight:700">{asset["openWorkOrders"]}</td></tr>'
        f'<tr><td style="padding:6px 12px;color:#888">Critical Alerts</td>'
        f'<td style="padding:6px 12px;font-weight:700;color:'
        f'{"#ff1744" if asset["criticalAlerts"] > 0 else "#00e676"}">'
        f'{asset["criticalAlerts"]}</td></tr>'
        f'<tr><td style="padding:6px 12px;color:#888">Pending Parts</td>'
        f'<td style="padding:6px 12px">{asset["pendingParts"]}</td></tr>'
        f'<tr><td style="padding:6px 12px;color:#888">Running Hours</td>'
        f'<td style="padding:6px 12px">{asset["runningHours"]}h</td></tr>'
        f'</table></div>'
        f'<div style="text-align:center;padding:16px 0;font-size:11px;color:#555">'
        f'Generated by TfL Live Operations Dashboard &middot; D365 Finance &amp; Operations'
        f'</div></div></div>'
    )


@app.route("/api/work-order", methods=["POST"])
def create_work_order():
    data = request.get_json()
    vid  = data.get("vehicleId") if data else None
    if not vid or vid not in maintenance_data:
        return jsonify({"error": "Vehicle not found"}), 404

    asset     = maintenance_data[vid]
    wo_number = f"WO-{vid}-{int(time.time())}"
    html      = build_work_order_email(wo_number, asset)

    # Always save locally
    wo_file = os.path.join(BASE_DIR, "work_orders.json")
    try:
        existing = json.load(open(wo_file, encoding="utf-8")) if os.path.exists(wo_file) else []
    except Exception:
        existing = []

    existing.append({
        "workOrder": wo_number, "vehicleId": vid,
        "lineName": asset["lineName"],
        "condition": asset["overallConditionPct"],
        "serviceStatus": asset["serviceStatus"],
        "created": datetime.now(timezone.utc).isoformat(),
    })
    with open(wo_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    # Attempt email via Graph API (best-effort)
    email_sent  = False
    email_error = ""
    try:
        token = get_graph_token()
        if token:
            payload = {
                "message": {
                    "subject": (f"[D365 F&O] Work Order {wo_number} ÔÇô "
                                f"Train {vid} ({asset['lineName']} Line)"),
                    "body": {"contentType": "HTML", "content": html},
                    "toRecipients": [
                        {"emailAddress": {"address": GRAPH_SENDER_EMAIL}}
                    ],
                }
            }
            resp = http_requests.post(
                f"https://graph.microsoft.com/v1.0/users/{GRAPH_SENDER_EMAIL}/sendMail",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            if resp.status_code in (200, 202):
                email_sent = True
            else:
                email_error = f"Graph API {resp.status_code}: {resp.text[:200]}"
        else:
            email_error = "Graph API not configured"
    except Exception as e:
        email_error = str(e)[:120]

    return jsonify({
        "success": True, "workOrder": wo_number,
        "emailSent": email_sent, "emailError": email_error or None,
    })


# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
# Main
# ÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉÔòÉ
if __name__ == "__main__":
    load_static_data()

    print("­ƒôí Initial train fetch ÔÇª")
    try:
        initial = fetch_live_trains()
        live_data = {
            "trains": initial,
            "fetch_epoch": time.time(),
            "count": len(initial),
        }
        print(f"   Ô£à {len(initial)} vehicles")
    except Exception as e:
        print(f"   ÔÜá {e}")
        initial = []

    generate_maintenance_dataset(initial)
    TrainRefresher().start()

    graph_ok = ("Ô£à" if all([GRAPH_TENANT_ID, GRAPH_CLIENT_ID, GRAPH_CLIENT_SECRET])
                else "ÔÜá not configured")
    print(f"\n{'='*56}")
    print(f"  ­ƒîÉ  http://localhost:5050")
    print(f"  ­ƒöä  TfL API ÔåÆ {REFRESH_S}s refresh | 1s poll | 60fps")
    print(f"  ­ƒôè  {len(maintenance_data)} vehicle assets")
    print(f"  ­ƒôº  Graph API: {graph_ok}")
    print(f"{'='*56}\n")

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5050")), debug=False, threaded=True)
