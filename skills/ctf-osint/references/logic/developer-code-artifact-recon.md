# Developer Footprint and Code Repository Recon

> category: osint · slug: `developer-code-artifact-recon` · evidence: 16 writeups from 11 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Target repository default branch is empty, cleaned, or shows only minimal boilerplate while challenge narrative implies leaked secrets or developer mistakes. [ev: d0d9b9, 8fdd83, 194bde, 974b1d]
- Challenge revolves around developer OPSEC failures, force-pushed commits, credential redaction, or accidental exposure. [ev: 248f8a, 8fdd83, 194bde, 4d7517]
- Developer handle connects code repositories (GitHub, GitLab, SVN) with social footprints (Twitter/X, Bluesky, LinkedIn, forums). [ev: 536e14, 9f4b12, 248f8a, fb687b, 745209, d6d01d]
- Public profiles feature non-code artifact surfaces such as SSH keys (`.keys`), custom dotfiles, PR/issue comments, or profile metadata fields. [ev: 579079, 248f8a, fb687b]
- Target handle appears in commit sign-offs or author emails, leading to real identities or alternate profile usernames. [ev: 248f8a, 8fdd83, 194bde]
- Clues hint at vintage software, retro hobbyist developer tooling, or historical web archives. [ev: 745209, aff7de, 96f17e]
- E-commerce or simulated web app initiates network exfiltration or links to secondary developer repositories and mock domains. [ev: 4d7517, 06f1fa]

## Opening sequence (do in this order)
1. **Audit git history and log objects** — clone repository and run `git log --all -p` or `svn log`; search diffs with challenge keywords; time-box 3 min. Why: commits frequently contain leaked keys or endpoints later cleaned in head. [ev: d0d9b9, 974b1d, 96f17e, 745209]
2. **Harvest unreferenced SHAs from public activity feeds** — query GitHub user `/activity` or atom feed to identify force-pushed/orphan commit hashes and fetch `/<repo>/commit/<sha>.patch`; time-box 4 min. Why: force-pushed commits are not purged from GitHub storage and remain directly accessible by SHA. [ev: 8fdd83, 194bde]
3. **Inspect non-code profile and hidden repository surfaces** — check `https://github.com/<user>.keys`, profile bio/company fields, issue comments, PR descriptions, and hidden directories like `.maude/` or `.github/`; time-box 4 min. Why: authors routinely stash flags in public key comments, metadata fields, or agent configs. [ev: 579079, 248f8a, fb687b]
4. **Grep codebases for hardcoded constants and network endpoints** — search repository files for URLs, S3 buckets, coordinates, and base64 strings; time-box 3 min. Why: repositories often serve as pivots pointing to external buckets or geographic locations. [ev: 974b1d, fb687b, d6d01d]
5. **Trace developer aliases across external platforms and archives** — pivot secondary usernames across LinkedIn, Twitter, Bluesky, and forums, and check Wayback Machine snapshots for deleted interactions; time-box 5 min. Why: cross-platform personas link to external blogs, Pastebins, or deleted posts holding keys. [ev: 536e14, 9f4b12, 745209, d6d01d]
6. **Inspect web requests and simulated infrastructure** — check DevTools Network tab for external exfiltration domains or search in-game forums for simulated service names; time-box 4 min. Why: challenges with mock services or compromised web apps communicate with author-controlled staging domains or repos. [ev: 4d7517, 06f1fa]

