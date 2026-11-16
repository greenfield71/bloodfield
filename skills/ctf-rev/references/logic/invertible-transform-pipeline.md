# Invertible Transform Pipeline

> category: rev · slug: `invertible-transform-pipeline` · evidence: 60 writeups from 32 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Decompiled code reveals sequential loops applying byte-by-byte or block arithmetic, bitwise shifts/rotations, rolling XORs, or S-box lookups to input characters. [ev: dfa532, b87695, 48b12d, 1a4eac]
- Verification concludes with a direct `memcmp` or loop comparison between the transformed buffer and fixed constant bytes in `.rodata` or `.data`. [ev: 2e3f9e, ae10f0, 4dd429, f7a4b3]
- Forward operations are deterministic, unkeyed, and strictly bijective (ARX, rotations, modular arithmetic, substitutions) with no lossy one-way hash or truncation. [ev: dfa532, b87695, 10f5ca, 55b89d]
- Presence of recognized symmetric cipher components or permutation constants (e.g., ChaCha constants, Salsa20, RC4 state, SplitMix64). [ev: e2561d, 2bd3ec, 860e13, 90db76]
- Running state feedback (rolling XOR or CBC-like accumulation) depends strictly on immediately preceding output or plaintext bytes. [ev: 2e3f9e, 03bc55, 333c14, 975702]
- Input is partitioned into fixed-width chunks or multi-lane word arrays processed independently across symmetric rounds. [ev: ae10f0, c902f2, 55b89d, 2b1253]

## Opening sequence (do in this order)
1. **Locate the comparison sink** — cross-reference failure/success strings or locate `memcmp` and loop checks to identify target ciphertext buffer address and expected byte length; time-box 3 min. Why: establishes the final expected state and buffer size before reverse-engineering individual transformations. [ev: 2e3f9e, ae10f0, 4dd429, dfa532]
2. **Check for staging/unpacking layers** — verify whether the binary decompresses or decrypts an inner payload from staged sections (`.init.*`, `.bss.*`, zlib) before running verification; time-box 3 min. Why: analyzing loader wrapper code instead of the staged transformation core wastes valuable time on setup logic. [ev: 16c799, 81f699, aa5f98]
3. **Trace backward from sink to input** — identify each pipeline stage, loop boundary, and chunk division; verify that every transform is an invertible bijection; time-box 5 min. Why: confirms that backward algebraic inversion is viable and avoids wasting time setting up heavy symbolic execution engines. [ev: dfa532, b87695, 1a4eac, 55b89d]
4. **Extract target constants and lookup tables** — dump expected ciphertext arrays, S-boxes, and constants from `.rodata`, verifying byte endianness and accounting for language runtime metadata (e.g., Rust fat pointer slice headers); time-box 3 min. Why: indexing off-by-metadata offsets injects pointer bytes into cipher targets, corrupting inversion. [ev: 2e3f9e, 03bc55, f3a451, 333c14]
5. **Determine feedback dependency direction** — inspect rolling accumulator loops to determine whether `out[i]` depends on `in[i-1]` (plaintext feedback) or `out[i-1]` (ciphertext feedback); time-box 2 min. Why: chaining against the wrong array corrupts all recovered bytes after index 0. [ev: 2e3f9e, 03bc55, 333c14, 975702]
6. **Verify word packing and endianness** — inspect whether input bytes are packed into 32-bit or 64-bit integer words before ARX stages; verify little-endian vs big-endian layout with `struct.unpack`; time-box 2 min. Why: mismatched word endianness scrambles multi-byte rotations and modular additions. [ev: 10f5ca, 55b89d, 2b1253]

