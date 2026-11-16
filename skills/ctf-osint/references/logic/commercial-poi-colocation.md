# Commercial POI and Storefront Co-Location

> category: osint · slug: `commercial-poi-colocation` · evidence: 10 writeups from 7 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Photograph displays a commercial strip mall, retail cluster, gas station corridor, or dining facade with multiple visible business signs or adjacent tenant logos. [ev: 9ed8cd, 17d59d, a1cf9a, 22d6e4]
- Business names on primary signs appear generic or ubiquitous (e.g., "Tattoo", "Gift Shop", "McDonald's", "BP"), but secondary subtext, regional banners, or adjacent boutiques are partially visible. [ev: 9ed8cd, 17d59d, a1cf9a]
- Challenge prompt requires high-precision micro-targeting such as a what3words three-word address (`word1.word2.word3`), verified street address, or local postal ZIP code. [ev: 9ed8cd, d3ee48, f91c14, a1cf9a, 5f20fb, 17d59d, 22d6e4]
- Scene depicts commercial street furniture, specialized automated kiosks, high-voltage transmission lines, or highway route shields intersecting retail areas. [ev: 70eaac, 8b02a9, 17d59d, 22d6e4]
- Challenge description or title incorporates subtle wordplay, infrastructural nicknames, historical disaster dates, or host institution context (e.g., "Gateway to the Turnpike", "ohno", UT Austin vicinity). [ev: 70eaac, 17d59d, d3ee48, 22d6e4, 5f20fb, f91c14]

## Opening sequence (do in this order)
1. **Prompt semantic & host-context triage** — inspect the challenge title, description flavor text, and host CTF environment for puns, route nicknames ("Gateway to the Turnpike"), local geographic references, or author wordplay ("ohno"); time-box 2 min. Why: CTF authors frequently place intentional geographic constraints and chain name hints directly into flavor text, avoiding unconstrained global searches. [ev: 70eaac, 17d59d, d3ee48, 22d6e4, 5f20fb]
2. **Tight crop & reverse visual search** — crop tight boundaries around distinctive architectural elements, iconic highway service strips, or branded machines rather than full cluttered scenes; time-box 3 min. Why: Full images containing cars, skies, or windshield reflections degrade visual embeddings, whereas cropped logos and iconic junctions match indexed stock/travel photography instantly. [ev: 70eaac, d3ee48, 22d6e4, 5f20fb]
3. **Exact-phrase multi-business co-location query** — extract two or more distinct non-generic business names, adjacent boutique titles, or street signs visible in the scene and query them together in quotes (e.g., `"Haven Hair Studio" "The Blue Hen"`); time-box 5 min. Why: Multi-tenant co-location queries eliminate nationwide franchises and pinpoint unique multi-tenant retail plazas in standard search engines. [ev: 9ed8cd, 70eaac, 17d59d, a1cf9a]
4. **Specialized locator & infrastructure GIS pivot** — if standard mapping tools yield broad geographic clusters or image search fails, query specialized operator kiosk maps (e.g., Smart Exchange locator), official corporate directories, or vector infrastructure layers (OpenInfrastructureMap, OpenRailwayMap); time-box 5 min. Why: Specialized utilities, automated kiosks, and infrastructure intersections maintain dedicated coordinates absent from generic map scrapers. [ev: 70eaac, 8b02a9, 3eb7db]
5. **Street View perspective alignment & micro-grid resolution** — locate the building or intersection on Google Maps Street View, match camera angles and surrounding utility furniture, and resolve the requested geocode format (aerial building centroid vs. photographer stance on what3words, or local postal ZIP); time-box 5 min. Why: Strict 3m×3m what3words grids and municipal ZIP delivery boundaries diverge completely if coordinates shift by even a few meters. [ev: 9ed8cd, 17d59d, d3ee48, f91c14, 22d6e4, 5f20fb]