## Decision points
- **IF** the repository tree appears clean or commits were rewritten **THEN** query the GitHub `/activity` feed or user events API for orphan commit SHAs **ELSE** search full local commit history using `git rev-list --all | xargs git grep <pattern>`. [ev: d0d9b9, 8fdd83, 194bde]
- **IF** no flag is visible in committed code files **THEN** audit external profile metadata (`.keys`, bio, company, issue comments, PR descriptions) **ELSE** inspect repository configuration dotfiles and hardcoded constants. [ev: 579079, 248f8a, fb687b]
- **IF** a social media lead or persona post appears deleted on live platforms **THEN** query historical snapshots on the Wayback Machine (web.archive.org) **ELSE** examine high-resolution profile banners and avatars for hidden text watermarks. [ev: 536e14, 9f4b12, 745209]
- **IF** commit history is flooded with dozens of dummy commits **THEN** filter logs by challenge title keywords or check commit date distributions for contribution grid art **ELSE** review diffs sequentially. [ev: d0d9b9, 745209, 96f17e]
- **IF** the developer profile references retro protocols or vintage hardware **THEN** access the service using dedicated CLI tools (`lynx`, `curl`) over `gopher://` **ELSE** inspect modern web traffic in DevTools Network tab. [ev: aff7de, 96f17e, 4d7517]
- **IF** an encoded string decodes to an author teaser or garbled output **THEN** inspect the transformation pipeline for inverted steps (e.g., reverse after base64 decode) or check for alternative Unicode tag layers **ELSE** submit the recovered string. [ev: fb687b, 06f1fa]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Orphan commit hash in GitHub `/activity` feed → indicates force-pushed revision containing author secrets → append `.patch` to commit URL to read original diff. [ev: 8fdd83, 194bde]
- Repository root contains custom hidden directory (`.maude/`, `.github/`) → holds agent configuration or workflow scripts → decode nested base64 and string inversion to extract payload. [ev: fb687b, 579079]
- Deleted interaction or dead profile link on social media → content was indexed before deletion → inspect Wayback Machine captures to recover linked associate accounts or Pastebins. [ev: 745209, 536e14]
- Floating-point coordinates or external cloud storage URLs in source constants → problem shifts from code review to spatial/infrastructure tracking → reverse-geocode coordinates or inspect remote S3 assets. [ev: 974b1d, d6d01d]
- Unusually high commit count on a dummy file (e.g., 400+ commits) → timestamps form visual contribution art on GitHub activity calendar → plot commit dates to render pixel text. [ev: 745209, d0d9b9]
- Personal website links to a `gopher://` URL → author uses retro protocols for developer services → read gopher hole via `lynx` to extract donation address or contact flag. [ev: aff7de, 96f17e]
- Initial decoded string contains author trolling or placeholder text → challenge contains layered encoding or secondary files → search for alternative codepoints (Unicode tags) or sibling config files. [ev: 06f1fa, fb687b]

## Dead ends & stop-loss
- Guessing flags from thematic repository documentation or scientific papers — abandon after 2 failed attempts; it failed because exact CTF flags with leetspeak/punctuation cannot be inferred from subject prose. [ev: 579079, aff7de]
- Reverse-searching generic stock profile avatars — abandon after 10 min if results yield thousands of stock catalog hits; it failed because creators use stock photos as placeholders while hiding textual clues in banner corners or custom graphics. [ev: 536e14, 9f4b12]
- Manually inspecting every commit one-by-one in flooded repositories — abandon if commit log exceeds 30 entries without keyword hits; it failed because noise commits are generated to waste time; use automated grepping or commit date analysis. [ev: d0d9b9, 96f17e, 745209]
- Deobfuscating minified frontend JavaScript before observing runtime traffic — abandon immediately; it failed because minified libraries are standard bundles while network requests and domain root pages directly expose author repositories. [ev: 4d7517, 06f1fa]
- Investigating third-party video creators linked in persona posts — abandon when channel content is unrelated; it failed because the creator is an uninvolved bystander and the persona only interacted via comment sections. [ev: 536e14, 9f4b12]
- Reversing encoded base64 strings before base64-decoding — abandon when decoding throws padding or invalid character errors; it failed because string reversal was applied to the plaintext before encoding, requiring decode followed by reverse. [ev: fb687b, 248f8a]

## Author tricks / decoys seen
- Commit flooding: generating hundreds of identical or dummy commits to hide a single modified revision or encode calendar pixel art. [ev: d0d9b9, 745209]
- Decoy constants and troll messages: embedding dummy base64 strings or zero-width payloads that decode to explicit author mockery ("this constant does nothing"). [ev: 06f1fa, fb687b]
- Visual watermarking: concealing secondary handles or URLs in low-contrast corners of social banners or avatar graphics to evade text search. [ev: 536e14, 9f4b12]
- Force-push wiping: rewriting repository history to give the illusion of an empty repository while leaving commit objects recoverable via activity feeds. [ev: 8fdd83, 194bde]
- SSH key abuse: embedding flag strings directly into authorized public keys at `https://github.com/<user>.keys` with substituted characters. [ev: 579079, 248f8a]
- Inverted or chained transformations: applying string reversal, base64 encoding, or multi-part splits across diverse profile and repo surfaces to break naive automated extractors. [ev: 579079, fb687b]

