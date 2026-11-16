# Multimedia Broadcast and Video Audio Recon

> category: osint · slug: `multimedia-video-audio-recon` · evidence: 7 writeups from 3 events · strength: moderate

**When this applies (recognition, first 5 minutes):**
- Challenge provides a video file (MP4, MKV), a streaming URL (YouTube, YouTube Shorts), or a text prompt specifying a historical television broadcast date, program synopsis, and airtime. [ev: 376e36, 786867, 1d4232, 0e33b7, 8633cf, bc3176, 49cb47]
- Audio track or spoken dialogue (news narration, police/expressway dispatch chatter, interview quotes) contains municipal district names, route designations, or named institutional facilities that narrow geographic scope prior to visual mapping. [ev: 786867, 0e33b7, 8633cf, 49cb47]
- Visual stream contains transient visual indicators: passing roadside commercial billboards, corporate branch signage, or distinctive transit/aviation liveries dispersed across frames or travel montages. [ev: 376e36, 786867, bc3176, 49cb47]
- Objective demands high-precision ground recovery: exact venue/hotel name, registered property owner from land registries, OpenStreetMap entity ID, or geographic coordinates within a 20–50m tolerance. [ev: 376e36, 786867, 1d4232, 0e33b7, 8633cf, 49cb47]

## Opening sequence (do in this order)
1. **Source Archival Retrieval** — If given an air date, quoted statement, or program synopsis, search Google, YouTube, or specialized archives (e.g. KCNA Watch) to locate the full uncropped broadcast recording; time-box 5 min. Why: Short snippets or text prompts frequently excerpt longer broadcast packages that contain vital wide-angle footage. [ev: 1d4232, 8633cf, 49cb47]
2. **Audio Transcription & Chyron Parsing** — Transcribe spoken narration, radio communications, and lower-third on-screen graphics (chyrons) immediately upon retrieving the video (using manual transcription or multimodal LLM); time-box 5 min. Why: Spoken administrative districts, route numbers, or facility names collapse a global or metropolitan search space into a single road segment or district before examining pixels. [ev: 786867, 0e33b7, 49cb47]
3. **Keyframe Sampling & Contact Sheet Overview** — Extract video frames at low frequency (e.g. `ffmpeg -vf "fps=1/3"`) or sample keyframes across scene cuts rather than scrubbing at 1x in a media player; time-box 5 min. Why: 1x playback suffers from motion blur and misses brief peripheral signs, whereas static contact sheets expose stationary commercial text, rooflines, and landmarks simultaneously. [ev: 376e36, bc3176, 49cb47]
4. **Targeted Visual Anchor & Logo Identification** — Crop high-contrast commercial signage, bank/corporate logos, or branded transit/aviation liveries from keyframes and execute reverse image searches (Google Lens / Yandex); time-box 5 min. Why: Full-frame reverse search on generic streets or architecture returns thousands of global false positives, whereas tightly cropped logos or liveries immediately anchor the specific company or city hub. [ev: 786867, 8633cf, bc3176, 49cb47]
5. **District-Filtered Directory & Regional GIS Triangulation** — Combine the extracted district/city anchor with the identified commercial entity to query official branch locators, regional map engines (Yandex Maps / 2GIS for CIS, Wikimapia for North Korea), or 3D street views; time-box 5 min. Why: Corporate store locators and localized GIS portals provide exact street addresses and building footprints that generic global map search engines omit. [ev: 786867, 1d4232, bc3176, 49cb47]

## Decision points
- **IF** the input video is a vertical/cropped snippet (Shorts/TikTok/Reels) or viral quote **THEN** search the spoken phrase to find the full horizontal broadcast and subject identity for multi-angle footage **ELSE** proceed directly to keyframe extraction on the source file. [ev: 8633cf, bc3176]
- **IF** spoken narration is in a foreign language (e.g. Korean) or lacks subtitles **THEN** ingest audio/video with a multimodal LLM (NotebookLM) to extract named facilities **ELSE** transcribe dispatch names, route numbers, and chyrons manually. [ev: 0e33b7, 49cb47]
- **IF** candidate institution names in non-Latin script regions yield zero results on standard Latin map searches **THEN** re-query OpenStreetMap and search engines using native script (Hangul, Hanja, Cyrillic) **ELSE** search transliterated or English variations. [ev: 1d4232, 0e33b7]
- **IF** the target is in a country poorly indexed by Google Maps (e.g. North Korea, CIS nations) **THEN** pivot to specialized regional databases (Wikimapia for DPRK, Yandex Maps Panoramas and 2GIS for CIS) **ELSE** use Google Maps 3D and Street View. [ev: 1d4232, bc3176]
- **IF** the challenge requires a legal property owner or cadastral parcel record **THEN** take the street address from corporate branch locators and query the official national land registry (e.g. ČÚZK) **ELSE** resolve spatial coordinates or OSM Way IDs directly. [ev: 786867, 1d4232]
- **IF** multiple buildings or sprawling campuses match the visual area **THEN** use vertical camera pitch/line-of-sight geometry or check OSM object types (site boundary way vs individual building way) to isolate the exact feature **ELSE** submit the identified coordinates or name. [ev: 376e36, 1d4232]
- **IF** candidate venue or owner names have multiple variations **THEN** strictly validate word counts, character lengths, and separator patterns against the prompt flag wrapper before submitting **ELSE** submit the primary legal name. [ev: 376e36, 786867]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Spoken radio dispatch or lower-third chyron reveals a highway junction, route number, or municipal district → narrows hundreds of kilometers of road/city to a 200m search corridor → scan roadside billboards and corporate facades along that narrow stretch. [ev: 786867, 49cb47]
- Reverse image search of a distinct vehicle/aircraft livery (e.g. Air Astana) or stadium roofline anchors the regional metropolitan hub → provides the exact city/district keyword needed to resolve generic overpasses or road scenes. [ev: 8633cf, bc3176]
- Commercial signage directly below or beside the target vantage point ('RIVERSIDE POINT', 'FUKU...') → anchors candidate building footprint and line-of-sight geometry along the identified roadway/riverfront. [ev: 376e36, 49cb47]
- Google Maps search fails to resolve a non-Western facility or provides no street imagery → pivoting to region-specific platforms (Wikimapia, 2GIS/Yandex) resolves precise coordinates and street panoramas from native-language institution names. [ev: 1d4232, bc3176]

