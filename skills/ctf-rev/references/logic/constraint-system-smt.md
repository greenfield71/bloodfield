# Coupled Constraint System and SMT Solving

> category: rev · slug: `constraint-system-smt` · evidence: 19 writeups from 14 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Circular, cyclic, or sliding multi-variable equality constraints across overlapping input characters where manual step-by-step inversion is blocked. [ev: 666a42, e46213, ae10f0, 57fd34, 2762f0]
- Verification logic evaluates GF(2) linear systems, parity matrix checks, or cellular automata XOR-sums over bit arrays. [ev: ac0a19, 70d6ff, f9927d, 976104]
- Massive boolean or ternary logic netlists (DAGs of basic gates like bsr/bzhi, bitwise combinations, or wire tuples) with no data-dependent branching. [ev: dcce7e, dff053, a83e1b]
- Modular matrix-vector products or modular arithmetic congruences (`sum(c * x) == target mod M` or Z/256Z linear systems). [ev: dcce7e, 4ff5d8, ae10f0]
- Syntactic or functional obfuscation wrapping straightforward constraint checks (nested Church lambdas, JS bitwise chains, WASM stack expressions). [ev: fe2446, 811af8, e46213]

## Opening sequence (do in this order)
1. **Input structure & entry point recon** — verify candidate input format (length, chunking, character set), entry point integrity (native JNI vs DEX, supervisor vs child, overlapping code), and confirm whether auxiliary files are actually accessed vs unreferenced decoys; time-box 5 min. Why: eliminates red herrings and dead decoy branches before doing math. [ev: 6c0ca7, 960b0e, 70d6ff, 31502d, 2762f0]
2. **Decouple subsystems & trace dataflow** — determine if the input partitions into orthogonal components (e.g. route parameters vs cipher data, or independent chunks) or feeds an acyclic DAG; time-box 10 min. Why: breaks an exponential joint state search into small, independently solvable subproblems. [ev: 6c0ca7, dcce7e, ae10f0, e46213]
3. **Classify mathematical domain of verification logic** — test whether transformations are GF(2) linear, modular ring arithmetic (Z/2^k Z or Z/mZ), boolean logic gates, or integer multiplication; time-box 10 min. Why: choosing the correct solver (Gaussian elimination vs Z3 BitVec vs CDCL SAT vs integer factoring) avoids catastrophic solver stalls and OOM kills. [ev: ac0a19, dcce7e, 4ff5d8, 976104, 666a42]
4. **Validate operator & constant semantics using known flag prefix** — test hypothesized operators (e.g. ADD vs XOR, operator precedence in stack/AST) against the known flag prefix (e.g. `flag{`, `ctf{`, `0xfun{`); time-box 5 min. Why: catches AST/decompiler precedence bugs and mistranslated opcodes before formulating full constraints. [ev: a4b4b0, fe2446, 57fd34]

## Decision points
- **IF** constraints form an uncoupled or forward-chaining GF(2) linear system **THEN** extract matrix coefficients and solve directly via Gaussian elimination **ELSE** model in an SMT/SAT solver. [ev: ac0a19, 70d6ff, f9927d, 976104]
- **IF** a logic circuit / netlist contains independent topological slices or chunks **THEN** partition backwards from output summary nodes and solve chunks separately **ELSE** solve monolithically. [ev: dcce7e, a83e1b, ae10f0]
- **IF** an operation involves modular multiplication by an odd constant C mod 2^k **THEN** invert algebraically via modular inverse `pow(C, -1, 2**k)` **ELSE** transcribe into bit-vector constraints. [ev: ae10f0, 4ff5d8]
- **IF** high-level decompilers (wasm-decompile, JS beautifiers) produce ambiguous operator precedence in arithmetic/logic expressions **THEN** lift directly from low-level disassembly or stack instructions (WAT, AST) into SMT expressions **ELSE** use decompiled C logic. [ev: fe2446, e46213]
- **IF** a validator distributes dozens of linear checks across obfuscated classes or functions driven by deterministic state transitions **THEN** extract the transition graph and constraints via regex or AST parsing scripts into Z3 **ELSE** trace dynamically. [ev: 2762f0, e46213]
- **IF** a solver returns multiple valid solutions or slightly corrupted prefixes due to under-constrained bits **THEN** pin known flag prefix/suffix assertions and enforce printable ASCII bounds (0x20..0x7e) **ELSE** proceed without bounds. [ev: 57fd34, 976104, 666a42]
- **IF** the binary includes runtime integrity hashing (.text checksums, TracerPid, anti-debug hooks) **THEN** use hardware execution breakpoints (`hbreak`), syscall catchpoints (`catch syscall mprotect`), or concrete emulation without debuggers to dump live state **ELSE** use standard dynamic debugging. [ev: ac0a19, 70d6ff, 31502d]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Perturbation / basis testing reveals sliding influence windows or constant multiples mod M → Circuit is not arbitrary random logic but high-level arithmetic (carry chains / modular linear equations / matrix algebra) → Switch from CDCL SAT / SMT to factoring or integer/linear algebra solvers. [ev: dcce7e, 976104]
- Known flag prefix produces contradictions or UNSAT under hypothesized operators → Underlying operator semantics or precedence were misidentified (e.g. XOR vs ADD, decompiler precedence error) → Correct operator definitions or re-lift from raw assembly/stack to restore solvability. [ev: a4b4b0, fe2446]
- Static analysis reveals clean plaintext tables/strings alongside runtime mutation/decryption → Static data is an author decoy leading to plausible fake flags → Intercept live runtime memory (via syscall catchpoints or hooks) to extract true dynamic matrices/keys. [ev: ac0a19, 70d6ff, 960b0e]
- Verification contains circular / sliding cross-byte dependencies ((i+k) % N) → Manual step-by-step inversion is blocked by mutual recursion → Transcribe equations directly into Z3 BitVec to solve simultaneously. [ev: 666a42, e46213, ae10f0]
- Direct matrix inversion over GF(2) fails due to rank deficiency (non-trivial nullspace) → Under-constrained degrees of freedom exist → Augment linear system with known flag prefix bit equations to restore full rank and solve uniquely. [ev: 976104, 57fd34]

