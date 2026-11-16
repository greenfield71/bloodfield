---
name: ctf-rev
description: >-
  Reverse engineering CTF challenges. Use when given a binary, executable, or
  bytecode (ELF, PE/.exe, Mach-O, .pyc, .jar/.class, .apk, .NET) and the goal is
  to understand its logic to recover a flag/key/password — not exploit it. Covers
  Ghidra headless, radare2/rizin, objdump, ltrace/strace, emulation-first RE with
  Unicorn ("run the real code"), custom-VM / SIGILL-dispatch / lambda-calculus
  decoding, obfuscation (OLLVM control-flow flattening, MBA), angr for pure
  flag-check math, Python/.NET/JVM/APK decompilation, mobile (iOS Mach-O,
  Android JNI, on-device ML / MNN FlatBuffers), algorithmic reductions (tetration
  / power towers mod m), and symmetric cipher recognition (XTEA / TEA). Triggers
  on: "reverse", "reversing", "rev", "disassemble", "decompile", "Ghidra",
  "radare2", "r2", "angr", "keygen", "license check", "flag check", "pyc",
  "decompile python", "dnSpy", ".NET", "binary", "Unicorn", "emulate", "emulation",
  "firmware", "AArch64", "ARM64", "qemu-user", "SIGILL", "ud2", "VM", "bytecode",
  "lambda calculus", "Scott encoding", "OLLVM", "control flow flattening", "MBA",
  "Frida", "MNN", "Mach-O", "iOS", "mobile", "on-device ML", "tetration", "power
  tower", "XTEA", "memfd_create", "in-memory loader", "stuck", "how to
  approach", "methodology", "next step", "where to start", "crackme", "unpack",
  "deobfuscate".
---

# CTF Reverse Engineering

Reverse engineering in modern CTFs (2025–2026+) prioritizes **emulation-first analysis**, **deobfuscation of compiler transforms (OLLVM CFF, MBA)**, **custom VM / signal-dispatch reverse engineering**, and **mobile / on-device ML reversing**.

<!-- logic-distill:begin -->
## Solver Mindset — how experienced players attack rev (distilled from 200 writeups)

Reasoning layer on top of the tool sections below. Full discipline: [`references/logic/meta_reasoning.md`](references/logic/meta_reasoning.md). Playbook index: [`references/logic/INDEX.md`](references/logic/INDEX.md).

### The loop
1. **Inventory**: identify format, architecture, toolchain, runtime and packaging before disassembling; do not assume a standard Linux userspace ELF. [ev: f63cee, 2e3f9e, 274017, 9f74f1]
2. **Assess the CFG**: open entrypoint and `main`; decide whether it is a clean pipeline, a VM loop, flattening, or signal/exception-driven dispatch. [ev: 2742bf, 0ffc7b, 1d2e38, a4b4b0]
3. **Hold 2-3 hypotheses** (standard crypto / custom pipeline / SMT system / bytecode VM), each with a falsification condition, before writing solver code. [ev: 2bd3ec, 70d6ff, ae10f0, ac0a19]
4. **Run the cheapest discriminating test**: `ltrace`/`strace`, a watchpoint, an instruction-count diff, or a constant lookup, before heavy symbolic work. [ev: 4529d2, f05c62, dcce7e, 4dd429]
5. **Extract and invert**: prefer direct algebraic inversion when every step is bijective; use Z3 or graph search otherwise. [ev: 6b0cbb, 57fd34, 08be32, 5a2d31]
6. **Stop-loss check**: apply the time-boxes below; when stalled, pivot to emulation or dynamic tracing. [ev: 76e27c, 142c04, 48b12d, 5e0808]
7. **Verify**: replay the candidate through the unmodified binary and check the flag format before submitting. [ev: 57fd34, 0ab809, 4dd429, a4b4b0]

