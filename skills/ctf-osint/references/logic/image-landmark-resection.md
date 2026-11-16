# Image Landmark Resection and Viewpoint Triangulation

> category: osint · slug: `image-landmark-resection` · evidence: 18 writeups from 10 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- An outdoor or elevated photograph showing campus buildings, urban facades, monuments, or rooftops with stripped or absent EXIF metadata. [ev: 8d47c8, 181713, 2be8e2, 1e2154, 8c6eff]
- Two or more distinct architectural or structural anchors visible at varying depths (e.g., foreground entrance/road fork and background tower, arena, or mast) suitable for line-of-sight resection. [ev: 8d47c8, 0c7310, 2be8e2, 1e2154, 8c6eff, 60b123]
- Challenge prompt asks for the observer's camera vantage point (building name, floor, or coordinates) rather than the prominent landmark visible in the center of the frame. [ev: 8d47c8, 181713, 2be8e2, 1e2154, fed9c0, 60b123]
- Street-level commercial imagery or road scenes where default or current Google Street View imagery does not match, indicating historical captures or recent construction. [ev: 53850d, fed9c0, 7fd1f0]
- Indoor exhibition placards, wire photographs, or restricted-context scenes requiring specialized platforms or thematic pivots rather than blind reverse image queries. [ev: c46289, 7b59fd, 1be2ea, 9ca8fd]

## Opening sequence (do in this order)
1. **Check competition host and prompt metadata constraints** — look for local university/club affiliations, series numbering, or domain keywords ("for sale", "official readout", "directly behind"); time-box 2 min. Why: Local CTF creators overwhelmingly photograph their own campus or neighborhood, instantly bounding the search area from global to local. [ev: 8d47c8, 0c7310, 2be8e2, 181713, 1e2154, e23ac7, 8c6eff]
2. **Extract high-entropy text, signage, and structural anchors** — look for business names, street intersection geometry (Y- or T-junctions), unique rooflines, water bodies, or prominent vertical towers; time-box 3 min. Why: Distinctive text or topological combinations prune 99% of map space faster than generic reverse image search. [ev: 0c7310, 8c6eff, 827920, b291e6, 7fd1f0]
3. **Targeted reverse search on isolated salient crops** — look for isolated architectural elements, exhibition placards, or wire photos using Google Lens, Yandex, or agency quotation templates; time-box 5 min. Why: Cropping out sky and generic ground avoids decor decoys and retrieves the specific property listing, press event, or landmark. [ev: e23ac7, 9ca8fd, fed9c0, 7b59fd, 1be2ea]
4. **3D Satellite & Street View resection** — look for the collinear alignment between two visible landmarks (foreground anchor + background anchor) to trace the camera sightline backwards to the observer's building/floor; time-box 10 min. Why: Prevents submitting the subject building instead of the camera vantage point. [ev: 8d47c8, 2be8e2, 181713, 1e2154, 60b123, 8c6eff]
5. **Inspect historical imagery timeline** — look for the Street View capture date selector (clock icon / "See more dates") if modern surroundings, storefronts, or road markings mismatch; time-box 5 min. Why: CTF authors frequently capture photos from older Street View passes (e.g., 2016 or 2023) or prior to recent construction. [ev: 53850d, fed9c0, 7fd1f0]

