# Meta-Reasoning Discipline: Reverse Engineering (rev)

## 1. The Solver Loop for Reverse Engineering
1. **Artifact Inventory & Format Triage**: Identify binary format, target architecture, toolchain, runtime, and packaging (`file`, `readelf -l`, `checksec`) to isolate managed runtimes and packers before disassembling. [ev: f63cee, 2e3f9e, 274017, 9f74f1]
   - Verify entrypoint headers, dynamic segment presence, and non-standard base addresses before assuming a standard Linux userspace ELF environment. [ev: 2e3f9e, f9c26a, 24aecd]
2. **Decompilation & CFG Assessment**: Open binary in Ghidra/IDA/BinaryNinja, inspect entrypoint and `main`, and evaluate control-flow graph complexity to detect VM loops, flattening, or clean pipelines. [ev: 2742bf, 0ffc7b, 1d2e38, a4b4b0]
   - Screen for abnormal control flow mechanisms including signal-based dispatchers (`SIGILL`, `SIGSEGV`) or exception handlers (`VEH`, `SEH`) replacing call/ret instructions. [ev: 465bca, 81f244, 860e13, 64c704]
3. **Hypothesis Formulation**: Propose 2-3 competing hypotheses (e.g. standard cryptographic primitive vs custom algebraic pipeline vs SMT constraint system vs bytecode VM). [ev: 2bd3ec, 70d6ff, ae10f0, ac0a19]
   - Frame each hypothesis with explicit falsification conditions and expected data structures before writing extraction or solving code. [ev: ac0a19, 70d6ff, 57fd34]
4. **Cheapest Discriminating Test**: Execute a rapid probe (dynamic trace under `ltrace`/`strace`, hardware watchpoint, instruction count differential, or constant table lookup) to falsify hypotheses. [ev: 4529d2, f05c62, dcce7e, 4dd429]
   - Prioritize zero-cost environmental observations (e.g. imported crypto APIs, recognizable bitmasks, or library cross-references) over heavy symbolic execution. [ev: 001ea7, 140821, 2bd3ec]
5. **Core Logic Extraction & Inversion**: Extract transformation logic, clean parameters, and solve via direct algebraic inversion, Z3 BitVec modeling, or graph search. [ev: 6b0cbb, 57fd34, 08be32, 5a2d31]
   - Strive for algebraic inversion over SMT solving when all operations in the validation sequence are bijective (XOR, additions, bit rotations). [ev: ae10f0, b87695, dfa532]
6. **Stop-Loss Check & Track Pivot**: Evaluate concrete time-boxes (5 min SMT hang, 15 min manual reading); abandon stalled approaches for Unicorn emulation or dynamic tracing. [ev: 76e27c, 142c04, 48b12d, 5e0808]
   - Switch from static disassembly to black-box dynamic instrumentation whenever control flow flattening or MBA obscuration causes cognitive stall. [ev: e46213, 619cae, 4ff5d8]
7. **Pre-Submission Verification**: Replay recovered candidate through local native binary, assert table bijections, and verify flag format before submission. [ev: 57fd34, 0ab809, 4dd429, a4b4b0]
   - Ensure the solution executes cleanly through the unaltered native binary under local execution to catch unmodeled runtime padding or constraints. [ev: 2742bf, d0934a, 4dd429]

## 2. First 10 Minutes: Ordered Triage Checklist
- Minute 0-2 (Header & Packaging Triage): Inspect file headers with `file` and `readelf -l`; check for packed sections, embedded filesystems, or managed runtime containers (.NET, Python pyc, Unity IL2CPP) without opening decompilers. [ev: 2e3f9e, 9f74f1, 274017, 4be8f2]
- Minute 2-4 (Strings & Section Reconnaissance): Screen strings and symbol tables with cross-reference checks; identify comparison buffers, prompt strings, and flag format prefixes while flagging unreferenced decoy strings. [ev: 4be8f2, ac0a19, 0ffc7b, f63cee]
- Minute 4-6 (Dynamic Sandbox Baseline): Run the binary under `ltrace -s 128` or `strace` with dummy inputs; observe exit codes, syscall patterns, string comparisons, and early anti-debug terminations. [ev: 4529d2, 2742bf, dcce7e, 4dd429]
- Minute 6-8 (Control Flow & Entrypoint Decompilation): Open main logic in Ghidra/IDA; trace input ingestion to locate where user input enters the verification loop, measuring CFG size and cyclomatic complexity. [ev: 1d2e38, a4b4b0, c1b450, 73fc0d]
- Minute 8-10 (Archetype Routing & Strategy Selection): Map observed signals to a taxonomy archetype, define 2 competing hypotheses, and write the initial solver skeleton or dynamic probe script. [ev: 2bd3ec, 70d6ff, 6b0cbb, 84932b]

