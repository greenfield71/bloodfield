# Document and Media Container Metadata Forensics

> category: osint · slug: `document-media-metadata-forensics` · evidence: 12 writeups from 10 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Challenge provides a downloadable document, media file, or 3D asset (DOCX, PDF, PNG/JPEG, MP3/WAV, FBX) suspected of concealing author traces, timestamps, or hidden payloads. [ev: 6df928, a8af6e, cf345c, c668c1]
- Media file is hosted on a CMS/CDN (WordPress, blog) where URL query parameters (`?w=1024`) or visual truncation indicate transformed or cropped assets. [ev: bab68f, c5288c]
- File exhibits superficial decoys, automated service accounts (`svc-docgen`), or bait flag prefixes that contradict internal container properties. [ev: 6df928, a8af6e, 8f4074, ab3361]
- Handout contains chronological photo sequences or multimedia without GPS coordinates, where EXIF timestamps or location branding establish physical movement. [ev: d955d3, d657e7]
- Investigation narrative describes user attribution or infostealer traces concealed in local client export metadata. [ev: 51a29b, cf345c]

## Opening sequence (do in this order)
1. **Container & Header Triage (exiftool / strings)** — inspect container tags with `exiftool -a -u` and scan raw strings (`strings -a` / text editor) for Author, Creator, LastModifiedBy, Source URL, software/AIGC tags, or local client paths (`C:\Users\...`); time-box 2 min. Why: Metadata properties and leaked filesystem paths frequently yield direct author attribution without rendering the asset. [ev: 51a29b, c668c1, cf345c, d657e7]
2. **OOXML Archive Unpacking (unzip / grep)** — if inspecting Office Open XML files (.docx, .xlsx), unpack as zip archives (`unzip -q file.docx`), inspect `docProps/app.xml` for template paths, and grep `word/document.xml` for revision marks (`<w:del>`, `<w:ins>`, `<w:comment>`); time-box 3 min. Why: Desktop office suites hide tracked deletions in default views or scrub them upon saving, whereas raw XML exposes deleted text and real author usernames. [ev: 6df928, a8af6e]
3. **WordPress resize-parameter stripping** — if the image is served from WordPress.com with a resize query (`?w=1024`), remove the query string and download the original file, then re-run `exiftool`; time-box 2 min. Why: seen once: the resized delivery was a WebP with no metadata, the original JPEG kept the Exif `UserComment`. [ev: c5288c]
4. **Dimension & Chunk Integrity Audit** — for images with truncated content or abnormal boundaries, check if decompressed payload scanlines match declared header dimensions (e.g. PNG IDAT vs IHDR height) or if LSB planes contain riddles; time-box 5 min. Why: Authors alter header dimensions or LSB planes to conceal data while leaving the file format structurally valid. [ev: bab68f, ab3361]
5. **Chronological Itinerary & Profile Pivoting** — map intact EXIF timestamps to order events chronologically or pivot from metadata handles/URLs to external creator profiles (Suno, Spotify, threat intel API); time-box 5 min. Why: Container metadata frequently serves as an anchor bounding a geographic radius or pointing to external multi-stage platforms. [ev: d955d3, c668c1, 8f4074, 51a29b]

