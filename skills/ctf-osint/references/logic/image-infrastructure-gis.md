# Infrastructure and Spatial GIS Data Mining

> category: osint · slug: `image-infrastructure-gis` · evidence: 15 writeups from 7 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Imagery depicts rural roads, highway junctions, agricultural fields, or generic commercial lots without famous landmarks, where raw reverse image search fails or returns stock landscape photos. [ev: 0f19e3, 18d72f, 182e32]
- Visible standardized regional infrastructure: utility pole markings, transformer insulator geometry, highway warning wraps, or transit fleet liveries. [ev: 182e32, 391fcd, b6bec9]
- Co-occurrence of two or more distinct spatial entities or POIs in close proximity (e.g. retail brand pairs in a commercial lot, house numbers adjacent to churches, bare POI labels in an enclosed facility). [ev: 6dc5f2, b4a132, b07eb3, f4eb7a]
- Prompts requiring official administrative or cadastral attributes: exact decimal elevation from public surveys, cadastral parcel lot numbers (`chiban`), or municipal urban planning route codes. [ev: 532ed8, ca1490, d2cf28, 28c691]

## Opening sequence (do in this order)
1. **Isolate standardized hardware markers** — inspect utility pole plates, transformer mountings, insulator lengths, hazard striping, or vehicle liveries; time-box 5 min. Why: Standardization links the scene to a specific national grid, regional power company, or transit operator without visual brute-force. [ev: 182e32, 391fcd, b6bec9]
2. **Discard UI chrome and decoy media** — separate browser session UI chrome (locale/footer labels), crowdsourced user-uploaded gallery noise, and challenge-title decoys from structured scene metadata; time-box 5 min. Why: Authors routinely insert misleading foreground objects or session indicators that distract from queryable GIS tags. [ev: 6dc5f2, f4eb7a]
3. **Bound search area to national or administrative boundaries** — establish an ISO 3166 country code, state/prefecture boundary, or macro-topographical corridor before issuing queries; time-box 5 min. Why: Unconstrained national or global Overpass queries trigger gateway timeouts (HTTP 504), 406 errors, or tens of thousands of unmanageable results. [ev: 0f19e3, b07eb3, f4eb7a]
4. **Formulate structured spatial proximity or exclusion queries** — construct Overpass QL queries intersecting two distinct entity types (e.g., house number + church denomination) or subtracting urban proximity buffers; time-box 10 min. Why: Spatial intersection collapses national datasets from tens of thousands down to a verifiable candidate shortlist (<20-200 nodes). [ev: 0f19e3, b4a132, b07eb3, f4eb7a]
5. **Filter candidates via 2D map geometry before loading panoramas** — compare candidate road curvature, orientation, stream crossings, or elevation profiles directly on 2D map views; time-box 5 min. Why: 2D geometry checks prune dozens of false candidates per minute without incurring Street View loading latency. [ev: 694cad, 182e32]

## Decision points
- **IF** candidate infrastructure instances (e.g. roundabouts, small bridges) number in the thousands across rural terrain **THEN** use negative spatial proximity filtering in Overpass QL (`.features - .exclude` subtracting urban landuses or settlement nodes) **ELSE** filter by positive proximity to intersecting natural features (e.g. stream, hill, mountain ridge). [ev: 0f19e3, 182e32]
- **IF** low-resolution signage, panorama tiles, or angled dot-matrix LED displays fail OCR after initial passes **THEN** abandon character OCR and pivot to commercial brand logos, trade dress, transit liveries, or macro-topographical morphology **ELSE** use extracted high-confidence text directly. [ev: 18d72f, b07eb3, 391fcd]
- **IF** the target requires official legal attributes (land parcel numbers, urban planning routes) or centimeter-grade elevation **THEN** query national/municipal geoportals, open cadastral maps (`chisekizu`), or raw LiDAR point clouds (`LAZ`) **ELSE** use OpenStreetMap and commercial map services. [ev: 532ed8, ca1490, d2cf28, 28c691]
- **IF** two or more generic or national chain brands/POIs share a single lot or facility **THEN** run an OpenStreetMap Haversine nearest-neighbor proximity join (<300 m) across both feature sets **ELSE** search for rare single-instance tags. [ev: 6dc5f2, b07eb3]
- **IF** an automated HTTP coordinate validator with known radial tolerance (e.g. ±20 m) is provided **THEN** densify candidate road polylines at sub-tolerance intervals (`step = 0.9 * tolerance`, seen once [ev: 18d72f]) or script an automated candidate sweep **ELSE** visually confirm candidates via Google Street View or Yandex Panorama. [ev: 18d72f, b07eb3, 391fcd]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Utility pole hardware markings or insulator geometry identified → matched against regional infrastructure guides (Plonkit/Geotips) or utility grid specifications → isolates region to a single power company zone or decodes into direct coordinate percentages. [ev: 182e32, b6bec9]
- Challenge title feature or foreground gallery photo recognized as decoy bait (e.g. "Chimney" smokescreen, irrelevant motorcycle in POI gallery) → pivot focus to structured address tags (house numbers) and spatial POI co-occurrences. [ev: 6dc5f2, f4eb7a]
- Outdoor signage OCR producing garbled characters or false town names under enhancement → switch immediately to national brand co-occurrence and Overpass spatial nearest-neighbor joins. [ev: 18d72f, b07eb3]
- Latest geoportal LiDAR survey tile misses target structure (ground/pedestal returns only) → batch-download historical multi-year aerial survey acquisitions (`LAZ`) → uncovers unmasked structure apex in older survey runs. [ev: 532ed8, ca1490]
- Linear swath of cleared buildings/demolition lots observed in aerial imagery → indicates municipal right-of-way acquisition for planned urban road (`都市計画道路`) → search local municipal planning PDFs for official route designation to locate Wikidata QID. [ev: d2cf28, 28c691]

