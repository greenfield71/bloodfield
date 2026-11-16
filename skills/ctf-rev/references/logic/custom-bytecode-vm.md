# Custom Bytecode Virtual Machine

> category: rev · slug: `custom-bytecode-vm` · evidence: 33 writeups from 19 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Main check or execution loop contains a central fetch-decode-execute loop with a large switch-case or indirect jump table indexed by instruction opcodes. [ev: a4b4b0, 9d630d, 4ff677, c1b450]
- Contiguous bytecode array embedded in `.rodata`, `.data`, or appended overlay sequentially traversed by a virtual program counter (`pc`). [ev: ac0a19, a4b4b0, 0e250f, 06267e, 1c751e]
- Signal handling machinery (`sigaction`, `sigaltstack`) registers handlers for `SIGILL` (signal 4) with intentional `ud2` instructions acting as opcode dispatchers. [ev: 64c704, 465bca, 305d06, 81f244]
- Strict input length verification precedes dispatch (e.g. `input_length ^ CONST == 0` or exact byte bounds) without direct string comparison APIs. [ev: 73fc0d, 9d630d, 81f244, 05e4b7, 56fa0d]
- Decompiler shows simulated CPU state context (virtual registers, accumulator, operand stack) manipulated by custom ALU handlers. [ev: 97afe8, 8ff6f0, 6b0cbb, 9b4694, 2b52b8]
- Binary implements anti-debugging or checksumming over `.text` / payload that corrupts VM salt or state if breakpoints are placed. [ev: ac0a19, 31502d, 64c704, 06267e, 4ff677]

## Opening sequence (do in this order)
1. **Triage container & unpack protectors** — look for UPX headers, direct syscall loaders (`memfd_create`), or appended payload overlays; time-box 5 min. Why: reveals real bytecode container before static decompilation fails on stagers. [ev: 64c704, 465bca, d7a46d, 0e250f]
2. **Audit signal handlers and anti-analysis gates** — look for `sigaction` registering `SIGILL` handlers, `ptrace`, `TracerPid`, or `.text` checksum loops; time-box 5 min. Why: prevents stepping into debugger traps or corrupting decryption keys with standard `0xCC` software breakpoints. [ev: ac0a19, 31502d, 305d06, 81f244]
3. **Locate virtual machine dispatch core** — look for the central `while(running)` loop, opcode switch-case, or indirect jump table `jmp [base + op*8]`; time-box 10 min. Why: establishes instruction size, operand layout, and virtual registers/stack context pointers. [ev: a4b4b0, 9d630d, 4ff677, 2b52b8]
4. **Locate and extract bytecode stream** — look for referenced global pointers, `.rodata` buffers, or embedded asset blobs traversed via the virtual PC; time-box 10 min. Why: allows offline decoding, slicing, or lifting without fighting host binary complexity. [ev: a4b4b0, 06267e, f71f2b, 05e4b7]
5. **Trace first transformation cycle vs. static lifting** — run a known test prefix or hook `vm_execute` to observe register transforms; time-box 15 min. Why: determines immediately whether the VM is an uncoupled modular check, a standard block cipher, or a full emulator. [ev: 2b52b8, 64c704, 001ea7, 73fc0d]