## Dead ends & stop-loss
- Running monolithic symbolic execution (angr / Z3) on multi-million instruction or complex synthesized circuits — abandon when memory climbs rapidly or stalls; it failed because state explosion and OOM kill the solver; partition into topological slices or lift to SAT/algebra. [ev: dcce7e, 666a42]
- Running CDCL SAT solvers (CaDiCaL) on integer multiplication / carry-chain arithmetic — abandon when solver progress stalls at 0-1% remaining constraints; it failed because CDCL has exponential complexity on multiplier carry chains; probe influence window and factor via factordb. [ev: dcce7e, ae10f0]
- Trusting high-level decompilation (wasm-decompile, minified JS AST) for operator precedence without verification — abandon when solver returns UNSAT on known prefix; it failed because decompilers misplace parentheses on mixed boolean-arithmetic; lift from stack/WAT directly. [ev: fe2446, a4b4b0]
- Interactive debugging with software breakpoints on binaries with `.text` or timing/tracer integrity checks — abandon when execution aborts or state silently corrupts (e.g. TracerPid != 0, checksum mismatch); it failed because `0xCC` or debugger presence mutates execution flow into decoys; switch to hardware breakpoints, syscall catchpoints, or concrete script emulation. [ev: ac0a19, 70d6ff, 31502d]
- Attempting manual algebraic inversion on circularly coupled multi-byte loops — abandon after 10-15 minutes of circular dependency tracing; it failed because cross-index operations require simultaneous equation solving; transcribe into Z3. [ev: 666a42, e46213]
- Reversing unreferenced decoy files bundled in the archive (e.g. unopened `flag.enc`) — abandon if `strace` or binary strings show no open/read calls; it failed because authors package unused red herrings. [ev: 6c0ca7, 960b0e]

## Author tricks / decoys seen
- Plausible decoy flags and decoy constraint systems hardcoded in `.rodata`/`.data` to trap static analyzers. [ev: ac0a19, 70d6ff, f9927d]
- Decoy arrays in output/target specs that disclose legitimate parameter values by process of elimination. [ev: 6c0ca7, f9927d]
- Splitting validation state machines across languages or layers (e.g. Java DEX classes + native JNI `.so`, or client web UI + compressed blobs) to hide execution flow. [ev: 2762f0, 811af8]
- Silent corruption of internal state/keys via anti-debugging checks (TracerPid, code checksums) steering solvers to fake solutions without crashing. [ev: ac0a19, 70d6ff, 31502d]
- Overlapping instructions / computed entry points designed to make disassemblers follow dead decoy paths. [ev: 70d6ff, 960b0e]
- Hardware-specific floating-point arithmetic quirks (x87 80-bit precision, 66-bit pi reduction, FMA rounding) weaponized so portable IEEE-754 libraries hit decoy flags. [ev: f9927d, 70d6ff]
- High-level decompilation traps where C-like lifters distort operator precedence on stack operations. [ev: fe2446, e46213]