## Dead ends & stop-loss
- Manual street-view or satellite scanning on unconstrained nationwide road features — abandon when candidate set > 50; failed because inspecting thousands of rural junctions by hand wastes hours and leads to visual exhaustion. [ev: 0f19e3, 182e32]
- Fine-tuning image upscaling, color masks, and OCR PSM modes on low-resolution signs or distant text — abandon after 10-15 minutes; failed because perspective distortion and compression artifacts generate hallucinated text and false geographic hypotheses. [ev: 18d72f, b07eb3, 391fcd]
- Chasing title-named visual objects, foreground photo bait, or browser UI chrome (e.g. vintage motorcycle in POI gallery, title chimney as primary tag, footer country labels) — abandon when initial searches yield conflicting near-misses; failed because author decoys and crowdsourced photos lack structured geographic linkages to the target facility. [ev: 6dc5f2, f4eb7a]
- Submitting unconstrained regex GET queries to primary Overpass endpoints — abandon upon HTTP 406 or gateway timeout; failed because public OSM endpoints rate-limit heavy queries; switch to POST queries against mirrors (e.g. `overpass.kumi.systems`). [ev: b07eb3, f4eb7a]
- Adding news article structure dimensions to ground elevation models for exact decimal flags — abandon when flag demands two decimal places; failed because challenge scoring keys strictly to raw sensor/survey point-cloud returns. [ev: 532ed8, ca1490]

## Author tricks / decoys seen
- Misdirection via challenge titles, prominent foreground objects, or browser UI chrome (e.g. naming the challenge "Chimney", displaying an unrelated motorcycle in a canteen gallery, or showing client session country in Google Maps footers) that lack reliable OSM tags or reflect client session locale. [ev: 6dc5f2, f4eb7a]
- Extraneous flavor files (`logo.png`, `painting.png`) and rotating server insult strings in coordinate validators designed to mislead automated string checkers. [ev: 18d72f, b07eb3]

## Verify before submitting
- For automated coordinate validators, confirm candidate hits return HTTP 200 with flag text (`THC{`, `L3AK{`) and require retry verification to avoid transient socket resets or connection timeouts being treated as successes. [ev: 18d72f, b07eb3]
- When exact decimal precision or strict string formatting is specified (e.g. 4-decimal coordinates preserving trailing zeros, or 2-decimal LiDAR elevations), verify format strings strictly (e.g. `f'{val:.4f}'`) rather than standard float conversion. [ev: 6dc5f2, 532ed8, ca1490]
- Filter candidate geometry visually on 2D map views (road curvature radius, stream crossing angles) before opening individual Street View panoramas. [ev: 694cad, 182e32]
- When extracting structural heights from LiDAR point clouds, verify ASPRS classification codes (e.g. class 6 for buildings) and inspect 3D scatter plots across multi-year flight surveys to ensure the point sits on the structure apex rather than sensor noise. [ev: 532ed8, ca1490]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Overpass Turbo / Overpass API (mirror `overpass.kumi.systems`) | Spatial proximity joins, negative buffer exclusion, POI queries | in 7 writeups |
| Google Street View / Yandex Panorama | Visual viewpoint alignment and landmark ground-truth confirmation | in 8 writeups |
| OpenStreetMap / Nominatim | Extracting road geometries, transit routes, and administrative boundaries | in 7 writeups |
| Python (`urllib`, `requests`, `laspy`, `numpy`, Haversine) | Validator sweep automation, polyline densification, LiDAR point cloud extraction | in 5 writeups |
| National Geoportals / Cadastre Portals (Maa-amet X-GIS 2, Tokyo Tax Bureau, EHR) | Downloading open LiDAR point clouds (`LAZ`), municipal cadastral maps (`chisekizu`) | in 4 writeups |
| Pillow / Tesseract OCR / OpenCV | Crop generation, image upscaling, and OCR attempts on signage | in 4 writeups |
| Geotips / Plonkit Regional Infrastructure Guides | Identifying utility pole hardware, transformer styles, and national road markings | in 2 writeups |
| QGIS / 3D Point Cloud Visualizers | Processing LiDAR point clouds and inspecting elevation profiles | in 2 writeups |

