# Managed Runtime Decompilation (.NET, JVM, Python, WASM)

> category: rev · slug: `managed-runtime-decompile` · evidence: 25 writeups from 17 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Binary is a container, dropper, or multi-stage unpacker embedding secondary payloads, compressed bytecode, or inner PE/ELF binaries [ev: 9f74f1, 34526b, fbedf0, d7a46d, 4bba00]
- Distribution contains managed runtime bytecode files or intermediate representations (.pyc, .class, .jar, .wasm, .scpt) [ev: 512c78, 34526b, fe2446, cd0145, d88a77, 56fa0d]
- Java application runs on a JVM with an AOT cache (`-XX:AOTCache`) or AppCDS archive (`-XX:SharedArchiveFile`) where class files are omitted or behavior diverges from decompiled JAR bytecode [ev: c9560f, ccbd87, 5de53e]
- Obfuscated script (Python/JS) presents flattened control flow, junk arithmetic, or homoglyph identifiers while checking user inputs via native comparisons or character slicing [ev: 067aaa, d4f0db, e46213]
- Repetitive custom virtual machine or stack operations evaluate mathematical expressions (powers, logarithms, bitwise logic) over flag chunks [ev: fe2446, 46e8b4, 729538]
- Challenge delivers local machine learning model configurations and weights (`model.safetensors`, Flax/JAX `params.pkl`) acting as a memorized secret store [ev: 274017, 69dcf9]
- Multi-stage Python script unpacks bytecode objects dynamically via chained transformations (base64/base85, zlib, `marshal.loads`) [ev: 81f699, af1e2f]

## Opening sequence (do in this order)
1. **Identify container format and carve embedded payloads** — check binary entropy, section names, or file headers with `file`, `pefile`, `rabin2`, or `nm` for embedded PE, ELF, or PyInstaller markers (`<<<PAYLOAD_START>>>`, `MEI`); time-box 5 min. Why: Outer executables are frequently thin loader wrappers; reversing wrapper code wastes time when inner payloads can be carved directly. [ev: 9f74f1, fbedf0, d7a46d, 4bba00]
2. **Audit execution command line and bytecode source of truth** — check runner scripts (`exec.sh`, Dockerfiles) for runtime flags like `-XX:AOTCache` or specific Python minor versions; time-box 5 min. Why: AOT caches override decompiled JAR methods, and Python bytecode magic headers (`.pyc`) must match the expected minor runtime version for valid execution or key derivation. [ev: 34526b, d7a46d, c9560f, ccbd87, 5de53e]
3. **Attempt automated decompilation before manual opcode disassembly** — run language-specific decompilers (`decompyle3`, `pycdc`, `ilspycmd`, `javap`) on extracted bytecode files (.pyc, .class, .dll); time-box 5 min. Why: Clean bytecode reconstructs into readable high-level source code in seconds, avoiding tedious manual stack analysis. [ev: 512c78, 4bba00, cd0145]
4. **Locate input ingestion and output comparison sinks** — search for I/O boundary primitives (WASI `fd_read`/`fd_write`, `PrintStream`, network requests, format strings); time-box 10 min. Why: Establishes input length constraints, isolates verification logic, and flags decoy checks before time is wasted on fake branches. [ev: 34526b, 4bba00, d88a77, e46213]
5. **Probe functional behavior dynamically before full deobfuscation** — evaluate helper functions or runtime comparisons with small test inputs using lightweight runners (`quickjs`, monkey-patching, greedy sampling); time-box 10 min. Why: Black-box dynamic sampling exposes underlying arithmetic or slice equality without requiring manual AST simplification. [ev: 274017, 69dcf9, d4f0db, e46213]