## 3. Signal to Archetype Routing
| Recognition Signal | Target Archetype | Primary Action |
|---|---|---|
| Switch-case or jump table looping over byte array with PC | `custom-bytecode-vm` | Extract dispatch table, map virtual registers, decode bytecode stream. [ev: 2742bf, a4b4b0, c1b450, 73fc0d] |
| Sequential unrolled loops with bitwise transforms ending in memcmp | `invertible-transform-pipeline` | Invert pipeline operations in reverse order from ciphertext target. [ev: 2e3f9e, 2bd3ec, ae10f0, 4dd429] |
| Multi-variable coupled equations or dense bitwise logic circuits | `constraint-system-smt` | Extract coefficients into Z3 BitVec model or solve linear system via GF(2). [ev: ac0a19, 70d6ff, f9927d, dcce7e] |
| High Shannon entropy (>7.2), W^X permissions, memfd_create | `packed-self-modifying-loader` | Break before execution transition or hook mprotect to dump unpacked payload. [ev: 0ffc7b, 9f74f1, 76e27c, f05c62] |
| Flat CFG backbone with state variable dispatcher, MBA, or SIGILL/ud2 | `obfuscated-control-flow` | Trace active path dynamically, filter dispatcher variables, simplify MBA. [ev: 1d2e38, 84932b, 067aaa, 465bca] |
| Managed runtime metadata (.NET, JVM, Python pyc, WASM, AppleScript) | `managed-runtime-decompile` | Decompile bytecode to high-level source via ILSpy, jadx, pycdc, or wasm2wat. [ev: 274017, 512c78, 34526b, cd0145] |
| APK archive with JNI native shared library (lib*.so) and Java UI | `mobile-app-reverse` | Decompile Java in JADX, locate exported Java_* JNI bridge, reverse native check. [ev: 84932b, 3d3586, e26e67, a0a66d] |
| Freestanding non-x86 ELF loading at 0x80000000 with MMIO/HTIF | `non-standard-arch-firmware` | Emulate via system QEMU/Spike or lift standalone check function into Unicorn. [ev: 2e3f9e, 142c04, f9c26a, 24aecd] |
| Repeated srand/rand calls, LFSR feedback, or bounded 32-bit seeds | `prng-and-seed-recovery` | Identify generator algorithm, synchronize seed, and reproduce keystream in Python. [ev: 4ed234, d0934a, 6c0ca7, 1f8a0b] |
| WASD directional inputs, maze map, state machine, or game engine assets | `interactive-game-and-state-machine` | Extract map/state transition graph and solve target state via BFS or Dijkstra. [ev: 91681a, 142c04, 4ed234, c3763c] |
| Kernel modules (.ko), ioctl commands, /dev/ nodes, or Intel AMX tiles | `system-kernel-and-hardware-interface` | Trace ioctl handlers, emulate specialized CPU instructions with Intel SDE. [ev: 91681a, f9927d, cd395d, 0ec1db] |
| Corrupted ELF headers, unstripped Go pclntab, or single jz validation | `triage-shortcuts-and-binary-patching` | Restore headers/symbols via GoReSym or patch conditional branch for quick pass. [ev: f63cee, dcce7e, 69c2e0, 4529d2] |

- Routing confirmation rule: When binary characteristics match multiple archetypes (e.g. custom VM embedded inside a packed loader), isolate the outer loader first before attempting bytecode analysis. [ev: 0ffc7b, 76e27c, f05c62]
- Decompiler fallback rule: If high-level decompiler output produces incomprehensible AST graphs or crashes, route immediately to CLI disassemblers (`objdump -d`, `radare2`) to analyze native opcode sequences. [ev: b03ebc, 48b12d, 4ff5d8]

