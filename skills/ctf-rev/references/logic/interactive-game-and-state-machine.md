# Interactive Game and State Machine Reversing

> category: rev · slug: `interactive-game-and-state-machine` · evidence: 22 writeups from 15 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Challenge binary presents an interactive terminal or graphical interface prompting for directional moves (WASD/arrows) that update coordinates, grid cells, or 2D bitboards. [ev: 5f9b50, 668d34, 4ed234, ad0e94]
- Distfiles contain game engine containers or asset archives (Unity Mono `Assembly-CSharp.dll`/.assets, Godot `.pck`, Source Engine `.bsp`, iOS `.ipa`). [ev: be8ea1, 17ee43, 16d1af, 5d972d, 6df9c3, 90db76]
- Text adventure prompt or numbered menu interface updates an internal state array checked against a target winning condition. [ev: f91f1a, 2742bf, 16d1af]
- Execution crashes immediately at startup due to missing environment files or unhandled ISA/permission syscalls (`strace` reveals `.game_license` or `arch_prctl` errors). [ev: 91681a, 19e110]
- Disassembly exposes cellular automaton neighbor lookup tables, grid bitboards, or large table-driven state machine dispatch loops. [ev: 5f9b50, 668d34, 596a50, 349344, 2742bf, 90db76]

## Opening sequence (do in this order)
1. **Triage container & inspect runtime startup** — run `file`, unpack archives (`unzip`, `tar`), check if target is an engine package (Unity, Godot, Source BSP) or native binary; if it crashes on launch, run `strace` to identify missing license files or unsupported syscalls; time-box 3 min. Why: high-level engine extractors immediately recover C#/GDScript logic, while strace flags missing preconditions before wasting time in decompilers. [ev: be8ea1, 16d1af, 5d972d, 6df9c3, 90db76, 19e110, 91681a]
2. **Locate victory condition & trace data flow backwards** — search strings and cross-references for flag decoders, victory routines, or win checks (`handle_flag`, `flag.txt`, `show_flag()`, `target`, status == 1); time-box 5 min. Why: determines immediately whether the flag is decrypted by a gameplay accumulator or if gameplay score is an uncoupled decoy. [ev: f91f1a, 90db76, 6df9c3, 5f9b50, be8ea1, c3763c]
3. **Determine if game mechanics are coupled or decoupled (decoy check)** — verify whether gameplay inputs (keystrokes, scores, timers) feed into cryptographic key derivation or if the transition path / decryption key is static or cancelled out; time-box 10 min. Why: prevents spending hours playing or simulating gameplay mechanics when key derivation is deterministic or input merely steers an RNG. [ev: 90db76, 6df9c3, f91f1a, ad0e94, 4ed234]
4. **Extract state transition rules and validation invariants** — inspect the step/dispatch loop (menu handlers, VM opcode tables, neighbor update rules, or ioctl commands) to identify allowed moves and per-step constraints; time-box 15 min. Why: turns manual play into an algorithmic graph search (BFS/DFS/A*), linear system, or SAT model. [ev: 91681a, c3763c, 5f9b50, 668d34, 5d972d, 3f57b3]
5. **Script offline simulator / solver** — implement state transitions in Python or C, prune paths using target constraints or Hamiltonian heuristics, and compute the winning sequence; time-box 20 min. Why: blind brute-force or manual playthrough across large state spaces (e.g. 4^28 WASD moves or 48x16 matrices) is impossible within competition limits. [ev: 5f9b50, 668d34, 91681a, c3763c, 3f57b3]