### First 10 minutes
- **0-2** Headers and packaging: `file`, `readelf -l`; look for packed sections, embedded filesystems, managed runtimes (.NET, pyc, IL2CPP). No decompiler yet. [ev: 2e3f9e, 9f74f1, 274017, 4be8f2]
- **2-4** Strings and symbols with xref checks: prompts, comparison buffers, flag prefix; mark unreferenced strings as decoys. [ev: 4be8f2, ac0a19, 0ffc7b, f63cee]
- **4-6** Dynamic baseline: run under `ltrace -s 128` / `strace` with dummy input; note exit codes, syscalls, comparisons, anti-debug exits. [ev: 4529d2, 2742bf, dcce7e, 4dd429]
- **6-8** Decompile the entry logic: follow input from ingestion to the verification loop; gauge CFG size. [ev: 1d2e38, a4b4b0, c1b450, 73fc0d]
- **8-10** Route to an archetype, state 2 competing hypotheses, write the first probe or solver skeleton. [ev: 2bd3ec, 70d6ff, 6b0cbb, 84932b]

### Route by signal
Open the matching playbook **before going deep**; follow its "Opening sequence". If two rows match, handle the outer layer (loader/packer) first. [ev: 0ffc7b, 76e27c, f05c62]

| Signal | Playbook |
|---|---|
| Switch/jump table over a byte array with a virtual PC | [`custom-bytecode-vm`](references/logic/custom-bytecode-vm.md) |
| Unrolled bitwise transform loops ending in `memcmp` | [`invertible-transform-pipeline`](references/logic/invertible-transform-pipeline.md) |
| Coupled multi-variable equations, dense logic circuits | [`constraint-system-smt`](references/logic/constraint-system-smt.md) |
| High entropy, W^X sections, `memfd_create` | [`packed-self-modifying-loader`](references/logic/packed-self-modifying-loader.md) |
| Flat CFG with state-variable dispatcher, MBA, `SIGILL`/`ud2` | [`obfuscated-control-flow`](references/logic/obfuscated-control-flow.md) |
| .NET, JVM, Python pyc, WASM, AppleScript metadata | [`managed-runtime-decompile`](references/logic/managed-runtime-decompile.md) |
| APK with JNI `lib*.so`, iOS app | [`mobile-app-reverse`](references/logic/mobile-app-reverse.md) |
| Freestanding non-x86 ELF at `0x80000000`, MMIO/HTIF | [`non-standard-arch-firmware`](references/logic/non-standard-arch-firmware.md) |
| `srand`/`rand`, LFSR, bounded 32-bit seed | [`prng-and-seed-recovery`](references/logic/prng-and-seed-recovery.md) |
| WASD input, maze map, state machine, game assets | [`interactive-game-and-state-machine`](references/logic/interactive-game-and-state-machine.md) |
| `.ko`, `ioctl`, `/dev/` nodes, Intel AMX | [`system-kernel-and-hardware-interface`](references/logic/system-kernel-and-hardware-interface.md) |
| Corrupted ELF header, Go `pclntab`, single `jz` gate | [`triage-shortcuts-and-binary-patching`](references/logic/triage-shortcuts-and-binary-patching.md) |
| Root-required, "breaks under debugger", tiny `main` + trap stub, libbpf/`.ko`/embedded eBPF blob | [`system-kernel-and-hardware-interface`](references/logic/system-kernel-and-hardware-interface.md) (verdict is in the privileged component) |
| File size >> last segment, trailer magic near EOF, MEI/payload marker, resource-embedded XOR layers | [`packed-self-modifying-loader`](references/logic/packed-self-modifying-loader.md) (carve inner binary first) |
| `fork`+`ptrace`, `memfd_create`, SIGILL/SIGSEGV stream, slow huge binary | [`obfuscated-control-flow`](references/logic/obfuscated-control-flow.md) (tracer is the VM decoder) |
| Easy crackme, exact-length check, no flag in strings | [`invertible-transform-pipeline`](references/logic/invertible-transform-pipeline.md) |
| Small APK, one opaque asset, decoy flags | [`mobile-app-reverse`](references/logic/mobile-app-reverse.md) (strings-first) |
| Game map/engine assets with no logic, overlay entities | [`triage-shortcuts-and-binary-patching`](references/logic/triage-shortcuts-and-binary-patching.md) (look visually first) |

