# gdb + pwndbg cheatsheet (CTF pwn)

Install: `command -v pwndbg >/dev/null || paru -S pwndbg` (adds `source /usr/share/pwndbg/gdbinit.py` to `~/.gdbinit`).

## Launch / attach
- `gdb ./chall` then `r` to run; `starti` to stop at the first instruction.
- Attach to a pwntools `process`: in the script use `gdb.attach(io, GDB_SCRIPT)`
  or `gdb.debug(EXE, gdbscript=...)`; set `context.terminal=["tmux","splitw","-h"]`.
- `pwndbg> ` prompt shows registers/stack/disasm automatically on each stop.

## Breakpoints & stepping
- `b *main+40` / `b vuln` — break at addr or symbol.
- `b *$rebase(0x1234)` — break at PIE offset (pwndbg resolves the load base).
- `c` continue · `ni`/`si` step over/into · `fin` finish frame.

## Inspecting
- `telescope $rsp 20` — dereference-chase the stack (pwndbg).
- `x/40gx $rsp` · `x/8i $rip` · `x/s 0x...` — examine memory/instructions/string.
- `vmmap` — memory map, segment perms, libc/stack/heap base.
- `p/x $rdi` · `info registers` · `context` — redraw the pwndbg view.
- `search -t string "/bin/sh"` · `search 0xdeadbeef` — scan memory.

## Pwn helpers (pwndbg)
- `checksec` — mitigations.
- `canary` — current stack canary value.
- `cyclic 200` / `cyclic -l 0x6161...` — pattern create / find offset.
- `rop --grep "pop rdi"` · `ropgadget` — gadget search.
- `got` / `plt` — resolved GOT/PLT tables.
- `heap`, `bins`, `fastbins`, `tcache`, `vis_heap_chunks` — heap state (tcache CTFs).
- `nextcall`, `nextret` — run to next call/ret.

## Finding libc base / offsets
- `vmmap` → first libc mapping is the base.
- `p system` / `p &system` with libc loaded; `p/x (long)system - (long)__libc_start_main`.
- Defeat ASLR locally: `echo 0 | sudo tee /proc/sys/kernel/randomize_va_space`
  (re-enable with 2) — but always finalize the exploit with ASLR on.

## Common signals
- SIGSEGV in `__memmove_avx_unaligned` / `movaps` inside `do_system` = 16-byte
  stack misalignment → add a bare `ret` gadget before the call.
- `$rip` full of `0x4141...` = you control return; use `cyclic` to get the offset.
