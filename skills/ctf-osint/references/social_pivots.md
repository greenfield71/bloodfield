# Social & Cross-Platform Activity Pivots (CTF OSINT 2025–2026)

This reference guide provides actionable methodologies and command recipes for tracing target identities, usernames, developer footprints, and outdoor activity across modern platforms.

---

## 1. Email Permutation & Passive Verification

CTF challenges frequently present a target's real name (or company alias) and challenge participants to discover their email address, login portal, or linked service.

### 1.1. Common Corporate & Personal Permutations
Given First Name: `John`, Last Name: `Doe`, Domain: `corp.com`:

| Permutation Schema | Pattern | Example |
|--------------------|---------|---------|
| `first.last` | `{first}.{last}@{domain}` | `john.doe@corp.com` |
| `flast` | `{f}{last}@{domain}` | `jdoe@corp.com` |
| `firstl` | `{first}{l}@{domain}` | `johnd@corp.com` |
| `lastf` | `{last}{f}@{domain}` | `doej@corp.com` |
| `first_last` | `{first}_{last}@{domain}` | `john_doe@corp.com` |
| `first` | `{first}@{domain}` | `john@corp.com` |
| `last.first` | `{last}.{first}@{domain}` | `doe.john@corp.com` |
| `f.last` | `{f}.{last}@{domain}` | `j.doe@corp.com` |
| `first-last` | `{first}-{last}@{domain}` | `john-doe@corp.com` |

Quick Python generator:
```python
def generate_email_permutations(first, last, domain):
    f, l = first.lower(), last.lower()
    patterns = [
        f"{f}.{l}@{domain}", f"{f}{l}@{domain}", f"{f[0]}{l}@{domain}",
        f"{f}{l[0]}@{domain}", f"{f}_{l}@{domain}", f"{l}.{f}@{domain}",
        f"{f}@{domain}", f"{l}@{domain}", f"{f[0]}.{l}@{domain}"
    ]
    return patterns
```

### 1.2. Gravatar MD5 Hash Pivot
Gravatar calculates avatar URLs using the MD5 hash of the lowercased, trimmed email address:
`hash = md5(email.strip().lower())`

1. **Verify if email has an avatar / profile:**
   ```bash
   EMAIL="john.doe@example.com"
   HASH=$(echo -n "$EMAIL" | tr '[:upper:]' '[:lower:]' | md5sum | awk '{print $1}')
   curl -s "https://en.gravatar.com/$HASH.json" | jq .
   ```
2. **Reverse Gravatar Hash to Email:**
   If a website displays an avatar link `https://www.gravatar.com/avatar/4f647...`, generate wordlist candidates using permutations and compute MD5 until a collision is found:
   ```python
   import hashlib
   target_hash = "4f647..."
   for cand in candidates:
       if hashlib.md5(cand.strip().lower().encode()).hexdigest() == target_hash:
           print(f"[!] Email found: {cand}")
   ```

---

## 2. Git & Developer Footprint OSINT

Git commit history preserves permanent, author-supplied metadata that is often omitted from web profiles.

### 2.1. Extracting Unmasked Author Emails from Git
Even if a developer marks their email private on GitHub, local commits or old repositories contain raw headers:

```bash
# Extract unique commit authors and emails from a local git repository
git log --format='%an <%ae>' | sort -u

# Include commit timestamps and commit hashes
git log --format='%h | %ad | %an <%ae> | %s' --date=short

# Search commit messages and diffs for secrets, flags, or handles
git log -S "FLAG{" -p
git log -S "token" -p
git log -G "password|secret|key" -p
```

### 2.2. The GitHub Patch / Diff Secret Pivot
GitHub automatically generates raw patch files for any public commit or pull request. Even if a user replaces their commit author afterwards:
- Append `.patch` or `.diff` to any commit URL:
  `https://github.com/{owner}/{repo}/commit/{commit_hash}.patch`
- Look at the `From: Name <email@example.com>` header line.

### 2.3. GitHub Public Events & Gists
The GitHub REST API exposes the last 90 days (or 300 events) of public activity:
```bash
# Query recent push events (PushEvent payload contains commit author email!)
curl -s "https://api.github.com/users/{username}/events/public" | jq -r '
  .[] | select(.type=="PushEvent") | .payload.commits[]? | "\(.author.name) <\(.author.email)>: \(.message)"
' | sort -u

# Retrieve user SSH and GPG public keys (useful for key IDs and email linkages)
curl -s "https://github.com/{username}.keys"
curl -s "https://github.com/{username}.gpg"
```

