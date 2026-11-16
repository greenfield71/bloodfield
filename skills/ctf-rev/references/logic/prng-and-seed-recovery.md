# PRNG State and Seed Recovery

> category: rev · slug: `prng-and-seed-recovery` · evidence: 10 writeups from 7 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Disassembly shows explicit seeding calls (`srand(time(NULL))`, `time(0)`, or deterministic index formulas) directly preceding repeated `rand()` or modulo arithmetic calls. [ev: d0934a, fa693c, 668d34]
- Global keystrokes or standard input characters are mixed, XORed, or shifted directly into internal PRNG state or shift registers. [ev: 4ed234, ad0e94, b9796e]
- Seed or internal state space is small or bounded (<= 2^28 total states, 20-bit modulus, 1-second timestamp resolution, or small network tick jitter). [ev: 5e0808, 1f8a0b, d0934a, fa693c]
- Verification routine tests input-driven state against a deterministic PRNG sequence, or uses PRNG output as a keystream to decrypt an embedded XOR ciphertext. [ev: 5f9b50, 668d34, 5e0808]
- Binary structure reveals standard mathematical PRNG implementations (xorshift32/64, Galois LFSRs, SplitMix, or glibc linear feedback shift registers) in checking loops. [ev: b9796e, ad0e94, 6c0ca7, 5e0808]

## Opening sequence (do in this order)
1. **Filter strings and trace file/socket syscalls** — inspect strings for fake flags and run `strace -e open,openat,connect` to verify which files and network endpoints are actually referenced; time-box 2 min.
   Why: binaries often package unreferenced decoy flags (`flag.txt`, `flag.enc`) or connect to unadvertised remote sockets. [ev: 6c0ca7, b9796e, 4ed234]
2. **Decompile the check function and locate PRNG loops** — identify the main verification logic and isolate loops that invoke random generators or iterative state updates; time-box 5 min.
   Why: locating the core check clarifies whether the PRNG produces target validation data or encrypts an embedded ciphertext. [ev: 5f9b50, 668d34, b9796e, ad0e94]
3. **Trace seed inputs and data dependencies** — decompile the seeding routines (`srand`, LFSR seed setup, xorshift state) and trace whether seeds derive from timestamps, index formulas, user input, or fixed constants; time-box 5 min.
   Why: seed dependency determines whether to synchronize, steer, precompute, or brute-force the PRNG sequence. [ev: d0934a, fa693c, 668d34, 5e0808, ad0e94]
4. **Quantify entropy and bound the search space** — calculate the total number of candidate seeds or state transitions; time-box 3 min.
   Why: bounded seed spaces (<= 2^28) or narrow timing jitter windows can be exhausted or synchronized in seconds, making complex symbolic inversion unnecessary. [ev: 5e0808, 1f8a0b, d0934a, fa693c]
5. **Replicate PRNG faithfully via native C or libc bindings** — write solver routines in C or bind directly to system `libc.so.6` via `ctypes.CDLL('libc.so.6')` instead of hand-coding glibc PRNG algorithms in Python; time-box 5 min.
   Why: glibc `rand()` uses an additive feedback shift register with subtle state nuances that pure Python implementations frequently get wrong. [ev: d0934a, fa693c, 5f9b50, 668d34]