## Decision points
- **IF** the loader drops or executes binaries via system calls (`memfd_create`, temporary directory writes) **THEN** capture the payload dynamically from memory using GDB or filesystem/Wine tracing **ELSE** reverse the static decompression/decryption algorithm (LZMA, XOR, LCG) offline. [ev: 9f74f1, fbedf0, d7a46d, 4bba00]
- **IF** runtime execution uses JVM `-XX:AOTCache` and behavior contradicts decompiled JAR bytecode **THEN** trace the method's `Symbol*` pointer in the AOT cache file to extract and reverse the substituted `ConstMethod` bytecode **ELSE** analyze standard decompiled class files. [ev: c9560f, ccbd87, 5de53e]
- **IF** a flag checker performs piecewise equality or character comparisons in an interpreted/managed runtime (Python/WASM) **THEN** dynamically monkey-patch string equality (`str.__eq__`) or hook WASM comparison opcodes (`i32.ne`) to leak characters sequentially **ELSE** lift the verification logic into an SMT solver (Z3). [ev: d4f0db, fe2446, d88a77, e46213]
- **IF** lifting stack bytecode (WASM, Python stack machine) to Z3 produces `unsat` from high-level decompiler output **THEN** write a minimal symbolic stack interpreter directly on raw instructions (WAT) to guarantee exact operator precedence **ELSE** evaluate constraints algebraically. [ev: fe2446, 46e8b4, 729538]
- **IF** the challenge provides local ML model weights (safetensors, transformer checkpoints) without an executable **THEN** run greedy autoregressive prefix completion (temperature=0) seeded with known flag prefixes or single-byte seeds **ELSE** inspect weight tensors and configuration metadata for embedded payloads. [ev: 274017, 69dcf9]
- **IF** an obscure language or esolang source is provided with a small functional footprint **THEN** reimplement the mathematical pipeline and lookup tables directly in Python **ELSE** analyze compiled bytecode using patched disassemblers. [ev: 0ab809, 21c6dd, 56fa0d]
- **IF** input validation splits into independent small chunks (e.g. 8 bytes) or linear modular constraints **THEN** solve chunks independently via branch-and-bound backtracking or algebraic elimination **ELSE** formulate a unified constraint system. [ev: 067aaa, 46e8b4, 729538, 437afe]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Obfuscated state machine in Python/WASM repeatedly branches on input slices or single characters → control flow flattening is wrapping naive comparisons → monkey-patch string equality (`str.__eq__`) or hook WASM comparison opcodes (`i32.ne`) to log operands and turn execution into a plaintext leak oracle. [ev: d4f0db, d88a77]
- Decompiled JAR bytecode checks literal strings (e.g. "supersecret") but server rejects them with "Invalid password" or disabled login → JVM `-XX:AOTCache` substituted the method body during archive recording → search method `Symbol*` pointers in the AOT cache file to find and reverse the replacement `ConstMethod` bytecode. [ev: ccbd87, c9560f, 5de53e]
- Nested homoglyph expressions or complex stack instructions evaluate to algebraic invariants (e.g. `(a*b)%a == 0`, powers of base 73.21) → complex math is an algebraic decoy for linear recurrences or chunk-wise polynomials → simplify algebraic no-ops and solve via forward recurrence or backtracking. [ev: 067aaa, 46e8b4, 729538]
- Apparent password validation routine passes decrypted strings into format strings containing `"FAKE"` or unreachable `RET` (`0xc9`) opcodes → routine is an elaborate decoy designed to trap static analysts → abandon the decoy function and trace persistent dropped files or background threads. [ev: 9f74f1, fbedf0, 4bba00]
- Language model prompt queries produce repetitive noise loops until seeded with specific token prefixes → model was overfitted to memorize a specific sequence → execute a single continuous autoregressive greedy rollout from the trigger seed without re-prompting. [ev: 274017, 69dcf9]
- Esoteric or obscure functional languages implement multi-stage ciphers where a complex data-dependent parameter collapses into a single 8-bit scalar shift → parameter domain is at most 256 values → brute-force the scalar value mod 256 and verify consistency rather than setting up complex runtimes. [ev: 0ab809, 21c6dd]