---

## 3. Fitness, Outdoor & Activity Tracking OSINT

Some OSINT challenges require tracking a target's physical movements via fitness and caching apps.

### 3.1. Strava (Heatmap, Segments & Profiles)
- **Strava Global Heatmap**: `https://www.strava.com/heatmap`
  - High-intensity paths reveal popular running/cycling routes, private compound perimeters, or military base activity.
- **Segment Leaderboards**:
  - If a challenge reveals a specific road segment, search the segment on Strava (`https://www.strava.com/segments/{segment_id}`).
  - Filter the leaderboard by date (e.g., date of the photographed event) to find athlete IDs who passed the segment at that exact time.
- **Athlete ID Enumeration**:
  - `https://www.strava.com/athletes/{athlete_id}` reveals recent public activities, gear (bike/shoes), and club memberships.

### 3.2. Komoot (Tours & Highlights)
- Widely used in Europe and outdoor CTF challenges.
- User profile: `https://www.komoot.com/user/{user_id}`
- Highlights & Photos: Users upload geo-tagged photos attached to specific trail waypoints. Searching highlights near a target landmark often reveals candid photos taken from the exact same vantage point as the challenge photo.

### 3.3. Geocaching
- Geocaching cache logs frequently document user handles, visit dates, and physical logbook signatures.
- Cache page: `https://www.geocaching.com/geocache/{cache_code}` (e.g. `GC12345`).
- Finding logs: Look for logs posted on the target date. Users often post hint photos of nearby landmarks, benches, and trail signs.

---

## 4. Modern & Decentralized Social Networks (2025–2026)

CTFs increasingly pivot across decentralized and next-generation networks rather than legacy platforms.

### 4.1. Bluesky & AT Protocol (`did:plc:...`)
Bluesky identities are cryptographic DIDs (Decentralized Identifiers). Even if a user changes their handle, their DID and historic handle changes are publicly recorded:

1. **Resolve Handle to DID:**
   ```bash
   HANDLE="target.bsky.social"
   DID=$(curl -s "https://bsky.social/xrpc/com.atproto.identity.resolveHandle?handle=$HANDLE" | jq -r .did)
   echo "Resolved DID: $DID"
   ```
2. **Audit Handle History via PLC Directory:**
   Every handle change, rotation key, and service endpoint is permanently appended to the PLC log:
   ```bash
   curl -s "https://plc.directory/$DID/log" | jq .
   ```
3. **Inspect Target's Public Repository Records:**
   ```bash
   curl -s "https://bsky.social/xrpc/com.atproto.repo.describeRepo?repo=$DID" | jq .
   ```

### 4.2. Mastodon / ActivityPub WebFinger
Any ActivityPub-compatible server (Mastodon, Lemmy, Pixelfed) supports WebFinger:

```bash
# Query WebFinger for target user:
curl -s "https://mastodon.social/.well-known/webfinger?resource=acct:username@mastodon.social" | jq .

# Fetch user public outbox (recent posts, attachments, replies):
curl -s -H "Accept: application/activity+json" "https://mastodon.social/users/username/outbox?page=true" | jq .
```
- Look for `attachment` fields with `rel="me"` links (e.g., personal websites, verified GitHub accounts).

### 4.3. Telegram OSINT
- Web preview: `https://t.me/s/{channel_name}` displays public channel messages without requiring a Telegram client or phone login.
- Forwarded message analysis: Forwarded messages preserve the original sender's display name and channel ID.
- Bot lookups: Open bot services (`@userinfobot`, `@SangMataInfo_bot`) resolve Telegram numeric User IDs and historical username/name changes.

---

## 5. Cross-Platform Handle Enumeration Methodology

1. **Run Sherlock / Maigret:**
   ```bash
   command -v sherlock >/dev/null && sherlock --timeout 10 --print-found {username}
   ```
2. **Filter False Positives:**
   - Always check HTTP status codes vs soft-404 redirects (e.g. platforms that return 200 OK with "user not found" body).
   - Cross-check profile creation dates and avatar similarity.
3. **Trace Common Passwords / Hashes:**
   - In ethical CTF environments with supplied mock data breaches: search breach files for username matches to find linked emails or password reuse across simulated accounts.
