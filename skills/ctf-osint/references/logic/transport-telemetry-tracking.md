# Transportation and Telemetry Tracking

> category: osint · slug: `transport-telemetry-tracking` · evidence: 7 writeups from 6 events · strength: moderate

**When this applies (recognition, first 5 minutes):**
- Challenge provides travel media, boarding pass stubs, or transport photography containing machine-readable payloads or unstripped capture metadata. [ev: 4de930, 0b68cc]
- Scenario features maritime assets, cargo manifests, vessel radio intercepts, or port calls indexed by MMSI, IMO, or vessel callsigns. [ev: 8c4e57, 7d7aa7]
- Challenge supplies raw aircraft flight tracking logs, ADS-B transponder messages, squawk codes, or radar approach trajectories. [ev: 88dc55, 0b68cc]
- Problem demands reconstructing transit routes or subject movements governed by strict quantitative constraints (elapsed travel minutes or high-precision coordinates). [ev: 4a3522, e1029c]

## Opening sequence (do in this order)
1. **Extract machine-readable payloads and metadata** — inspect images for intact 2D barcodes (PDF417 / IATA BCBP) or run `exiftool` to harvest GPS coordinates and capture timestamps before doing visual analysis; time-box 3 min. Why: machine metadata unlocks deterministic identities, routes, and times directly without OCR errors. [ev: 4de930, 0b68cc]
2. **Resolve transient identifiers to permanent structural IDs** — convert mutable names, painted markings, or radio MMSI into immutable structural identifiers (IMO registration numbers or standard 3-letter IATA airport pairs); time-box 5 min. Why: painted vessel names change or drop spaces and ticket text is often redacted, while IMO and IATA codes uniquely index arrival ledgers and flight routes. [ev: 8c4e57, 4de930, 7d7aa7]
3. **Filter and reconstruct movements via historical tracking databases** — query historical flight tracking platforms (ADS-B Exchange replay, FlightAware) or maritime port arrival ledgers using resolved IDs and spacetime windows; time-box 10 min. Why: scheduled ticket times or theoretical itineraries differ from actual historical touchdown or berthing times due to delays. [ev: 4de930, 0b68cc]
4. **Isolate target trajectories from routine background traffic** — apply quantitative movement filters (altitude stability to separate low fluctuating surveillance orbits from level holding patterns, or directional stop ordering across transit lines); time-box 10 min. Why: 2D heading sweeps alone match civilian holds and background traffic, creating high false-positive rates without vertical or topological filtering. [ev: 4a3522, 88dc55]

## Decision points
- **IF** challenge provides a document or photo with machine-readable data (PDF417 barcode or EXIF GPS/timestamp) **THEN** decode the barcode or replay the spacetime coordinate on ADS-B trackers **ELSE** reconstruct movement via network topology and schedule calculators. [ev: 4de930, 0b68cc]
- **IF** vessel or transport names are informal, spoken, or visually altered **THEN** resolve radio MMSI or callsign to the immutable IMO/ICAO number before querying port/movement ledgers **ELSE** query tracking ledgers directly by registration. [ev: 8c4e57, 4de930, 7d7aa7]
- **IF** candidate routes or entities satisfy all hard quantitative/topological constraints but conflict with ambiguous semantic definitions (engineer vs scientist, or minor name spacing) **THEN** accept and test the quantitative candidate **ELSE** prune only based on numeric or waypoint violations. [ev: 4a3522, 7d7aa7]
- **IF** spatial centroid or database query returns only a partial segment of the flag **THEN** inspect secondary transponder channels (octal squawk codes, callsign hex tokens, or trailing polyglot bytes) **ELSE** format the verified findings into the flag wrapper. [ev: 8c4e57, 88dc55]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Unredacted barcode or metadata on redacted media → authors redact visible text but overlook machine-readable data → crop the 2D barcode for PDF417 decoding or run `exiftool` to recover flight route and capture timestamp instantly. [ev: 4de930, 0b68cc]
- Registry search returns minor name variation (e.g. dropped space) → vessel or entity underwent administrative rename → pivot to immutable IMO number to query port arrival ledgers unambiguously. [ev: 8c4e57, 7d7aa7]
- Circular flight paths show constant vs fluctuating altitude → civilian holding patterns maintain fixed flight levels (6,000–18,000 ft) while surveillance flights orbit low (<5,000 ft) and vary altitude → filter telemetry by altitude ceiling and variance to isolate the target aircraft. [ev: 88dc55, 0b68cc]
- Quantized spatial lookup returns default nulls or partial token → spatial grid requires multi-pass centroid averaging or transponder carries secondary steganographic text → average all low-altitude points across flights and decode squawk/callsign fields as ASCII. [ev: 8c4e57, 88dc55]