## Decision points
- **IF** multiple distinct business names appear on the same plaza facade **THEN** search the least common brand names enclosed in quotation marks together in Google Search **ELSE** crop the single most distinctive architectural feature or machine logo for reverse image search. [ev: 9ed8cd, 17d59d, a1cf9a, 22d6e4]
- **IF** a visible primary sign displays a generic business category (e.g., "Tattoo", "Gift Shop", "Roast Beef") **THEN** crop secondary subtext, window decals, banners, or route numbers for regional modifiers (e.g., "MAUI GIFTS", "5 Breezewood Rd", "ohno") **ELSE** search the primary business title directly. [ev: 9ed8cd, 70eaac, 17d59d, a1cf9a]
- **IF** reverse visual search returns generic fanart, unconstrained stock photos, or broad mountain vistas **THEN** switch to specialized GIS datasets (OpenInfrastructureMap, OpenRailwayMap) or dedicated brand locator maps **ELSE** inspect Google Maps Street View to confirm landmark perspective. [ev: 70eaac, 8b02a9, 17d59d, 22d6e4]
- **IF** reverse image search returns tourism aggregator pages (e.g., TripAdvisor listings) for a city **THEN** pivot immediately to local municipal/institutional registries or Street View to identify the specific building **ELSE** accept direct visual matches on verified map locations. [ev: 70eaac, d3ee48, 5f20fb]
- **IF** the challenge asks for a what3words 3-word triplet **THEN** determine from prompt phrasing whether the author targeted the building centroid (center of roof geometry) or the photographer's camera stance and test adjacent 3m×3m grid cells **ELSE** extract the verified street address or 5-digit USPS ZIP code from the commercial POI profile. [ev: 9ed8cd, d3ee48, f91c14, a1cf9a, 5f20fb, 17d59d, 22d6e4]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Multiple distinct business names on one plaza facade (e.g., "The Blue Hen" and "Haven Hair Studio 2") → plaza co-location immediately isolates a unique commercial lot → searched both names in quotes and retrieved the exact street address. [ev: 9ed8cd, a1cf9a]
- Interstate shields paired with a specific local road name (e.g., "I-70" and "5 Breezewood Rd") → iconic highway bottleneck and viral service strip rather than an anonymous exit → matched Breezewood, PA and resolved the postal ZIP code. [ev: 17d59d, 22d6e4]
- Reverse image search matches collegiate architecture near the hosting institution → CTF authors frequently shoot challenges around their own campus → focused on university neighborhood street view to pinpoint the photographer's exact stance. [ev: d3ee48, 5f20fb]
- Niche commercial hardware or branded kiosk visible in street furniture (e.g., yellow currency exchange machine) → vendor maintains a public online store locator with precise geolocation coordinates → intersected kiosk coordinates with candidate restaurant locations. [ev: 70eaac, 3eb7db]
- High-voltage power transmission pylon or level crossing in mountainous terrain → landscape features can be traced deterministically via specialized GIS layers → intersected OpenInfrastructureMap power corridors with OpenRailwayMap crossings. [ev: 8b02a9, 17d59d]

## Dead ends & stop-loss
- Querying generic franchise names or single ubiquitous business categories (e.g., "McDonald's", "BP", "Tattoo", "Gift Shop") — abandon after 3 minutes if results span hundreds of cities; it failed because national chains repeat at thousands of exits and commercial strips without isolating the plaza. [ev: 9ed8cd, 17d59d, a1cf9a]
- Unconstrained reverse image search on windshield-shot highway photos or stylized imagery — abandon after 3 minutes when results return generic anime fanart or stock highway scenes; it failed because visual clutter and image processing disrupt reverse search algorithms. [ev: 8b02a9, 17d59d, 22d6e4]
- Guessing random what3words squares across a large building footprint — abandon after 2 rejected submissions; it failed because what3words uses strict 3m×3m grid cells where each step completely changes the 3-word triplet; re-read the prompt to confirm centroid vs camera perspective. [ev: 9ed8cd, d3ee48, 5f20fb]
- Brute-force scanning entire metropolitan areas or mountain ranges on satellite imagery — abandon when candidate sets exceed manageable manual verification; it failed because subtle prompt puns or infrastructural intersection layers narrow the search area deterministically. [ev: 70eaac, 8b02a9]
- Relying on tourism aggregators or third-party travel blogs for building names — abandon after 5 minutes if tags list multiple adjacent attractions; it failed because aggregators bundle multiple city landmarks under a single photo tag. [ev: d3ee48, 5f20fb]

## Author tricks / decoys seen
- Prominent generic sign headers masking small regional subtext — large primary signs (e.g., "Merchandise & Gift Shop", "Tattoo") distract from critical small text or local road numbers. [ev: 9ed8cd, 17d59d, a1cf9a]
- Puns and institutional hints buried in challenge descriptions — hiding target business names or famous bottlenecks in conversational prose (e.g., "ohno" for Roast Beef Ohno, "Gateway to the Turnpike" for Breezewood). [ev: 70eaac, 17d59d, 22d6e4]
- Ambiguous what3words coordinate targets — leaving whether the 3-word square applies to the photographer's physical stance, the entrance door, or the building centroid unstated or subtly phrased. [ev: 9ed8cd, d3ee48, 5f20fb]
- Visual stylization or filters applied to landscape photos — applying artistic or blur filters to defeat naive reverse image search and force infrastructural GIS deduction. [ev: 8b02a9, 17d59d]