## Decision points
- **IF** VM dispatch triggers on `SIGILL` / `ud2` or invalid opcode traps **THEN** analyze register contexts inside the `SA_SIGINFO` signal handler and hook/trace via GDB catchpoints or LD_PRELOAD **ELSE** reverse the native switch-case / indirect jump table directly. [ev: 64c704, 465bca, 305d06, 81f244]
- **IF** the binary calculates checksums or hashes over `.text` **THEN** use hardware execution breakpoints (`hbreak`), syscall catchpoints (`catch syscall mprotect`), or binary patching with checksum bypass **ELSE** use standard dynamic breakpoints in GDB. [ev: ac0a19, 31502d, 64c704, 4ff677]
- **IF** instructions perform uncoupled character-wise or byte-independent arithmetic operations **THEN** invert modular equations algebraically in Python or solve independent bytes via Z3 **ELSE** model the coupled multi-round state machine (ARX / block cipher) or trace dynamic execution states. [ev: 9d630d, a4b4b0, 05e4b7, 56fa0d, 2b52b8]
- **IF** the VM logic is nested across multiple self-modifying or decrypted layers **THEN** log intermediate memory loads and ALU operands at the VM dispatch boundary (`vm_execute`) **ELSE** extract the entire bytecode blob once and disassemble statically. [ev: 2b52b8, ac0a19, 31502d, 4ff677]
- **IF** native execution is throttled by synthetic slow loops or O(N) operations **THEN** profile the hot loop, replace repeated arithmetic additions with direct multiplication, and run in a custom Python VM **ELSE** execute candidate inputs directly against the binary or symbolic solver. [ev: 512c78, 6b0cbb, 9d8241]
- **IF** the constraint system is sparse with small multi-index modular checks **THEN** implement forward-checking backtracking with unary pruning in Python **ELSE** formulate the full constraint system in Z3 bitvectors. [ev: 81f244, 05e4b7, a4b4b0, 31502d]
- **IF** the VM runs a modified standard or esolang interpreter (e.g. SPL) **THEN** diff the grammar/opcodes against upstream reference implementations to spot non-standard extensions or type desynchronizations **ELSE** map custom opcodes from scratch via semantic ALU grouping. [ev: c1b450, f794df]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Static table in `.data` or `.rodata` yields a solvable but suspicious flag → The static tables are deliberate decoys while the true opcode table is decrypted or mutated at runtime → Dump the live opcode table using non-invasive memory catchpoints (`catch syscall mprotect`) after decryption completes. [ev: ac0a19, 6b0cbb, 9d8241]
- Bytecode operator behaves inconsistently under XOR assumptions with known flag prefix → The mystery arithmetic glyph/opcode is modular addition (`+ mod 256`) or subtraction rather than XOR → Switch algebraic hypothesis in the solver to align all known prefix constraints. [ev: a4b4b0, 56fa0d]
- Binary crashes under GDB or silently enters dead branches on valid input → Anti-debugging checks (`ptrace`, `TracerPid`, software breakpoint detection) are corrupting internal keys or VM salts → Bypass anti-debug by NOPing detection routines or hooking decoder output via `LD_PRELOAD`. [ev: 31502d, 64c704, 305d06]
- Nested multi-layer VM bytecode is too vast or obfuscated for manual static lifting → All layers share an identical core execution dispatch structure wrapping a standard lightweight cipher (e.g. Speck-64) or invertible ARX block → Hook `vm_execute` to log operands, extract layer keys dynamically, and invert backwards layer by layer. [ev: 2b52b8, 6b0cbb, 4ff677]
- Static decompilation abruptly halts at `ud2` instructions without revealing validation logic → The challenge uses illegal instruction exception dispatching where the registered `SIGILL` signal handler functions as the virtual CPU interpreter → Instrument the signal handler, map VM context registers from the signal frame, and extract instruction streams from handler memory. [ev: 64c704, 465bca, 81f244]
- Candidate flag prefix matches cyclic key pattern over a constant buffer → Cyclic XOR key schedule allows the known flag prefix to recover the majority of key bytes directly → Reduce the search space to a tiny 8-bit or 16-bit brute force for remaining key bytes. [ev: 64c704, 465bca, d7a46d]