## Dead ends & stop-loss
- Deciphering blurred or redacted ticket labels via image enhancement — abandon when an intact barcode is present; it failed because OCR on low-resolution text hallucinates whereas PDF417 barcodes contain raw plaintext passenger and flight records. [ev: 4de930, 0b68cc]
- Querying movement ledgers using informal or painted names — abandon when searches return zero records; it failed because vessels and carriers undergo renames while structural identifiers (IMO, IATA) persist. [ev: 4de930, 7d7aa7]
- Cross-referencing auxiliary POI lists (e.g. `sites.csv`) provided in challenge archives — abandon when raw telemetry centroids fall kilometers away; it failed because authors insert distractor location lists to trap solvers doing relational joins. [ev: 4a3522, 88dc55]
- Relying on scheduled ticket times or news summaries for numerical data — abandon when exact times or coordinates fail; it failed because flights suffer real-world delays and news outlets truncate precision decimals required by sensor telemetry. [ev: 4de930, e1029c]

## Author tricks / decoys seen
- Providing auxiliary reference lists (e.g. `sites.csv`) where all listed coordinates are distractors located kilometers from the empirical telemetry centroid. [ev: 4a3522, 88dc55]
- Redacting human-readable passenger names and flight details while leaving the high-density 2D stacked barcode (PDF417) completely unredacted. [ev: 8c4e57, 4de930]
- Introducing minor orthographic renames (such as dropping whitespace: 'BRINE WALKER' → 'BRINEWALKER') to break direct string searches in port arrival ledgers. [ev: 4a3522, 7d7aa7]
- Embedding entire mock registries and port arrival databases directly into client-side JavaScript bundles (`/assets/index-*.js`) instead of hosting an active backend database. [ev: 8c4e57, 7d7aa7]

## Verify before submitting
- Cross-corroborate movement records against secondary identifiers (customs seal IDs, transponder callsigns, or waypoint stop order) to prove the specific event matches the witness record. [ev: 8c4e57, 7d7aa7]
- Query actual historical touchdown/arrival timestamps rather than scheduled itinerary departure/arrival times to account for operational flight delays. [ev: 4de930, 0b68cc]
- Format coordinates and measurements strictly according to prompt instructions: check whether airport codes require standard IATA vs city abbreviations, and strip thousands separators from decimal floats. [ev: e1029c, 0b68cc]
- Reassemble all required findings manually when validation endpoints return boolean status (`allCorrect: true`) without emitting a flag string. [ev: 88dc55, 7d7aa7]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Python (standard library, `hashlib`, `json`) | Telemetry parsing, heading delta calculation, centroid averaging, and transponder octal/hex decoding | 4 writeups |
| ADS-B Exchange / FlightAware | Historical ADS-B transponder flight replay and actual landing touchdown timestamp verification | 3 writeups |
| PDF417 / BCBP Barcode Reader (Dynamsoft) | Decoding stacked 2D boarding pass barcodes to extract IATA airport pairs and flight numbers | 1 writeup |
| Browser Developer Tools / JS Parser | Extracting mock vessel registers and port authority ledgers embedded in client-side React bundles | 1 writeup |
| Transit Route Planner (`bonjour-ratp.fr`) | Paris Metro line timetable calculations and topological waypoint constraint filtering | 1 writeup |
| Garmin inReach / MapShare | Reconstructing high-precision GPS expedition waypoints and elevation logs | 1 writeup |
| `exiftool` | Extracting intact GPS coordinates and capture timestamps from challenge photographs | 1 writeup |
| `binwalk` / `unzip` | Carving trailing ZIP polyglot payloads appended after image EOF markers | 1 writeup |
| Google Maps | Mapping observer coordinates relative to airport runway approach corridors | 2 writeups |

