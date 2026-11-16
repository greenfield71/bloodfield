# OSINT logic index — route by signal

How to use:
1. Spend minutes 0-10 on the checklist in `SKILL.md` (Solver Mindset), then match what you see to a row below.
2. Open that playbook and follow its "Opening sequence" in order; respect each step's time-box.
3. Two rows match? Start with the cheaper/stronger one, keep the other as hypothesis #2.
4. Stuck > 20 min: re-read `meta_reasoning.md` (stop-loss, author tricks) and the playbook's "Decision points".
5. Before any submission, run the playbook's "Verify before submitting" list.
6. Strength = evidence base: strong (>= 8 writeups, many events), moderate (7 writeups, few events).

| Signal (minute 0-10) | Archetype | Playbook | Strength |
|---|---|---|---|
| Photo of campus facades, skyline, monument; view from an elevated window/balcony; EXIF stripped; asks for camera position / vantage building / what3words | Image landmark resection & viewpoint triangulation | [image-landmark-resection.md](image-landmark-resection.md) | strong (18 writeups, 10 events) |
| Rural road, power lines, pylons, railway, no famous landmark; full-image reverse search fails | Infrastructure & spatial GIS data mining | [image-infrastructure-gis.md](image-infrastructure-gis.md) | strong (15 writeups, 7 events) |
| Adjacent storefronts, strip-mall signs, restaurant logos, local-script business names | Commercial POI & storefront co-location | [commercial-poi-colocation.md](commercial-poi-colocation.md) | strong (10 writeups, 7 events) |
| Prompt asks exact minute/hour/date; sharp ground shadows from poles/buildings | Chronolocation, solar shadows, event timing | [chronolocation-sun-shadow-timing.md](chronolocation-sun-shadow-timing.md) | strong (8 writeups, 7 events) |
| Handle, alias, personal email, or one profile link; track a persona across the web | Username enumeration & SOCMINT pivot chain | [username-socmint-pivot-chain.md](username-socmint-pivot-chain.md) | strong (17 writeups, 13 events) |
| GitHub/GitLab profile, repo URL, commit hash; empty/cleaned main branch, leaked secrets | Developer footprint & code repository recon | [developer-code-artifact-recon.md](developer-code-artifact-recon.md) | strong (16 writeups, 11 events) |
| Company name, corporate domain, IP block, regulatory filing, funding round | Corporate entity & network infrastructure recon | [corporate-domain-network-footprint.md](corporate-domain-network-footprint.md) | strong (12 writeups, 9 events) |
| Attached DOCX/PDF/PNG/JPG/3D model/audio; hidden author traces, container oddities | Document & media container metadata forensics | [document-media-metadata-forensics.md](document-media-metadata-forensics.md) | strong (12 writeups, 10 events) |
| URL is 404 / parked / edited; question about a past state, past event, historical date | Web archive & historical temporal recon | [web-archive-temporal-recon.md](web-archive-temporal-recon.md) | strong (9 writeups, 7 events) |
| Boarding pass, ticket stub, flight track, ICAO hex, vessel MMSI/IMO, MAVLink telemetry | Transportation & telemetry tracking | [transport-telemetry-tracking.md](transport-telemetry-tracking.md) | moderate (7 writeups, 6 events) |
| Cryptic prose, literary quote, lyrics, historical hoax, game-world coordinates | Cultural lore, trivia, domain knowledge retrieval | [cultural-lore-knowledge-retrieval.md](cultural-lore-knowledge-retrieval.md) | strong (14 writeups, 11 events) |
| Video file, broadcast excerpt, YouTube URL, background sirens / transit announcements | Multimedia broadcast & video/audio recon | [multimedia-video-audio-recon.md](multimedia-video-audio-recon.md) | moderate (7 writeups, 3 events) |

Cross-cutting discipline (loop, hypothesis management, stop-loss, author tricks, AI failure modes, verification): [meta_reasoning.md](meta_reasoning.md).