## 4. Hypothesis Management & Discrimination
- **Standard Crypto vs Custom Cipher**: Discriminate by scanning data sections for standard S-boxes (AES, RC4) and magic constants (e.g. `0x9e3779b9` for TEA, MD5 init vectors); if constants match, use standard crypto libraries rather than manual reversing. [ev: 2bd3ec, f05c62, 001ea7, 140821]
- **Real Validation Flow vs Author Decoy Branch**: Discriminate by verifying cross-references and tracking input propagation from standard input; reject uncalled strcmp routines or static string comparisons that do not consume transformed user input. [ev: ac0a19, 4be8f2, 27bfc3, 619cae]
- **Coupled SMT System vs Independent Byte Slices**: Discriminate by examining variable dependency trees; if output byte `i` depends exclusively on input byte `i`, solve character-by-character; if dependencies are dense and coupled, formulate a full Z3 BitVec model. [ev: 70d6ff, ae10f0, 57fd34, dfa532]
- **Direct Machine Execution vs Custom VM Dispatch**: Discriminate by checking whether basic blocks transition through linear compiler control flow or cycle back to a central switch statement indexing an instruction pointer register. [ev: 2742bf, a4b4b0, c1b450, 81f244]
- **Static Decryption Table vs Dynamic Runtime Mutation**: Discriminate by checking memory write permissions (W^X violations) on lookup tables; if tables are modified at runtime or decrypted in `.init_array`, capture values via dynamic breakpoints rather than static data dumping. [ev: ac0a19, 64c704, 38e970, 7149ae]
- **Exhaustive Brute-Force Feasibility vs Algorithmic Pruning**: Discriminate by calculating total keyspace size; if total combinations exceed 2^32, discard pure brute force and test for meet-in-the-middle, graph traversal pruning, or character-by-character side-channels. [ev: 24aecd, 5e0808, 08be32, 5a2d31]

## 5. Concrete Stop-Loss Rules & Time-Boxes
- **SMT / Symbolic Execution Hang (5-minute limit)**: If Z3 or angr hangs for >5 minutes due to non-linear operations (modulo, multiplication), SIMD vector intrinsics, or cryptographic hash functions, abandon symbolic solving and pivot immediately to concrete tracing or algebraic reduction. [ev: 76e27c, 5e0808, 4ff677, dcce7e]
- **Manual Flattened Assembly Reading (15-minute limit)**: If manual reading of control-flow flattened functions (OLLVM) or opaque dispatch loops exceeds 15 minutes without identifying state transitions, abandon static reading and switch to dynamic instruction trace logging or state-variable filtering. [ev: 142c04, e46213, 619cae, 4ff5d8]
- **Unconstrained Keyspace Brute-Force (5-minute limit)**: If brute-force keyspace exceeds 2^32 operations without byte-level independence, abandon full-keyspace computation immediately and search for meet-in-the-middle splits, algebraic invariants, or side-channel leakage. [ev: 24aecd, 5e0808, 1a4eac, 8ff6f0]
- **Interactive Debugger Deadlock (10-minute limit)**: If GDB session is stalled by aggressive anti-debugging (ptrace, RDTSC), transient child process forks, or self-modifying code, abandon live debugging and pivot to static script extraction and Unicorn emulation. [ev: 2742bf, b74c9e, 619cae, 7149ae]
- **GUI Decompiler Hang (3-minute limit)**: If a heavy decompiler (Ghidra/IDA) freezes on initial whole-program analysis for >3 minutes, kill the process and fall back to CLI tools (`readelf`, `objdump -d`, `strings`) and targeted xref disassembly. [ev: 48b12d, 4ff5d8, 305d06, b03ebc]
- **User-Mode QEMU Firmware Trap (5-minute limit)**: If user-mode QEMU crashes on illegal instructions or unmapped MMIO, stop debugging Linux loader flags; pivot immediately to system emulation (Spike / QEMU-system) or lift the check function into Unicorn. [ev: 2e3f9e, f9c26a, 24aecd]
- **Game Engine Asset Search Stagnation (15-minute limit)**: If static searching across decompiled game scripts yields no cryptographic or checking logic after 15 minutes, pivot immediately to raw asset extraction using AssetStudio or UnityPy. [ev: 17ee43, 142c04, ff8049]
- **Patched Binary Post-Bypass Crash (10-minute limit)**: If patching an anti-debugging check results in downstream crashes or invalid outputs, abandon blind NOP patching and trace downstream registers modified by the bypassed function. [ev: 7149ae, ac0a19, 619cae]