## Verify before submitting
- Align what3words targeting with prompt wording — verify whether the prompt requests the building centroid (center of roof geometry on satellite view) or the photographer's viewpoint on the street before picking the grid cell. [ev: 9ed8cd, d3ee48, 5f20fb]
- Confirm Street View perspective and facade alignment — ensure adjacent storefronts, utility poles, curb cuts, and background signage match the photograph in both geometry and historical date. [ev: 17d59d, f91c14, 22d6e4]
- Validate postal ZIP codes against official USPS or local municipal boundary data — verify that the physical address falls within the specified postal delivery district rather than an adjacent township or unincorporated county area. [ev: 17d59d, 22d6e4]
- Check historical timeline captures on Google Street View — toggle past street view passes ("See more dates") if current imagery shows different storefront tenants or missing temporary street furniture. [ev: f91c14, 3eb7db]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Google Maps / Google Earth | Storefront matching, satellite aerial inspection, Street View perspective verification | 8 |
| what3words | Translating micro-coordinates into 3-word grid triplets (3m×3m resolution) | 6 |
| Google Search | Multi-business exact-phrase co-location searches, brand lookup, news queries | 5 |
| Google Image Search / Lens | Reverse visual search for iconic highway junctions, collegiate facades, and logos | 4 |
| TripAdvisor | Cross-referencing city-level tourist attractions and restaurant branch listings | 2 |

## Worked micro-traces
- `[ev: 9ed8cd]` An image showed a commercial strip mall with storefront signs "The Blue Hen", "Tattoo", and "Haven Hair Studio 2", asking for the what3words address at the center of the building. Solvers avoided reverse image searching the generic "Tattoo" sign, which produces thousands of false hits across the country. Instead, they ran an exact-phrase Google search combining the two specific boutique names `"The Blue Hen" "Haven Hair Studio 2"`, instantly identifying the plaza at 271 US-6 in Mahopac, NY. Opening what3words satellite view, they aligned the building roof outline and selected the center 3m×3m grid square to retrieve the flag `///besides.vesting.sang`.
- `[ev: 70eaac]` An image `Summer_trip.jpeg` depicted Kenkaku Shoubai manga visuals, bilingual Japanese/Chinese/English signs, a yellow currency exchange kiosk, and adjacent dining signage. Rather than brute-force scanning hundreds of foreign currency exchange booths across Tokyo, the solver identified the yellow kiosk brand as "Smart Exchange" and opened its official locator map (`en.map.smartexchange.jp`). Noting the author's awkward "ohno" remark in the challenge prompt, the solver correlated it with the restaurant chain "Roast Beef Ohno". Intersecting the kiosk locator map coordinates with candidate Roast Beef Ohno branch locations immediately isolated the exact storefront in Akihabara, verified via Google Earth.
- `[ev: 3eb7db]` Target debeyohiru's Bluesky timeline showed a dinner check-in on January 10, 2026, requiring the exact Japanese menu item name. The target's January 10 post had text only ("came again tonight"), but traversing to the parent post in the thread revealed an omurice dish with a distinctive "Pomme no Ki" plate logo. Knowing the target operated in Shibuya, the solver identified the Shibuya Spain-zaka branch and inspected Google Maps reviews submitted specifically on 2026-01-10, discovering the target's review with a photo of a winter limited-time dish. Searching company campaign releases for the winter fair matched the dish photo to the exact Japanese title `豚肉とリンゴのホタテトマトクリームオムライス`.

## Weak signals (single source — treat as hints, not rules)
- Fetch missing challenge attachments directly from CTF platform APIs (e.g. MetaCTF challenge endpoint) using active session cookies when local challenge directories contain only markdown stubs. [ev: 17d59d]
- Cross-platform persona bridging from social media check-ins to date-filtered Google Maps restaurant reviews to uncover unposted meal photos. [ev: 3eb7db]
- Toggling Google Street View historical timeline imagery ("See more dates") to inspect temporary disaster barriers or post-incident construction features that have since been removed. [ev: f91c14]
- Intersecting specialized vector infrastructure datasets (OpenInfrastructureMap power line corridors with OpenRailwayMap level crossings) to locate rural mountain crossings when visual reverse search fails. [ev: 8b02a9]
- Searching corporate campaign press releases and promotional fair archives rather than standard permanent menus when reviews reference limited-time items (`限定メニュー`). [ev: 3eb7db]