## Verify before submitting
- Validate syntax across multi-part flags: verify flag prefix, separator underscores, and curly braces match expected competition format across all gathered pieces. [ev: 579079, fb687b]
- Test recovered keys against challenge tooling: execute local decryption or validation scripts with recovered passwords to ensure valid plaintext output. [ev: fb687b, 745209]
- Verify municipal POI candidates against prompt naming rules (e.g. CamelCase, park classification) after resolving hardcoded coordinates. [ev: d6d01d, aff7de]
- Confirm commit timestamps and activity dates fall within the challenge release window or prompt timeline constraint. [ev: 579079, 745209]
- Filter out non-base64 characters or stego padding: verify decoded payload structure before submitting raw output. [ev: 248f8a, fb687b]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| git / GitHub Web UI | Auditing commit history, inspecting diffs, tracking `/activity` feed, viewing `.keys` and `.patch` endpoints | 10 |
| Python (general/PIL/requests) | Fetching APIs, parsing JSON/Unicode, decoding base64/reverse strings, plotting commit contribution grids | 7 |
| curl / urllib | Querying GitHub API, downloading raw patch diffs, and testing web endpoints | 4 |
| Google Search | Discovering developer social profiles, personal websites, and indexed blogs | 3 |
| svn | Querying retro Subversion repository commit logs and revision diffs | 2 |
| Wayback Machine | Recovering deleted social media posts, old profile revisions, and historical links | 2 |
| lynx | Accessing legacy Gopher protocol URLs (`gopher://`) on developer servers | 2 |
| Browser DevTools | Inspecting dynamic exfiltration traffic (Network tab) and inspecting web requests | 2 |

## Worked micro-traces
- `[ev: 8fdd83]` Given GitHub user `DNetWalker` and repository `Secure-LLM-Gateway`. Solver cloned the repository but found only clean boilerplate code on `main` and no active branches. Rather than bruteforcing commit hashes, solver queried the user's public GitHub `/activity` feed and spotted an unreferenced commit SHA from a force-push event. Navigating to `https://github.com/DNetWalker/Secure-LLM-Gateway/commit/<sha>.patch` immediately recovered the deleted diff containing the secret flag.
- `[ev: 745209]` Given an AI newspaper clipping of Karl Heisenburger, solver pivoted from a Bluesky profile to a deleted thread recovered via Wayback Machine, revealing associate @hank-loves-brewing. A blurred Pastebin URL on a monitor in Hank's photo yielded a GitHub repo with an image encryption script and a repo with 480 suspicious commits modifying a dummy file. Grepping git diffs for a password failed because the diffs were identical. Solver pivoted to analyzing commit date distribution: plotting the commit frequency per calendar day with Python PIL rendered a 7xN pixel-art grid displaying the decryption key `14m7h30neWh0Kn0ckzzz`.
- `[ev: fb687b]` Given in-game forum chatter about an operative's code tool 'Maude', solver searched GitHub for 'DEADFACE Maude' and located the target repository. Solver initially attempted to decode base64 constants in `build.js`, which turned out to be author decoys with mocking taunts. Solver pivoted to exploring the hidden `.maude/` directory, discovering agent prompt files and an obfuscated string in `payload-gen`. Inverting the author's pipeline (first base64-decoding, then reversing the string) recovered the valid flag.

## Weak signals (single source — treat as hints, not rules)
- Unicode Tag characters (codepoints 0xE0000 to 0xE007F) hidden alongside zero-width spaces in forum post text to bypass standard zero-width decoders. [ev: 06f1fa]
- Domestic social network APIs (e.g. draugiem.lv JSON-RPC) allowing guest-session lookups to bypass login gates when developer handles indicate a specific country. [ev: bc1fcf]
- Image EXIF comment fields pointing to legacy API endpoints in multi-hop cloud relay repos. [ev: 974b1d]
- Hardcoded coordinate constants (`base_lat`, `base_lon`) in Python source files pointing to municipal parks for geolocation challenges. [ev: d6d01d]
- Submitting organizer support tickets when an external third-party comment (e.g. YouTube) is shadowbanned or missing due to platform anti-spam filters. [ev: 536e14]