## Dead ends & stop-loss
- Manually unpacking commercial packers (VMProtect, Themida) under a debugger — abandon when dynamic anti-debug triggers or unpacking stalls; it failed because the packer was merely a container for dropped payloads or uncompressed data that could be carved statically or captured via Wine file/process logging. [ev: 9f74f1, fbedf0]
- Static AST/source deobfuscation of flattened control flow or functional combinators — abandon when nested expression trees balloon after 10-15 minutes; it failed because junk arithmetic and flattened state machines are designed as time sinks, whereas runtime I/O sampling or comparison hooking extracts truth instantly. [ev: d4f0db, e46213]
- Reversing complex decoy virtual machines or unreached opcode handlers — abandon if entry-point reachability analysis shows immediate returns or pointers to dummy strings; it failed because authors plant complete decoy VMs to divert attention from real data containers. [ev: 9f74f1, fbedf0, 4bba00]
- Searching strings in AOT caches or decompiled JARs when `-XX:AOTCache` is active — abandon when decompiled credentials fail against the server; it failed because interned symbol tables retain old strings while executable logic has been replaced. [ev: ccbd87, 5de53e]
- Attempting to install, build, or configure full compiler/interpreter environments for obscure languages (e.g. Opal) — abandon after initial setup friction; it failed because simple algebraic transforms, substitutions, and encodings can be reimplemented directly in Python. [ev: 0ab809, 21c6dd]
- Conversational prompting or general prompt engineering on CTF language models — abandon when output degenerates into repetitive noise; it failed because CTF models are overfitted on specific flag sequences or trigger tokens rather than general conversation. [ev: 274017, 69dcf9]
- Full instruction-by-instruction symbolic simplification of verbose generated stack machines — abandon when thousands of opcodes stall symbolic analysis; it failed because macro patterns (powers, chunk boundaries) are immediately apparent by tracing concrete values at block boundaries. [ev: 46e8b4, 729538]

## Author tricks / decoys seen
- Decoy flag strings or fake password validation routines that decrypt into `"FAKE"` or dead ends [ev: 34526b, 4bba00]
- Multi-stage wrappers embedding decoy virtual machines that immediately exit via `RET` (`0xc9`) or unreached GameBoy ROMs [ev: 9f74f1, fbedf0]
- Multiple candidate `.pyc` files or modules bundled in PyInstaller with mismatched Python runtime magic numbers [ev: 34526b, d7a46d]
- Using AppCDS / JVM AOT caches (`-XX:AOTCache`) to silently substitute method bodies while leaving old source code and symbols in the JAR [ev: c9560f, ccbd87, 5de53e]
- Obfuscating trivial modular arithmetic behind visual unicode homoglyphs or transcendental functions (Decimal exp/ln) [ev: 067aaa, 46e8b4, 729538]
- Environmental anti-analysis gates requiring specific process basenames, sibling files, or runtime versions to proceed [ev: d7a46d, 4bba00]