## 6. Author Intent: Recurring Decoys and Misdirection
- **Plaintext Decoy Flags**: Challenge authors place believable plaintext flag strings in `.rodata` or uncalled functions to trap regex grepping and waste solver time on invalid submissions. [ev: ac0a19, 4be8f2, 91681a, 619cae]
- **Disguised Standard Cryptography**: Authors disguise standard algorithms (TEA, RC4, AES) using unrolled loops, non-standard variable names, and arithmetic masking to trick analysts into assuming complex novel mathematics. [ev: 2bd3ec, f05c62, 1d2e38, c902f2]
- **Anti-Analysis Traps & Fake Success Messages**: Handlers catch software breakpoints or debugger attachments and silently diverge execution to fake success blocks that print plausible but incorrect flags. [ev: cd395d, 84932b, 465bca, 64c704]
- **SMT Path Explosion Traps**: Authors inject intentional non-linear operations, rolling cyclic hashes, or floating-point rounding to induce solver timeouts when solvers blindly apply symbolic execution. [ev: 76e27c, ae10f0, f9927d, 70d6ff]
- **Exotic Container Camouflage**: Authors wrap simple algorithmic puzzles inside unfamiliar runtime envelopes (bare-metal RISC-V, eBPF rootkits, on-device ML models) to cause intimidation and toolchain paralysis. [ev: 2e3f9e, c1b450, 142c04, f9c26a]
- **Dynamic Key Table Self-Mutation**: Authors place valid static lookup tables in `.data` but mutate them during runtime `.init_array` execution, ensuring static analysis yields corrupted solutions. [ev: ac0a19, 64c704, 38e970, 7149ae]
- **Artificial Timing & Latency Delays**: Authors embed sleep calls or slow verification loops to discourage automated brute force and mask linear instruction-count side channels. [ev: b6c778, 512c78, 4529d2]
- **Transport Framing Red Herrings**: Network reversing challenges intentionally ignore newline-delimited inputs to mislead solvers into assuming authentication failure rather than framing failure. [ev: f63cee, 27bfc3, 72fdd4]

## 7. AI-Agent Failure Modes: Top 10 Anti-Patterns
1. **Unsynchronized PRNG State Recovery** [ev: d0934a, fa693c, 1f8a0b]:
   - Mistake: Assuming PRNG outputs are unguessable (guessing or brute-forcing the outputs) or missing `time()` seed synchronization. [ev: d0934a, fa693c, 1f8a0b]
   - Better Move: Extract the PRNG algorithm, identify the exact seed generation mechanism, and reproduce state sequences in Python. [ev: 062442, 4ed234, 1f8a0b]
2. **Blind Dynamic Debugging** [ev: 0180b1, 05e4b7, 06267e]:
   - Mistake: Attaching GDB or running binaries without screening for ptrace or signal traps (SIGILL/ud2). [ev: 0180b1, 05e4b7, 06267e]
   - Better Move: Triage anti-analysis mechanisms first, patch detection branches, or install API hooks. [ev: 08be32, cd395d, 84932b]
3. **Assuming Custom Cryptography** [ev: 001ea7, 05e4b7, 0feb9f]:
   - Mistake: Reversing complex mathematical loops under the assumption of a novel custom cipher. [ev: 001ea7, 05e4b7, 0feb9f]
   - Better Move: Search data sections and immediates for standard cryptographic constants and S-boxes before manual reversing. [ev: 0ffc7b, 2bd3ec, f05c62]
4. **Manual Decompilation of Bloated/Flattened Code** [ev: 06267e, 08be32, 0ab809]:
   - Mistake: Manually tracing hundreds of flattened basic blocks or unrolled loops in Ghidra/IDA. [ev: 06267e, 08be32, 0ab809]
   - Better Move: Use dynamic execution tracing, Unicorn memory logging, or state-variable filtering to trace the active path. [ev: 0e250f, 1d2e38, 84932b]