### Top rules (highest support first)
1. Coupled multi-variable constraints (rotated or cross-byte indices): transcribe them into Z3 BitVecs of the binary's word size, pin the flag prefix and printable range. Independent bytes: solve per byte or invert algebraically, no Z3. [ev: 57fd34, 666a42, 9b4957, 9d630d]
2. Validation that is a walk over a state graph, maze or grid: extract the transition table and solve with BFS/DFS/Dijkstra. [ev: 08be32, 5a2d31, 3f57b3, 91681a]
3. Constants such as `0x9e3779b9`, SplitMix64 multipliers, a 256-byte KSA/PRGA loop or ARX rotations: identify the standard primitive first (RC4, Speck, SplitMix64; `0x9e3779b9` may be a plain hash/PRNG mixer, not TEA) and re-implement or invert that known algorithm instead of reversing the compiled internals. [ev: 2b52b8, 16c799, 90db76, 01d01b]
4. Switch or function-pointer table looping over bytes with a PC: it is a VM; locate the dispatch loop and bytecode, then trace executed opcodes or inspect the decoded data first; reverse only the handlers that touch input/compare. [ev: 2b52b8, 06267e, 05e4b7, 31502d]
5. Deriving a key or decryption routine iteratively: test each candidate against the known flag prefix (`flag{`, `CTF{`) before running the full search or accepting solver output. [ev: 465bca, 5e0808, 06267e, 57fd34]
6. Keys or shuffles from `rand()`, LFSR or another PRNG: identify the generator and where the seed comes from; replay it (static seed, `time()` sync with +/-1 s offsets) or brute-force a bounded seed. [ev: d0934a, fa693c, 5e0808, 1f8a0b]
7. APK delegating to a `.so`: search the export table for `Java_<pkg>_<class>_<method>` to link UI input to the native check; inspect `JNI_OnLoad` only if no such export exists. [ev: 062442, 841073, d02322, 7e13c5]
8. Plaintext flag or bare `strcmp` in strings: check xrefs to prove it is on a live path; uncalled ones are decoys. [ev: 0180b1, 03bc55, 062442, 0feb9f]
9. Game with a win/score threshold: trace back from the flag decryptor to check whether score or gameplay state feeds the key; if not, simulate the state machine offline; if it does, reverse the handlers that update it. [ev: 90db76, 6df9c3, 19e110]
10. Code unpacked or decrypted at runtime: break at the decryption/transfer boundary (or hook a PLT call such as `memcpy` around `memfd_create`) and dump the payload; do not reverse the stub. If the unpack is a plain XOR/zlib over file data, redo it offline instead. [ev: 142c04, 31502d, 76e27c, 16c799]
11. Runtime decryption or anti-tamper: hook with Frida or hardware watchpoints on the target buffer and read the plaintext at the boundary. [ev: 305d06, 31502d, 33f3ef, 3d3586]
12. Sequential pipeline of invertible ops (XOR, ROL/ROR, substitution): run it backwards from the target instead of building Z3 constraints. [ev: 01d01b, 03bc55, 0ab809, 10f5ca]
13. Check that validates one character (or prefix) at a time: recover byte by byte - brute-force the ~95 printable candidates per position against the per-step target, or hook the comparison and read the expected operand. [ev: 0180b1, d88a77]
14. Anti-debug present (`ptrace`, `TracerPid`, TLS callbacks): first check whether the data can be recovered statically/offline; only if dynamic analysis is needed, neutralize at the boundary (patch the branch, `LD_PRELOAD`), supplying any state the check writes. [ev: 06267e, 16c799, 465bca, 2addf5, 7149ae, 305d06]
15. Environmental gate (license file, anti-debug divergence): patch the branch only after confirming the gate result does not feed downstream keys/state; otherwise build the valid license/keygen. [ev: 2addf5, 19e110, 7149ae, 666a42]
16. Root-required or debugger-hostile binary with tiny `main`, trap stub and a loader library (libbpf, `register_binfmt`): the verdict is in a privileged component; carve and decrypt the embedded object statically, disassemble it, invert its rounds offline; do not lead with anti-debug probes. [ev: 647312, 2d00be, cd395d]
17. File size far beyond the last segment or a trailer magic near EOF: it is a self-extracting package; carve the overlay or copy the dropped temp files (`strace -f`) and analyze the inner binary. XOR-masked layers: recover each key from known plaintext (`MZ`, flag prefix) and log them. [ev: b03ebc, aa5f98, 9f74f1, 465bca, 7ba241]
18. `fork`+`ptrace`/SIGILL/SIGSEGV stream in a slow binary: the tracer's decoder of faulting bytes is the VM; list its primitive ops, lift call sites to a linear model and solve. [ev: 0180b1, 305d06, 81f244]
19. Obfuscation around a 256-byte init + swap + XOR loop: name the primitive (RC4), lift key and table from `.rodata`, decrypt offline instead of deobfuscating. [ev: 1d2e38, 4dd429, 2d00be, 6df9c3]
20. Small APK with one opaque asset: dump dex/native strings, derive the key from literals, try XOR/AES on the asset before deep decompilation; flag-shaped literals are decoys. [ev: 64f78e, 062442, 7e13c5]
21. Easy crackme (password is flag, exact length, nothing in strings): read the check, invert the per-index transform against the constant table. [ev: 1d2e38, 4dd429, 467425, b87695]
22. Asset-only game/engine distfile with no check logic: render or open it visually before modeling logic. [ev: 17ee43, 16d1af, 65d714]