## Decision points
- **IF** the target is packaged in a known game engine (Unity Mono, Godot PCK, Source BSP) **THEN** extract assets and scripts directly via high-level engine tooling (`dnSpy`, `gdre`, `bspsrc`, `UnityPy`) **ELSE** decompile native binary dispatch routines and data tables in IDA/Ghidra. [ev: be8ea1, 17ee43, 16d1af, 5d972d, 2742bf, 90db76]
- **IF** gameplay score / snapshot does not affect flag key derivation (data-flow tracing shows score variables cancel out or state transitions use static constants) **THEN** simulate the state machine offline to derive the key directly **ELSE** reverse the required gameplay preconditions and build an input sequence or keygen that satisfies them. [ev: 90db76, 6df9c3, 19e110, 5f9b50]
- **IF** user keystrokes modify RNG state or board generation on each frame **THEN** treat player keystrokes as PRNG steering parameters to force favorable board layouts **ELSE** treat the game board/maze as static and apply graph search (BFS/DFS/A*). [ev: 4ed234, ad0e94, 5f9b50, 668d34, c3763c]
- **IF** the state machine contains irreversible traps or terminal failure states **THEN** use reset commands / ioctl resets and replay path prefixes from root to explore branches **ELSE** rely on standard bidirectional backtracking search. [ev: c3763c, 5d972d]
- **IF** the transition graph or cellular automaton recurrence is algebraically reversible (e.g. second-order XOR update `board[t+1] = f(board[t]) ^ board[t-1]`) **THEN** step the state backwards directly from known terminal states **ELSE** model forward step constraints in a SAT/SMT solver (Z3/Glucose3) or run pruned BFS. [ev: 596a50, 349344, 5f9b50, 811af8]
- **IF** the state machine is driven by hundreds or thousands of repetitive callback handlers or VM table records **THEN** lift them into a high-level emulator or AST parser using IDAPython / Ghidra scripts **ELSE** manually reverse individual handlers. [ev: 2742bf, 90db76, 6df9c3]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Data-flow analysis shows score/snapshot parameters XOR in and later cancel out via identical constants along the execution path → gameplay score is a decoy; state machine progression is purely deterministic → simulate VM transitions offline with a null snapshot to recover the key directly. [ev: 90db76, 6df9c3]
- Recurrence formula is a second-order XOR update (`board[t+1] = life(board[t]) ^ board[t-1]`) and consecutive final target states are embedded in `.rodata` → XOR is self-inverting; knowing two consecutive future states uniquely determines all past states → step the automaton backwards deterministically without SAT or constraint solving. [ev: 596a50, 349344]
- Asset directory contains hundreds of serialized scene/level files with repetitive dummy sizes, but one file is an extreme outlier (e.g. 1115 KB vs 18 KB) → asset file sizes reflect genuine geometry while intermediate scenes are decoy filler → focus inspection entirely on the outlier asset. [ev: be8ea1, 17ee43]
- Deterministic PRNG generates target grid bitmasks and the Hamming distance / required bit flips matches the allowed move budget exactly → every move must visit an unvisited target cell with zero backtracks → formulate pathfinding as a tightly constrained Hamiltonian path or pruned DFS, reducing search space from 4^28 to ~100 nodes. [ev: 5f9b50, 668d34]
- PRNG update formula mixes the player's last input key directly into the seed right before computing hazard or terrain masks → keystrokes are an RNG steering mechanism rather than mere player navigation → calculate exact keystrokes that steer the PRNG to generate safe paths. [ev: 4ed234, ad0e94]
- Compiler pass inspects LLVM IR call graphs and instruction patterns (counting `CallInst`, matching `CmpInst` predicates and pointer names) rather than machine code → reverse the plugin visitor methods in IDA/Ghidra → synthesize C source annotated with `__attribute__((noinline))` to reproduce the expected IR basic block topology. [ev: 69c2e0, 8021fe]
- Menu/quest actions perform algebraic operations on an internal array checked against a hardcoded target array before invoking the flag printer → challenge is a state-machine manipulation puzzle, not a cryptographic reverse engineering challenge → chain rotations, additions, and sign flips to match the target array directly. [ev: f91f1a, 2742bf]