## Decision points
- **IF** it is an easy crackme where the password is the flag, the program checks an exact length, and strings show no flag-like text **THEN** read the short check function first, find the per-index transform and the constant target table (the flag is stored transformed), and invert it in a few lines of script before trying compare hooks or anti-debug work **ELSE** follow the generic opening sequence. [ev: 1d2e38, 4dd429, 467425, b87695, dfa532]
- **IF** all forward pipeline stages are local bijective byte/word operations **THEN** invert each stage algebraically in reverse order in a direct Python script **ELSE** if stages involve coupled non-linear multi-variable systems, formulate SMT constraints in Z3. [ev: dfa532, b87695, 55b89d, 48b12d, 9b4957]
- **IF** the pipeline mixes cyclic word-level equations with chunk-wise state machine updates **THEN** decouple into two phases: solve intermediate word values with Z3 first, then invert character chunk transformations deterministically **ELSE** invert end-to-end in Python. [ev: ae10f0, 9b4957]
- **IF** an operation is an involution (XOR with constant, byte swapping, chunk reversal where `f(f(x)) = x`) **THEN** reuse the exact forward function as its own inverse **ELSE** replace with its mathematical dual (`+ C mod 256` ↔ `- C mod 256`, `ROL` ↔ `ROR`, `* C mod P` ↔ `* pow(C, -1, P) mod P`, `sbox` ↔ `inv_sbox`). [ev: dfa532, b87695, db25e2, 975702]
- **IF** input bytes undergo S-box substitution **THEN** construct an inverse lookup array `inv_sbox = [sbox.index(i) for i in range(256)]` and map backwards **ELSE** apply arithmetic duals. [ev: 2bd3ec, 10f5ca, b87695, 0ab809, 21c6dd]
- **IF** fixed-width word bitwise rotations are used (`rol`/`ror`) **THEN** implement circular rotation with exact word masking `((x << k) | (x >> (W - k))) & ((1 << W) - 1)` for word bit-width W **ELSE** avoid unbounded integer shifts. [ev: db25e2, 10f5ca, 55b89d]
- **IF** input bytes are accessed out-of-order via a computed permutation index `inp[pos]` while updating a sequential accumulator **THEN** simulate in loop iteration order (0..N-1) where accumulator state is sequential, placing each inverted byte into `flag[pos]` **ELSE** invert in array index order. [ev: 333c14, 01d01b]
- **IF** the binary partitions input into segmented tokens (`scanf("%4s-%d-%10s")` or fixed-size chunks) **THEN** solve each token/chunk independently rather than modeling the full key as a joint state space. [ev: c902f2, ae10f0, 03bc55]

## Pivot triggers (the "aha" signals that cracked these challenges)
- All pipeline stages are verified as bijections → no irreversible data loss occurred → invert elementary stages backward (N down to 1) starting from target buffer without constraint solvers. [ev: dfa532, b87695, 10f5ca]
- Cyclic accumulator updates use stride indexing `i & (K - 1)` with no cross-lane mixing → independent parallel lanes → partition problem into K independent streams and de-interleave recovered characters. [ev: 03bc55, 55b89d, 2b1253]
- PRNG or keystream state transitions update without user input dependency → unkeyed deterministic stream → evaluate PRNG forward and directly XOR with target constants `input[i] = target[i] ^ prng[i]`. [ev: f3a451, 333c14, 90db76]
- Rolling accumulator uses unmodulo'd polynomial formula `state = state * B + char` → radix-B representation → extract characters via sequential modulo and integer division `char = state % B; state = state // B`. [ev: 03bc55, 975702]
- Decompiled logic decomposes into massive repetitions of fixed-size instruction sequences → repetitive macro blocks → pattern-match instruction sequences into macro operations and invert macro-by-macro. [ev: 1a4eac, 9dddfe]

## Dead ends & stop-loss
- Throwing Z3 or angr at deep unrolled loops, ARX rounds, or custom emulators — abandon when solver takes > 2 minutes or encounters non-linear bitvector/path explosion; it failed because bijective operations can be inverted algebraically in milliseconds. [ev: dfa532, b87695, 10f5ca, db25e2]
- Inverting pipeline stages in forward order (1..N) instead of reverse order (N..1) — abandon immediately upon seeing unprintable output; it failed because composition inversion requires `(f ∘ g)⁻¹ = g⁻¹ ∘ f⁻¹`. [ev: dfa532, b87695, b5e9ce]
- Chaining rolling XOR inversion against previous target/ciphertext bytes instead of previous recovered plaintext bytes — abandon when index 0 is valid but subsequent bytes turn into garbage; it failed because plaintext feedback requires chaining against `in[i-1]`. [ev: 2e3f9e, 333c14]
- Carving target arrays from raw offsets immediately after strings in Rust/Go binaries — abandon when inversion yields pointer-like binary values; it failed because `.rodata` contains `(ptr, len)` slice metadata preceding actual byte arrays. [ev: 2e3f9e, 4dd429]
- Attempting forward brute-force across multi-round transform chains (> 2^24 search space) — abandon when combinatorial combinations exceed practical limits; it failed because each round possesses an exact analytical inverse. [ev: 1a4eac, 9dddfe, 10f5ca]
- Omitting 32-bit or 64-bit integer overflow masks in Python (`& 0xFFFFFFFF`) — abandon when values diverge or fail assertions; Python arbitrary-precision integers do not wrap naturally like C fixed-width types. [ev: 10f5ca, 55b89d, db25e2]
- Decompiler analysis hanging on whole-program CFG recovery for > 3 minutes — terminate whole-program analysis and focus disassembler directly on validation cross-references from main or prompt strings. [ev: 48b12d, 10f5ca]

## Author tricks / decoys seen
- Decoy flag strings and fake success messages embedded in `.rodata` or emitted by decoy dispatcher branches to trap naive strings/symbol search. [ev: 03bc55, 64f78e, 975702, 35310d]
- Decoy game loops and impossible gameplay score thresholds wrapping self-contained cryptographic derivations that do not actually depend on game state. [ev: 6df9c3, 90db76]
- Target ciphertexts positioned behind fat pointer slice headers `(ptr, len)` in Rust/Go binaries to induce off-by-metadata decoding errors. [ev: 2e3f9e, 4dd429]
- Embedding complex standard cryptographic primitives or large static tables as distractions while the actual verification relies on an easily broken custom MAC or linear formula. [ev: 2b1253, 16c799]
- Intentional binary corruption or failing archive integrity checks (e.g., modified S-boxes or corrupted Makeself headers) forcing players to patch or carve payload files. [ev: 2bd3ec, aa5f98]

