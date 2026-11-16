# Triage Shortcuts, Repair, and Binary Patching

> category: rev · slug: `triage-shortcuts-and-binary-patching` · evidence: 18 writeups from 12 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Corrupted binary headers where `file` reports generic `data` or analysis tools (`readelf`, decompilers) crash, while raw hex reveals modified magic bytes or invalid section header offsets (`e_shoff`). [ev: 57ba79, b03ebc]
- Dynamically linked or unstripped binary executing standard library string comparisons (`strcmp`, `strncmp`, `memcmp`) against dynamically generated buffers. [ev: 62ebfa, 881b5f, 86b792]
- Remote challenge accepting TCP connections but remaining completely silent on newline (`\n`, `\r\n`) inputs without printing banners or prompts. [ev: f63cee, f4c455]
- Stripped Go or Rust statically-linked binaries where symbols are either retained in language metadata sections (`.gopclntab`) or decompiler auto-analysis hangs on runtime bloat. [ev: 55b89d, 48b12d]
- Unstripped ELF with descriptive win symbols or isolated check routines (`main`, `turn_in`, `handle_flag`, `LICENSE_KEY`, `EXPECTED`, `SBOX`, `scanf`) where target states or variables are statically defined. [ev: 2bd3ec, c902f2, 86b792]
- Challenges evaluating compiler intermediate representations (LLVM IR `.ll` / pass plugins `.so`) or sprawling repetitive control flow graphs (hundreds of identical basic blocks or state jump tables). [ev: 69c2e0, 8021fe, 08be32, 5a2d31]

## Opening sequence (do in this order)
1. **File format triage & raw header check** — inspect magic bytes and section header sanity (`file`, `readelf -h`, hex view); time-box 2 min. Why: detects immediate corruption (e.g. modified magic, space-padded NULs, or invalid section offsets) before launching heavy tools. [ev: 57ba79, b03ebc]
2. **Library call & dynamic comparison probe** — trace libc calls with `ltrace -s 500` or attach a debugger breakpoint to comparison functions (`strcmp`, `memcmp`); time-box 3 min. Why: if the binary generates plaintext flags in memory before a standard comparison, dynamic interception solves it in seconds without static analysis. [ev: 881b5f, 86b792]
3. **Symbol table & runtime metadata recovery** — scan unstripped symbols (`objdump -t`, `nm`, radare2 `afl`) or language metadata (`strings | grep '^main\.'` for Go `.gopclntab` or Rust mangling); time-box 3 min. Why: reveals win handlers, target constants, or entry points directly, bypassing runtime wrapper code. [ev: 2bd3ec, c902f2, 55b89d, 48b12d]
4. **Transport delimiter & wire-framing probe** — if facing a silent remote TCP listener, fuzz non-newline delimiters (`\x00`, length prefixes) via socket scripts; time-box 5 min. Why: silent sockets often wait on framed binary packet protocols (like COBS) and emit parser error oracles when given null bytes. [ev: f63cee, f4c455]
5. **Win condition & target state localization** — navigate straight to the check function (or tail convergence block) and inspect the comparison operand; time-box 5 min. Why: verify if the expected state is already hardcoded or decoupled into independent byte/word checks before reversing the generation logic. [ev: 08be32, 5a2d31, 86b792, 55b89d, 48b12d]