## Dead ends & stop-loss
- Reverse image searching full video frames of generic roads, overpasses, or graffiti — abandon immediately if first pass yields generic global results; it fails because lack of distinct visual features produces thousands of irrelevant matches; crop specific corporate logos, signs, or anchor liveries instead. [ev: 786867, bc3176]
- Scrubbing video manually at 1x speed in a media player — abandon after one pass; it fails because motion blur and playback speed cause solvers to miss transient roadside signage or subtle architectural details. [ev: 376e36, 49cb47]
- Relying exclusively on Google Maps / Street View in countries with minimal or restricted coverage (North Korea, CIS nations) — abandon within 5 minutes when searches fail; it fails because Google lacks local indexing and street panoramas in these regions; pivot to Wikimapia, Yandex Maps, or 2GIS. [ev: 1d4232, bc3176]
- Searching the submission map engine (e.g. OpenStreetMap) directly for private commercial tenant or corporate names — abandon after first failed query; it fails because OSM's volunteer tagging frequently omits private corporate names; locate the commercial site on Google Maps/3D view first, find an adjacent public feature (park, school, temple), and search that feature on OSM. [ev: 1d4232, 49cb47]
- Estimating fine standing coordinates solely from telephoto/cropped background horizon alignment — abandon after initial rough fix; it fails because optical compression across deep fields causes hundreds of meters of positional error; anchor the position using foreground ground markers or search for alternate production camera angles. [ev: 376e36, 8633cf]

## Author tricks / decoys seen
- Elevated highway or high-rise vantage points obscuring ground level — challenge footage hides direct ground context behind sound barriers, elevated structures, or window mullions, forcing reliance on rooftop commercial logos, eye clinic billboards, or steep downward line-of-sight geometry. [ev: 376e36, 49cb47]
- Cropped vertical format or restricted field of view — challenge presents a tightly cropped vertical Short or narrow window pan, stripping peripheral horizon markers and forcing solvers to hunt for uncropped broadcast archives or calculate vertical pitch angles. [ev: 376e36, 8633cf]

## Verify before submitting
- Check OSM object type requirements: distinguish between individual building ways and encompassing site/campus perimeter way IDs or relations before submitting. [ev: 1d4232, 0e33b7]
- Verify exact word lengths and separator format against challenge pattern (e.g. `HackCTF{7_9_6_4}` or `Diver26{LastName1_LastName2}`) to eliminate ambiguous official vs colloquial brand names or title prefixes. [ev: 376e36, 786867]
- Anchor coordinate pins against discrete surface ground markings (zebra stripes, parking stall lines, adjacent public parks) visible on satellite imagery rather than relying on distant horizon line-of-sight. [ev: 8633cf, 49cb47]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| YouTube | Locating full broadcasts, news specials, music videos, and road trip footage | 5 |
| Google Lens / Reverse Image Search | Identifying corporate logos, stadium rooflines, aircraft liveries, and DPRK facilities | 5 |
| Google Search | Discovering broadcast archive links, news articles, and corporate directories | 4 |
| OpenStreetMap | Extracting Way IDs, inspecting campus perimeter relations, and coordinate placement | 4 |
| Google Maps (3D, Satellite, Street View) | Overhead satellite alignment, elevated highway tracing, and façade verification | 4 |
| ffmpeg / ffprobe | Keyframe sampling at fixed intervals and inspecting container encoder metadata | 2 |
| Yandex Maps (Panoramas) & 2GIS | Navigating street-level panoramas and local business directories across CIS regions | 1 |
| Wikimapia | Locating educational and governmental facilities in North Korea | 1 |
| NotebookLM | Ingesting video/audio for multimodal transcription and foreign-language summarization | 1 |
| Czech Cadastral Office portal (ČÚZK) | Querying public land parcel ownership records from street addresses | 1 |
| TikTok | Verifying recent local business presence and storefront signage | 1 |
| Pillow | Stitching downsampled video frames into contact sheet grids | 1 |