## Verify before submitting
- Re-run the binary's forward transformation in Python on the recovered candidate string and assert it matches the target buffer byte-for-byte. [ev: 1a4eac, 9dddfe, 48b12d]
- Pipe the recovered string into the original binary (or native emulator) and verify it prints the true success message and exits cleanly with return code 0. [ev: 2e3f9e, ae10f0, c902f2, 4dd429, 03bc55]
- Inspect the character set and structure of the recovered flag to confirm standard ASCII/printable UTF-8 formatting and correct CTF flag wrapper syntax (`FLAG{...}`). [ev: 2e3f9e, 860e13, e41763, dfa532]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Python 3 / Python | Solver scripting and direct algebraic inversion | 55 |
| Ghidra | Static decompilation and control-flow recovery | 24 |
| file | Binary architecture and format triage | 15 |
| strings | String extraction and prompt identification | 12 |
| struct (Python) | Binary packing/unpacking and endianness decoding | 6 |
| radare2 / rabin2 | Section inspection and symbol triage | 5 |
| objdump | Disassembly of specific functions and sections | 5 |
| IDA Pro | Static decompilation and CFG inspection | 5 |
| xxd | Hexdumping and extracting target constant arrays | 4 |
| GDB | Dynamic debugging and runtime memory dumping | 4 |
| readelf | ELF headers, segments, and symbol table analysis | 3 |
| Z3 | SMT solving for coupled non-linear word constraints | 2 |

## Worked micro-traces
- `[ev: 2e3f9e]` Given bare-metal RV32 ELF without Linux syscalls; first look in readelf revealed entry 0x80000000 and Rust runtime strings with inline memcmp at 0x80000a1a; wrong turns tried running under user-mode QEMU (crashed with exit code 1), inverted raw data at 0x1dd0 (corrupted by Rust slice fat pointer headers), and chained XOR on previous ciphertext; pivot recognized rolling XOR `out[i] = in[i] ^ (i==0 ? 0x55 : in[i-1])` using plaintext feedback; solved by indexing 20 bytes past slice header and inverting sequentially with plaintext feedback `in[i] = out[i] ^ in[i-1]` in Python, verifying via a custom rv32imac emulator.
- `[ev: 10f5ca]` Given custom emulator binary (`qemu-asisarch`) and guest ROM (`challenge.rom`); first look showed stripped host dispatch loop and 10 unrolled guest rounds of S-box, additions, and rotations; wrong turns ran angr on the native host (suffered immediate path explosion) and applied register unscrambling only once (causing emulator desynchronization and infinite loops); pivot identified host instruction whitening `key = (((pc ^ 0x9e37) * 0x1039) + 0x79b9) & 0xffff` and verified all guest rounds were strictly bijective ARX; solved by implementing a Python instruction lifter matching host execution and algebraically inverting the 10 rounds backwards in LIFO order to recover the flag.
- `[ev: 1a4eac]` Given a 5.8MB Commodore 64 binary (`code.bin`); first look observed C64 address space is only 64KB while gzip compressed the binary to 257KB (~4% size), indicating massive repetition across PLA, PHA, TYA, TAY, TXS, TSX operations; wrong turn considered forward brute-force on the 3-byte input tuple (A, X, Y) across all instructions, which would take days; pivot realized the 5.8MB binary splits into 250,000 macro instances matching only 10 unique invertible ARX templates; solved by translating macros into symbolic operations and executing each macro's inverse in reverse order (step N down to 1), recovering the flag in milliseconds.

## Weak signals (single source — treat as hints, not rules)
- LLVM compiler pass synthesis: when `-fpass-plugin` is provided in Makefile, reverse the AST/TypeID checks (e.g. `Type::getTypeID()` enums) and synthesize C source to satisfy compiler passes rather than inspecting runtime binaries. [ev: 16ffe2]
- Makeself self-extracting archive integrity bypass: when archive checksums fail, parse script header `skip='<N>'` and carve payload gzip stream directly via `tail -n +$skip`. [ev: aa5f98]
- GDI / font rasterization flag checkers: when pixel comparison loops validate rendered text bitmaps against embedded XORed buffers, treat the check as an image comparison and use visual rendering or OCR rather than SMT solving. [ev: f7a4b3]
- AOT cache / AppCDS tampering: when Java runtime replaces method bytecode via AppCDS metadata, dump runtime bytecode or trace worker syscalls to capture the actual executed classes. [ev: ccbd87]