## Decision points
- **IF** the distfile is only a game map/engine container or scene whose code holds no verification logic, with custom images/geometry and many small same-class entities sharing coordinates **THEN** open it visually in the native editor or render it first (fly away from the cluster, composite layers at one mip/scale using entity offsets, rasterize embedded vertex buffers) before building any logic model **ELSE** trace the logic. [ev: 17ee43, 16d1af, 65d714, 19edb2]
- **IF** the binary runs cleanly under Linux but crashes `readelf`/decompilers **THEN** bypass section table analysis and inspect raw program headers or EOF overlay data **ELSE** repair the header fields (magic bytes / zeroing `e_shoff`) in Python. [ev: 57ba79, b03ebc]
- **IF** an unstripped or dynamically linked binary compares input using standard `strcmp`/`memcmp` against a dynamically computed buffer **THEN** intercept the plaintext argument dynamically (`ltrace -s 500` or GDB breakpoint) **ELSE** isolate and extract the generation tables statically. [ev: 62ebfa, 881b5f, 86b792]
- **IF** the binary is a stripped Go or Rust executable **THEN** locate entry points via `.gopclntab` or use lightweight CLI decompilation (radare2 + r2ghidra `pdg`) targeting specific functions **ELSE** avoid heavy graphical decompiler auto-analysis that freezes on runtime bloat. [ev: 55b89d, 48b12d]
- **IF** input verification decomposes into independent byte-wise or word-wise modular arithmetic (e.g. ARX or modular equations without cross-byte carries) **THEN** invert each slice algebraically in Python **ELSE** evaluate with specialized SAT/SMT or integer solvers only when inter-slice dependencies exist. [ev: 55b89d, 48b12d, c902f2]
- **IF** the binary verifies an input key/token and then dynamically decrypts/derives the flag at runtime **THEN** execute the binary natively with the recovered key to emit the flag **ELSE** avoid reimplementing runtime decryption routines in Python. [ev: 55b89d, 48b12d]
- **IF** the challenge verifies compiler intermediate representations (LLVM IR) **THEN** reverse the pass plugin `.so` to extract structural AST/IR requirements and mark synthesized C functions with `__attribute__((noinline))` **ELSE** compiler optimizations will inline calls and fail IR pattern matches. [ev: 69c2e0, 8021fe]
- **IF** an FSM has hundreds of state jump tables converging on a visit counter check **THEN** extract the transition CFG into an adjacency list and solve via graph algorithms (Warnsdorff heuristic DFS) **ELSE** symbolic execution (angr/Z3) will suffer state explosion. [ev: 08be32, 5a2d31]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Silent TCP listener emits an error like `"not enough input bytes for length code"` when sent `\x00` → identifies Consistent Overhead Byte Stuffing (COBS) framing over raw TCP → wrapped credentials in COBS frames (`b'\x06admin\x00'`) to authenticate. [ev: f63cee, f4c455]
- Decompilation reveals uncoupled per-byte or per-word arithmetic checks (`rol`, `xor`, `add`) followed by native flag decryption → verification requires no solver and post-check decryption is handled by the binary → inverted each slice algebraically in Python and passed the recovered token to the binary. [ev: 55b89d, 48b12d]
- Win condition check compares user state against hardcoded constants loaded at program startup or isolated in .data → the required state is statically known without solving game logic or traversing the state machine → fed the target state directly into the decryption routine or patched state memory at the check in GDB. [ev: 86b792, c902f2]
- Disassembly of dynamic comparison reveals unstripped standard libc `strcmp@plt` or leaf functions returning single immediate ASCII bytes → generation logic is a direct character mapping and the expected string exists in plaintext in memory → intercepted full flag via `ltrace -s 500` or dumped return constants with objdump/awk. [ev: 62ebfa, 881b5f]
- Disassembler CFG shows repetitive indirect jumps over jump tables with a state visit counter array → problem is graph traversal (Hamiltonian path) rather than cryptographic reversing → extracted jump tables into an adjacency list and solved pathing with Warnsdorff's heuristic DFS. [ev: 08be32, 5a2d31]
- Tool crashes on ELF parsing despite successful native OS execution, or hex inspection shows uniform byte replacement in header → corruption is localized to section headers or simple global character substitution → repaired magic bytes globally or bypassed section headers to inspect raw EOF overlay payloads. [ev: 57ba79, b03ebc]
- Compiler pass verification fails because expected `CallInst` nodes are missing from emitted IR → compiler optimizer inlined or dead-code-eliminated pure functions lacking side effects → added `__attribute__((noinline))` and volatile side effects to force call emission. [ev: 69c2e0, 8021fe]

