---
name: ctf-osint
description: >-
  Open-source intelligence CTF challenges — find a place, person, event, or hidden
  page from public data. Use for geolocation (signage/feature pivots via
  OpenStreetMap + Google Street View), spatial data mining (Overpass QL queries for
  chimneys, towers, substations), chronolocation & shadow math (SunCalc, solar elevation,
  azimuth, time/latitude solving), global infrastructure heuristics (bollards, utility poles,
  license plates, Street View camera gens & car meta), passive domain & endpoint discovery
  (Certificate Transparency crt.sh, Wayback CDX API), user & developer footprints
  (unmasked Git emails, Gravatar MD5, Strava/Komoot tracks, Bluesky ATProto), anti-bot scraping
  (Playwright headed + persistent profile to beat Cloudflare), image OCR (tesseract), and
  telemetry geoint (MAVLink track plotting). Triggers on: "osint", "geolocation",
  "geoint", "street view", "OpenStreetMap", "OSM", "Overpass", "SunCalc", "chronolocation",
  "shadow", "shadow ratio", "solar elevation", "bollard", "delineator", "utility pole",
  "geoguessr", "crt.sh", "Wayback", "CDX", "reverse image", "Yandex", "TinEye",
  "tesseract", "OCR", "CTFtime", "username", "find this person", "find this place",
  "Strava", "Komoot", "MAVLink", "Playwright", "stuck", "how to approach",
  "methodology", "next step", "where to start", "what3words", "boarding pass".
---

# CTF OSINT — find the place / person / page / time

Answers are **findable in public data** — never brute-force or harass real people,
never touch non-public accounts or attempt credential attacks. Keep to the challenge's
intended pivot chain.

<!-- logic-distill:begin -->
## Solver Mindset — how experienced players attack osint (distilled from 150 writeups)

**The loop**
1. Audit the container before looking at the picture: `exiftool`, unzip OOXML (author, revisions), PNG IHDR size, EXIF GPS/time. [ev: bab68f, 6df928, a8af6e, 0b68cc]
2. Decompose the scene: crop and transcribe micro-signage, sign subtext, road shields, pole plates. [ev: a1cf9a, 17d59d, ea14c6, b6bec9]
3. Scope first: host campus, organizer blogs, language/script and plate country, then search wider. [ev: 8d47c8, 2be8e2, bab68f, 7fd1f0]
4. Search crops, not scenes; for CIS scenes use Yandex Maps panoramas, 2GIS and Yandex Images. [ev: 86786c, 22d6e4, bc3176, 694cad]
5. Triangulate relations: co-located business names together, or Overpass / infrastructure-layer intersections (bridge x stream, rail x power line, brand x brand). [ev: 9ed8cd, b07eb3, 182e32, 8b02a9]
6. Resect and ground-truth: trace the sightline back from the landmark on 3D imagery; check the Street View date timeline. [ev: 8d47c8, 2be8e2, 1e2154, 53850d]
7. Normalize the flag: decimal places as stated, sub-facility name, what3words cell, wrapper and character rules. [ev: 6dc5f2, 0c7310, 9ed8cd, 0aa3ed]

**First 10 minutes**
- [ ] 0-3: `file` + `exiftool`; unzip OOXML (`docProps/core.xml`, `docProps/app.xml`, `word/document.xml`); check PNG IHDR height. [ev: bab68f, 6df928, a8af6e, 51a29b]
- [ ] 3-5: test home-ground bias: host university campus map, organizer blogs. [ev: 8d47c8, 2be8e2, 181713, bab68f]
- [ ] 5-7: transcribe every shop name, sign subtext, road name, route shield, plate style. [ev: 17d59d, a1cf9a, 9ed8cd, 7fd1f0]
- [ ] 7-8: crop away water/sky/clutter; reverse-search the distinctive crop (Google Lens, Yandex, Bing). [ev: 86786c, a1cf9a, 22d6e4, 1e2154]
- [ ] 8-10: co-located names on Google Maps, or an Overpass proximity/intersection query, to lock candidates. [ev: 9ed8cd, b07eb3, 182e32, 0f19e3]