## Decision points
- **IF** the file is an Office container (.docx, .xlsx) **THEN** unpack it as a zip archive and correlate `docProps/app.xml` template paths with `word/document.xml` `<w:del>` author attributes **ELSE** do not rely on visible signatures or `docProps/core.xml` creator tags. [ev: 6df928, a8af6e]
- **IF** a WordPress.com image URL carries a resize query (e.g. `?w=1024`) and the download has empty metadata **THEN** strip the query string and fetch the original **ELSE** continue with container triage on the file as delivered. [ev: c5288c]
- **IF** an author username or workstation handle is recovered from metadata **THEN** cross-reference the challenge narrative: IF infostealer/malware is mentioned, query threat intelligence breach databases (e.g. Hudson Rock Cavalier API) for infection paths and directory GUIDs; ELSE enumerate social media and creator profiles using the handle. [ev: 51a29b, cf345c]
- **IF** metadata lacks GPS coordinates **THEN** use intact EXIF timestamps to order the photos chronologically and anchor the search radius to the most identifiable primary landmark **ELSE** extract coordinates directly from place pins rather than map viewport centers. [ev: d955d3, d657e7]
- **IF** an extracted flag candidate has the wrong competition prefix or mockery text (e.g. `AXIOS{...}`, `KPMG_CTF{n0t_th3_r34l_0n3}`) **THEN** treat it as a decoy or secondary password for the next asset stage **ELSE** submit only after verifying prefix and formatting constraints against prompt rules. [ev: 8f4074, ab3361]
- **IF** analyzing a specialized or unfamiliar exported format (e.g. 3D model FBX, office document) **THEN** search for `<format> metadata privacy` or `<format> 個人情報` to check for known path disclosures in headers **ELSE** avoid spending time disassembling complex geometry or rendering layouts in heavy GUI suites. [ev: 6df928, cf345c]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Leaked local workstation path (`C:\Users\<username>\...`) inside template metadata (`app.xml`) or 3D model headers (FBX) → reveals the real human author, bypassing sanitized document bylines and anonymous social personas. [ev: 6df928, a8af6e, cf345c]
- Decoy / non-matching flag prefix or riddle text embedded in media → re-purpose the extracted string as a decryption key or password for the subsequent staging archive. [ev: 8f4074, ab3361]
- Missing GPS coordinates paired with intact EXIF timestamps / town-level metadata → establish tight geographic anchor or chronological itinerary to isolate venue or regional archive. [ev: d955d3, d657e7]
- URL query parameters (`?w=1024` or web asset paths) stripping or hiding underlying media assets → inspecting network/source URLs reveals uncropped or uncompressed raw files with intact metadata. [ev: c5288c]

## Dead ends & stop-loss
- **Trusting document bylines or `core.xml` creator fields** — abandon after 5 min; authors routinely use decoy compliance officers or automated service accounts (`svc-docgen`); real attribution resides in `app.xml` template paths or revision tags. [ev: 6df928, a8af6e]
- **Opening container files in GUI rendering software (Word, Blender)** — abandon immediately; standard viewports render only final layout or geometry, hiding tracked deletions (`<w:del>`) and container header paths; always inspect raw XML/strings first. [ev: 6df928, cf345c]
- **Treating audio or media files as complex steganography before checking metadata** — abandon after 5 min if no obvious signals; avoid running blind LSB/spectral demodulation before inspecting container ID3/EXIF tags for source URLs or creator profiles. [ev: c668c1, 8f4074]
- **Submitting the first extracted flag string with wrong format wrapper or taunts** — stop immediately; strings with mismatched prefixes (e.g. `AXIOS{...}` vs expected format) or taunts are decoys or decryption passwords. [ev: 8f4074, ab3361]
- **Searching for generic hospitality or architectural features without anchoring location** — abandon after 10 min; chronological photo sequences without GPS require anchoring the municipality from the primary landmark before searching thematic POIs. [ev: d955d3, d657e7]

## Author tricks / decoys seen
- Disguising human authorship behind automated service accounts (`svc-docgen`) or superficial bylines in document metadata to distract from filesystem paths. [ev: 6df928, a8af6e]
- Planting decoy flags or acrostic strings that fail platform prefix validation to mislead solvers into bad submissions or encrypt subsequent stages. [ev: 8f4074, ab3361]
- Hiding data in non-rendered portions of media containers (tracked deletions `<w:del>` in OOXML, header strings in 3D models) while standard viewports render clean assets. [ev: 6df928, cf345c]
- Distracting solvers with complex media analysis (spectral analysis, steganography tools, 3D mesh rendering) when the payload or key is in plain metadata or container headers. [ev: c668c1, cf345c]