## Dead ends & stop-loss
- Setting standard software breakpoints (`0xCC`) inside `.text` — abandon when the binary immediately terminates, crashes, or takes wrong paths; it failed because code integrity hashing (SHA-256 / CRC32) detects breakpoint byte patches and corrupts VM state. [ev: ac0a19, 31502d, 64c704, 06267e]
- Trusting plaintext opcode tables or target arrays in `.rodata`/`.data` — abandon when recovered flag resembles a leet decoy or fails submission; it failed because authors embed static decoy structures while live opcodes are decrypted dynamically at runtime. [ev: ac0a19, 6b0cbb, 9d8241]
- Writing a full standalone VM bytecode lifter/decompiler from scratch under time pressure — abandon when instruction set has dozens of complex or layered opcodes; it failed because dynamic register tracing (`vm_execute` logging) or emulator hooks extract keys and inputs significantly faster. [ev: 2b52b8, 2742bf, 001ea7]
- Letting a native binary or JVM calculation run for hours hoping it finishes — abandon when progress throttles or timeouts occur after minutes; it failed because challenge intentionally uses synthetic slowdowns (e.g. 64-bit multiplication implemented as repeated additions). [ev: 512c78, 6b0cbb]
- Attempting to NOP or patch out branchless crash routines or license checks — abandon when downstream computation crashes or yields corrupted memory offsets; it failed because computed pointer offsets and divisors are mathematically entangled with state rather than conditional jumps. [ev: 19e110, 73fc0d]
- Submitting partial constraint solutions without tracing subsequent verification logic — abandon when an initial puzzle or stage solve is rejected; it failed because trailing VM code enforces additional global invariants, checksums, or block rules. [ev: 2742bf, 31502d, 81f244]
- Submitting an exploit or script without handling userspace I/O buffering across `execve` — abandon when interactive shell spawned by VM exits immediately; it failed because C++ `std::cin` readahead buffers swallow trailing payload bytes before child shell inherits standard input. [ev: c1b450, f794df]

## Author tricks / decoys seen
- Plaintext decoy target vectors and opcode tables in `.data` that produce plausible but incorrect fake flags. [ev: ac0a19, 6b0cbb, 9d8241]
- Self-checksumming code (.text SHA-256 or CRC32) that silently mutates VM salts or opcodes when debugged with `0xCC` breakpoints. [ev: ac0a19, 31502d, 64c704]
- Exception-driven execution utilizing `SIGILL` / `ud2` instructions to hide VM dispatch loops from decompiler call graphs. [ev: 64c704, 465bca, 305d06, 81f244]
- Multi-layer nested VM stagers where each unlocked stage acts as a decryptor for subsequent bytecode blobs. [ev: 31502d, 2b52b8, 4ff677]
- Subtly non-standard language extensions or type desynchronizations (e.g. 64-bit pushes into 32-bit stacks) hidden in familiar esolang parsers. [ev: c1b450, f794df]
- Branchless pointer arithmetic entanglement that converts input mismatches directly into unmapped memory addresses / SIGSEGV without conditional jumps. [ev: 19e110, 73fc0d]
- Intentional algorithmic slowdowns (e.g. repeated addition loops implementing multiplication) causing apparent hangs on unoptimized solvers. [ev: 512c78, 6b0cbb]

## Verify before submitting
- Feed candidate solution directly into the unmodified challenge binary or host script to confirm it prints the terminal success message. [ev: a4b4b0, 81f244, 305d06, 73fc0d, 9d630d]
- Check all trailing constraints, row/column checksums, or post-VM MAC/integrity hashes before submitting partial solutions. [ev: 2742bf, 6b0cbb, 81f244, 27bfc3]
- Verify flag length against the strict length invariant identified during initial triage (e.g. `input_length ^ CONST == 0`). [ev: 73fc0d, 81f244, 9d630d, 56fa0d]
- Ensure candidate output conforms to expected flag formatting and leetspeak semantics, avoiding uncommitted or decoy transaction outputs. [ev: ac0a19, 9d8241, 06267e, 2b52b8]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Python | Disassembly, custom VM emulators, Z3 solvers, arithmetic inversion, trace parsers | in 30 writeups |
| Ghidra | Static decompilation, control flow analysis, opcode mapping, structure definition | in 12 writeups |
| GDB | Dynamic debugging, catchpoints (`catch syscall`), hardware breakpoints, trace logging | in 11 writeups |
| IDA Pro | Binary disassembly, decompiler AST inspection, IDAPython lifting scripts | in 6 writeups |
| file / strings | Initial triage, architecture identification, finding prompts and embedded headers | in 5 writeups |
| Z3 | Symbolic constraint solving of modular arithmetic and multi-index VM equations | in 3 writeups |
| UPX | Unpacking packed binary wrappers concealing core VM interpreters | in 3 writeups |
| Binary Ninja | Control flow graph visualization, medium-level IL analysis, VM loop decompilation | in 3 writeups |
| Unicorn Engine | Offline CPU/firmware emulation, executing raw VM bytecode slices | in 2 writeups |
| radare2 / objdump | Quick disassembly, section header inspection, symbol and string audits | in 2 writeups |

