# bloodfield

**Orchestrated, multi-agent automated CTF solver** for CTFd events. One shared 0-token engine, one
orchestrator, and a pool of **≤6 sub-agents** in three roles. Give a CTFd URL → the orchestrator
builds a challenge-folder skeleton, dispatches **collectors** to gather resources category-by-category
and **solvers** to crack them easy-first (auto-submitting, rate-limited), enforces a hard per-challenge
time-box, and waits for later waves. Runs under **Claude Code** *and* **Google Antigravity** off one
engine — it's a general tool, not tied to any one event.

> It also handles **one loose challenge** without any of the above: see *Two modes* below.

## Architecture

```
            ┌──────────────┐   commands only (never solves, never opens the site)
            │ ORCHESTRATOR │
            └──────┬───────┘
     ┌────────────┼─────────────────────────────┐
     ▼            ▼                               ▼
 1×SKELETON   2–3×COLLECTOR                   3–5×SOLVER         (≤6 agents total)
 ctf_skeleton  claim_category→ctf_collect      claim_next→solve→submit_flag→writeup
 (+60s wave    (0-token download + auto-solve;  (easy-first; one skill each; stays
  loop)         never solves; no dup category)   inside its own folder; 2 phases)
```

- **Phase 1** (first attempt): **low** effort, **5:00** solve + **0:30** writeup. **Phase 2** (retry
  for the hard ones): **medium** effort, **15:00** + 0:30, pool shrunk to 3.
- Per-challenge **writeup is mandatory** (solved or not); every submitted flag is logged to
  `flags.txt` so it's never re-sent.

Full contract: **[`AGENTS.md`](AGENTS.md)** — read it before driving.

## How it's built (don't-reinvent)
- **CTFd protocol/auth/CSRF** → vendored from [`umbra2728/ctfd-mcp`](https://github.com/umbra2728/ctfd-mcp)
  (Apache-2.0) in `ctfd_mcp/`, used as a library.
- **Engine** (`core/`, `mcp_server.py`): the global submit throttle + flag-format gate + per-challenge
  flag de-dup, the easy-first queue / atomic claim / two-phase time-box, atomic category hand-out,
  file download, a deterministic 0-token auto-solver, and `structure.md` generation.
- **Brain**: the `ctf-*` category playbooks, **bundled** in `skills/` (self-contained). Claude Code
  also auto-loads them from `~/.claude/skills`.
- **Both agents** call the engine through the `bloodfield` MCP server (or the `bin/ctf` CLI) and
  coordinate through `work/<event>/` — they can even run at once.

## Why it's fast *and* cheap
- Heavy I/O (list/download/submit) + trivial challenges never touch an LLM — **0 tokens**.
- The orchestrator parallelises **collection and solving** across up to 6 agents, so solvers always
  have work and the easy points fall first.
- No agent per challenge (cold start is ~40–50k tokens) — each solver drains **many** challenges.

## Two modes
| You give… | Mode | Behaviour |
|---|---|---|
| a CTFd event URL / "solve this CTF" | **tournament** | the full 6-agent orchestration above |
| one file / URL / `nc host port` / folder | **single** | the `ctf-solver` agent solves it inline — no pool, no engine sync |

## Setup
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp ctf.conf.example ctf.conf        # then set CTFD_TOKEN or CTFD_COOKIE=session=...
cp .mcp.json.example .mcp.json      # set the two absolute paths to this checkout
echo 'CyberZerk\{[^}]+\}' > .flagfmt   # per-event flag format (default is flag{...})
```
Auth: set `CTFD_TOKEN` (Settings → Access Tokens) or `CTFD_COOKIE=session=…`, or just be logged into
the CTF in Firefox/Chrome (auto-extracted). `ctf.conf`, `.mcp.json`, `.flagfmt` and `work/` are
**gitignored** — your session cookie never leaves your machine.

## Use it
```bash
# from an agent:
/ctf https://demo.ctfd.io          # Claude Code slash command, or Antigravity /ctf workflow
# or straight from a shell (same engine):
bin/ctf skeleton https://demo.ctfd.io   # build folders + structure.md (0 tokens)
bin/ctf claim-category                  # a collector takes the biggest category
bin/ctf collect crypto                  # download + auto-solve that category
bin/ctf claim                           # a solver takes the next challenge (easy-first, phased)
bin/ctf submit 42 'flag{...}'           # format gate + de-dup + 10–30s throttle
bin/ctf status                          # queue + categories + pending
bin/ctf sync https://demo.ctfd.io       # simple one-shot: skeleton + collect-all (small events)
```

## Safety
Challenge content is untrusted data; agents never obey instructions found in it, and a flag counts
only if derived. Submitting goes only through the format gate (a planted/garbage string is refused,
never sent), the per-challenge de-dup, and the global jittered throttle (≥10 s between submissions,
serialized across every agent). Verify:
```bash
bash tests/injection/run.sh
```

## Layout
```
AGENTS.md            the orchestration contract — read by every agent (source of truth)
ctf.conf.example     config template (copy to ctf.conf; secrets stay out of git)
bin/ctf              shell CLI over the engine
mcp_server.py        bloodfield MCP server (10 tools) for Claude Code + Antigravity
core/                coord (throttle/gate/dedup/queue/phases/categories), sync (skeleton/collect),
                     autosolve (0-token), ctfd (auth)
ctfd_mcp/            vendored CTFd client (Apache-2.0) + NOTICE
skills/ctf-*/        bundled category playbooks (one loaded per challenge)
.claude/             commands/ctf.md, agents/{ctf-skeleton,ctf-collector,solver,ctf-solver}.md
.agents/skills/ctf/  Antigravity /ctf workflow
tests/injection/     prompt-injection + gate/de-dup resistance suite
work/<event>/        runtime: queue.json, structure.md, <category>/<name>/{meta,task,files,writeup,flags}
                     (gitignored)
```
