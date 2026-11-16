# Chronolocation, Solar Shadows, and Event Timing

> category: osint · slug: `chronolocation-sun-shadow-timing` · evidence: 8 writeups from 7 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Challenge provides an image, video, or persona profile and asks for the exact date, timestamp, minute, or chronological sequence of an event. [ev: ea14c6, 1c170d, 8bf611, 630a99, 04179d]
- Scene contains temporary event infrastructure (stages, festival banners, reception booths, marathon bibs) or anomalous infrastructure use (pedestrians on motor expressways). [ev: ea14c6, 8bf611, 630a99]
- Provided file preserves internal timestamp or sensor metadata (EXIF `DateTimeOriginal`, GPS, embedded Motion Photo video), or points to downloadable raw review photos that do. [ev: 1c170d, 04179d, ce7b5a]
- Permanent landmarks, building facades, or geographic terrain are identifiable, but the temporal anchor (year, day, or minute) is the primary unknown. [ev: ea14c6, d9ef67, ba53c7, 630a99, ce7b5a]
- Prompts state or imply specific date/time formats, tolerances (e.g. ±3 minutes), or day-of-week constraints. [ev: 1c170d, 630a99, 04179d]

## Opening sequence (do in this order)
1. **Triage embedded file metadata (`exiftool`)** — inspect raw files immediately for `DateTimeOriginal`, GPS coordinates, camera model, and container video streams (e.g. `Motion Photo: 1`); time-box 2 min. Why: Metadata extraction is instantaneous and can yield the exact minute or narrow the timestamp window completely without visual guesswork. [ev: 1c170d, 04179d, ce7b5a]
2. **Geolocate venue and macro-landmarks** — run reverse image search (Google Lens) on wide shots, architectural facades, or distinctive terrain (elevated bridges, intersections, shorelines) to anchor city and venue; time-box 5 min. Why: Chronolocation requires a spatial anchor before local event calendars, solar azimuths, or flight corridors can be queried. [ev: ea14c6, ba53c7, 8bf611, 630a99, ce7b5a]
3. **Isolate single-day ephemeral props & temporary signage** — scan frame margins for stage banners, temporary reception booths ("報道受付"), exhibition posters, or ceremonial props (flags, podiums); time-box 5 min. Why: Permanent architecture gives only location, whereas temporary event collateral narrows multi-year site history down to an exact calendar day. [ev: ea14c6, ba53c7, 8bf611, 630a99]
4. **Search constrained municipal schedules, tour dates, and exhibition listings** — query discovered event names, performer strings, or road closures constrained strictly by the identified venue name or city; time-box 5 min. Why: Broad search queries produce noise, while venue-constrained queries immediately return official schedules and press releases. [ev: ea14c6, 8bf611, 630a99]
5. **Correlate verified timestamps with authoritative external telemetry** — if an exact or coarse timestamp is known, query domain-specific external logs (official race leaderboards, historical ADS-B flight replays, public transit timetables) rather than deblurring noisy pixels; time-box 10 min. Why: Regulated competitions, flights, and municipal events maintain second-by-second records that eliminate visual ambiguity. [ev: 1c170d, ce7b5a]

## Decision points
- **IF** the raw image or downloadable user upload retains EXIF metadata (`DateTimeOriginal`, GPS) **THEN** pivot immediately to authoritative time-stamped logs (live sports timing sheets, flight replay, map timelines) **ELSE** isolate visual chronological clues (event signage, solar alignment, street clocks). [ev: 1c170d, 04179d, ce7b5a]
- **IF** reverse search on a cropped event logo or banner yields ambiguous/generic matches **THEN** append the identified venue or city name as a search constraint **ELSE** query the unconstrained crop. [ev: ea14c6, 8bf611]
- **IF** the scene contains both long-term infrastructure/construction and temporary event staging **THEN** date the temporary event performer/banner **ELSE** use construction phases only as broad year/season bounds. [ev: ea14c6, 630a99]
- **IF** signage text or characters are blurry, low-contrast, or ambiguous under poor lighting **THEN** apply aggressive contrast adjustment/channel curves before searching band/event names **ELSE** search the plain text directly. [ev: ea14c6, 1c170d]
- **IF** a review platform or web UI displays only relative timestamps (e.g. "7 years ago") **THEN** download original user-uploaded photos to inspect raw CDN-hosted EXIF tags **ELSE** extract timestamps from DOM or API payloads. [ev: 04179d, 1c170d]

## Pivot triggers (the "aha" signals that cracked these challenges)
- **Blurry character stems distorting entity search** → letters appearing to have diacritics (e.g. `_aü` vs `Kaj`) were contrast artifacts → apply extreme contrast curves to reveal true lettering, unlocking single-date concert listings. [ev: ea14c6, 1c170d]
- **Anomalous or restricted public usage of urban infrastructure** → pedestrians walking on an elevated expressway or closed bridge indicate a permitted public festival → search municipal closure/walk event records to pin the exact weekend. [ev: ea14c6, 630a99]
- **Exact EXIF timestamp without legible visual target** → night race car numbers or distant plane registrations are unreadable due to compression/blur → query official minute-by-minute external telemetry (race leaderboards, ADS-B replay) synchronized to the EXIF time. [ev: 1c170d, ce7b5a]
- **Platform frontend displays only coarse relative timestamps** → web UI shows "7 years ago" or strips metadata → download original user-uploaded images and extract raw `DateTimeOriginal` from CDN-hosted files. [ev: 04179d, 1c170d]