## Dead ends & stop-loss
- Running symbolic execution (angr / monolithic Z3) on large state machines or multi-thousand instruction dispatches — abandon when tool exceeds 3 minutes or memory balloons; it failed because hundreds of indirect jumps or complex circuit gates cause catastrophic path and RAM explosion. [ev: dcce7e, 08be32, 5a2d31]
- Reimplementing runtime crypto or flag decryption routines in Python after recovering the key/target state — abandon when the binary is runnable locally; it failed because native binary execution already implements the full decryption and avoids transcription or padding errors. [ev: 55b89d, 48b12d, 86b792]
- Reversing complex string-generation logic (tokenizers, struct arrays, function pointers) when main compares output via standard libc `strcmp` — abandon when dynamic tracing is available; it failed because `ltrace -s 500` or a GDB breakpoint extracts the target buffer in seconds without reverse engineering. [ev: 62ebfa, 881b5f]
- Testing higher-level ASCII credentials, command variants, or keyboard scancodes on a silent TCP service — abandon when repeated newline-terminated strings yield no output; it failed because transport-level packet framing (such as COBS) must be satisfied before any application-layer commands are processed. [ev: f63cee, f4c455]
- Waiting on graphical or automated whole-program decompiler analysis (e.g. Binary Ninja / Ghidra auto-analysis) on stripped Go or Rust binaries — abandon when analysis hangs for >3 minutes; it failed because massive standard library runtimes and monomorphized functions overwhelm full-binary analyzers; pivot to targeted CLI decompilers (`r2ghidra pdg` or `.gopclntab` parsing). [ev: 55b89d, 48b12d]
- Writing pure C algorithmic code without compiler annotations for LLVM IR-checking passes — abandon when emitted IR lacks expected call instructions; it failed because optimizing compilers inline or eliminate functions lacking observable side effects. [ev: 69c2e0, 8021fe]
- Attempting to rebuild or decompile corrupted ELF section headers when the binary already runs — abandon when tools crash on invalid `e_shoff`; it failed because the Linux kernel ignores section headers entirely, allowing direct execution or raw hex inspection of trailing overlays. [ev: 57ba79, b03ebc]

## Author tricks / decoys seen
- Thematic or historical name misdirection: using famous problem names (e.g. Königsberg Seven Bridges suggesting Eulerian edge traversal) when the implementation strictly enforces vertex coverage (Hamiltonian path). [ev: 08be32, 5a2d31]
- Puns and wordplay in challenge descriptions: hiding protocol clues in flavor text (e.g. "cobbled mess" for COBS framing, "remoose" for ELK magic byte corruption). [ev: f63cee, f4c455, 57ba79]
- Deliberate tool-breaker metadata corruption: invalidating ELF section header offsets (`e_shoff`) or substituting NUL bytes to crash standard decompilers while preserving executable program headers. [ev: 57ba79, b03ebc]
- Decoy complexity in unstripped binaries: implementing elaborate multi-step state machines, menu dispatchers, or tokenizers when the target state is hardcoded or the final check is a plaintext libc `strcmp`. [ev: 62ebfa, 881b5f, 86b792]
- Dead-code crypto traps: inserting complex mathematical derivation routines guarded by unconditional early returns (`if (var_54 == 0) return`) or unreachable branches to mislead static analysis. [ev: 0feb9f, 86b792]