**Route by signal** — open the matching playbook BEFORE going deep (full table: `references/logic/INDEX.md`).

| Signal | Playbook |
|---|---|
| Skyline / campus / monument, view from a window, EXIF stripped | `references/logic/image-landmark-resection.md` |
| Rural road, pylons, rail, no landmark; reverse search fails | `references/logic/image-infrastructure-gis.md` |
| Adjacent storefronts, strip-mall signs, local-script shop names | `references/logic/commercial-poi-colocation.md` |
| Exact time/date wanted; sharp shadows | `references/logic/chronolocation-sun-shadow-timing.md` |
| Handle, alias, email, single profile link | `references/logic/username-socmint-pivot-chain.md` |
| GitHub/GitLab profile, repo, commit hash, cleaned branch | `references/logic/developer-code-artifact-recon.md` |
| Company, domain, IP block, filing, funding round | `references/logic/corporate-domain-network-footprint.md` |
| Attached DOCX/PDF/image/3D model/audio | `references/logic/document-media-metadata-forensics.md` |
| 404 / parked / edited page; past state or date | `references/logic/web-archive-temporal-recon.md` |
| Boarding pass, flight track, ICAO hex, MMSI/IMO, MAVLink | `references/logic/transport-telemetry-tracking.md` |
| Cryptic prose, quote, lyrics, hoax, game coordinates | `references/logic/cultural-lore-knowledge-retrieval.md` |
| Video, broadcast, YouTube URL, background audio | `references/logic/multimedia-video-audio-recon.md` |

**Top rules**
1. Prompt names OSM as the source of truth (or asks for an OSM ID): use the exact OSM `name` tag / way ID, not the Google Maps label. [ev: 921848, 0e33b7, 1d4232]
2. Prompt quotes lyrics/prose or lists biographical oddities: search the distinctive phrases verbatim, then check the backstory against the title (hoax, credited pseudonym vs legal name). [ev: c215e0, dbd2e7, 81f6f2, 0cd353]
3. Found a handle: enumerate it across other platforms (Sherlock / Maigret / WhatsMyName, Bluesky). [ev: 141d2c, 01f908, be97e3, 549549]
4. Repo looks cleaned or force-pushed: read the public activity feed and fetch orphan SHAs via `.patch` URLs (both cards: same event). [ev: 8fdd83, 194bde]
5. Before submitting coordinates: match the prompt's decimal places, delimiter and spacing exactly. [ev: acfca6, c2be73, 6dc5f2, e1029c]
6. Full-image reverse search gives generic lookalikes: crop to one distinctive silhouette, facade or sign and search again. [ev: 86786c, a1cf9a, 1e2154, 22d6e4]
7. Street View does not match the photo: open the capture-date timeline and check older panos. [ev: 53850d, fed9c0, 7fd1f0]
8. Decoded string has the wrong wrapper (`AXIOS{..}`, `synt{..}`) or the prompt alters the format: treat it as a decoy/intermediate or transform it; submit exactly the prompt's format. [ev: 8f4074, be97e3, 248f8a, 0aa3ed]
9. Campus photo: bound to the host campus map + 3D imagery to find the building; for the name read the entrance signage — the map name may be the parent complex. [ev: 8d47c8, 2be8e2, 1e2154, 0c7310]
10. Any downloaded media: `exiftool` (EXIF time/GPS, UserComment) before visual analysis. [ev: 04179d, 0b68cc, ce7b5a, 76e4ed]
11. CIS / Russian-language scene: use Yandex Maps panoramas, 2GIS and Yandex Images. [ev: bc3176, 694cad]
12. Scene has a mappable feature combination (bridge x stream, rail x power line, house number + POI): write an Overpass intersection/proximity query. [ev: 182e32, 8b02a9, 0f19e3, b4a132]
13. Video clip: sample keyframes / build a contact sheet (`ffmpeg` fps=1/3); transcribe narration and chyrons (multimodal LLM for foreign speech). [ev: 376e36, 1d4232, 0e33b7, 49cb47]
14. Postal code in a handle/prompt or a plate style in frame: use it as a country/town anchor. [ev: d6d01d, 7fd1f0, a01bae]
15. Photo from a window/balcony: the answer is the observer's building — trace the sightline back from the visible landmark on 3D imagery. [ev: 8d47c8, 2be8e2, 1e2154, 181713]

