"""``ctf`` CLI — tool-agnostic frontend over the engine. Any agent (Claude Code, Antigravity)
or a human drives the whole pipeline through these subcommands via a plain shell:

    ctf skeleton [URL]        build folder tree + structure.md, wave-aware (0 tokens)  -> JSON
    ctf collect CAT [-w W]    download+auto-solve one category into its folders (0 tokens)
    ctf collect --all         download+auto-solve every category
    ctf claim-category [-w W] atomically take the biggest un-collected category (collectors)
    ctf sync [URL]            skeleton + collect-all (simple one-shot mode)
    ctf status                queue counts + categories + easy-first pending list
    ctf claim [-w W]          atomically take the next challenge (easy-first, phase/time-boxed)
    ctf submit ID FLAG        submit through the format-gate + de-dup + global throttle
    ctf mark ID STATUS [N]    record outcome: SOLVED / FAILED / SKIP
    ctf structure             rebuild structure.md from the current queue
    ctf serve                 run the MCP server (stdio) for native tool use
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import coord, ctfd, sync as syncmod  # noqa: E402


def _p(obj) -> None:
    print(json.dumps(obj, indent=1, default=str))


async def _submit(cid: str, flag: str) -> dict:
    client, _, _ = ctfd.make_client()
    try:
        return await coord.throttled_submit(lambda i, f: client.submit_flag(i, f), cid, flag)
    finally:
        await client.aclose()


def main() -> None:
    ap = argparse.ArgumentParser(prog="ctf")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sk = sub.add_parser("skeleton"); sk.add_argument("url", nargs="?")

    co = sub.add_parser("collect")
    co.add_argument("category", nargs="?")
    co.add_argument("--all", action="store_true")
    co.add_argument("-w", "--worker", default="collector")
    co.add_argument("--no-auto", action="store_true")

    cc = sub.add_parser("claim-category"); cc.add_argument("-w", "--worker", default="collector")

    s = sub.add_parser("sync"); s.add_argument("url", nargs="?"); s.add_argument("--no-auto", action="store_true")
    sub.add_parser("status")
    c = sub.add_parser("claim"); c.add_argument("-w", "--worker", default="cli")
    su = sub.add_parser("submit"); su.add_argument("id"); su.add_argument("flag")
    m = sub.add_parser("mark"); m.add_argument("id"); m.add_argument("status"); m.add_argument("note", nargs="?", default="")
    sub.add_parser("structure")
    sub.add_parser("serve")
    a = ap.parse_args()

    if a.cmd == "skeleton":
        _p(asyncio.run(syncmod.skeleton(a.url)))
    elif a.cmd == "collect":
        if a.all or a.category in (None, "all"):
            _p(asyncio.run(syncmod.collect_all(do_autosolve=not a.no_auto)))
        else:
            _p(asyncio.run(syncmod.collect(a.category, worker=a.worker, do_autosolve=not a.no_auto)))
    elif a.cmd == "claim-category":
        _p(coord.claim_category(a.worker) or {"done": True})
    elif a.cmd == "sync":
        _p(asyncio.run(syncmod.sync(a.url, do_autosolve=not a.no_auto)))
    elif a.cmd == "status":
        _p(coord.queue_summary())
    elif a.cmd == "claim":
        _p(coord.claim_view(a.worker))
    elif a.cmd == "submit":
        _p(asyncio.run(_submit(a.id, a.flag)))
    elif a.cmd == "mark":
        _p(coord.mark(a.id, a.status, a.note))
    elif a.cmd == "structure":
        _p({"structure_md": str(coord.event_dir() / "structure.md"),
            "bytes": len(coord.build_structure_md())})
    elif a.cmd == "serve":
        import mcp_server
        mcp_server.mcp.run()


if __name__ == "__main__":
    main()