### Weak signals (single source - hints, not rules)
- Unfamiliar ISA extension (Intel AMX): write a small Python emulator and validate its intermediate states against Intel SDE / debugger dumps instead of symbolic execution. [ev: 91681a]
- SIMD/crypto transform (AVX2, Salsa) where each output byte depends on one input byte: skip angr; probe the per-byte mapping black-box under a debugger. [ev: 76e27c]
- Game or GUI binary with no useful strings/xrefs: diff memory dumps taken before/after an in-game action to locate the state buffer and its checker. [ev: 142c04]

### Stop-loss & AI pitfalls
- Z3/angr running > 5 min (hashes, non-linear mixing, SIMD): stop; switch to concrete tracing, emulation or algebraic reduction. [ev: 76e27c, 5e0808, 4ff677, dcce7e]
- Reading flattened or opaque-dispatch code > 15 min without recovering state transitions: stop; log an instruction trace or filter on the state variable. [ev: 142c04, e46213, 619cae, 4ff5d8]
- Keyspace > 2^32 without byte independence: do not brute-force; look for meet-in-the-middle, invariants or a side channel. [ev: 24aecd, 5e0808, 1a4eac, 8ff6f0]
- GDB blocked > 10 min by anti-debug, forks or self-modifying code: move to static extraction plus Unicorn. [ev: 2742bf, b74c9e, 619cae, 7149ae]
- Decompiler frozen > 3 min on initial analysis: kill it; use `readelf`, `objdump -d`, `strings` and targeted xrefs. [ev: 48b12d, 4ff5d8, 305d06, b03ebc]
- Do not reverse every VM opcode: trace the executed bytecode and isolate the I/O and compare handlers. [ev: 16ffe2, 2742bf, a4b4b0]
- Do not NOP a check blindly: first trace whether the bypassed code computes downstream keys or state. [ev: 10f5ca, 7149ae, 619cae]
- Do not trust static tables: `.init_array` or runtime code may mutate them; capture the values at a breakpoint. [ev: ac0a19, 64c704, 38e970, 7149ae]

**Stuck > 20 min** → re-read [`references/logic/meta_reasoning.md`](references/logic/meta_reasoning.md) and the matched playbook's "Decision points".
<!-- logic-distill:end -->

### Tools & Setup (Arch Linux)
Check `command -v` first (honoring "Install Nothing Silently"):
```bash
# Core disassembly & dynamic analysis
command -v r2 || sudo pacman -S radare2
command -v gdb || sudo pacman -S gdb
command -v objdump || sudo pacman -S binutils
command -v ltrace || sudo pacman -S ltrace
command -v strace || sudo pacman -S strace
command -v qemu-aarch64-static || sudo pacman -S qemu-user-static

# Decompilers & GUI tools
command -v ghidra || paru -S ghidra
command -v rizin || paru -S rizin
command -v ilspycmd || paru -S ilspy
command -v jadx || paru -S jadx

# Python emulation & constraint solvers
python3 -c "import unicorn" 2>/dev/null || pip install --user unicorn capstone
python3 -c "import z3" 2>/dev/null || pip install --user z3-solver
python3 -c "import angr" 2>/dev/null || pip install --user angr
```