## Verify before submitting
- Execute the original or repaired binary natively with the recovered key, license, or patched inputs to confirm the positive success banner and flag output. [ev: 2bd3ec, 55b89d, 48b12d, 62ebfa]
- Check string inspection limits: when using dynamic tracing tools (`ltrace`), verify strings are not truncated with trailing `...` by setting `-s 500`. [ev: 881b5f, 62ebfa]
- Transmit generated payloads (delimited packets or formatted state inputs) against the live remote TCP/TLS service to verify network transport parity. [ev: f63cee, f4c455, 08be32, 5a2d31, 8021fe]
- Validate mathematical reversibility: assert forward evaluation of recovered tokens or patches against original validation constants before submitting. [ev: 55b89d, 48b12d]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| python3 / Python | Scripting packet framing, algebraic inversion, graph DFS, and header patching | 15 |
| objdump | Disassembling repaired binaries, inspecting leaf functions, and extracting jump tables | 6 |
| file | Identifying ELF format, corruption status, architecture, and stripped state | 6 |
| strings | Identifying unstripped function names, Go `.gopclntab` symbols, and runtime crypto imports | 4 |
| radare2 / r2ghidra | Inspecting unstripped symbols and targeted function decompilation (`pdg`) on stripped Go/Rust | 4 |
| subprocess | Running binaries as black-box oracles or executing native binaries with recovered tokens | 3 |
| Ghidra | Decompiling binaries, reversing LLVM pass plugins, and spotting corrupted logic | 3 |
| pwntools / nc / ncat | Interacting with remote TCP/TLS services and transmitting framed binary packets | 4 |
| Binary Ninja | CFG edge recovery, computed jump table extraction, and emulator analysis | 2 |
| ltrace | Intercepting dynamic libc calls (`strcmp`, `memcmp`) with `-s 500` | 1 |
| gdb | Dynamic memory inspection and breakpoint patching of target states | 1 |

## Worked micro-traces
- `[ev: 881b5f]` Given unstripped 64-bit ELF `my_secret_recipe` expecting flag as `argv[1]`. Disassembly of `main` showed `parse_recipe` constructing a string followed immediately by libc `strcmp@plt`. Running default `ltrace` intercepted `strcmp` but truncated the flag at 32 characters. Solver reran with `ltrace -s 500 ./bin/my_secret_recipe aa`, instantly revealing the full untruncated flag argument in seconds without reversing any recipe parsing logic.
- `[ev: 55b89d]` Given stripped Go binary `tollgate` prompting for an admin token. Standard disassembler auto-analysis failed, but `.gopclntab` symbols revealed `main.main`, `main.check`, and `main.unlock`. Solver initially considered reversing the AES decryption in `main.unlock`, but pivoted upon seeing that `main.main` performed four independent 32-bit ARX word checks. Solver inverted each word algebraically in Python, executed `./tollgate <token>`, and let the native binary decrypt and print the flag.
- `[ev: f63cee]` Given a silent remote TCP service with prompt mentioning a USB device and a "cobbled mess". Sending ASCII credentials with `\n` or `\r\n` left the socket completely idle, and 15 minutes were wasted testing alternate keyboard layouts. Solver pivoted to delimiter fuzzing; sending `admin\x00` provoked the error `"not enough input bytes for length code"`, recognizing Python's COBS wire framing. Solver implemented a Python COBS packet encoder, sent framed credentials sequentially, and received the flag.

## Weak signals (single source — treat as hints, not rules)
- Massive ternary logic circuits synthesized from `bsr`/`bzhi` instructions can be sliced topologically into independent sub-circuits and solved by domain-specific solvers (CaDiCaL SAT for boolean logic, MILP for modular equations, and factordb for multiplier carry chains). [ev: dcce7e]
- A binary outputting incremental prefix hashes allows linear byte-at-a-time chosen-plaintext recovery via `subprocess` without reversing the underlying hash function (MD2). [ev: 4529d2]
- Deliberately corrupted crypto routines in unstripped binaries can be repaired by checking standard mathematical invariants: bijective S-box distribution (histogram of 0..255), 8-bit rotation shift sum (complement equals 8), and reversible bitwise operators (patching non-invertible OR to XOR). [ev: 2bd3ec]
- Segmented inputs parsed via `scanf("%4s-%d-%10s")` may have stack variable memory addresses that differ from the textual clause order in conditional checks; sort by ascending stack offsets. [ev: c902f2]
- Custom emulator binaries with hundreds of bundled ROMs often hide a backdoor opcode (e.g. `0xFXFF`) in the instruction decoder rather than vulnerabilities in the ROMs; check for delayed key propagation across execution cycles. [ev: 0feb9f]