**Stop-loss & AI pitfalls**
- Plausible flag variants rejected: stop permuting; re-audit metadata, source and prompt syntax. [ev: 0c7310, bab68f, 579079, d6d01d]
- Uncropped reverse search: 5 min max, then distinctive crops only. [ev: 22d6e4, 18d72f, 86786c]
- Manual map/satellite scanning without a hard filter: stop; build one (Overpass exclusion query, pole-plate code). [ev: 0f19e3, b6bec9]
- WHOIS redacted: registrant question -> historical WHOIS (Whoxy) [ev: b3c636]; hosting question -> DNS A + IP WHOIS [ev: f75ae0]; hidden hosts -> crt.sh [ev: bbaf8b].
- Handle trail cold on live profiles: check Wayback snapshots of the profile and playlist/paste/gist pivots instead of more spraying. [ev: 745209, af2f0d, 8f4074]
- Place name rejected: the author keys on another level — hall inside the complex [ev: 0c7310], parent city / tenant company instead of suburb / building [ev: a01bae], actual venue vs the famous neighbour in the caption [ev: ba53c7].
- Do not submit the landmark you see; submit the observer's building (resect the sightline). [ev: 8d47c8, 2be8e2, 181713, 1e2154]
- what3words: prompt says building centre -> centre cell of the roof [ev: 9ed8cd]; prompt asks where the photo was taken -> photographer's stance [ev: d3ee48, 5f20fb]; then test adjacent 3 m cells. Lat/long of an area: prefer the existing POI pin over a computed centroid [ev: c2be73].

Stuck > 20 min → re-read `references/logic/meta_reasoning.md` and the playbook's "Decision points".
<!-- logic-distill:end -->

Tools (Arch / CachyOS): check before installing (`command -v <tool>`):
```bash
command -v tesseract >/dev/null || sudo pacman -S --needed tesseract tesseract-data-eng exiftool curl jq
command -v sherlock >/dev/null || paru -S --needed sherlock-git
python3 -c "import playwright" 2>/dev/null || (pip install --user playwright pytesseract requests && playwright install chromium)
```
Run all python reference scripts with `python3 -I`.

---

## Decision Tree & Specialty Helpers Matrix

| Challenge Input / Clue Type | Primary Reference / Helper | Key Methodology & Pivot |
|-----------------------------|----------------------------|-------------------------|
| **Landmark combination (no text)** (e.g. chimney + tower + railway) | `references/overpass_query.py` | Query OSM tags via Overpass QL around coordinate or inside bounding box |
| **Shadow / Sun in image**, unknown time of day or date | `references/chronolocation.py` | Calculate $\alpha = \arctan(h/s)$, solve candidate times or noon latitude |
| **Roadside bollards, utility poles, road lines, car meta** | `references/geoguessr_meta.md` | Identify country/region via infrastructure standards & Street View gen |
| **Domain / Organization**, deleted pages, hidden endpoints | `references/domain_recon.py` | Passive Certificate Transparency (`crt.sh`) + Wayback Machine CDX API |
| **Target name, handle, Git commits, outdoor trail** | `references/social_pivots.md` | Email permutations + Gravatar MD5, Git author logs, Strava/Komoot, Bluesky |
| **Torn news clipping / page behind Cloudflare 403** | `references/antibot_scraper.py` | Headed persistent Playwright profile + Tesseract OCR (`--psm 6`) |
| **CTF team name, player leetspeak handle across events** | `references/ctftime_pivot.py` | CTFtime REST API + HTML scraper with regex variant generator |
| **Drone / aircraft telemetry stream in capture** | `ctf-rf-space` (`mavlink.py`) | Parse MAVLink v2 `GLOBAL_POSITION_INT` messages, plot coordinates |