## Worked micro-traces
- `[ev: 88dc55]` Given a week of ADS-B telemetry across 16 aircraft, candidate sites, and a grid registry. The solver initially checked circular flight tracks for surveillance, but found civilian airport holding patterns also orbited. The solver pivoted by filtering for low altitude (<5,000 ft) with dynamic altitude fluctuations, isolating two surveillance aircraft (DCA418 and DCA522) whose shared orbit centroid unlocked spatial grid cell `47.620,-122.350` (`5a3f`) while discarding the decoy `sites.csv`. Final flag was assembled by decoding secondary transponder fields: squawk octal digits to 'over' and callsign hex to 'watch', yielding `number{overwatch_confirmed_5a3f}`.
- `[ev: 7d7aa7]` Given a dock scribe note describing a vessel 'BRINE WALKER' with shorter stern lettering, MMSI `257771420`, and cargo seal `EC-4418` on a web console. Initial instinct to search port arrival ledgers by the spoken name failed due to a recent rename. Solved by pivoting from the radio MMSI in the embedded client-side JS bundle to the permanent IMO `9384728` and current registered name `BRINEWALKER` (space dropped). Correlating the IMO with the port ledger and matching customs seal `EC-4418` confirmed berth `E-06` and previous port `Saltmere Roads`, allowing manual assembly of `HTB{BRINEWALKER_9384728_E-06_SALTMERE_ROADS}`.
- `[ev: 4de930]` Given an airline boarding pass image with blurred passenger text, flight date (Feb 15), and an unredacted 2D stacked barcode. Rather than wasting time on OCR or visual deciphering of the redacted ticket stubs, the solver cropped the barcode and parsed it using a PDF417 IATA BCBP decoder. The resulting text revealed cleartext origin/destination pair `KRRSVX` (Krasnodar to Yekaterinburg) and flight `U6 0210`. Instead of trusting scheduled arrival times, the solver looked up the actual historical landing on FlightAware for February 15, confirming touchdown at 21:39 local to format `KubSTU{U6210_Ekaterinburg_21:39}`.

## Weak signals (single source — treat as hints, not rules)
- Demands for high-precision decimal formatting (elevation to 2 decimal places, coordinates to 6 decimal places) indicate raw satellite tracking hardware feeds (e.g. Garmin inReach MapShare) rather than news summaries. [ev: e1029c]
- In AES-CBC decryption, corrupted plaintext in the first 16 bytes followed by clean plaintext indicates a valid key paired with an incorrect IV source (requiring a switch to the ciphertext prefix). [ev: 8c4e57]
- Trailing polyglot ZIP data appended after image `IEND` markers can be unlocked using radio identifiers (callsign, MMSI) from preceding scenario intercepts. [ev: 8c4e57]
- Intermediate transit waypoint constraints require confirming that the transit hub's stop sequence index lies strictly between origin and destination on the same route. [ev: 4a3522]
- Challenge authors occasionally conflate standard 3-letter IATA codes with colloquial city abbreviations (e.g. `NAS` instead of `BNA` for Nashville). [ev: 0b68cc]
- Circular ADS-B tracks: separate surveillance orbits from airport holding patterns by low, fluctuating altitude (<5,000 ft in that dataset; the threshold is dataset-specific). [ev: 88dc55]
