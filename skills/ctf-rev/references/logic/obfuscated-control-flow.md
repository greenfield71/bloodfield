# Obfuscated Control Flow (CFF and MBA)

> category: rev · slug: `obfuscated-control-flow` · evidence: 30 writeups from 19 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Control flow is routed through exception handlers (`signal(SIGILL)`, `ud2`, `SIGSEGV`, `VEH`) where handlers manipulate context registers (`ucontext_t` / `REG_RIP`) instead of standard branch instructions [ev: 05e4b7, 81f244, 7f76cc, 03bc55, 4ff677].
- Decompiler displays flattened dispatcher loops with large switch-case structures governed by an evolving state variable (OLLVM CFF) [ev: 1d2e38, 4dd429, d4f0db, b74c9e, 2addf5].
- Functions contain bloated expressions combining bitwise and arithmetic operators (MBA) or nested polynomial expansions to mask simple constants or byte-level relations [ev: 46e8b4, 729538, ff8049, 067aaa, d4f0db].
- Anti-debug checks (`ptrace`, `/proc/self/status` `TracerPid`, breakpoint scanners) are directly coupled with global state initialization or cryptographic seed derivation [ev: 70d6ff, 7149ae, 9bb016, 64c704, 2addf5].
- Binary decrypts obfuscated byte blobs dynamically into `mmap` buffers or stack arrays via XOR or stream ciphers prior to validation [ev: f3a451, 01d01b, 333c14, 0ffc7b].
- Android applications incorporate root or Frida detection routines guarding native JNI validation logic [ev: 84932b, 3d3586, e3c4b0, 6c0727, 4127d2].