**Meta note (2025–2026+):** Custom VMs are pervasive and targets are increasingly non-x86 firmware, mobile apps, or on-device ML models. **Emulation-first with Unicorn** ("run the binary's real routine") is the default paradigm—prefer it over reimplementing complex custom hashes or ARX transforms. angr remains powerful for pure constraint math, but avoid it on flattened or signal-driven control flows.

### Reference Files
- Deep-dive reference & cookbook: [`references/modern_reversing.md`](references/modern_reversing.md)
- Multi-arch (x86-64 / ARM64) Unicorn emulator: [`references/unicorn_skel.py`](references/unicorn_skel.py)
- Truth-table linear MBA deobfuscator & Z3 verifier: [`references/mba_deobfuscator.py`](references/mba_deobfuscator.py)
- Symbolic execution skeleton: [`references/angr_solve.py`](references/angr_solve.py)
- Ghidra headless batch decompiler: [`references/DecompileAll.java`](references/DecompileAll.java)

---

## Decision Tree

Match observed binary clues and structural characteristics to the reversing paradigm:

| Clue / Target Characteristic | Vulnerability / Paradigm | Immediate Action | Tool / Reference |
| :--- | :--- | :--- | :--- |
| **Stripped firmware / custom ARX / non-standard hash / AEAD** | Emulation-first RE | Map ROM at base; set ABI registers; emulate routine; read output buffer | `unicorn_skel.py` |
| **Non-x86 binary** (AArch64, ARM, MIPS, RISC-V) | Foreign architecture execution | Emulate target function via Unicorn or execute binary under `qemu-user-static` | `unicorn_skel.py` |
| **Blocks terminate in `ud2` (`0x0f 0x0b`)**; `sigaction(SIGILL)` present | Exception-driven VM | Trace via GDB `handle SIGILL nostop noprint pass`; read opcodes after `ud2` | `modern_reversing.md` §2.1 |
| **Graph-walking interpreter** building functional lambda terms | Scott-encoded functional VM | Dump reachable term graph; evaluate offline with call-by-need (Thunk) reducer | `modern_reversing.md` §2.2 |
| **Bytecode loop** (`while(*pc) switch(*pc++)`) emitting bytes | Bytecode VM | Code-cave patch or hook `write`/`puts` syscalls in GDB to capture stream | `modern_reversing.md` §2.3 |
| **Massive `switch(state)` inside `while(1)`** hiding linear flow | OLLVM Control-Flow Flattening (CFF) | Identify dispatcher & state variable; symbolically trace transitions; deflatten | `modern_reversing.md` §3.1 |
| **Expressions mixing `^`, `&`, `\|`, `~`, `+`, `-`** | Mixed Boolean-Arithmetic (MBA) | Decompose into truth-table basis $\{1, x, y, x \land y\}$; verify with Z3 | `mba_deobfuscator.py` |
| **Multi-stage loader** using `memfd_create` and `/proc/self/fd/` | In-memory unpacking chain | Catch `memfd_create` and `write` syscalls in GDB; dump `\x7fELF` buffers | `modern_reversing.md` §3.3 |
| **iOS ARM64 Mach-O binary** | iOS Swift / ObjC reversing | Parse `LC_SEGMENT_64`; demangle Swift symbols; emulate isolated state VM | `modern_reversing.md` §4.1 |
| **Android APK** with native `.so` (OLLVM protected) | Android JNI reversing | Jadx for Java layer; analyze `JNI_OnLoad` (`RegisterNatives`); Frida hook | `modern_reversing.md` §4.2 |
| **Encrypted `.mnn` / `.tflite` model** in assets | On-device ML reversing | Extract dynamic key (e.g. FNV-1a + SplitMix64); decrypt FlatBuffer; invert | `modern_reversing.md` §4.3 |
| **Power towers ($a^{a^{\dots}}$)** with GMP and `nanosleep` delays | Modular tetration reduction | Reduce exponent mod $\phi(m)$; evaluate via Python built-in `pow(b, e, m)` | `modern_reversing.md` §5.1 |
| **Magic constant `0x9E3779B9` or `-0x61c88647`** | XTEA / TEA block cipher | Recover key schedule from `.rodata`/stack; invert symmetric rounds in Python | `modern_reversing.md` §5.2 |
| **Pure math constraints** on printable ASCII input | Constraint verification | Model input bytes symbolically; solve with angr or Z3 | `angr_solve.py` |