## Worked micro-traces
- `[ev: ac0a19]` Given a stripped binary implementing a 5-layer cascading VM with plaintext opcode tables in `.data` and `.rodata`. First look revealed clean linear equations, but solving them produced decoy flag `Null0rigin{you_trusted_the_first_draft}`. Standard GDB breakpoints inside `.text` corrupted the binary's SHA-256 self-checksum, aborting execution. Solvers pivoted to non-invasive `catch syscall mprotect` in GDB to capture the live, dynamically decrypted opcode table from memory without patching code bytes. Solving the reconstructed GF(2) linear constraint matrix against the real target vector yielded the authentic flag.
- `[ev: 81f244]` Given a stripped Linux x86-64 binary requiring a 56-character token and returning "rejected". First look showed CFG dead-ending at `ud2` instructions without obvious comparison logic. Solvers initially attempted standard static decompilation, which failed to trace the fragmented flow. The pivot came when recognizing an `SA_SIGINFO` handler registered for `SIGILL` (signal 4) at startup, revealing that the entire verification VM was dispatched via illegal instruction exceptions. By instrumenting the signal frame in GDB and modeling the 96 three-index modular equations, solvers wrote a forward-checking backtracking solver in Python to recover all 24 secret bytes and pass the downstream ARX seal check.
- `[ev: 2b52b8]` Given a Linux x86-64 binary evaluating an array of 30 64-bit integers through nested VM layers. Static analysis stalled because deeper VM layers were dynamically decrypted only upon successful execution of earlier stages. Attempting to write a full standalone bytecode emulator from scratch proved too complex and time-consuming under CTF constraints. Solvers pivoted to dynamic execution tracing, hooking `vm_execute` to log raw memory accesses and ALU operands directly. The trace exposed a 27-round Speck-64 block cipher and ALU XOR stage; solvers extracted the subkeys directly from register dumps and inverted the bijective cipher layers backwards to recover the flag.

## Weak signals (single source — treat as hints, not rules)
- Non-standard calling conventions in Go binaries (e.g. error flags passed in `RBX`) can cause decompilers like IDA to truncate functions abruptly at call sites, requiring manual NOPing of error branches to reveal the complete VM dispatcher. [ev: d7a46d]
- AppleScript bytecode containers (`.scpt`) may embed second-stage compiled scripts as raw bytes prefixed by `scptFasdUAS` dispatched via `run script` (`sysodsct`), which crash standard community disassemblers on unhandled record types. [ev: 56fa0d]
- Custom emulator CLI debuggers (e.g. `wromwarp`) that allow cartridge reloading without clearing CPU registers or WRAM enable TAS-style glitch exploitation by skipping bounds-initialization instructions. [ev: 97afe8]
- Multi-protocol incident-response VM challenges can split exfiltrated flag fragments across independent protocols (e.g. HTTP cookie fragments and DNS subdomains) requiring prefix-aligned reassembly. [ev: 27bfc3]
- Obfuscated native Android libraries may combine an OLLVM-flattened VM with an embedded on-device neural network (MNN) where static layer operator names act as decoys, requiring dynamic runtime inference callback logging. [ev: a0a66d]