## Worked micro-traces
- `[ev: 8633cf]` **Arlington Stadium YouTube Short Geolocation**:
  - *Given*: YouTube Shorts clip of a Japanese speaker saying "I'm excited" outdoors with a curved stadium roof in the background, requiring Google Maps coordinates within 20m.
  - *First look & wrong turn*: Attempted direct calculation of 20m standing coordinates from the cropped background and AT&T Stadium line-of-sight; focal compression across the vast parking facility created unacceptable positional ambiguity.
  - *Pivot*: Switched from visual mapping to subject OSINT. Searched the viral spoken quote on YouTube to retrieve the full uncropped news broadcast, identified the interviewee as KNB announcer Hirochika Nakakuki, and searched KNB's official channel for behind-the-scenes World Cup coverage.
  - *Solve & verify*: Located KNB's special broadcast containing an alternate-angle camera at timestamp 11:46 showing the interview from behind; aligned distinct pavement zebra stripes, parking gates, and bollards on Google Maps satellite view to pin exact coordinates `32.748160, -97.086044`.

- `[ev: 49cb47]` **Tokyo Shuto Expressway Debris Drop Point**:
  - *Given*: Text prompt describing a Japanese TV news documentary broadcast on 2025-12-08 following patrol car 108 recovering a fallen bulk bag on an expressway, requiring drop point coordinates within 50m.
  - *First look & wrong turn*: Searching the TV air date located the YouTube news recording (incident starting at 9:43). Solvers initially contemplated visual highway scanning across the network, which would take hours.
  - *Pivot*: Transcribed audio patrol dispatch and lower-third captions ('上りの護国寺合流先' past Gokokuji merge, '首都高 池袋線 Route 5') to collapse the search radius to a 200m inbound section. At 10:59, the bag lay directly next to an elevated building marked 'FUKU...', identified as printing company 'フクイン' on Google Maps 3D.
  - *Solve & verify*: The challenge map picker ran on OpenStreetMap, which omitted the private corporate name 'フクイン'. Solvers cross-referenced adjacent public landmarks to find '関口三丁目公園' (Sekiguchi 3-Chome Park) on OSM, placing the pin on the expressway beside it at `35.713272, 139.729549`.

- `[ev: bc3176]` **Kazakhstan Music Video Overpass & Café Identification**:
  - *Given*: YouTube music video URL featuring travel footage; solvers must identify the Latin name of a newly opened café closest to a covered pedestrian overpass shown in one scene.
  - *First look & wrong turn*: Reverse image searching the generic pedestrian overpass returned thousands of highway bridges worldwide with zero matches.
  - *Pivot*: Scanned the multi-scene montage for a distinctive anchor asset. At 0:58, an airliner with Air Astana livery at a terminal matched Almaty International Airport via Google Earth 3D. Filtering the overpass image search with keyword 'Almaty' instantly located a local road trip video showing the exact overpass.
  - *Solve & verify*: Enhanced storefront signage at 1:13 revealed 'Qara Qazan', confirmed as an Almaty café on TikTok. Because Google Street View was absent, solvers navigated Yandex Maps Panoramas and 2GIS to verify the location, and resolved a discrepancy between 2024 street imagery and the video by inspecting recent user-contributed photospheres at an adjacent renovated market.

## Weak signals (single source — treat as hints, not rules)
- Feed foreign-language broadcast clips directly to multimodal LLMs (e.g. NotebookLM) with audio understanding to transcribe named facilities without manual phonetic guessing. [ev: 0e33b7]
- Query specialized state media watchdog archives (e.g. KCNA Watch) when hunting broadcasts from closed or restricted regimes (North Korea) where YouTube removes or blocks official state accounts. [ev: 1d4232]
- Use Wikimapia to locate military, governmental, or educational institutions in North Korea when Google Maps returns empty search results. [ev: 1d4232]
- Query national or municipal land cadastre portals (e.g. ČÚZK in the Czech Republic) with street addresses from corporate branch locators to retrieve legal property owner surnames. [ev: 786867]
- Cross-reference user-contributed photospheres or business TikTok accounts to verify storefront signage when official street panoramas (Yandex/Google) are several years out of date. [ev: bc3176]
- Downsample video frames (e.g. `ffmpeg -vf "fps=1/3,scale=960:-1"`) into 2x2 contact sheets to bypass playback motion blur and review full panning sequences at a glance. [ev: 376e36]
- Check container metadata with `ffprobe`; if `Lavf` or FFmpeg re-encoding signatures appear, immediately abandon metadata and raw binary regex scans as time-wasting decoys. [ev: 376e36]