## Dead ends & stop-loss
- Blind brute-force over movement permutations without extracting target constraints — abandon when search space exceeds 10^6 states (e.g. 4^27 WASD moves); it failed because unpruned combinatorial expansion is computationally intractable during a CTF. [ev: 5f9b50, 668d34, 17ee43, 91681a]
- Playing or patching game mechanics when flag derivation is uncoupled — abandon when data-flow tracing reveals score/snapshot variables cancel out or when keys derive from static tables; it failed because reaching score thresholds does not affect decryption key mathematics. [ev: 6df9c3, 90db76, 142c04]
- Interactive GDB debugging on self-modifying, multi-process, or emulated targets — abandon when execution repeatedly alternates between shell scripts and transient binary spawns or when emulator GDB stubs crash; it failed because process recreation and in-place file modifications break debugger attachment. [ev: 2742bf, 142c04]
- Decompiling bloated third-party game engines or static libraries line-by-line — abandon when decompilation spans hundreds of thousands of lines (Unity Mono, Godot ARM64, OpenSSL); it failed because engine internals clutter analysis; pivot to asset extractors (`gdre`, `UnityPy`) or domain string references. [ev: 16d1af, 17ee43, 19e110, 142c04]
- Statically analyzing complex concurrency or mailbox graphs in decompilers — abandon when thread dispatch and IPC graph setup code is convoluted; it failed because static analysis is tedious and error-prone; pivot to LD_PRELOAD logging or strace to capture communication topologies dynamically. [ev: 596a50, 349344, 2742bf]
- Submitting partial puzzle solutions without verifying trailing constraints — abandon partial solutions when trailing verification code remains uninspected; it failed because authors layer secondary global constraints (Sudoku row/col/box rules, corridor transit triggers) on top of local clues. [ev: 2742bf, 5d972d]
- Relying on compiler optimization or empty stubs during source synthesis — abandon default inlining (`-O2`) and empty function bodies; it failed because LLVM module passes strictly count `CallInst` and instruction opcodes, which compiler optimization aggressively eliminates. [ev: 69c2e0, 8021fe]
- NOPing or patching branchless protection checks — abandon binary patching when protection routines calculate addresses or divisors via arithmetic formulas; it failed because patched jumps leave required pointers or PRNG seeds corrupted, causing downstream memory faults. [ev: 19e110, 5f9b50]

## Author tricks / decoys seen
- Score and achievement thresholds used as psychological decoys to lure reversers into playing or hacking gameplay metrics while key derivation is purely deterministic. [ev: 90db76, 6df9c3]
- Massive decoy scene/level inflation (176 to 200 serialized files) to punish linear exploration, while asset file sizes reveal the true challenge scene immediately. [ev: be8ea1, 17ee43]
- User input keystrokes covertly driving procedural RNG / state generation, disguising an input-steering mathematical challenge as an arcade platformer. [ev: 4ed234, ad0e94]
- Multi-layered constraint puzzles disguised as simpler archetypes (e.g. Circle 9 / Sudoku layered on Minesweeper, or AMX matrix operations masking a 6x6 grid BFS). [ev: 2742bf, 91681a]
- Convoluted multithreaded / mailbox architectures masking simple algebraic reversibility (e.g. hundreds of cell threads wrapping a reversible XOR recurrence). [ev: 596a50, 349344]
- Decoy flag strings or local test flags embedded in binaries to misdirect string triage away from live remote state machines. [ev: 4ed234, c3763c]
- Obfuscated flag routines paired with simple state transitions, tempting reversers into static cryptographic deobfuscation instead of executing the state machine. [ev: f91f1a, 2742bf]

## Verify before submitting
- Replay computed input sequence end-to-end against local binary and remote service to ensure it triggers the legitimate flag output rather than an intermediate check. [ev: 5f9b50, 668d34, 91681a, 4ed234, c3763c]
- Confirm PRNG state and decrypt flag payload offline using the terminal state to ensure plaintext matches the expected competition flag format before submitting. [ev: 5f9b50, 6df9c3, 90db76, 142c04, 349344]
- Verify that intermediate transit triggers (e.g. corridor triggers mutating counters) and secondary constraints (row/col sums, turn caps) are factored into the input payload. [ev: 2742bf, 5d972d, ad0e94]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| python3 | Offline state machine emulation, BFS/DFS pathfinding, SMT/PRNG solving, and remote network automation | 17 writeups |
| IDA Pro | Disassembling stripped binaries, locating state tables, and scripting AST lifting (IDAPython) | 6 writeups |
| Ghidra | Decompiling state machine dispatch loops, actor VM structures, and LLVM pass shared objects | 5 writeups |
| file | Initial file format identification (stripped ELF, PE, Mach-O, kernel image) | 5 writeups |
| strings | Searching for victory messages, flag formats, and embedded game engine assets | 5 writeups |
| objdump | Inspecting disassembly of input loops, instruction extensions (AMX), and section headers | 3 writeups |
| gdb | Dynamic inspection of memory structures, breakpoint verification, and ROM memory dumping | 3 writeups |
| dnSpy | Decompiling and patching .NET assemblies (`Assembly-CSharp.dll`) in Unity Mono games | 2 writeups |
| strace | Tracing startup crashes, missing files/licenses, and syscall feature negotiation | 2 writeups |
| LD_PRELOAD | Intercepting input reads, logging dynamic graph/mailbox setup, and patching branch checks | 2 writeups |
| unzip | Extracting iOS `.ipa` archives and game application bundles | 2 writeups |
| Binary Ninja | HighIL decompilation of WASD movement loops and terminal TTY game state | 2 writeups |
| gcc | Compiling LD_PRELOAD shims, C solver clients, and offline PRNG helpers | 2 writeups |
| bash | Shell execution tracing (`bash -v`) and running local test pipelines | 2 writeups |