---

## Step 1 — Recon & Dynamic Triage

Fast initial characterization:
```bash
file ./chall                                 # Architecture, linking, stripped status
strings -n 6 ./chall | grep -aiE 'flag|correct|wrong|pass|key|verify'
checksec --file=./chall 2>/dev/null          # PIE, NX, Canary status
```

Dynamic execution first (often yields quick wins or leaks):
```bash
ltrace ./chall                               # Leaks strcmp, memcmp, strncmp plaintext
strace -f ./chall                            # Detects ptrace, timing, memfd_create, open
echo "test" | ltrace ./chall 2>&1 | grep -iE 'cmp'
```

---

## Step 2 — Architecture & Format Routing

| Binary Type (`file`) | Recommended Primary Tool | Strategy |
| :--- | :--- | :--- |
| **Native x86-64 / ELF / PE** | Ghidra headless / rizin | Decompile check function; identify dispatcher |
| **AArch64 / ARM Firmware** | **Unicorn** (`unicorn_skel.py`) | Load raw ROM at physical base; run real routines |
| **iOS Mach-O (ARM64)** | Hopper / Ghidra + Unicorn | Parse `LC_SEGMENT_64`; isolate game-state VM |
| **Android APK / JNI `.so`** | Jadx + Ghidra + Frida | Decompile Java; locate native check; hook runtime |
| **`.pyc` / `.pyo`** | `pycdc` / `decompyle3` | Decompile bytecode (match Python version) |
| **`.NET` / Mono (PE)** | ILSpy (`ilspycmd`) / dnSpy | Near-perfect C# decompilation |
| **JVM `.jar` / `.class`** | `cfr` / `procyon` / `jd-gui` | Decompile Java bytecode |
| **WASM `.wasm`** | `wasm2wat` / `wasm-decompile` | Convert to WebAssembly text representation |

---

## Step 3 — Emulation-First Workflow (Unicorn)

When a binary applies custom cryptographic transformations (bespoke hashes, non-standard ARX, custom AEAD, or self-decrypted payloads), **never waste hours reimplementing them in Python**. Run the real binary routines directly inside Unicorn:

```bash
# Run self-tests to verify multi-architecture environment
python3 -I references/unicorn_skel.py --test

# Emulate stripped firmware snippet or target routine
python3 -I references/unicorn_skel.py --arch arm64 --bin ./firmware.bin --base 0x0 --start 0x1240 --end 0x1380
```

### Key Emulation Capabilities
1. **Calling-Convention Abstraction**:
   - x86-64: `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9` -> `RAX`
   - ARM64: `X0`, `X1`, `X2`, `X3`, `X4`, `X5`, `X6`, `X7` -> `X0`
2. **Auto-Mapping (`UC_HOOK_MEM_UNMAPPED`)**: Automatically maps 4KB pages when firmware accesses unmapped MMIO or heap buffers.
3. **Anti-Debug Hooking**: Intercept instructions at check addresses (e.g. `ptrace`, `rdtsc`, `clock_gettime`), patch return registers to `0`, and advance `PC`/`RIP`.
4. **Self-Decrypted Payloads**: Emulate entry up to the final comparison instruction, then dump the stack/heap buffer where decrypted code/flags reside.

---

## Step 4 — Custom VMs & Exotic Dispatchers

### 4.1 SIGILL / `ud2` Signal Dispatch
- Recognized by `sigaction(SIGILL, ...)` and blocks ending in `0x0F 0x0B` (`ud2`).
- The kernel signal handler reads `uc->uc_mcontext.gregs[REG_RIP]`, fetches virtual opcodes immediately following `ud2`, executes them, and advances `REG_RIP`.
- **GDB Tracing Command**:
  ```gdb
  handle SIGILL nostop noprint pass
  b *handler_addr
  ```
- Recover virtual instruction set, extract equations, and solve with Z3.