## Decision points
- **IF** PRNG is initialized with `srand(time(NULL))` or `time(0)` **THEN** synchronize process execution in the same second via shell pipe (`./solve | ./target`) or Python `ctypes.CDLL('libc.so.6').srand(int(time.time()))` with adjacent second offsets (±1) **ELSE** analyze algorithmic seed derivations. [ev: d0934a, fa693c]
- **IF** the stateful PRNG check validates input prefix-by-prefix (`0..i`) without backward dependencies **THEN** solve sequentially via greedy forward byte-by-byte brute force over printable ASCII **ELSE** evaluate the full state space. [ev: b9796e, 5e0808]
- **IF** the PRNG target is generated from deterministic constant/index formulas **THEN** precalculate the target bitmask/bytes offline and map the problem to graph pathfinding or direct inversion **ELSE** recover the dynamic seed. [ev: 668d34, 5f9b50]
- **IF** user input bytes are mixed directly into PRNG state update formulas **THEN** calculate keystrokes that steer PRNG outputs into desired columns, terrain, or state outcomes **ELSE** decouple input navigation from PRNG logic. [ev: 4ed234, ad0e94]
- **IF** candidate PRNG seeds decrypt a ciphertext with a known flag prefix (`flag{`, `lactf{`) **THEN** filter and reject bad candidates after the first few bytes before decrypting the entire buffer **ELSE** verify against full target constraints. [ev: 5e0808, 5f9b50]
- **IF** reversing an interactive turn-based or hazard-avoidance loop **THEN** check the outer loop termination condition for hardcoded tick or step caps before designing wait strategies **ELSE** allow full simulation to proceed. [ev: ad0e94, 5f9b50]
- **IF** the input structure partitions candidate characters into decoupled functional components (e.g. route selector nibble vs cryptographic block payload) **THEN** analyze and solve data dependencies independently rather than modeling an end-to-end monolithic search. [ev: 6c0ca7, b9796e]
- **IF** an interactive game or maze binary exhibits dynamic layout or hazard changes upon movement **THEN** verify whether input bytes are consumed by the terrain/RNG generator before investing in static map navigation algorithms. [ev: 4ed234, ad0e94]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Seed space is constrained to <= 20 bits or narrow timing jitter → algebraic inversion of non-linear feedback or circular dependencies is unnecessary → switch immediately to exhaustive brute force with early prefix pruning. [ev: 5e0808, 1f8a0b, d0934a]
- Verification target is generated by a deterministic PRNG formula → target state is static and fully calculable offline → XOR target output with initial data to isolate exact required bit flips and turn search into Hamiltonian pathfinding. [ev: 5f9b50, 668d34]
- User keystrokes are incorporated into the RNG state update before spawning hazards or mutating terrain → inputs do not just navigate, they steer random generation → invert the 1-byte RNG mixing step to force desired spawn patterns. [ev: 4ed234, ad0e94]
- Validating the PRNG check dynamically triggers internal string decoding routines → static reversal of complex string decryptors is wasted effort → satisfy PRNG checks dynamically and let the binary print the flag. [ev: fa693c, d0934a, 4ed234]
- Binary validation depends on reaching a target bitmask in exactly N moves → calculate Hamming distance between start and target bitmasks; if equal to N, no backtracking is allowed → switch to distance-pruned DFS or A*. [ev: 5f9b50, 668d34]

## Dead ends & stop-loss
- Unpruned brute force across exponential move sequences or guessing multi-stage random choices — abandon when search space > 10^7; it failed because state explosion guarantees timeouts without distance heuristics or seed recovery. [ev: 5f9b50, 668d34, 1f8a0b]
- Modeling unrolled PRNG bitwise feedback loops or spatial grid walks in SAT/SMT (Z3) — abandon when solver hangs or takes minutes; it failed because SMT lacks spatial locality heuristics and chokes on non-linear bitwise shifts that native code evaluates in milliseconds. [ev: 5f9b50, 5e0808, b9796e]
- Reimplementing glibc `rand()` in pure Python from generic LCG formulas — abandon when keystream diverges; it failed because glibc uses an internal linear feedback shift register state table with platform-specific behavior. [ev: d0934a, fa693c, 5f9b50]
- Trusting plaintext strings or unreferenced files (`flag.enc`, decoy flags in `.rdata`) — abandon when target rejects the string or strace shows the file is never opened; it failed because authors plant deliberate decoys to penalize naive string scraping. [ev: b9796e, 6c0ca7, 4ed234]
- Manually reverse-engineering complex string decryption functions inside win handlers — abandon immediately; it failed because once the PRNG check is satisfied, the binary executes its own decryption routines to print the flag. [ev: fa693c, d0934a]
- Assuming an interactive terminal game loop runs indefinitely without checking loop counter termination conditions — abandon conservative wait strategies when no progress occurs; it failed because the binary enforces a hard tick or step cap (e.g. 105 ticks or 28 moves) that aborts the session. [ev: ad0e94, 5f9b50]

## Author tricks / decoys seen
- Planting fake flag strings or decoy notes in `.rdata`/`.data` that pass regex searches but fail validation. [ev: b9796e, 4ed234]
- Bundling red herring files (e.g. `flag.enc`, local test flags) while the real flag is remote or computed in memory. [ev: 6c0ca7, 4ed234]
- Enforcing strict loop counters or turn timeouts in interactive games that abort conservative wait strategies. [ev: ad0e94, 5f9b50]
- Interleaving user input bytes into PRNG state or terrain buffers at non-obvious frame intervals (e.g. every 4 frames). [ev: 4ed234, ad0e94]

