# Corporate Entity and Network Infrastructure Recon

> category: osint · slug: corporate-domain-network-footprint · evidence: 12 writeups from 9 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Target is an IP address, custom web port (e.g. 8443), or corporate domain requiring server infrastructure, hosting provider, or unlinked relay identification. [ev: d3e556, bbaf8b, f75ae0]
- Investigation targets company names, subsidiaries, procurement filings, or complex corporate holding structures across multiple jurisdictions. [ev: 545204, 6b3080, e69afe]
- Challenge prompt specifies financial deal metrics ($79M Series B), accelerator cohorts (YC), executive career hops, or corporate sponsorships. [ev: 6d8d67, 6f1119, e69afe]
- Prompt features commercial vehicles (fleet trucks, cargo vessels) requiring corporate ownership and regulatory identifier lookups (USDOT, IMO) rather than scene geolocation. [ev: d00b8f, 545204]
- Leaked network infrastructure artifacts are provided, such as DNS zone transfer dumps (AXFR) or operational changelogs. [ev: c57c7d, bbaf8b]

## Opening sequence (do in this order)
1. **Scope and prompt keyword triage** — Parse the exact required entity (company name, founding date, hosting abuse contact, executive email) and isolate target identifiers from decoy goals (e.g., street geolocation or unrelated open ports); time-box 2 min. Why: Prevents getting trapped in elaborate visual or network rabbit holes when the flag strictly requires registry or certificate data. [ev: d3e556, d00b8f]
2. **Client-side bundle & source asset inspection** — If the target is a web-based corporate directory, simulated investigative desk, or SPA, inspect `/assets/*.js` in DevTools before navigating the UI; time-box 3 min. Why: Mock corporate registers, vessel fixtures, and procurement tables are frequently hardcoded client-side in the React/Vue bundle, eliminating manual UI clicking. [ev: 545204, 6b3080]
3. **Passive infrastructure & certificate metadata extraction** — For domains and IP targets, query Certificate Transparency logs (`crt.sh`) for unlinked subdomains, or dump TLS certificates using `openssl s_client -connect <host>:<port> -showcerts < /dev/null 2>/dev/null | openssl x509 -text -noout`; time-box 5 min. Why: Public CT logs expose hidden/dark hosts without noisy brute-forcing, while self-signed cert Subject fields leak internal emails, org names, or plaintext flags. [ev: d3e556, bbaf8b]
4. **WHOIS: pick the lookup by what is asked** — Question is about the hosting provider / abuse contact: resolve DNS A records and run IP WHOIS on the address (read `OrgName` / `OrgAbuseEmail`) [ev: f75ae0]. Question is about the registrant and domain WHOIS is privacy-redacted: query historical WHOIS (Whoxy), then reverse WHOIS on the recovered email [ev: b3c636]; time-box 5 min. Why: redacted live WHOIS answered neither question; IP WHOIS named the host, the historical snapshot named the registrant. [ev: b3c636, f75ae0]
5. **Regulatory & statutory identifier lookup** — Search authoritative government registries using primary compliance numbers (USDOT/MC for commercial vehicles, IMO for vessels, INN/CHE for foreign corporate registries); time-box 10 min. Why: Mandatory regulatory registries bypass missing branding and directly resolve physical assets to legal corporate entities. [ev: 545204, e69afe]

## Decision points
- **IF** the question is about the registrant and domain WHOIS is privacy-redacted **THEN** query historical WHOIS snapshots (e.g. Whoxy) for the original registrant contact [ev: b3c636] **ELSE IF** the question is about hosting / abuse contact **THEN** resolve DNS A records and query IP WHOIS [ev: f75ae0] **ELSE IF** the target is an unlinked host **THEN** search `crt.sh` [ev: bbaf8b].
- **IF** investigating an unlinked or dark host on a root domain **THEN** search Certificate Transparency logs (`crt.sh`) for issued TLS certs **ELSE** check DNS zone transfer records (AXFR) or correlate TXT records against changelogs. [ev: bbaf8b, c57c7d]
- **IF** a corporate ownership trail hits professional nominee directors, shell companies, or restricted-disclosure trusts **THEN** abandon top-down shareholding and pivot laterally to operational contracts, time charterers, commercial operators, or shared board directors **ELSE** trace parent holding companies directly. [ev: 545204, 6b3080]
- **IF** a challenge portal is a client-side SPA (React/Vue) **THEN** extract the entire entity graph directly from `/assets/index-*.js` **ELSE** query the backend API programmatically as a verification oracle. [ev: 545204, 6b3080]
- **IF** investigating a company with an entity suffix mismatch (e.g. US LLC with European presence) **THEN** search international trademark registries (EUIPO, WIPO) and statutory commercial gazettes (SHAB) across holding jurisdictions **ELSE** query domestic business registries. [ev: a01bae, e69afe]
- **IF** investigating corporate executive personas or extracted emails **THEN** pivot through developer/social footprints (Gravatar MD5, LinkedIn, GitHub) **ELSE** search news archives and corporate press releases. [ev: a01bae, d3e556]