## Verify before submitting
- Cross-validate author identity across at least two independent container artifacts (e.g. `app.xml` template path, `<w:del w:author="...">` revision attribute, and signature initials). [ev: 6df928, a8af6e]
- Confirm flag wrapper prefix and formatting restrictions against challenge instructions (e.g. short Plus Code `XXXX+XX` vs full code, directory GUID without curly braces, Title Case romaji name). [ev: d955d3, 51a29b, cf345c]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| exiftool | Extracting EXIF, IPTC, and ID3 metadata tags (Author, Source URL, timestamps, GPS) | 4 writeups |
| Google Search | Cross-referencing organizer blogs, venue decor, and county archives | 4 writeups |
| unzip / Python zipfile | Unpacking OOXML (.docx/.xlsx) containers to access internal XML files | 2 writeups |
| Text editor (Notepad / strings / grep) | Auditing raw ASCII headers in 3D models (FBX) and grepping XML revision tags | 3 writeups |
| Web browser / DevTools (F12) | Inspecting image URLs, stripping CDN resize parameters, and inspecting page markup | 3 writeups |
| Python 3 (struct, zlib, OLC, hashlib) | Recalculating PNG IHDR dimensions, CRC32 patching, Plus Code derivation, and decryption | 4 writeups |
| Google Lens / Reverse Image Search | Identifying landmarks, historical scenes, and uncropped photograph sources | 2 writeups |
| Google Maps / Open Location Code | Verifying venue location pins and converting coordinates to short Plus Codes | 1 writeup |
| Hudson Rock / Cavalier API | Querying compromised victim logs for infostealer malware execution paths and GUIDs | 1 writeup |
| Audio Spectrogram / Player | Visualizing frequency spectrograms and listening to hidden audio cues | 1 writeup |
| morsecode.world audio decoder | Automated transcription of rhythmic audio beeping pulses into plaintext | 1 writeup |
| Blender | Inspecting 3D geometry of exported models before falling back to container headers | 1 writeup |

## Worked micro-traces
- `[ev: 6df928]` Given a compliance memo in .docx format visually signed by M. Reyes. Opening `docProps/core.xml` showed the decoy author and an automated modifier `svc-docgen`. Instead of accepting changes in Word (which strips deleted content), unpacked the file as a zip archive and checked `docProps/app.xml`, discovering local template path `C:\Users\akessler\AppData\...`. Grepped `word/document.xml` for `<w:del>` and recovered a deleted whistleblowing paragraph signed 'AK' with attribute `w:author="akessler"`. Triangulated the author across all three artifacts to extract the final flag.
- `[ev: c5288c]` Given a WordPress blog post claiming a Tokyo Station photo was taken with a new camera, with task to identify the AI generator. Initial browser right-click download delivered a WebP image with zero Exif metadata tags. Avoided wasting time attempting visual AI style attribution and inspected DevTools to examine the network asset URL. Discovered the image URL ended in resize parameter `?w=1024`; stripping the parameter downloaded the original uncompressed JPEG file. Inspecting the raw JPEG Exif UserComment tag revealed embedded AIGC provenance JSON identifying the Dreamina AI service.
- `[ev: cf345c]` Given a target persona's tweet sharing an FBX 3D model via Gigafile with a prompt asking for the creator's real name. Opening the file in Blender displayed only the accessory geometry and no identifying author data in the 3D viewport. Avoided deep-diving into mesh geometry, textures, or materials, and researched documented FBX container leakage vectors. Opened the FBX in a text editor to audit raw ASCII header strings, immediately finding the absolute local path `C:\Users\shiharu_nanaogi\Documents\...`. Formatted the extracted username into the prompt's required Romanized Title Case format.

## Weak signals (single source — treat as hints, not rules)
- When prompt mentions infostealer malware, query Hudson Rock Cavalier API with extracted username to retrieve infection `malware_path` and directory GUID. [ev: 51a29b]
- When challenge artifact is an AI music track (MP3), check ID3 `Source URL` to pivot to creator profile on Suno and assemble base64 fragments across all uploaded tracks. [ev: c668c1]
- When a challenge prompt has zero attachments and references "the past", audit organizer retrospective blog posts and HTML comments for hidden scoreboard crop clues. [ev: bab68f]
- In self-contained synthetic CTF universes (offline case files), respect documented adversary opsec rules to eliminate false-positive candidate passwords. [ev: ab3361]
- When target is a globally famous historical photograph, scrutinize format constraints (credited professional surname vs birth surname, exposure date vs catastrophe date). [ev: 0cd353]
- When audio contains rhythmic pulse tones, feed into automated Morse decoders and correlate unique transcript phrases with local county archives. [ev: d657e7]
- Recalculate true PNG rows from decompressed IDAT stream length and patch IHDR height chunk when image displays truncated tables. [ev: bab68f]
- When deriving coordinates from embedded Google Map iframes, extract marker pin or place ID coordinates rather than iframe `?center=` viewport parameters. [ev: d955d3]
- If decrypting an encrypted payload with a candidate key, verify magic bytes (e.g. `PK\x03\x04` for ZIP) rather than relying solely on successful PKCS#7 padding checks. [ev: ab3361]
- Check whether an extracted string is an incomplete fragment; an open brace indicates distributed fragments across related assets. [ev: c668c1]