## Decision points
- **IF** challenge is hosted by a specific university or regional club **THEN** bound initial satellite and facilities map search strictly to the host campus or municipality **ELSE** extract regional meta (signage language, road markings, domain ccTLD) to isolate the country. [ev: 8d47c8, 2be8e2, 181713, 7fd1f0, 827920]
- **IF** the prompt asks for the vantage point or camera coordinates **THEN** identify the central landmark and resect backwards along the line of sight through foreground features to locate the photographer's building **ELSE** target the subject landmark or business directly. [ev: 8d47c8, 181713, 2be8e2, 1e2154, fed9c0, 60b123]
- **IF** candidate location in Google Street View shows mismatched modern facades or missing target objects **THEN** open the Street View date/history timeline selector and scrub through older capture passes **ELSE** verify nearby pedestrian photospheres or alternate intersections. [ev: 53850d, fed9c0, 7fd1f0, 1e2154]
- **IF** storefront signage or street signs are degraded or below OCR resolution **THEN** pivot to topological road layout (Y/T-junctions, parallel streets) and filter local POI categories **ELSE** query exact business names directly in Google Maps. [ev: 8c6eff, 0c7310, 827920]
- **IF** an image contains an exhibition board or archival photo within a venue **THEN** search for the curatorial exhibition theme or host museum **ELSE** search the depicted physical scene directly. [ev: 7b59fd, a37dc1]
- **IF** top-level complex or building name fails submission **THEN** inspect entrance marquee signage or directory maps for internal sub-facilities, halls, or auditoriums **ELSE** verify formatting delimiters and coordinate precision. [ev: 0c7310, 9ca8fd]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Two aligned landmarks at different depths (e.g., cell mast behind building entrance, foul pole against stadium rim) → defines an unambiguous 2D line of bearing → traced the sightline backward on 3D satellite view to pinpoint the exact building, floor, or seat. [ev: 8d47c8, 2be8e2, 1e2154, 60b123]
- Verified address or business in Street View looks completely different from the challenge photograph → author used an older Google Street View car pass → clicked the date selector / timeline in Street View to load the matching historical capture. [ev: 53850d, fed9c0, 7fd1f0]
- Top-level building name rejected on submission despite confirmed visual match → author flagged the specific internal venue, hall, or sub-facility → checked entrance marquee signage and campus directory boards in Street View. [ev: 0c7310, 9ca8fd]
- Unreadable storefront or blurry sign from an elevated or rear window → sign OCR will hallucinate; search area is bounded by spatial relation (e.g. "directly behind") → mapped the parallel rear street, matched intersection geometry (Y-junction), and filtered POI categories. [ev: 8c6eff, 0c7310]
- Image depicts a historical disaster or public event on an informational placard → the photo is an exhibition element, not the physical location → searched for museum exhibitions matching the curation topic to locate the venue. [ev: 7b59fd, a37dc1]
- Broad visual match on generic manufactured structure (e.g., mass-market gazebo or car model) → object alone yields endless false positives → correlated non-reproducible contextual landscape details (paver layout, retaining wall blocks, siding vents, tree lines) to confirm the exact property. [ev: e23ac7, a37dc1]

## Dead ends & stop-loss
- Submitting the prominent subject building visible in the center of the frame — abandon when the prompt asks where the photo was taken or where Waldo stood; it failed because the camera was located across the courtyard or on an opposite rooftop. [ev: 8d47c8, 181713, 2be8e2, 1e2154, 60b123]
- Relying on default/current Google Street View imagery — abandon when the candidate landmark matches the geographic area but modern buildings/decorations differ; it failed because the author captured the scene from historical Street View passes dating back years. [ev: 53850d, fed9c0, 7fd1f0]
- Global or unconstrained reverse image search on author-shot campus or outdoor photos — abandon after 3 minutes without exact matches; it failed because custom amateur snapshots of modern brick/panel buildings return thousands of lookalike campuses worldwide instead of the host university. [ev: 8d47c8, 2be8e2, 181713, 1e2154]
- Attempting OCR, digital sharpening, or deconvolution on degraded/blurry storefront signs — abandon after initial zoom fails; it failed because pixel interpolation creates false letterforms; vector road geometry and POI category filtering are vastly faster. [ev: 8c6eff, 0c7310]
- Geolocating the historical event depicted on an exhibition panel — abandon when the text indicates a commemorative or scientific exhibit; it failed because the flag requires the host museum/venue, not the historical disaster site. [ev: 7b59fd, a37dc1]
- Global environmental deduction (foliage, pavers, utility poles) on generic enclosed yards — abandon when no horizon or distinctive topography is visible; it failed because mass-manufactured outdoor goods appear identically across multiple regions; prompt clues point to indexed listing databases. [ev: e23ac7, 7fd1f0]

## Author tricks / decoys seen
- Vantage reversal decoy: placing a famous, easily identifiable landmark dead-center to trick solvers into submitting the target building rather than the photographer's camera location. [ev: 8d47c8, 181713, 2be8e2, 1e2154, 60b123]
- Time-lag / Historical Street View trap: selecting a viewpoint whose modern appearance has undergone renovation, demolition, or street repaving, forcing historical timeline navigation. [ev: 53850d, fed9c0, 7fd1f0]
- Secondary news syndication and transliteration drift: relying on prominent news outlets (which use varied transliterations or rewritten captions) to decoy solvers away from primary government readouts or wire service templates. [ev: 9ca8fd, 1be2ea]
- Content vs. Container decoy: showing an archival photograph of a historical disaster or concert prop inside a museum or venue, prompting solvers to geolocate the disaster coordinates instead of the exhibit hall. [ev: 7b59fd, a37dc1]
- Sub-facility / Marquee masking: hiding the accepted flag name under a specific sub-facility (e.g. Concert Hall) rather than the parent complex shown on maps. [ev: 0c7310, 9ca8fd]