## Dead ends & stop-loss
- **Pixel-peeping and filter-tuning on compressed, blurry, or low-resolution numbers** — abandon when 2-3 contrast adjustments yield conflicting candidate readings; it failed because high-compression codecs (HEVC/JPEG) introduce noise artifacts that look like digits. Pivot to external timing sheets. [ev: 1c170d, ce7b5a]
- **Reconstructing dates from broad municipal construction, renovation, or railway closure logs** — abandon when logs span multi-week or multi-month maintenance windows; it failed because long-term work does not distinguish specific event days. Pivot to single-day performers or event banners. [ev: ea14c6, 630a99]
- **Treating blown-out highlights or dark shadows as empty scenes** — abandon concluding an object was absent based on uniform white or black pixels; it failed because dynamic range clipping destroys contrast between light objects and the sky. [ev: ba53c7, ea14c6]
- **Searching guessed words or names with diacritics from low-contrast crops** — abandon when initial searches for apparent foreign characters return zero relevant results; it failed because low-contrast shadows simulate umlauts or accents. Re-process the image before re-querying. [ev: ea14c6, 1c170d]

## Author tricks / decoys seen
- **Landmark substitution in official media captions**: Press releases, government tweets, or photo captions name prominent landmark backdrops (e.g. India Gate, major transit hubs) rather than the precise sub-venue (e.g. adjacent park lawn) where the event took place. [ev: ba53c7, 8bf611]
- **Stripped GPS but retained timestamp (or vice-versa)**: Setters strip geographic GPS coordinates while intentionally leaving `DateTimeOriginal` intact (or toggle metadata availability between parts of a challenge series), forcing reliance on visual landmarking fused with historical telemetry. [ev: 04179d, ce7b5a]
- **Visual decoys in multi-use areas**: Prominently visible adjacent facilities (television studios, ongoing track repairs, work vehicles) mislead solvers into searching unrelated filming or maintenance schedules instead of the temporary stage/banner in the background. [ev: ea14c6, 630a99]
- **Social media post timestamps as temporal decoys**: Social media posts claiming recent presence (e.g. "just arrived in Kansai") reuse photos taken days or weeks earlier during high-profile events. [ev: 8bf611, 04179d]

## Verify before submitting
- **Cross-check secondary temporal constraints (day of week, daylight vs 12-hour clock)**: If a clock or timestamp shows 04:15 or 10:14, verify daylight conditions, scheduled operating hours, or AM/PM context to ensure 24-hour compliance (e.g. 16:15 vs 04:15, 22:14:12 EST). [ev: 1c170d, 630a99]
- **Validate date against simultaneous physical constraints**: Cross-reference the identified event date with concurrent site conditions (construction progress, weather, solar angle, or teammate positioning). [ev: ea14c6, 1c170d, 630a99]
- **Inspect exact flag formatting requirements**: Verify date and time separators (`YYYY-MM-DD` vs `YYYY/MM/DD`, 24-hour vs 12-hour, underscores vs hyphens, popular press spelling vs formal place name). [ev: ba53c7, 8bf611, 630a99]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Google Search | Querying event banners, tour dates, municipal road closures, and news archives | in 6 writeups |
| Google Lens | Reverse image search for architectural landmarks, venues, and cropped logos | in 5 writeups |
| exiftool | Extracting `DateTimeOriginal`, GPS coordinates, and Motion Photo embedded streams | in 3 writeups |
| Image editing (contrast/curves) | Aggressive contrast and luminance adjustment on low-visibility signage | in 2 writeups |
| SunTrace3D / SAF tables | Simulating 3D solar azimuth and validating bi-annual urban solar alignments | in 1 writeup |
| ADS-B Exchange | Historical flight replay mode synchronized to photo capture timestamp | in 1 writeup |
| ffmpeg / ffprobe | Extracting video streams and individual frames from smartphone Motion Photos | in 1 writeup |