## Pivot triggers (the "aha" signals that cracked these challenges)
- *Self-signed TLS certificate on custom port (e.g. 8443)* → X.509 Subject fields contain plaintext Organization or emailAddress → dump raw cert chain with OpenSSL to extract credentials, flags, and persona emails for downstream lookups. [ev: d3e556, bbaf8b]
- *Nominee shell directors or restricted-disclosure holding trusts* → Nominal ownership is an author decoy concealing beneficial control → pivot to commercial operating entities, charter agreements, or lateral director intersections across subsidiaries. [ev: 545204, 6b3080]
- *Historical WHOIS snapshot reveals unmasked registrant email* → Registrant reused personal/corporate email across multiple domains → execute reverse WHOIS (email-to-domains) and filter by specific TLD or keyword. [ev: d3e556, b3c636]
- *Multiple candidate subdomains all return HTTP 200 OK* → Status codes alone do not discriminate live servers from author decoys → diff HTTP response body sizes, DOM elements, and panel status indicators. [ev: bbaf8b, 6b3080]
- *Distinctive financial metrics ($79M Series B) or startup accelerator keywords (YC)* → Search query noise is eliminated by combining exact funding dollar amounts, round stages, and calendar months in quotes → isolate specific venture deals, executive biographies, or Substack exposes. [ev: 6d8d67, 6f1119]

## Dead ends & stop-loss
- *Geolocating street scenes or background terrain when prompt asks for corporate entity data* — abandon immediately when prompt specifies company ownership or founding date; street signs, intersections, and hills are author geo-bait decoys. [ev: a01bae, d00b8f]
- *Following nominee directors and anonymous/restricted trusts* — abandon after identifying nominee services or "restricted disclosure" trustees; real-world and CTF beneficial control sits in operational and commercial subsidiaries. [ev: 545204, 6b3080]
- *DNS wordlist brute-forcing against randomized or high-entropy hostnames* — abandon within 5 minutes if hosts use high-entropy numeric IDs or hashes; passive CT logs (`crt.sh`) reveal all issued hostnames instantly. [ev: bbaf8b, c57c7d]
- *Querying live WHOIS servers for privacy-redacted domains* — abandon live WHOIS queries immediately once privacy proxies (Withheld for Privacy, Domains By Proxy) are seen; switch to historical WHOIS archives (registrant question) [ev: b3c636] or IP WHOIS (hosting question) [ev: f75ae0].
- *Port scanning adjacent open ports on multi-challenge IP infrastructure* — abandon out-of-scope ports; multi-challenge infrastructure hosts unrelated tracks on adjacent ports. [ev: d3e556, bbaf8b]
- *Relying on browser GUI certificate viewers or compressed image previews* — abandon GUI inspectors and thumbnail previews; GUI certificate viewers truncate extended X.509 fields, and compressed previews blur regulatory compliance placards (USDOT). Use raw OpenSSL text dumps and full-resolution distfiles. [ev: d3e556, d00b8f]

## Author tricks / decoys seen
- *Geo-bait street furniture & landscape scenery:* Populating scene images with clear intersection signs, gas stations, or hills to bait solvers into wasting time geolocating rather than checking vehicle regulatory placards. [ev: a01bae, d00b8f]
- *Uniform HTTP 200 decoy web pages:* Setting up multiple candidate subdomains that all respond with identical HTTP 200 status codes, differing only in subtle DOM/body status panel text. [ev: bbaf8b, 6b3080]
- *Nominee corporate shells & restricted trusts:* Inserting top-level holding companies with nominee directors or "restricted disclosure" trustees to mislead solvers searching for beneficial owners. [ev: 545204, 6b3080]
- *Decoy enterprise TXT records:* Flooding leaked DNS zone files with realistic Microsoft (`MS=ms-fake...`) and SPF (`v=spf1...`) verification tokens that lack payload correlation serials. [ev: bbaf8b, c57c7d]
- *Lookalike corporate names & near-identical corporate naming variants:* Adding similarly named companies (e.g. Sorn & Associates vs Ash & Wick) in the registry requiring resolution via exact registration ID codes. [ev: 6b3080, e69afe]

