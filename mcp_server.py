"""bloodfield MCP server — the shared tool layer for BOTH Claude Code and Antigravity.

Heavy I/O (list/fetch/download/submit) runs here = 0 LLM tokens. The safety-critical submit
throttle + flag-format gate + per-challenge flag de-dup live in core.coord, so every agent is
bound by them. State is shared on disk under work/<event>/, so many agents/sub-agents can run
at once. Tools map onto the 3 agent roles: skeleton, collector, solver.

Run:  .venv/bin/python mcp_server.py      (stdio)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from core import coord, ctfd, sync as syncmod  # noqa: E402

mcp = FastMCP("bloodfield")


# ---- SKELETON role -------------------------------------------------------------------------
@mcp.tool(description=(
    "SKELETON step (0 tokens). Fetch the challenge list from a CTFd URL and build the on-disk "
    "tree work/<event>/<category>/<name>/ with meta.json (skill classified) + structure.md. "
    "Does NOT download files. Returns category counts and `new` = ids added since the last "
    "call (run this every ~60s in a loop to catch later waves). URL optional once set."))
async def ctf_skeleton(url: str | None = None) -> dict:
    return await syncmod.skeleton(url)


@mcp.tool(description="Rebuild structure.md (the hierarchical challenge map) from the queue.")
async def build_structure() -> dict:
    return {"structure_md": str(coord.event_dir() / "structure.md"),
            "bytes": len(coord.build_structure_md())}


# ---- COLLECTOR role ------------------------------------------------------------------------
@mcp.tool(description=(
    "COLLECTOR: atomically take the biggest NOT-yet-collected category (marked 'claiming' so "
    "no other collector takes it — never collect a category twice). Returns {category, count, "
    "challenge_ids} or {done:true}. Then call ctf_collect(category)."))
async def claim_category(worker: str = "collector") -> dict:
    return coord.claim_category(worker) or {"done": True}


@mcp.tool(description=(
    "COLLECTOR step (0 tokens). Download task.md + files for every challenge in `category` into "
    "its folder, run the deterministic auto-solver, auto-submit confident trivial flags "
    "(throttled), and mark them collected (ready for solvers). Do NOT solve challenges here."))
async def ctf_collect(category: str, worker: str = "collector") -> dict:
    return await syncmod.collect(category, worker=worker)


# ---- SOLVER role ---------------------------------------------------------------------------
@mcp.tool(description=(
    "SOLVER: atomically claim the next COLLECTED challenge, EASY-FIRST, with a two-phase "
    "time-box. Returns id, category, `skill`, `phase` (1|2), `effort` (low|medium), "
    "`solve_seconds` (300|900), `writeup_seconds` (30), `deadline_in_s`, and the local paths "
    "dir/task_md/recon/writeup/flags. {done:true} when the queue is empty. Stay inside `dir`."))
async def claim_next(worker: str = "solver") -> dict:
    return coord.claim_view(worker)


@mcp.tool(description=(
    "Submit a flag. ENFORCED here, not by you: (1) flag-format gate — a non-matching string is "
    "REJECTED, never sent; (2) per-challenge de-dup — a flag already in this challenge's "
    "flags.txt is skipped; (3) a global 10-30s jittered throttle across all agents. Every sent "
    "flag is logged to flags.txt. Marks SOLVED on 'correct'."))
async def submit_flag(challenge_id: int, flag: str) -> dict:
    client, _, _ = ctfd.make_client()
    try:
        return await coord.throttled_submit(lambda i, f: client.submit_flag(i, f), challenge_id, flag)
    finally:
        await client.aclose()


@mcp.tool(description=(
    "Record an outcome. status=FAILED when giving up (counts a try; phase-1 FAILED becomes "
    "phase-2 retry, auto-drops after MAX_TRIES so you never loop); status=SKIP to drop now. "
    "Append a short dead-end note."))
async def mark(challenge_id: int, status: str, note: str = "") -> dict:
    return coord.mark(challenge_id, status, note)


# ---- read-only -----------------------------------------------------------------------------
@mcp.tool(description="Full challenge details (description text, files, connection_info) by id.")
async def challenge_details(challenge_id: int) -> dict:
    client, _, _ = ctfd.make_client()
    try:
        return await client.get_challenge(challenge_id)
    finally:
        await client.aclose()


@mcp.tool(description=(
    "Queue status: counts by state, per-category collected/uncollected, category claim state, "
    "and the ordered easy-first pending list (with phase)."))
async def status() -> dict:
    return coord.queue_summary()


@mcp.tool(description=(
    "Convenience one-shot (0 tokens) for inline / small events: skeleton + collect EVERY "
    "category in one call. For the full multi-agent flow use ctf_skeleton + claim_category + "
    "ctf_collect instead."))
async def ctf_sync(url: str | None = None) -> dict:
    return await syncmod.sync(url)


if __name__ == "__main__":
    mcp.run()