## Worked micro-traces
- `[ev: 90db76]` Given an iOS IPA archive containing an ARM64 Mach-O Pac-Man game with a UI requirement to reach score >= 10,000 to reveal the flag. First look revealed an embedded MachActorVM with 72 transition records and SplitMix64 mixing, but game snapshots were passed into the VM. Initial wrong turn was contemplating running the iOS app or patching game score to 10,000. Data-flow analysis of the 28-step traversal path revealed that snapshot parameters XOR in and later XOR out via an identical constant, cancelling to zero. Solvers simulated the 28-step VM transitions offline with a null snapshot to recover RC4 key `0x5ead5b71a04140a7` and decrypted the 40-byte flag.
- `[ev: 5f9b50]` Given a stripped x86-64 Linux ELF binary prompting for a 28-character WASD movement string to decrypt an XOR-encrypted flag buffer. First look showed a movement loop tracking (x, y) coordinates on an 8x8 torus and flipping bits in a 64-bit bitboard used to seed `srand`. Initial wrong turns included attempting raw brute-force across 4^28 combinations, LD_PRELOAD tampering (which broke flag decryption), and unpruned BFS which suffered state explosion. The critical pivot occurred upon realizing the Hamming distance between initial and PRNG target bitmasks was exactly 28 bits, meaning every move must flip an unvisited target cell with zero backtracks. Solvers implemented a DFS in Python with candidate pruning (pruning paths where remaining targets exceeded remaining moves), finding the unique 28-step path in under a second.
- `[ev: be8ea1]` Given a Unity Mono game build where the player is enclosed in a fenced area with in-game signs pointing to distant coordinates across 200 scene files. First look in `Assembly-CSharp.dll` via dnSpy revealed routine movement logic, while signs gave coordinates across multiple levels. Initial wrong turn was trying to sequentially explore scenes or directly modify `transform.position` in memory, which Unity's `CharacterController` repeatedly rejected. The pivot came from sorting the scene files in `Drippy Adventures_Data/` by file size, instantly spotting `level176` (1115 KB) as an extreme outlier among dozens of ~18 KB dummy scenes. Solvers patched `Player.cs` in dnSpy to disable `CharacterController` during teleports, patched camera zoom limits to inspect internal meshes, and teleported directly into level176 to extract the flag fragments.

## Weak signals (single source — treat as hints, not rules)
- Diffing differential RDRAM memory dumps before and after placing voxel blocks isolates checker buffers (`0x695d8`) without decompiling huge retro emulator ROMs. [ev: 142c04]
- Intel AMX hardware matrix multiplications loading B-format packed dwords mathematically project to diagonal column selectors (`diag(p)`). [ev: 91681a]
- Session-based kernel driver mazes with irreversible trap states can be solved by sending a reset ioctl (`0x6489`) and replaying the valid path prefix from root. [ev: c3763c]
- Unpacking Godot engine games into Godot Editor allows making invisible collision/vision cones visible and using damage-boost physics to skip obstacle mazes. [ev: 16d1af]
- Source engine BSP map entity puzzles may contain unavoidable corridor `trigger_once` entities that mutate puzzle accumulators in transit between input panels and check buttons. [ev: 5d972d]
- Disassembling CFGs in NetworkX requires pruning external library calls (e.g. `printf`, `puts`) that act as artificial shortcut bridges between maze entry and exit nodes. [ev: 3f57b3]
- Base64 blobs starting with gzip magic bytes `\x1f\x8b` in client-side web bundles may contain pre-computed puzzle constraints for all time-locked calendar days. [ev: 811af8]
- Multi-layered DRM employing branchless arithmetic crash pointers (`valid_addr + (sum - 33) * 0x1000`) and hardware-entangled physics floats requires algebraic de-entanglement and keygenning rather than binary NOP patching. [ev: 19e110]