## Worked micro-traces
- `[ev: 1c170d]` Given a blurry night photo of race cars (`20260124_221412.jpg`) with a hint about leaders "twinning". First look inspected the image visually, but car numbers were indecipherable; `exiftool` revealed GPS coordinates at Daytona Speedway, timestamp `2026:01:24 22:14:12 -05:00`, and an embedded HEVC Motion Photo. Wrong turn extracted 192 frames with `ffmpeg` and tuned contrast filters to decipher digits, producing conflicting noisy numbers (`9, 48, 4, 42`). Pivot recognized 22:14:12 marked Hour 9 of the 2026 Rolex 24 at Daytona, abandoning pixel-peeping for official NBC Sports timing PDFs. Solve: Hour 9 leaderboard confirmed Porsche Penske teammates Car 6 leading Car 7 (`texsaw{6_7}`).
- `[ev: 630a99]` Given a YouTube video of a sunny urban Japanese crossing requiring `Diver26{YYYY-MM-DD_HH:mm}`. First look used Google Lens on building facades to identify Sukiyabashi Crossing in Ginza, Tokyo, while an exhibition banner reading "100 80 60" established the year as 2026 via Ginza Sony Park archives. Wrong turn risked computing solar angles from shadows, but at timestamp 0:06 pedestrians were spotted walking on the elevated Tokyo Expressway (KK line). Pivot queried "ginza highway pedestrian 2026" to find Tokyo's "Roof Park Fest & Walk" on Saturday, April 25, 2026, then read an in-frame street clock showing 4:15. Solve: Daylight confirmed 16:15 local 24-hr time (`Diver26{2026-04-25_16:15}`).
- `[ev: ba53c7]` Given an undated black-and-white photograph of a crowd on a lawn before India Gate and a domed canopy. First look identified the India Gate architecture, but an overexposed empty canopy caused a wrong turn: solvers assumed the King George V statue was absent, falsely concluding a post-1968 date. Pivot noticed a tiny flagpole at the monument top edge indicating a ceremonial flag hoisting, matching Indian Independence on 15 August 1947, and recognized that official captions naming "India Gate" substituted the landmark for adjacent parkland. Solve: Historical press records confirmed Nehru's flag unfurling occurred on the adjacent lawn using popular press spelling Princess Park (`trace{Princess_Park_1947-08-15}`).

## Weak signals (single source — treat as hints, not rules)
- Astronomical axial alignment ("Manhattanhenge" / bi-annual sunset axes): When prompt describes the sun setting directly over a monument or along a street axis, check local astronomical society records or 3D solar ephemeris (SunTrace3D) for recurring bi-annual alignment dates. [ev: d9ef67]
- Biographical date offset deduction ('environ une semaine avant'): When narrative text specifies an approximate offset from an astronomical event, tabulate candidate birthdates within a ±3-day window across group members (e.g. Bourbaki founders). [ev: d9ef67]
- Historical ADS-B flight replay for aerial photos: When an aerial window photo provides a capture timestamp but stripped GPS coordinates, visually locate the departure runway/climb path via macro water bodies and replay ADS-B Exchange telemetry at that minute. [ev: ce7b5a]
- Disambiguating multi-runway airport departures: When flight replay returns multiple simultaneous departures during the timestamp window, filter candidates by aircraft bank angle, climb heading, and airline livery. [ev: ce7b5a]
- Embedded Motion Photo video extraction: When a smartphone JPEG contains `Motion Photo: 1` in EXIF tags, use `ffprobe` and `ffmpeg` to extract the embedded MP4/HEVC video clip to examine movement or alternative angles. [ev: 1c170d]
- Cross-referencing prompt narrative hints for telemetry validation: Match author clues (e.g. "like to twin around this time of night") against known team structures (e.g. Porsche Penske twin factory cars) on official leaderboards. [ev: 1c170d]
- Google Maps reviewer CDN metadata: When a review platform UI obfuscates exact calendar dates behind relative strings ("7 years ago"), download uploaded food/venue review photos to recover original `DateTimeOriginal` tags from CDN-hosted files. [ev: 04179d]
- Review candidate category pre-filtering: Restrict image downloads and metadata parsing to specific categories mentioned in prompt (e.g. food/restaurant) and coarse relative age (~7-8 years) to minimize network overhead. [ev: 04179d]
- Distinguishing landmark backdrops from actual event grounds: When public agencies or news sources caption an event with an iconic monument name, verify whether the actual gathering took place on adjacent park lawns. [ev: ba53c7]
- Testing popular press and search-engine spellings: When challenge flags reject formal academic archival place names (e.g. Princes Park), test the most common contemporary newspaper spelling (e.g. Princess Park). [ev: ba53c7]
- Elevated viewpoint perspective alignment: Align vertical bridge infrastructure (lift shafts, support towers) with track perspective lines on aerial imagery to pinpoint camera coordinates. [ev: ea14c6]
- Storefront and cultural exhibition banner dating: Determine the exact year or season of a recent street video by querying short-run exhibition campaigns (e.g. Ginza Sony Park exhibition titles). [ev: 630a99]
- Disambiguating venue reception sign queries: Search exact Japanese strings on temporary reception signs (e.g. "ご招待・報道受付") paired with the venue name ("大阪城ホール") to find specialized corporate concert schedules. [ev: 8bf611]
- Debunking social media travel alibis: Verify whether venue reception signage and operational setups align with the claimed posting date or reveal a previous event date. [ev: 8bf611]
- Visible analog clock in the frame: resolve the 12-hour AM/PM ambiguity from ambient daylight and the event's operating hours (4:15 read as 16:15). [ev: 630a99]