---

## 1. Spatial Data Mining & Overpass QL (`references/overpass_query.py`)

When challenges present visual landmarks without text (e.g. an industrial chimney repurposed as a telecom mast, or a church tower near an elevated reservoir):

```bash
# 1. Geocode a suspected city/region using Nominatim:
python3 -I references/overpass_query.py geocode "Mackay, Idaho"

# 2. Search for specific OSM features within radius (meters):
python3 -I references/overpass_query.py around --lat 44.812 --lon 20.461 --radius 5000 --tags "man_made=chimney"

# 3. Search inside bounding box (south, west, north, east):
python3 -I references/overpass_query.py bbox --south 44.80 --west 20.40 --north 44.85 --east 20.50 --tags "man_made=tower" "tower:type=communication"

# 4. Run CTF presets (chimney_telecom, railway_substation, water_tower, church_spire, sports_circuit):
python3 -I references/overpass_query.py preset chimney_telecom --lat 44.812 --lon 20.461 --radius 8000 --geojson /tmp/results.geojson
```

---

## 2. Chronolocation & Shadow Triangulation (`references/chronolocation.py`)

Determine the exact time of day, date, or latitude of an unlabelled photo using solar physics and geometry.

- **Shadow Ratio**: $R = \frac{L_{\text{shadow}}}{H_{\text{object}}} = \cot(\alpha) = \frac{1}{\tan(\alpha)}$
- **Solar Elevation**: $\alpha = \arctan\left(\frac{H_{\text{object}}}{L_{\text{shadow}}}\right)$
- **Shadow Direction**: $\text{Azimuth}_{\text{shadow}} = (\text{Azimuth}_{\text{sun}} + 180^\circ) \pmod{360^\circ}$
- **Solar Noon Shortcut**: Shortest shadow of the day occurs when the sun crosses the local meridian ($H \approx 0$).
  - If shadow points North (sun in South): $\text{Latitude} = \text{Declination} + (90^\circ - \alpha)$
  - If shadow points South (sun in North): $\text{Latitude} = \text{Declination} - (90^\circ - \alpha)$

```bash
# 1. Calculate solar elevation, azimuth, and expected shadow ratio for location & timestamp:
python3 -I references/chronolocation.py calc --lat 48.8584 --lon 2.2945 --time "2026-06-21T12:00:00Z"

# 2. Compute solar elevation angle from measured object height and shadow length:
python3 -I references/chronolocation.py shadow --height 12.0 --shadow 15.6

# 3. Solve for candidate times of day matching an observed shadow ratio:
python3 -I references/chronolocation.py solve-time --lat 40.7128 --lon -74.0060 --date 2026-04-15 --ratio 1.42

# 4. Estimate latitude from shortest shadow of the day (Solar Noon):
python3 -I references/chronolocation.py noon-lat --date 2026-05-10 --ratio 0.55 --shadow-dir north
```

---

## 3. Global Infrastructure & GeoGuessr Meta (`references/geoguessr_meta.md`)

When standard landmarks are missing, identify the country through physical infrastructure standards:
- **Utility Poles**:
  - Perforated concrete with round holes $\to$ **Poland** ("Żerdź wirowana").
  - Perforated concrete with rectangular/ladder holes $\to$ **France**, **Romania**, **Hungary**, **Ukraine**, **Brazil**.
  - A-frame wooden poles $\to$ **UK**, **Ireland**, **Scandinavia**.
  - Stepped climbing pegs $\to$ **Japan**, **Taiwan**.
  - Diagonal yellow/black striped pole bases $\to$ **Taiwan**.
- **Roadside Bollards**:
  - White post with black angled cap + white front reflector $\to$ **Germany** / **Austria**.
  - Cylindrical white post with red retroreflective ring $\to$ **France**.
  - White post with red reflector on left, white on right $\to$ **UK**, **Australia**, **New Zealand**.
  - Curved post with slanted red band $\to$ **Poland**.