## Verify before submitting
- Verify line-of-sight alignment in 3D Satellite / Earth view by checking that foreground and background anchors intersect the exact camera window or floor. [ev: 8d47c8, 2be8e2, 1e2154, 60b123]
- Check whether the prompt asks for the vantage point (where the photo was taken) vs the subject landmark (what is shown). [ev: 181713, 2be8e2, 1e2154, fed9c0]
- Match non-reproducible environmental micro-features (unique paving stones, siding vents, tree alignments, fence lines) before submitting residential or commercial candidates. [ev: e23ac7, 8c6eff, fed9c0]
- In Google Street View coordinate challenges, extract latitude and longitude from the camera position in the URL rather than the general map pin or building centroid. [ev: fed9c0, 7fd1f0]
- Check building entrance signage and official directory maps to verify whether the flag requires a sub-facility name or specific transliteration. [ev: 0c7310, 9ca8fd]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Google Maps | Vector maps, 2D satellite imagery, POI category inspection, and road topology | 10 |
| Google Street View / 3D imagery | Perspective verification, entrance marquee reading, and 360 photosphere inspection | 7 |
| Google Search / Lens | Crop-based reverse image search, text string queries, and business listing discovery | 10 |
| Google Street View Timeline / Date Selector | Navigating past capture passes (2016-2023) when current imagery has changed | 3 |
| Google Earth / 3D Satellite View | Line-of-sight sightline tracing and 3D architectural resection | 3 |
| Baidu Maps / Baidu Street View | Street-level imagery and POI mapping for locations in mainland China | 1 |
| REALTOR.ca | Commercial property listing galleries and syndicated real estate photo matching | 1 |
| Yandex Images | Face recognition and news agency press photo syndication searches | 1 |
| A View From My Seat / Seating Charts | Stadium perspective triangulation and seat section mapping | 1 |
| State Government Readout Portals (e.g., pid.gov.pk) | Authoritative official transliterations and diplomatic call-on press releases | 1 |

## Worked micro-traces
- `[ev: 0c7310]` Given an outdoor campus image showing a lake/pond, pedestrian bridge, and performance arena on George Mason University campus. First look identified Mason Pond and the adjacent Center for the Arts on satellite view. Wrong turn was submitting `pctf{center_for_the_arts}`, which was rejected by the scoring engine. Pivot occurred by zooming into Street View entrance photography to inspect marquee signage for sub-facilities. Solved by extracting `Concert Hall` from the entrance directory to submit `pctf{center_for_the_arts_concert_hall}`.
- `[ev: fed9c0]` Given a street-level photograph of a car dealership in a tropical setting asking for camera coordinates. First look matched the business facade via reverse image search to Straker Motors in Saint Croix, US Virgin Islands. Wrong turn occurred when modern Street View imagery showed updated lots and buildings that did not match the challenge perspective. Pivot was using the Street View timeline selector to navigate back to a September 2016 capture pass matching the exact photo angle. Solved by extracting the precise camera coordinates directly from the historical Street View URL.
- `[ev: 8c6eff]` Given a kitchen window photograph showing a rear street with rounded balconies and a blurry business sign, with intel stating the business sits directly behind a known safehouse. First look attempted OCR on the blurry storefront sign, which failed due to severe compression noise. Pivot was mapping the parallel rear street (Rue Antaki), identifying a distinctive Y-intersection geometry visible from the window, and filtering corner POIs by category for medical/dental practices. Solved by matching LM Dental Center and formatting its landline number into `SECOPS{0539373734}`.

## Weak signals (single source — treat as hints, not rules)
- Mainland China urban street scenes require pivoting from Google to Baidu Maps / Baidu Street View. [ev: c46289]
- Backyard property photos with "for sale" prompts index against syndicated real estate portals (e.g. REALTOR.ca) rather than standard map layers. [ev: e23ac7]
- Wire photography caption recovery benefits from querying agency quotation syntax (`"PHOTO /"`, photographer name) to bypass news aggregators. [ev: 1be2ea]
- Diplomatic meeting photos require retrieving official state government readouts (e.g. PID press releases) to resolve competing transliterations. [ev: 9ca8fd]
- Stadium perspective photos can be pinpointed by intersecting field boundary foul poles with stadium seating charts (e.g., A View From My Seat). [ev: 60b123]
- Stage prop vehicle identification can be resolved by searching kinematics and patent databases (Google Patents) for commercial drive assemblies. [ev: a37dc1]
- French cultural or colloquial puns in challenge titles ("Chaud devant") provide thematic clues to historical figures (volcanology cemetery graves). [ev: b291e6]