## Verify before submitting
- Pipe or inject the recovered input sequence into the binary or remote socket and confirm the victory message and uncorrupted flag string appear. [ev: d0934a, fa693c, b9796e, 668d34]
- Re-hash or re-encrypt the recovered plaintext locally to verify that it regenerates the identical seed and keystream. [ev: 5e0808, 6c0ca7]
- Test across ±1 second seed boundaries when deploying time-synchronized solvers against remote servers over network latency. [ev: fa693c, d0934a]
- Inspect decrypted text format and headers to ensure the decrypted bytes conform to expected flag wrappers (`amateursCTF{...}`, `0xfun{...}`, `lactf{...}`) without corrupt trailing bytes. [ev: 5f9b50, 5e0808, fa693c]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Ghidra / Binary Ninja / Capstone | Disassembling and decompiling PRNG seeding, loop bounds, and check logic | 10 |
| Python 3 | Writing offline simulation, PRNG steering, graph search, and socket solvers | 9 |
| ctypes (`libc.so.6`) / gcc | Calling native glibc `srand`/`rand` or compiling twin solvers with identical PRNG state | 5 |
| pwntools | Automating interactive socket interaction, timing synchronization, and payload delivery | 3 |
| strace / strings / file | Filtering decoy flags, inspecting binary properties, and tracing opened file descriptors | 4 |
| z3-solver | Modeling and solving decoupled bit-vector constraints / SPN cipher blocks | 2 |
| pty / docker | Reproducing terminal buffering and raw TTY semantics to prevent frame desynchronization | 2 |

## Worked micro-traces
- `[ev: 5e0808]` Given a 16-bit MS-DOS executable inside a floppy disk image that hashes input into a seed to generate an LFSR keystream. First look revealed an apparent circular dependency where the flag determines the seed which decrypts the flag. Wrong turn was attempting to algebraically invert the hash and LFSR feedback simultaneously. Pivot was noticing the seed modulo is `1048576` (exactly 20 bits), making exhaustive search trivial. Solved by iterating all 2^20 candidate seeds in Python, pruning candidates after 6 bytes against `lactf{`, and verifying the hash consistency.
- `[ev: 5f9b50]` Given a stripped x86-64 ELF reading 28 WASD movement characters to flip bits on an 8x8 grid, then seeding `srand(3)` to decrypt an XOR ciphertext. First look showed 4^28 possible paths, tempting raw brute force or heavy SAT/SMT modeling. Wrong turn was formulating thousands of CNF clauses in Glucose3 and Z3, which took minutes to evaluate without spatial heuristics. Pivot occurred upon computing the Hamming distance between start and target bitmasks: exactly 28 bits in 28 moves, meaning zero backtracking was allowed. Solved by implementing a DFS with `remaining_bits > remaining_steps` pruning in Python using `ctypes` libc `srand`/`rand`, discovering the unique path in 167 node visits.
- `[ev: ad0e94]` Given an x86-64 ELF interactive terminal game running over raw TTY where acid falls toward obstacles and player target 'F'. First look revealed falling acid generated by xorshift64star, prompting attempts to manually dodge or wait for obstacles to dissolve. Wrong turn was leaving the avatar standing on column 17 (blocking falling acid) and waiting 180 ticks, which hit a hidden 105-tick loop timeout. Pivot was discovering that `spawn_acid_row` mixes the player's last input byte into the PRNG seed, allowing keystrokes to deterministically steer acid spawns into column 17. Solved by writing a reactive pwntools script that injected calculated bytes to excavate the column, stepped the avatar aside to avoid blocking acid, and dropped onto 'F' just before tick 105.

## Weak signals (single source — treat as hints, not rules)
- Embedded game map scripts (Squirrel / vscript): extract BSP map packages to inspect scripts before native code; native PRNG bindings often take predictable client tick and command numbers bounded by network latency. [ev: 1f8a0b]
- Terminal I/O buffering divergence: interactive curses/raw terminal games diverge between standard pipes (`subprocess.PIPE`) and pseudo-terminals (`pty.openpty()` or Docker `-it`), causing off-by-one frame desynchronization. [ev: 4ed234]
- Decoy array elimination: when expected JSON output contains an array of decoy route locks alongside the target, run small parameter loops (16 values) to find the missing target route by elimination. [ev: 6c0ca7]
- Server error oracle calibration: when an interactive server game reveals the correct choice upon failure, sacrifice a probe attempt to calibrate client-server timing offsets and lock down PRNG seeds. [ev: 1f8a0b]
- Disambiguating 1-byte collisions with English context: when forward byte-by-byte brute-force produces multiple ASCII characters with identical hash outputs, branch and disambiguate using English words / leetspeak context. [ev: b9796e]