## Worked micro-traces
- `[ev: 0f19e3]` Given an image of a highway roundabout in a lush flat rural landscape with 'PARE' painted on asphalt and a distant hill. Solver recognized Latin America (Brazil) via the road marking and roundabout density (~12,000 nationwide). Because manual inspection was impossible, solver rejected positive tagging and built an Overpass QL query in the state of Tocantins that subtracted all roundabouts within 500m of urban landuse or 2000m of settlement nodes (`.features - .exclude`). This collapsed thousands of junctions to 166 rural candidates, which were scanned on satellite imagery against the distant hill to pinpoint the exact roundabout.
- `[ev: b07eb3]` Given an equirectangular panorama of a commercial parking lot with stripped EXIF and an HTTP coordinate validator (±20m tolerance). Solver initially spent time running 4x Lanczos upscaling and Tesseract OCR on distant signs, producing garbled characters and a false town hypothesis ('VITRÉ'). Pivoting away from OCR, solver recognized two national French chains sharing the lot: Carrefour Market and Coiff&Co salon. Solver queried an Overpass mirror (`overpass.kumi.systems`) for all instances of both brands in France, computed a Haversine proximity join (<300m) to reduce the search to 21 candidate pairs, and executed an automated HTTP sweep against the validator to retrieve the flag at Saint-Pourçain-sur-Sioule.
- `[ev: ca1490]` Given a prompt asking for the highest absolute elevation of the military radar radome in Estonia that blocked the Aidu wind farm, to two decimal places from public data. News search identified the Kellavere radar station in Vinni Parish. Solver navigated to the Estonian Land Board (Maa-amet) geoportal and downloaded the 2022 LiDAR tile 551644, but the maximum Z was only ~162.56m (pedestal only); an attempt to add nominal 12.5m radome height failed submission. Solver recognized that aerial survey acquisitions vary by flight year, downloaded historical LiDAR survey vintages (2009-2022), and parsed them in Python with `laspy`. The 2013 survey tile returned a class-6 building point at 178.02m, confirmed by 3D scatter plot as the spherical radome apex, solving the challenge.

## Weak signals (single source — treat as hints, not rules)
- Reflected window signage requires horizontal flipping before OCR or visual search can index reversed lettering. [ev: 921848]
- Multi-location coordinate clues can be resolved geometrically by calculating centroid or circle intersections when challenge prompts hint at intersecting circles. [ev: 921848]
- When a challenge explicitly specifies OpenStreetMap as source of truth, verify the exact node/way name tag rather than the Google Maps display name. [ev: 921848]
- Sensory narrative clues ('smells like sea' + mountains) delimit regional search to specific coastal strips, allowing immediate facility enumeration (e.g. bus stations in coastal towns). [ev: 694cad]
- Russian street address transliterations in CTF flags frequently drop silent orthographic characters such as the hard sign ъ (Объездная -> Obezdnaya). [ev: 694cad]
- Rare ecological structures (stork nests `birds_nest=stork`, `species~Ciconia|stork|bocian`) mapped in OSM can be spatially intersected with house numbers (`around:50m`). [ev: b4a132]
- Dedicated municipal transit corridors (`site propre`) and transit route relations (`ref=49`) intersected with multi-stream bring-bank recycling containers (`amenity=recycling`). [ev: 391fcd]
- Werkzeug debugger leaks on validator 500 errors can reveal distance metric formulas (`haversine < marge_erreur`) even when console execution is locked. [ev: 391fcd]
- Taiwan Power Company (Taipower) utility pole plates encode sector letters and two-digit percentage coordinates (X/Y) pinpointing geographic grid cells. [ev: b6bec9]
- Distance trilateration from multiple reference points around a Google Place ID to recover exact pin coordinates when Google Plus Codes provide only 14x14m cell precision. [ev: 6dc5f2]
- Searching municipal taxation bureau cadastral maps (`chisekizu` / 地籍図) to extract legal land parcel numbers (`chiban` / 地番) distinct from residential addresses (`jūkyo-hyōji`). [ev: d2cf28]
- Cross-referencing social media posts for quirky/viral street art to obtain wider contextual angles and background signage when primary crops are too tight. [ev: d2cf28]
- Urban demolition corridors on satellite imagery identify planned municipal roads (`都市計画道路`), linking to Japanese Wikipedia articles and Wikidata QIDs. [ev: 28c691]
