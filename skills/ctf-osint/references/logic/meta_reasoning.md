# Category Solving Discipline: OSINT

## 1. The Solver Loop for OSINT
- **Step 1 (Container audit)**: Run `exiftool` and unzip OOXML files before visual inspection; read EXIF time/GPS, author fields, revision XML, PNG IHDR size [ev: bab68f, 6df928, a8af6e, 0b68cc].
- **Step 2 (Scene decomposition)**: Crop and transcribe micro-signage, sign subtext, road names, route shields and utility-pole plates [ev: a1cf9a, 17d59d, ea14c6, b6bec9].
- **Step 3 (Scoping)**: Restrict the search to the CTF host campus, organizer blog posts, and the country given by script/plates before searching globally [ev: 8d47c8, 2be8e2, bab68f, 7fd1f0].
- **Step 4 (Cropped visual search)**: Reverse-search the distinctive crop, not the whole scene; for CIS scenes use Yandex Maps panoramas, 2GIS and Yandex Images [ev: 86786c, 22d6e4, bc3176, 694cad].
- **Step 5 (Relational triangulation)**: Search co-located business names together, or intersect features with Overpass QL / infrastructure layers (bridge x stream, rail x power line, brand x brand) [ev: 9ed8cd, b07eb3, 182e32, 8b02a9].
- **Step 6 (Resection and ground truth)**: Trace the sightline back from the visible landmark on 3D imagery; check the Street View date timeline when the present pano does not match [ev: 8d47c8, 2be8e2, 1e2154, 53850d].
- **Step 7 (Flag normalization)**: Match stated decimal places, sub-facility name, what3words cell, wrapper and character rules before submitting [ev: 6dc5f2, 0c7310, 9ed8cd, 0aa3ed].

## 2. First 10 Minutes: Ordered Checklist
- **Min 0-3 (Container audit)**: `file` + `exiftool`; unzip OOXML (`docProps/core.xml`, `docProps/app.xml`, `word/document.xml`); check PNG IHDR height against the data [ev: bab68f, 6df928, a8af6e, 51a29b].
- **Min 3-5 (Host grounding)**: Check the hosting university campus map and organizer blogs before any wide-area search [ev: 8d47c8, 2be8e2, 181713, bab68f].
- **Min 5-7 (Anchor inventory)**: Transcribe every shop name, sign subtext, road name, route shield and plate style [ev: 17d59d, a1cf9a, 9ed8cd, 7fd1f0].
- **Min 7-8 (Cropped search)**: Crop away water, sky and clutter; reverse-search the distinctive crop on Google Lens, Yandex and Bing [ev: 86786c, a1cf9a, 22d6e4, 1e2154].
- **Min 8-10 (Co-location / spatial bounding)**: Search co-located business names on Google Maps, or write an Overpass proximity/intersection query, to lock candidates [ev: 9ed8cd, b07eb3, 182e32, 0f19e3].

## 3. Routing: Signal -> Archetype Table
| Primary Recognition Signal | Target Archetype | Supporting Evidence |
| :--- | :--- | :--- |
| Campus facades, urban skylines, monument sightlines from elevated windows; stripped EXIF | `image-landmark-resection` | [ev: 8d47c8, 0c7310, 2be8e2, 181713] |
| Rural roads, transmission lines, railway switches, pylons, no famous landmarks; full image search fails | `image-infrastructure-gis` | [ev: 182e32, 8b02a9, 0f19e3, 18d72f] |
| Adjacent storefronts, strip mall signs, restaurant logos, local script business names | `commercial-poi-colocation` | [ev: 9ed8cd, 70eaac, a1cf9a, 17d59d] |
| Prompt requests exact minute/hour/date; event signage, visible clock, solar alignment | `chronolocation-sun-shadow-timing` | [ev: ea14c6, d9ef67, 630a99, 1c170d] |
| Target handle, alias, personal email, or single profile link; tracking persona across web | `username-socmint-pivot-chain` | [ev: 141d2c, 01f908, 549549, be97e3] |
| GitHub/GitLab profile, repository URL, commit hash; cleaned branch or leaked secrets | `developer-code-artifact-recon` | [ev: 579079, 194bde, 8fdd83, d0d9b9] |
| Company name, corporate domain, IP, registry filing, funding round | `corporate-domain-network-footprint` | [ev: b3c636, 6d8d67, d3e556, bbaf8b] |
| Attached DOCX, PNG/JPG, FBX 3D model, audio file; hidden author traces | `document-media-metadata-forensics` | [ev: bab68f, 6df928, cf345c, c668c1] |
| URL returns 404, edited page, login wall; past state or historical dates | `web-archive-temporal-recon` | [ev: af2f0d, 7bc9b1, 864c93, 843fe7] |
| Boarding pass, plane photo with EXIF, ADS-B tracks, MMSI/IMO, transit constraints | `transport-telemetry-tracking` | [ev: 4de930, 0b68cc, 88dc55, 7d7aa7] |
| Cryptic prose, lyrics, historical hoaxes, game guides, video game coordinates | `cultural-lore-knowledge-retrieval` | [ev: c215e0, 8f0604, 94bf88, dd938d] |
| Video file, broadcast excerpt, YouTube URL, spoken dialogue | `multimedia-video-audio-recon` | [ev: 376e36, 786867, 1d4232, 0e33b7] |