## Verify before submitting
- Normalize flag string capitalization: Certificate Subject fields or raw strings may preserve uppercase prefixes (e.g., `Deadface{...}`), but scoring platforms require canonical lowercase prefixes (`deadface{...}`). [ev: d3e556, 6f1119]
- Confirm regulatory founding dates have strict zero-padding format (e.g. `MM_DD_YYYY` -> `08_10_1961`, not `8_10_1961`). [ev: d00b8f, e69afe]
- Confirm network contacts are hosting provider infrastructure contacts (via IP WHOIS / ASN) rather than domain registrar privacy contacts, verifying against official Terms of Service. [ev: b3c636, f75ae0]
- Validate multi-part corporate role findings against API check oracles or prompt templates before final submission. [ev: 545204, 6b3080]
- Verify multi-token compound flag formatting (e.g. `VishwaCTF{Startup_Handle_Email}` or `HTB{SUPPLIER_FEEDS_TOWN}`), checking case sensitivity, underscore vs colon separators, and exact spelling. [ev: 6d8d67, 6b3080]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Google Search | Querying venture capital news, executive career bios, and Substack exposes | 4 |
| Browser DevTools | Inspecting network traffic and extracting embedded datasets from React SPA JS bundles (`/assets/*.js`) | 2 |
| OpenSSL | Dumping and decoding raw X.509 certificate chains from custom TLS ports (`openssl s_client`) | 2 |
| crt.sh / Cert Spotter | Querying public Certificate Transparency logs for passive subdomain enumeration | 2 |
| dig / nslookup | Forward DNS resolution (A record lookup) to map domains to host IP addresses | 2 |
| whois | Querying IP allocation WHOIS records for ASN and hosting OrgAbuseEmail | 2 |
| Whoxy | Historical WHOIS lookup for unredacted original registrant emails and reverse WHOIS domain pivots | 1 |
| FMCSA / dot.report | Commercial motor vehicle regulatory lookup via USDOT numbers | 1 |
| Commercial Registries (Moneyhouse, SHAB, EGRUL, Rosstat) | Tracking statutory company renamings and statistical ownership codes | 1 |
| CyberChef | Base32 decoding and structured string reassembly | 1 |

## Worked micro-traces
- `[ev: d3e556]` Target was a travel blog on port 8443 with an untrusted self-signed TLS cert and an explicit prompt hint. The solver avoided browser GUI truncation by running `openssl s_client -connect 170.187.156.131:8443 -showcerts < /dev/null 2>/dev/null | openssl x509 -text -noout`. The Subject Organization field contained `Deadface{c@tch_m3_if_y0u_c@n}`, which failed verification until normalized to lowercase `deadface{...}`. The cert's `emailAddress` field then provided the exact pivot key (`alicehankerty@gmail.com`) for downstream Gravatar persona investigation.
- `[ev: bbaf8b]` Given domain `northernlights.gg` with an unlinked relay hostname that could not be guessed by dictionary attacks. The solver queried Certificate Transparency logs via `crt.sh`, uncovering 10 subdomains with prefixes like `relay-` and high-entropy numeric IDs. When all 10 endpoints returned HTTP 200, the solver avoided superficial status-code filtering and diffed the HTML body content, isolating `relay-843481` with an active green operational panel rendering the flag.
- `[ev: 545204]` A maritime challenge provided a React SPA ('Court-Eaves Console') to trace the beneficial controller of vessel IMO 9724418. Instead of manually navigating nine draggable UI windows, the solver extracted `/assets/index-*.js` to obtain the complete mock registry offline. Tracing the registered hull owner hit a dead end in nominee directors and holding shells, prompting a pivot to the commercial operator and time charterer, which converged on parent company Marrowcairn Strategic Holdings and 72% controller Damas Marrowcairn.

## Weak signals (single source — treat as hints, not rules)
- When investigating commercial fleet trucks lacking corporate logos, zoom in on the cargo container for USDOT/MC regulatory numbers and query FMCSA / dot.report. [ev: d00b8f]
- Challenge titles with distinctive phrasing or puns often encode primary startup entities or author handles (e.g. "Deep in the Delve" -> startup "Delve", handle "deepdelver"). [ev: 6f1119]
- In leaked DNS zone transfer files (AXFR), filter out decoy Microsoft/SPF TXT records by looking for structured schema tags (`frag=`, `serial_ref`) and sort them chronologically using changelog serials before Base32 decoding. [ev: c57c7d]
- Cross-border corporate entities with legal suffix mismatches (e.g. US LLC with European presence) require searching international trademark databases (EUIPO, WIPO, Trademarkia) and official commercial gazettes (SHAB) for shelf-company renamings. [ev: e69afe]
- Russian corporate entities with suspected foreign ties can be cross-referenced between EGRUL founder registries and Rosstat statistical classification codes (OKFS 34 / OKOGU) to reveal hidden foreign participation. [ev: e69afe]
- Executive personal social profiles (e.g. CEO LinkedIn reposts of conference photos, company blogs, race timing results) bridge fragmented clues (drawings, hobbies, locations) to specific staff members. [ev: a01bae]