5. **Reversing All VM Opcodes** [ev: 001ea7, 05e4b7, 0feb9f]:
   - Mistake: Exhaustively disassembling every opcode handler in custom virtual machines. [ev: 001ea7, 05e4b7, 0feb9f]
   - Better Move: Trace executed bytecode instructions, isolate I/O and comparison handlers, and ignore dead opcodes. [ev: 16ffe2, 2742bf, a4b4b0]
6. **SMT Solver Over-Reliance** [ev: 01d01b, 05e4b7, 067aaa]:
   - Mistake: Feeding entire binary checks into Z3 without checking for non-linear operations or path explosion. [ev: 01d01b, 05e4b7, 067aaa]
   - Better Move: Decompose checks into byte-level constraints, invert linear chains algebraically, or use concrete traces. [ev: 08be32, 70d6ff, ae10f0]
7. **Submitting Unreferenced Strings** [ev: 0180b1, 03bc55, 16c799]:
   - Mistake: Grepping strings for flag patterns and submitting them without verifying cross-references. [ev: 0180b1, 03bc55, 16c799]
   - Better Move: Verify string xrefs and trace caller execution flow to ensure participation in active checks. [ev: 17ee43, ac0a19, 4be8f2]
8. **Naive Binary Patching** [ev: 0180b1, 06267e, 0ec1db]:
   - Mistake: Patching conditional jumps with NOPs without verifying whether bypassed code calculates downstream keys. [ev: 0180b1, 06267e, 0ec1db]
   - Better Move: Trace downstream register and memory uses before altering execution flow to avoid breaking state invariants. [ev: 10f5ca, 7149ae, 619cae]
9. **Unconstrained Brute-Force Searches** [ev: 1a4eac, 1f8a0b, 21c6dd]:
   - Mistake: Attempting to brute-force a full composite keyspace simultaneously without reduction. [ev: 1a4eac, 1f8a0b, 21c6dd]
   - Better Move: Check for byte-by-byte independence, meet-in-the-middle splits, or instruction-count side channels. [ev: 2b1253, 24aecd, 5e0808]
10. **Reversing Native Runtime Wrappers** [ev: 17ee43, 2762f0, 34526b]:
    - Mistake: Disassembling native stub loaders or GameAssembly.so without restoring symbols or managed metadata. [ev: 17ee43, 2762f0, 34526b]
    - Better Move: Extract managed payloads (.pyc, .NET assemblies, DEX) and use ecosystem decompilers (Il2CppDumper, dnSpy, jadx, pycdc). [ev: 3d3586, 274017, 512c78]

## 8. Verification Discipline Before Submitting
- **Concrete Local Binary Replay**: Always pipe the candidate flag string directly into the target binary via stdin or arguments (`./binary <<< "$FLAG"`) to verify exit code 0 and valid success output. [ev: 57fd34, 4dd429, 2742bf, d0934a]
- **Known-Plaintext Format & Printable ASCII Check**: Confirm that candidate decryption begins with the expected challenge prefix (`flag{`, `ctf{`) and contains valid printable ASCII before expending remote attempts. [ev: a4b4b0, 4ff677, 274017, 067aaa]
- **Forward Simulation Pass**: Run an independent forward execution pass of the challenge algorithm in Python on the derived input to confirm zero residual error and exact target state matching. [ev: 6b0cbb, 72fdd4, 0e250f, ac0a19]
- **Structural Invariant Checks on Extracted Tables**: Assert that recovered substitution tables form strict bijections (len(set(table)) == 256) and decrypted stubs contain valid instruction signatures. [ev: 0ab809, 8988ab, 4be8f2, f05c62]
- **Unbuffered Output Replay under Abort Crashes**: When binaries deliberately execute a crash (SIGFPE, divide-by-zero) after printing success verdicts, run under `stdbuf -o0 ./binary` to verify final stdout. [ev: 4dd429, 860e13, 0ffc7b]
- **Remote Network Protocol Framing Replay**: When verifying solutions against remote socket challenges, ensure packet framing, trailing null-bytes, or specific binary delimiters match local expectations. [ev: f63cee, 72fdd4, f71f2b]