## Verify before submitting
- Feed recovered flag string into the unmodified original runtime wrapper or service to confirm acceptance [ev: fe2446, d88a77, e46213]
- Check recovered plaintext against known flag wrapper format and linguistic sense (leetspeak, English phrases) [ev: 067aaa, cd0145, 21c6dd]
- Ensure cryptographic padding (PKCS#7) decodes cleanly without trailing corruption or CRC errors [ev: 9f74f1, 69dcf9, fbedf0]
- Confirm that in-place binary or AOT cache patches preserve exact file offsets, alignment, and container hash map ordering [ev: c9560f, 5de53e]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| `python3` | Offline solvers, bytecode unpacking, SMT lifts, dynamic hooks, and math inversion | 22 |
| `file` | Identifying binary file formats, architectures, and extracted payload types | 3 |
| `base64` | Decoding outer ciphertext layers and exfiltration payloads | 3 |
| `IDA Pro` | Disassembling native loader stubs, syscall dispatchers, and Go runtimes | 2 |
| `pefile` | Parsing Windows PE structures, section headers, and carving embedded payloads | 2 |
| `javap` | Inspecting JVM bytecode instructions, constant pools, and method stacks | 2 |
| `strings` | Extracting printable constants, error messages, and detecting runtime signatures | 2 |
| `pycryptodome` | Standalone AES and RC4 decryption of extracted payload blobs | 2 |
| `marshal` | Unmarshaling Python code objects extracted from multi-stage loaders | 2 |
| `hashlib` | Counter-mode SHA-256 keystream derivation and integrity verification | 2 |
| `Node.js` | Executing JS challenges and hosting WASM runtime environments with hooks | 2 |

## Worked micro-traces
- `[ev: fe2446]` **wasm-checker (AmateursCTF 2025)**: Given a WASM module (`module.wasm`) and Node runner (`main.mjs`) checking a 43-byte flag. First look decompiled WASM to pseudo-C using `wasm-decompile`, revealing 60 conditional checks. Wrong turn was regex-parsing the pseudo-C expressions into Z3 bit-vectors, which returned `unsat` due to decompiler operator precedence bugs. Pivot was disassembling raw WAT with `wasm2wat` and writing a 60-line Python symbolic stack interpreter that accumulated exact Z3 BitVec expressions directly from stack operations. Solved in seconds by querying Z3 for printable ASCII assignments satisfying all 60 constraints.
- `[ev: ccbd87]` **leftovers (GPN CTF 2026)**: Given a Kotlin/Javalin application JAR and a 51 MB JVM AOT cache (`cache.aot`) run with `-XX:AOTCache=cache.aot`. First look decompiled the JAR, finding an obvious admin password check against `"supersecret"` in `lambda$main$15`. Wrong turn was submitting `"supersecret"` to the server, which failed with HTTP 400 because `-XX:AOTCache` had substituted the method implementation during archive recording. Pivot was locating the string `lambda$main$15` in `cache.aot`, tracing its 64-bit `Symbol*` pointer to the CDS `Method` struct, and extracting the replaced 384-byte `ConstMethod` bytecode at offset `0x1f0c680`. Solved by inverting the 4-stage transformation (ROT13, string reverse, XOR) in Python to recover the real password (`algomaster99`) and exploit directory path traversal.
- `[ev: d88a77]` **Will u Accept Some Magic? (UofTCTF 2026)**: Given a WebAssembly binary compiled from Kotlin taking standard input via Node.js / index.js. First look traced WASI imports `fd_read` and `fd_write` to bound the verification routine, finding length check `eq 30` and a deep try/catch loop calling inner function `$132`. Wrong turn was attempting static reverse engineering of Kotlin exception tables, runtime array abstractions, and AST in raw WASM text. Pivot was hooking WebAssembly comparison instructions (`i32.ne`, `i32.eq`) inside `index.js` to log comparison operands at runtime, discovering the inner loop compared input characters directly against expected ASCII values one by one. Solved by using the comparison logger as a plaintext oracle, feeding the expected character into each slot iteratively until all 30 characters passed.

## Weak signals (single source — treat as hints, not rules)
- High-level decompiler pseudo-C can scramble operator precedence in mixed-boolean-arithmetic (MBA) expressions, causing Z3 `unsat`; lift raw stack instructions (WAT) directly via a symbolic stack interpreter instead [ev: fe2446]
- Intentional algorithmic slowdowns (e.g. 64-bit integer multiplication implemented via repeated addition loops in bytecode) cause native execution timeouts; hook or replace hot loops with native arithmetic in a custom emulator [ev: 512c78]
- Multi-stage payloads may include dozens of decoy modules; automate cryptographic authentication tag verification (e.g. AES-GCM) across all candidate blobs before manual triage [ev: 81f699]
- Stripped GnuCOBOL binaries implement variables and types via global `cob_field` and `cob_field_attr` descriptor tables in `.data`/`.rodata` [ev: 437afe]
- IDA Pro truncates decompilation of Go binaries when register propagation misinterprets multi-value error returns (RBX) as unconditional panics, requiring an error jump patch/NOP [ev: d7a46d]
- Python persistence via user-level systemd units loading `sitecustomize.py` from disk images with host-deterministic RC4 encryption keys [ev: 81f699]
- Patching community disassemblers (e.g. `applescript-disassembler`) to handle unmapped RawData types (0x0D) or OOB literal indexes to decode nested compiled AppleScript (.scpt) files [ev: 56fa0d]
- Machine learning models can store compressed executable files (e.g. gzipped ELF) in their autoregressive token sequences, triggered by a single seed character [ev: 69dcf9]