## Opening sequence (do in this order)
1. **Triage container and architecture boundaries** — look for bitness transitions (e.g. Heaven's Gate `PUSH 0x33; ... RETF`), self-modifying code, or packed sections; time-box 5 min. Why: Decompilers misinterpret stack offsets and fail function analysis if execution switches bitness or unpacks code in-flight. [ev: 0ffc7b, 0180b1, 70d6ff, 64c704]
2. **Scan for signal handlers and exception registrations** — look for `sigaction` / `signal` calls (`SIGILL`, `SIGSEGV`) or `AddVectoredExceptionHandler` before analyzing `.text`; time-box 5 min. Why: In exception-driven dispatchers, linear disassembly dead-ends at `ud2` traps; virtual opcodes and true control transfers are executed inside the signal handlers. [ev: 81f244, 64c704, 465bca, 305d06, 860e13]
3. **Audit anti-debug and tamper side-effects** — look for `ptrace`, `/proc/self/status` `TracerPid`, or breakpoint scanning and trace whether they write to global state or key seeds; time-box 5 min. Why: Anti-tamper state setup is frequently disguised within anti-debug checks; naive NOP patching leaves required state uninitialized and causes silent verification failures. [ev: 70d6ff, 7149ae, 9bb016, 2addf5]
4. **Identify dispatcher and control flow pattern** — look for central switch loops (CFF), sequential linear systems over GF(2), or accumulator loops; time-box 10 min. Why: Distinguishes whether the control flow can be inverted greedily step-by-step, simplified via algebraic rewriting, or requires dynamic execution logging. [ev: 1d2e38, 4dd429, d4f0db, 01d01b, 333c14, 70d6ff]
5. **Trace concrete execution or profile basic blocks** — trace basic blocks using Unicorn, Frida hooks, or dynamic logging with varying inputs; time-box 10 min. Why: Runtime tracing strips away synthetic dispatcher transitions and opaque predicates, isolating the exact instruction sequence touching input bytes. [ev: 1d2e38, 4dd429, 84932b, 4127d2, b74c9e, 067aaa]

## Decision points
- **IF** a large or static binary is slow, strace -f shows `clone`/`fork` + `ptrace`, `memfd_create` + `mmap`, or a stream of SIGILL/SIGSEGV/SIGBUS **THEN** the tracer/handler is the VM decoder: find the code that decodes the faulting instruction bytes, list the tiny primitive op set, lift each call site (track operand registers) into a symbolic or linear model and solve it (often affine over the input) **ELSE** analyze the traced code normally. Do not treat ptrace only as anti-debug. [ev: 0180b1, 305d06, 81f244]
- **IF** obfuscation wraps a loop that fills a 256-byte array, runs a key-dependent swap pass and XORs the input (RC4 shape) or shows other standard-primitive constants **THEN** name the primitive from loop shape, lift key and target table from `.rodata`, check for a small per-byte tweak, and decrypt offline instead of deobfuscating the whole binary **ELSE** trace blocks to expose data flow. [ev: 1d2e38, 4dd429, 2d00be, 6df9c3, af1e2f]
- **IF** control flow terminates in `ud2` or intentional faults guarded by signal handlers **THEN** analyze the signal handler's `ucontext_t` (specifically `REG_RIP` advancement and register decoding) as an instruction decoder **ELSE** follow standard basic block call/jump edges. [ev: 81f244, 64c704, 465bca, 305d06, 860e13]
- **IF** the function is flattened by an OLLVM-style state-variable switch loop **THEN** trace concrete state transitions dynamically (via emulation or dynamic hooks) to extract sequential basic block order **ELSE** invert state transitions symbolically or through static CFG restructuring. [ev: 1d2e38, 4dd429, d4f0db, b74c9e]
- **IF** verification updates an accumulator using a PRNG/hash stream independent of user input **THEN** solve iteratively in loop execution order (0..L-1) directly calculating each input byte and placing into `input[permuted_index]` **ELSE** formulate joint constraints across all characters in Z3. [ev: 01d01b, 333c14, f3a451]
- **IF** anti-debugging logic mutates global state or key seeds required by downstream win checks **THEN** patch both the detection branch and supply the expected runtime state values **ELSE** bypass the check cleanly without mutating memory. [ev: 70d6ff, 7149ae, 9bb016, 2addf5]
- **IF** expressions use Mixed Boolean-Arithmetic (MBA) on byte-sized variables **THEN** evaluate the transformation over a 256-entry lookup table or invert the affine linear transformation over GF(2) **ELSE** simplify algebraically or pass byte-sliced expressions to an SMT solver. [ev: 46e8b4, 729538, ff8049, 067aaa, d4f0db]
- **IF** Android application employs root or Frida detection **THEN** hook native functions (`Native.loadLibrary`, native JNI symbols) or inject early before detection routines run **ELSE** instrument target methods directly via standard Java Frida hooks. [ev: 84932b, 3d3586, e3c4b0, 6c0727, 4127d2]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Signal handler manipulates `uc_mcontext.gregs[REG_RIP]` at `ud2` sites → the binary is a trap-driven virtual machine; the handler is the virtual opcode dispatcher and constraint checker. [ev: 05e4b7, 81f244, 7f76cc]
- Global variable checked in success branch is modified inside an anti-debug function → the anti-debug routine functions as an anti-tamper state initializer; solvers must simulate the side-effect value instead of stripping the routine. [ev: 7149ae, 70d6ff, 9bb016]
- PRNG / hash state sequence in validation loop is independent of user input → the validation equation is strictly linear and invertible per step in iteration order without global constraint solving. [ev: 01d01b, 333c14]
- Decompiler displays hundreds of flattened switch blocks driven by a state variable → control flow is flattened; basic block execution traces under varied inputs expose the real execution sequence. [ev: 1d2e38, 4dd429, d4f0db]
- Multi-byte XOR decryptor unpacks `PUSH 0x33; CALL +0; ADD [ESP], 9; RETF` → execution transitions from WOW64 to 64-bit mode via Heaven's Gate; carving the 64-bit payload reveals the true check logic. [ev: 0ffc7b, 0180b1]
- Complex MBA expression combines bitwise and arithmetic ops on byte values → the expression implements an invertible byte-wise substitution or affine transform that can be inverted via a precomputed lookup table. [ev: 46e8b4, 729538, ff8049]

## Dead ends & stop-loss
- Blindly NOP'ing anti-debug calls without inspecting register or memory side-effects — abandon when patched binary crashes or fails valid checks; it failed because the anti-debug function initialized required state or cryptographic seeds. [ev: 7149ae, 70d6ff, 9bb016]
- Whole-program symbolic execution (angr / Z3) on binaries containing cryptographic hashes, transcendental float math, or signal dispatch — abandon after 10 min without constraint progress; it failed because SMT solvers cannot invert non-linear functions or model complex OS context mutations. [ev: 70d6ff, aefb94, 4ff677]
- Static CFG analysis of exception-based code (`ud2` / `SIGILL`) in standard decompilers — abandon after 5 min of linear disassembly reaching dead ends; it failed because control flow transfers occur via signal handler context adjustments invisible to static edges. [ev: 05e4b7, 81f244, 7f76cc]
- Manual reverse-engineering of OLLVM flattened switch dispatchers state-by-state — abandon after 15 min; it failed because automated state flattening expands into hundreds of synthetic cases designed to exhaust manual human effort. [ev: 1d2e38, 4dd429, b74c9e]
- Searching binary strings for flag patterns when thousands of fake flag strings exist in static data — abandon after 5 min; it failed because authors plant intentional decoy strings and decoy validation branches to mislead static grep. [ev: 70d6ff, 0ffc7b, 619cae]
- In-place 32-bit decompilation of Heaven's Gate payloads — abandon when instructions disassemble into nonsensical stack pointer operations; it failed because 32-bit decompilers cannot parse 64-bit segment transitions without isolation. [ev: 0ffc7b, 0180b1]

## Author tricks / decoys seen
- Seeded decoy flag strings and decoy validation paths that satisfy partial constraints or unmapped section offsets [ev: 70d6ff, 0ffc7b, 619cae].
- Dual-purpose anti-debugging routines that initialize critical global variables or cryptographic seeds while checking for tracers [ev: 7149ae, 70d6ff, 9bb016, 2addf5].
- Exception-driven execution utilizing `ud2` / `SIGILL` or invalid access handlers where `ucontext_t` advances `REG_RIP` to simulate a bytecode interpreter [ev: 05e4b7, 81f244, 7f76cc, 03bc55].
- Mixed-mode bitness switches (Heaven's Gate `RETF` to segment `0x33`) hiding core validation inside 64-bit shellcode within a 32-bit binary container [ev: 0ffc7b, 0180b1].
- Out-of-order array access permutations wrapping strictly sequential, invertible accumulator recurrence relations [ev: 01d01b, 333c14].
- Microarchitectural or transcendental hardware instruction quirks (e.g. x87 `FSIN` 66-bit pi reduction) deliberately breaking high-level language emulation [ev: 70d6ff, 03bc55].

## Verify before submitting
- Run the candidate flag natively against the unmodified binary outside of debuggers to ensure anti-debug checks (`TracerPid == 0`) succeed [ev: 70d6ff, 7149ae, 2addf5].
- Verify flag format wrapper, character set constraints (e.g., lowercase vs mixed-case before normalization), and length checks [ev: 0ffc7b, 81f244, b74c9e].
- Confirm execution path reaches success output ('accepted', 'Correct flag!') and normal exit code without relying on patched binary states [ev: 4dd429, 05e4b7, 333c14].

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Python 3 | Offline solver scripts, greedy recurrence inversion, GF(2) linear algebra, emulation | 22 |
| ADB | Deploying frida-server, interacting with emulator/device, logcat inspection | 6 |
| Ghidra | Static decompilation, CFG inspection, Heaven's Gate 64-bit shellcode analysis | 5 |
| Frida | Dynamic instrumentation, bypassing root/debug detection, hooking native JNI methods | 5 |
| JADX | Decompiling Android APKs, analyzing Java control flow, tracing native methods | 5 |
| IDA Pro | Disassembly, analyzing signal handler ucontext structures, decompiler CFG mapping | 5 |
| GDB | Dynamic register inspection, dumping decrypted mmap buffers, breakpoint state checks | 4 |
| radare2 | Opcode disassembly, function graph analysis, binary patching | 3 |
| Binary Ninja | Decompilation, identifying anti-debug functions and state variable mutations | 2 |
| pyelftools | Parsing ELF headers, extracting section blobs and raw .rodata tables | 2 |
| apktool | Unpacking APK resources, smali bytecode modification, rebuilding packages | 2 |
| hashcat | High-speed brute-force cracking of independent hash chunks | 2 |

## Worked micro-traces
- `[ev: 0ffc7b]` Given a 32-bit PE GUI binary (`0racle.exe`). First look decompilation failed across self-modifying code at offset `0x154AC2`. Wrong turn: attempted in-place 32-bit Ghidra decompilation and tested all-uppercase polynomial candidate words against FNV-1a hashes. Pivot: spotted `PUSH 0x33; CALL +0; ADD [ESP], 9; RETF` immediately following the XOR decryptor—a Heaven's Gate WOW64 switch into 64-bit shellcode. Solved by carving the 64-bit payload, reversing 7 independent chunk checks, and inverting raw mixed-case FNV-1a hashes via meet-in-the-middle.
- `[ev: 81f244]` Given a stripped 64-bit ELF (`vector-cache`) checking a 48-hex character token. First look in Ghidra/IDA showed standard setup functions abruptly dead-ending into `ud2` instructions. Wrong turn: attempted static CFG reconstruction and unguided symbolic execution across the full 24-byte secret space. Pivot: discovered a `sigaction` registration for `SIGILL` (signal 4) with `SA_SIGINFO` at startup, where the signal handler decodes VM opcodes from `ud2` contexts, verifies stage constraints, and advances `uc_mcontext.gregs[REG_RIP]`. Solved by extracting opcode handlers and stage constraints from the signal handler and pruning stage-by-stage with pairwise backtracking in Python.
- `[ev: 70d6ff]` Given a stripped ELF containing an embedded 230 MB data corpus and ~4,200 decoy flags. First look showed `_start` hashing its own code and a dead `call decoy_entry` bait leading to a decoy linear system. Wrong turn: walked the corpus with default buffer length (producing decoy flag D1), simulated Layer 2 using IEEE-754 `math.sin` in Python, and attached GDB for dynamic verification. Pivot: recognized validation is a 5-layer GF(2) linear system where each matrix is generated from runtime state, requiring exact x87 `FSIN` 66-bit pi reduction and undisturbed `TracerPid == 0`. Solved by re-implementing runtime derivations in Python, computing exact x87 math, avoiding debuggers, and solving each layer sequentially via GF(2) Gaussian elimination.

## Weak signals (single source — treat as hints, not rules)
- Hardware side-channel or speculative execution (Spectre v1) harnesses passing secret data via callee-saved registers (`r14`/`r15`) rather than standard ABI parameters [ev: aefb94].
- ELF section headers reporting decoy data offsets while kernel PT_LOAD program headers map true runtime data segments [ev: 619cae].
- Complex puzzle/game wrappers (e.g. 6x6 Rubik's cube) with massive IPC process trees validating state sequences in small periodic checkpoints (modulo N steps) [ev: b74c9e].
- Custom bytecode VMs containing compiler bugs in opcode handlers (e.g. register clobbering during bitwise rotation) that deviate from standard arithmetic [ev: 4ff677].
- Interleaved comparison tables where even entries store length progression counters and odd entries store sequential character transforms [ev: 4dd429].