### 4.2 Functional & Lambda-Calculus Term VMs
- Graph-walking binary constructing Scott-encoded data structures (Church booleans, Tree nodes, Glyph structures).
- Dump reachable term graph using GDB (`dumpterm.gdb`).
- Evaluate offline using a call-by-need (Thunk) reducer in Python ([`references/modern_reversing.md`](references/modern_reversing.md) §2.2).
- Use bit-coded 1-hot probes to map input bits to output validation branches.

---

## Step 5 — De-obfuscation (OLLVM & MBA)

### 5.1 OLLVM Control-Flow Flattening (CFF)
- Recognize the central dispatcher basic block (highest edge degree) and state variable inside `while(1) { switch(state) }`.
- For each relevant block, trace execution symbolically or via Unicorn emulation until the state variable is updated.
- Reconstruct the true control-flow graph and patch jumps directly to bypass the dispatcher.

### 5.2 Mixed Boolean-Arithmetic (MBA) Simplification
Compiler passes (OLLVM bcf, Tigress) replace arithmetic operations with complex bitwise formulas:
- Decompose expressions into linear truth-table bases using [`references/mba_deobfuscator.py`](references/mba_deobfuscator.py):
  ```bash
  python3 -I references/mba_deobfuscator.py --expr "(x ^ y) + 2 * (x & y)"     # -> x + y
  python3 -I references/mba_deobfuscator.py --expr "(x | y) - (x & ~y)"     # -> y
  python3 -I references/mba_deobfuscator.py --expr "(x ^ y) - 2 * (~x & y)" # -> x - y
  ```
- Verify equivalence across bit-widths using Z3 BitVecs (`--verify`).

### 5.3 Multi-Stage In-Memory Unpackers
- Detect `memfd_create` and `/proc/self/fd/` calls with `strace`.
- Hook `write` syscalls in GDB and carve embedded ELF files (`\x7fELF`).
- Once unpacked, inspect the inner stage—checks often reduce to simple invertible affine equations.

---

## Step 6 — Mobile & On-Device ML

- **iOS ARM64 Mach-O**: Parse `LC_SEGMENT_64` sections (`__TEXT`, `__DATA`). Demangle Swift symbols (`swift-demangle`). Emulate isolated validation routines directly in Unicorn ARM64 without an iOS device or simulator.
- **Android JNI + OLLVM**: Decompile Dalvik bytecode with `jadx`. Check `JNI_OnLoad` for dynamic registrations via `RegisterNatives`. Hook native function arguments and return values using Frida.
- **On-Device ML Models (MNN / FlatBuffers)**:
  - Models in `assets/` may be encrypted (e.g. AES-128-ECB).
  - Look for dynamic key derivation: FNV-1a hash of runtime operator names seeded into SplitMix64 PRNG.
  - Decrypt FlatBuffer model, inspect weights with Netron, and invert linear/Softmax decision boundaries.

---

## Step 7 — Symbolic Execution (angr)

For pure constraint flag checks (e.g., character-by-character transformation compared to static constant arrays):
```bash
python3 -I references/angr_solve.py ./chall
```
- Constrain input bytes to printable ASCII (`0x20` to `0x7E`).
- Use basic-block target addresses (`find=0x401234`, `avoid=[0x401250]`) rather than string matching to prevent state explosion.
- Hook slow library functions (`strlen`, `malloc`) using `proj.hook_symbol`.

---

## Step 8 — Common Algorithmic & Crypto Patterns

- **Modular Tetration / Power Towers**: If the binary builds power towers $a^{b^{c^\dots}}$ using GMP and artificial delays, reduce the exponent mod $\phi(m)$ (Euler's Totient). Modulo 256 exponents collapse in $\le 5$ iterations; evaluate instantly in Python with `pow(b, e, m)`.
- **Symmetric Cipher Identification**: Identify constants in disassembly:
  - `0x9E3779B9` / `-0x61c88647` -> **XTEA / TEA**.
  - `0x67452301`, `0xEFCDAB89` -> **MD5**.
  - `0x6A09E667`, `0xBB67AE85` -> **SHA-256**.
  - Invert rounds directly in Python with extracted keys instead of tracing every round.
- **Anti-Debugging**: `ptrace(PTRACE_TRACEME)`, `/proc/self/status` `TracerPid`, `rdtsc` timing differentials. Patch jumps directly (`r2 -w ./chall` -> `wa nop; nop` or `wa jmp 0x...`).