## Verify before submitting
- Assert uniqueness in Z3 by re-solving with the negation of the found solution (`solver.add(var != sol)`) to confirm exactly one satisfying input exists. [ev: 6c0ca7, 666a42, 57fd34]
- Verify recovered candidate directly against the target binary or emulator as the ground-truth oracle. [ev: 57fd34, 6c0ca7, a83e1b]
- Validate candidate satisfaction across all independent slices/layers before concatenating final flag string. [ev: dcce7e, 70d6ff, f9927d]
- Check candidate flag format prefix, suffix, and character printability (ASCII printable range 0x20..0x7E) to rule out spurious mathematical solutions. [ev: 57fd34, 666a42, dcce7e]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| python3 / Python | Scripting, AST transformation, matrix extraction, solver glue | 18 |
| Z3 / z3-solver | SMT bit-vector constraint solving, SAT solving | 13 |
| Ghidra / IDA | Static disassembly, deconstruction of constraint logic, CFG analysis | 6 |
| Gaussian elimination | Solving linear systems over GF(2) and modular rings (Z/256Z) | 4 |
| GDB / debuggers | Dynamic memory inspection, syscall catchpoints, buffer dumping | 4 |
| hashcat | GPU cracking of intermediate credential gates (sha512crypt) | 3 |
| CaDiCaL | High-performance CDCL SAT solving on lifted boolean netlists | 1 |
| factordb | Integer factorization of composite multiplier targets | 1 |
| Unicorn Engine | Symbolic token ID propagation and netlist recovery | 1 |
| wabt (wasm2wat) | Disassembling WASM bytecode to WAT stack instructions | 1 |
| jadx | Decompiling Android DEX classes to inspect character check methods | 1 |

## Worked micro-traces
- `[ev: dcce7e]` DEF CON CTF Quals 2026 challenge *My Favorite Instructions* presented a 68-byte flag check verified by a 19M-instruction ternary logic circuit built from `bsr`/`bzhi`. Initial attempts to run angr and monolithic Z3 crashed with OOM. Splitting the netlist into independent sub-circuits allowed CaDiCaL SAT to solve chunks 1, 5, and 6, but CaDiCaL stalled indefinitely on chunk 4 and chunk 2_3. Probing chunk 4 revealed basis output scaled by table multiples mod 3^21 - 1, solved via MILP, while chunk 2_3 showed an 80-trit sliding influence window indicating base-3 integer multiplication, cracked instantly by factoring the target integer via factordb.
- `[ev: ac0a19]` Null Origin CTF 2026 challenge *Palimpsest* presented a 5-layer cascading VM evaluating GF(2) linear constraints. Static disassembly revealed clean plaintext opcode tables in `.data` that solved to an intentional decoy flag `Null0rigin{you_trusted_the_first_draft}`. Placing software breakpoints in GDB corrupted an internal `.text` SHA-256 integrity hash and aborted execution. Pivoting to non-invasive debugging with `catch syscall mprotect` intercepted execution at table decryption, dumped the live runtime opcode table, and extracted the genuine rank-42 GF(2) linear system, solved via Gaussian elimination in 0.365s.
- `[ev: 666a42]` H7CTF 2026 Quals challenge *Constraint Yourself* presented a stripped ELF binary verifying a 16-byte key needed to AES-decrypt an embedded flag. Solvers initially attempted sequential byte-by-byte algebraic inversion of the verification loops. Analysis quickly showed loop 1 coupled index `i` with `(i+3)%16` and loop 3 coupled `i` with `(i+5)%16`, creating cyclic circular dependencies across the entire 16-byte buffer that blocked manual inversion. The solver abandoned manual algebra, transcribed all three loops directly into Z3 BitVec(8) constraints with printable ASCII bounds, and recovered the unique key in milliseconds to decrypt the flag.

## Weak signals (single source — treat as hints, not rules)
- Hardware-specific floating-point arithmetic (x87 80-bit precision, 66-bit pi reduction, FMA rounding) must be evaluated via native machine code stubs (ctypes/inline asm) on physical silicon rather than high-level math libraries to avoid landing on decoy flags. [ev: f9927d]
- Testing candidate parameter spaces to identify target keys by process of elimination against an array of known decoys bundled in the target specification. [ev: 6c0ca7]
- Emulating basic blocks in Unicorn with symbolic token IDs to extract a combinational hardware netlist without executing side effects. [ev: a83e1b]
- Client-side time gates in web/JS challenges can be bypassed by inspecting embedded compressed base64 blobs (gzip magic `\x1f\x8b`). [ev: 811af8]
- When analyzing functional obfuscation (nested Church-encoded lambdas), probe helper functions dynamically with small integer tables to identify arithmetic operations. [ev: e46213]
- Lifting WASM binary to WAT stack instructions via wabt rather than wasm-decompile to prevent precedence distortion in complex MBA expressions. [ev: fe2446]