- **License Plates**:
  - Yellow rear, white front $\to$ **United Kingdom**, **Cyprus** (older).
  - Yellow front and rear $\to$ **Netherlands**, **Luxembourg**, **Israel**, **Colombia** (public vehicles).
  - Red letters on white plate $\to$ **Belgium**.
  - Green plates on commercial vehicles $\to$ **Norway**.
- **Street View Camera & Vehicle Meta**:
  - Gen 2: low-res with distinct **purple / magenta fringing** on high-contrast edges.
  - Gen 4: 4K ultra-sharp, tiny circular blur.
  - Roof rack with snorkel on hood $\to$ **Kenya**.
  - Visible police escort truck $\to$ **Nigeria**.
  - Black electrical tape on front-right roof bar $\to$ **Ghana**.
  - Pickup truck with open bed and silver camping bars $\to$ **Mongolia**.

---

## 4. Passive Domain Recon & Asset Discovery (`references/domain_recon.py`)

Harvest subdomains, historical endpoints, and exposed configuration files without sending active network probes to the target:

```bash
# 1. Enumerate subdomains via Certificate Transparency logs (crt.sh):
python3 -I references/domain_recon.py subdomains example.com --resolve

# 2. Query Wayback Machine CDX API for historical sensitive endpoints:
python3 -I references/domain_recon.py wayback example.com --limit 500

# 3. Run complete passive footprint scan (.git, .env, backups, admin, swagger, flags):
python3 -I references/domain_recon.py scan example.com --out /tmp/target_recon.json
```

---

## 5. Social, Developer & Activity Footprints (`references/social_pivots.md`)

- **Git Commit Header Harvesting**:
  ```bash
  git log --format='%an <%ae>' | sort -u
  ```
  Append `.patch` to any GitHub commit URL (`github.com/user/repo/commit/{hash}.patch`) to expose unmasked author emails.
- **Gravatar MD5 Pivot**:
  `md5(email.strip().lower())` $\to$ query `https://en.gravatar.com/{hash}.json` or reverse hashes by wordlist permutation.
- **Strava / Komoot Geoint**:
  Search Strava Segment Leaderboards on the event date or inspect Komoot tour waypoints and photos taken at the challenge location.
- **Bluesky & AT Protocol**:
  Resolve handle to DID via `https://bsky.social/xrpc/com.atproto.identity.resolveHandle?handle={handle}` and audit all past handle renames via the public PLC log (`https://plc.directory/{did}/log`).

---

## 6. Anti-Bot Scraping & Image OCR (`references/antibot_scraper.py`)

When public archives or newspaper platforms (e.g. Chronicling America, local gazettes) present Cloudflare Turnstile or anti-bot interstitials that return HTTP 403 to `requests` or headless browsers:

```bash
# Fetch full rendered page bypassing bot challenges:
python3 -I references/antibot_scraper.py fetch "https://chroniclingamerica.loc.gov/..." /tmp/page.html

# Take full-page screenshot:
python3 -I references/antibot_scraper.py screenshot "https://target-portal.com/" /tmp/shot.png

# Extract text from low-contrast torn newspaper clippings using Tesseract PSM 6:
tesseract /tmp/clipping.png stdout --psm 6
```

---

## 7. Platform & Scoreboard Pivots (`references/ctftime_pivot.py`)

```bash
# Query CTFtime team metadata (JSON API with HTML fallback):
python3 -I references/ctftime_pivot.py team 1005

# Generate leetspeak-tolerant regular expression for obfuscated team handles:
python3 -I references/ctftime_pivot.py leet "flag"    # -> [f][l1|][a4@][g9]
```

---

## 8. General OSINT Methodology & Verification

See the evidence-backed **Solver Mindset** block at the top of this file, `references/logic/INDEX.md`
(signal → playbook routing) and `references/logic/meta_reasoning.md` (hypothesis management,
stop-loss, author tricks, verification before submitting).