## 4. Hypothesis Management
- **Franchise / chain brand in frame**: Do not search the chain alone; combine it with a second co-located business or the road name + route shield to isolate one site [ev: 9ed8cd, b07eb3, 17d59d].
- **Landmark vs observer**: When the prompt asks where the photo was taken from, keep "the visible building" and "the building opposite along the sightline" as separate hypotheses; resolve on 3D imagery [ev: 8d47c8, 2be8e2, 1e2154, 181713].
- **Which name level the flag wants**: Hold several candidates — hall inside the complex [ev: 0c7310]; parent city / tenant company instead of suburb / building name [ev: a01bae]; actual venue vs the famous neighbour named in captions [ev: ba53c7].
- **Which entity the prompt means**: In multi-hop corporate prompts write out each hop and parse pronoun antecedents; for famous subjects separate credited name vs legal name and exposure date vs event date [ev: 6d8d67, 0cd353].
- **Named persona vs real target**: The person named in the brief may be a subordinate; the real target can appear only in a recovered orphan commit [ev: 194bde, 8fdd83].

## 5. Stop-Loss Rules
- **Uncropped visual search, 5 minutes**: If full-image reverse search returns only generic scenery after 5 minutes, switch to distinctive crops [ev: 22d6e4, 18d72f, 86786c].
- **Manual map / satellite scanning**: Stop scanning thousands of candidate features by eye; build a hard filter first (Overpass exclusion query, pole-plate grid code) [ev: 0f19e3, b6bec9].
- **Redacted WHOIS**: Do not re-query live WHOIS. Registrant question -> historical WHOIS (Whoxy) [ev: b3c636]; hosting question -> DNS A + IP WHOIS [ev: f75ae0]; hidden hosts -> crt.sh [ev: bbaf8b].
- **Rejected flag variants**: After plausible variants of a name or format fail, stop guessing and re-read signage, container metadata and prompt syntax [ev: 0c7310, bab68f, 579079, d6d01d].
- **Cold handle trail**: When live profiles give nothing, check Wayback snapshots of the profile and follow playlist / paste / gist links instead of spraying more usernames [ev: 745209, af2f0d, 8f4074].
- **Stylized or drawn imagery**: Reverse search on sketches or art-filtered images returns fan art; pivot to invariant scene features or textual entities (event, attendee, employer) [ev: a01bae, 8b02a9].
- **Plane photo with EXIF time**: Do not try to read tail numbers from pixels; replay historical ADS-B for that time and place [ev: 0b68cc, ce7b5a].
- **Repo with nothing in the code**: Stop browsing source; read issue comments, PR descriptions, profile fields, the activity feed and all commit objects (`git rev-list --all | xargs git grep`) [ev: 579079, 8fdd83, d0d9b9].

## 6. How Authors Trick You: Decoys and Misdirection
- **Decoy flags and foreign wrappers**: Plausible strings with another wrapper (`AXIOS{...}`), short zero-width-stego jokes, decoy DNS TXT fragments, pronounceable bait keys; the real payload matches the event format and the in-universe rules [ev: 8f4074, 06f1fa, c57c7d, ab3361].
- **Cleaned branches with orphan commits**: Secrets removed by force-push or buried under noise commits stay reachable through the GitHub activity feed, `.patch` URLs, or a grep over all commit objects [ev: 194bde, 8fdd83, d0d9b9].
- **Name-level traps**: The checker rejects the complex / suburb / caption landmark and wants the hall, parent city or actual venue [ev: 0c7310, a01bae, ba53c7].
- **Title object as a red herring**: The object named in the title, or the largest logo in frame (rental equipment), is not the search key; use permanent address / POI features and keep the object for confirmation [ev: f4eb7a, 921848].
- **Ambiguous prompt referents**: Vague antecedents and trivial-looking famous subjects hide which entity, name form or date is asked [ev: 6d8d67, 0cd353].

## 7. AI-Agent Failure Modes: Top Anti-Patterns
- **Submitting the top-level name**: Submitting the complex, suburb or caption landmark when the author keyed on the hall, parent city or actual venue; read the signage and the prompt first [ev: 0c7310, a01bae, ba53c7].
- **Full-image reverse search**: Searching the whole photo and drowning in generic matches; crop to one distinctive structure or sign [ev: 86786c, a1cf9a, 22d6e4, 1e2154].
- **Ignoring Street View history**: Treating the current pano as ground truth; open the date timeline when the confirmed location does not match [ev: 53850d, fed9c0, f91c14, 7fd1f0].
- **Wrong what3words / coordinate target**: Picking a cell without reading the prompt. Building centre -> centre cell of the roof [ev: 9ed8cd]; where the photo was taken -> photographer's stance [ev: d3ee48, 5f20fb]; then test adjacent 3 m cells. For lat/long of an area prefer the existing POI pin over a computed centroid [ev: c2be73].
- **Brute-forcing flag permutations**: Resubmitting variants after rejections instead of re-auditing artifacts and prompt syntax [ev: 0c7310, bab68f, 579079, d6d01d].
- **Submitting the landmark instead of the vantage**: Answering with the building in view; trace the sightline back to the observer's building [ev: 8d47c8, 2be8e2, 181713, 1e2154].
- **Scanning maps by eye**: Hours of manual satellite or road scanning with no filter; extract an infrastructure or administrative anchor and query it [ev: 0f19e3, b6bec9].
- **Persisting with live WHOIS**: Re-querying redacted WHOIS; choose historical WHOIS, IP WHOIS or crt.sh by what the question asks [ev: b3c636, f75ae0, bbaf8b].

## 8. Verification Discipline Before Submitting
- **Sightline confirmation**: Match foreground features and the distant landmark together from the candidate vantage on Street View / 3D before locking the answer [ev: 8d47c8, 1e2154, d3ee48].
- **Street View date audit**: Confirm the pano date matches the photo's era; use the historical capture when signage differs [ev: 53850d, fed9c0, f91c14].
- **Canonical identifier check**: When the prompt names OSM, compare the answer against the OSM `name` tag / way ID, not the Google Maps label [ev: 921848, 0e33b7, 1d4232].
- **Coordinate format check**: Match the prompt's decimal places (3, 4 or 6 in the cards), delimiter and spacing; keep trailing zeros when asked [ev: acfca6, c2be73, 6dc5f2, e1029c].
- **Actual vs scheduled times**: For flight or transit answers use tracked actual times (FlightAware, ADS-B replay) or the official timetable constraint, not an assumed schedule [ev: 4de930, 0b68cc, 4a3522].
- **Wrapper and character rules**: Re-read the flag format: required wrapper, stripped characters (`+`), brace substitutions [ev: 0aa3ed, 248f8a, 8f4074].

## 9. Weak Signals (< 2 Supporting Cards)
- **Mirrored window text**: Signage photographed through a window or in a reflection reads reversed; flip the image horizontally before OCR or search [ev: 921848].
- **WordPress resize parameter**: A WordPress.com image URL ending in `?w=1024` serves a metadata-stripped WebP; strip the query string to get the original with EXIF intact [ev: c5288c].
- **Thumbnail vs original**: Fine markings (USDOT numbers) are unreadable in compressed previews; download the original full-resolution file first [ev: d00b8f].
- **Player troll accounts**: An account matching the persona's handle but created during the competition may be a player troll; if a clue link is dead, ticket the organizers [ev: 536e14].
- **Certificate subject fields**: Self-signed TLS certificates leak organization names, admin emails and flags in their subject fields [ev: d3e556].
- **crt.sh results**: Open the response body of every discovered subdomain; do not filter by HTTP status [ev: bbaf8b].
- **Visible clock**: Resolve 12-hour AM/PM ambiguity from daylight and event hours [ev: 630a99].
- **Minecraft seed reconstruction**: Bedrock patterns are deterministic and can be inverted to the world seed from floor + roof coordinates [ev: dd938d].
- **Session UI chrome**: A country label in a map screenshot footer reflects the viewer's locale, not the photographed place [ev: 6dc5f2].
- **Media stego on an identification task**: Running binwalk / spectrogram analysis on a video that only needs to be identified; identify the content first [ev: aff7de].
