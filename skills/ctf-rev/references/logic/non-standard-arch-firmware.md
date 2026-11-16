# Non-Standard Architecture and Firmware Reversing

> category: rev · slug: `non-standard-arch-firmware` · evidence: 17 writeups from 12 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Foreign architecture or bare-metal ELF: `readelf` or `file` reports non-x86 instruction sets (RISC-V rv32/rv64, MIPS, AArch64 bare-metal, AVR) lacking standard dynamic linkers (`PT_INTERP`), glibc syscalls, or shared libraries. [ev: 2e3f9e, b6c778, 4be8f2, 6b0cbb, 9d8241]
- Firmware dumps, ROMs, or raw storage images: Binary is provided as raw storage (.hex, .img, N64 ROM, GBA ROM, FPGA bitstream) requiring manual carving or explicit base RAM mapping. [ev: 142c04, 24aecd, 5e0808, a83e1b, 45596d, 6b0cbb]
- Direct host execution failure: Running the target directly on host Linux or under `qemu-user` crashes immediately (exit code 1 or SIGILL) due to missing Linux syscall tables, bare-metal entry points (0x80000000, 0x07C0), or custom opcodes. [ev: 2e3f9e, f9c26a, 10f5ca]
- CPU logic encapsulated inside unconventional host container: Architecture execution is simulated inside an external application container (Excel spreadsheet formulas, PDF JavaScript VM, FPGA bitstream netlist). [ev: f9c26a, 45596d, c1dbd4]
- Custom ISA or permuted instruction encoding: Target implements non-standard register widths (e.g., 23-bit registers) or applies runtime instruction whitening and opcode permutations. [ev: 10f5ca, 8ff6f0, ddafb0, 9b4694]

## Opening sequence (do in this order)
1. **Strings and metadata quick scan** — run `strings` and grep for flag formats, debug messages, and runtime markers; time-box 2 min. Why: multiple non-standard targets leak plaintext flags, format decoys, or runtime identities in strings before spinning up complex toolchains. [ev: 24aecd, 4be8f2, 9d8241]
2. **Architecture and container triage** — run `file`, `readelf -l -A`, or inspect container magic (`TOC0`, `RNK9`, Intel HEX, Excel XML) to determine target ISA, bit width, and RAM base load address; time-box 5 min. Why: disassembling or emulating without the correct architecture plugin and base address produces scrambled disassembly and broken address references. [ev: 2e3f9e, 142c04, 24aecd, 5e0808, 6b0cbb]
3. **Carve embedded binaries from container layers** — extract the guest executable, ROM, or instruction memory table using `dd`, binwalk, or custom scripts rather than analyzing the container environment; time-box 10 min. Why: the outer wrapper (PDF JS emulator, Excel manual formula sheet, DragonFS filesystem) is just a transport container; reversing inside the container creates immense overhead. [ev: 142c04, f9c26a, c1dbd4, ddafb0]
4. **Map memory segments and base load addresses** — configure disassembler memory maps with explicit base addresses (e.g. 0x80000000 for RISC-V, 0x07C0:0x0000 for 16-bit real mode) and separate Flash/ROM from SRAM/BSS; time-box 5 min. Why: bare-metal pointers and cross-references resolve correctly only after base addresses and Harvard architecture segments are aligned. [ev: 2e3f9e, 24aecd, 5e0808]
5. **Locate I/O boundaries and validation logic** — search for hardware mailbox interfaces (HTIF), MMIO registers, DMA transfers, or memory comparison calls (`memcmp`, checksum loops); time-box 10 min. Why: embedded and bare-metal targets lack standard POSIX I/O; locating the hardware registers or verification buffers immediately isolates the core algorithm. [ev: 2e3f9e, a83e1b, 8ff6f0, 9b4694]
6. **Inspect opcode encoding and custom extensions** — test small code blocks against standard disassemblers; if instructions fail or decode into invalid garbage, inspect emulator source or startup code for whitening formulas or custom instructions; time-box 10 min. Why: custom CPU opcodes or instruction whitening must be normalized before Ghidra/IDA can generate meaningful control-flow graphs. [ev: f9c26a, 10f5ca, 8ff6f0, 9b4694]

## Decision points
- **IF** the binary runs inside an unusual container (Excel formula CPU, PDF JS VM, FPGA netlist) **THEN** extract the instruction memory table or bitstream RAM blocks directly **ELSE** load the carved binary into a standard disassembler with configured base memory map. [ev: f9c26a, 45596d, c1dbd4]
- **IF** user-mode QEMU crashes immediately with SIGILL or exit 1 **THEN** inspect the target for custom CPU opcode extensions or bare-metal MMIO/HTIF requirements **ELSE** proceed with user-mode dynamic tracing. [ev: 2e3f9e, f9c26a, 10f5ca]
- **IF** the target executes on bare metal without OS syscalls **THEN** trace memory-mapped I/O (MMIO), HTIF mailboxes, or hardware peripherals to locate input buffers **ELSE** trace standard POSIX argument or file read routines. [ev: 2e3f9e, a83e1b, 9b4694]
- **IF** the target is an interactive system (game ROM, GUI, custom OS) with complex state **THEN** take differential RAM snapshots (before vs after user action) to isolate variable addresses **ELSE** trace input registers and validation functions statically. [ev: 142c04, a83e1b]
- **IF** the architecture uses non-standard word sizes (e.g. 23-bit) or modified cryptographic constants **THEN** emulate with Unicorn or implement explicit bitwise masking (`val & MASK`) in Python **ELSE** use standard modular solvers or Z3. [ev: 8ff6f0, 9d8241, 9b4694]
- **IF** the challenge filesystem contains journal or transaction records **THEN** trace checkpoint commit records and discard uncommitted/speculative transactions **ELSE** parse disk filesystem blocks directly. [ev: 6b0cbb, 9d8241]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Illegal instructions / opcode crashes in emulator → binary extends standard ISA with custom instructions → read emulator / container source (`main.js`, QEMU source) to extract custom opcode definitions and rewrite instructions. [ev: f9c26a, 10f5ca]
- Differential memory snapshot reveals persistent address change → emulator RDRAM diff highlights the exact input coordinate or state buffer → bypass reversing the graphics/game engine and reverse only the validation routine referencing that address. [ev: 142c04, a83e1b]
- Container cell formulas or bitstream INIT parameters reveal structured data → container logic is merely an instruction loader → dump the instruction hex table or RAM primitive contents to recover standard firmware bytecode. [ev: 45596d, c1dbd4]
- Instruction whitening formula or opcode PRNG discovered → instructions are algorithmically scrambled rather than standard compiler outputs → write an instruction de-whitening script in Python before analyzing in disassemblers. [ev: 10f5ca, 9b4694]
- Filesystem commit checkpoint record identified → journal operations past the commit marker are speculative decoys or rollbacks → filter journal to committed records to recover the genuine target files. [ev: 6b0cbb, 9d8241]
- Invertible arithmetic primitives or small key spaces detected → target algorithm uses rolling XOR, reversible DAG mixing (rotates, adds, xor), or bounded seed space (e.g. 20-bit seed) → reverse operations backwards or brute-force locally in seconds instead of heavy constraint solving. [ev: 2e3f9e, 5e0808, 6b0cbb]

## Dead ends & stop-loss
- Simulating or running inside the outer host container — abandon when container execution (Excel iterative calculations, PDF JS emulator) times out or runs too slowly; it failed because host container emulation overhead is massive and hides underlying machine code. [ev: f9c26a, c1dbd4]
- Executing bare-metal ELFs in user-mode QEMU (`qemu-arch-static`) — abandon immediately upon exit code 1 or crash; it failed because bare-metal firmware lacks Linux syscalls, glibc entry points, and POSIX signal handlers. [ev: 2e3f9e, 10f5ca]
- Blind static analysis of large stripped game or engine codebases — abandon when searching disassemblers for input variables exceeds 20 min without progress; it failed because stripped third-party engines contain thousands of unrelated functions, whereas differential memory dumping isolates targets instantly. [ev: 142c04, a83e1b]
- Using standard cryptographic libraries on modified algorithms — abandon when standard hashlib/AES fails validation; it failed because CTF firmware frequently uses custom IVs, non-standard Galois field polynomials (0x1D vs 0x1B), or modified compression constants. [ev: 9d8241, c1dbd4]
- Treating raw data tables or matrices as executable machine code — abandon when disassembly in Capstone or objdump yields nonsensical instruction sequences; it failed because data structures represented algebraic matrices, S-boxes, or lookup tables rather than CPU instructions. [ev: 24aecd, 9551c4]
- Replaying speculative filesystem journal records past commit boundaries — abandon when journal operations delete target files or create fake shortcuts; it failed because authors intentionally inject uncommitted rollback transactions as decoys. [ev: 6b0cbb, 9d8241]

## Author tricks / decoys seen
- Decoy plaintext flags in strings or uncommitted files (e.g. `REDFOX{Haha, Gotchya}`, fake one-button-clear replay) planted to mislead naive string searches and filesystem dumps. [ev: 24aecd, 6b0cbb, 9d8241]
- Speculative / rollback transaction traps where filesystem journal logs contain deletion or tampering transactions executed after the genuine commit checkpoint. [ev: 6b0cbb, 9d8241]
- Instruction scrambling and whitening (PC-dependent whitening formulas, destination register scrambling `((x*5)^3)&7`, PRNG opcode shuffling) designed to make standard disassemblers output nonsensical code. [ev: 10f5ca, 9b4694]
- Intimidating container architectures (Excel manual formula engines, PDF JavaScript VMs) used as wrappers to trick solvers into reversing complex simulators instead of the underlying machine code. [ev: f9c26a, c1dbd4]
- Non-standard bit widths and algebraic field tweaks (23-bit registers/modular arithmetic, GF(2^8) reduction polynomial 0x1D instead of 0x1B) intended to break standard 32-bit integer arithmetic and generic crypto libraries. [ev: 8ff6f0, c1dbd4]

## Verify before submitting
- Emulate reconstructed algorithm in genuine environment or cross-emulator: run candidate input through Unicorn, Spike, or a custom Python emulator to ensure normal termination and success message. [ev: 2e3f9e, 9d8241, 10f5ca, 9b4694]
- Forward-calculate full plaintext from candidate keys: execute forward decryption across all blocks to confirm standard flag format wrapper and coherent ASCII text. [ev: 24aecd, 5e0808, 6b0cbb]
- Local container or emulator test before remote execution: test solve scripts against local Docker containers or emulated instances before submitting over network services with rate limits or timeouts. [ev: f9c26a, ddafb0, 9b4694]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Python 3 | Algorithmic inversion, custom emulators, solve scripts, byte carving | 15 writeups |
| Ghidra | Decompiling non-standard architectures (RISC-V, 16-bit DOS, ARM) | 5 writeups |
| objdump / llvm-objdump | Disassembling raw binaries and custom ISAs (RISC-V, AVR) | 5 writeups |
| strings | Initial triage, finding plaintext flags and embedded format strings | 4 writeups |
| GDB | Dynamic memory inspection and emulator debugging | 3 writeups |
| file | Identifying target architecture, ELF headers, and container types | 3 writeups |
| readelf | Inspecting segment headers, entry points, and architecture flags | 2 writeups |
| Unicorn Engine | Emulating bare-metal routines and custom crypto functions | 2 writeups |
| qemu-system-aarch64 | Booting bare-metal OS kernels and attached disk images | 2 writeups |

## Worked micro-traces
- `[ev: 2e3f9e]` THCon 2K26 CTF — M4terM4xima's HINT Part 1&2: Given a bare-metal RISC-V ELF (`HINT.elf`). First look via `readelf` showed entry point 0x80000000 and rv32imac architecture with no dynamic linker or syscall table, while strings revealed Rust runtime but no plaintext flag. Solvers first attempted running `qemu-riscv32-static`, which failed immediately with exit code 1 due to lack of Linux ABI, and then tried inverting XOR data at 0x1dd0, producing non-UTF-8 garbage because it was a Rust slice header. Pivoted by identifying an inline `memcmp(buf, 0x80000ddc, 20)` following a rolling XOR loop `out[i] = in[i] ^ (in[i-1] + key[i])`. Inverted the rolling XOR in Python, verified by executing candidate input in a custom Python rv32imac emulator with HTIF mailbox support, and printed the success message.
- `[ev: 142c04]` DEF CON CTF Qualifier 2026 — Birdhouse: Given a Nintendo 64 ROM running a 3D block-placement world in the ares emulator. First look at ROM data revealed a DragonFS signature (`TOC0`) containing an embedded Big-Endian MIPS ELF executable. Solvers initially attempted dynamic debugging via the emulator's integrated GDB server (which proved unstable) and blind static analysis in IDA to locate block-checking logic in the large stripped engine. Pivoted by taking differential RDRAM memory dumps before and after placing blocks in-game, immediately identifying address `0x695d8` that tracked placed block coordinates. Reconstructed the MIPS PRNG state-hashing logic referencing that memory address, solved the block assignments, and generated the plaintext flag.
- `[ev: f9c26a]` squ1rrel CTF 2026 — squ1rrel-o-tron: Given a PDF challenge embedding a JavaScript-based virtual machine (`main.js`) running a RISC-V guest kernel and requiring 16-byte responses within a 5-second per-round timeout. First look identified the RISC-V guest executable inside the extracted filesystem. Solvers initially tried using the PDF JavaScript VM as a black-box execution oracle (which was too slow and flaky for the 5-second timeout) and attempted executing the binary in standard `qemu-riscv32`, which crashed on illegal instructions. Pivoted by inspecting the `main.js` opcode decode switch table to identify three custom CPU instructions (custom rotate, multiply, and XOR). Disassembled with `llvm-objdump-18`, mapped the custom opcodes, reimplemented the nonce transformation algorithm directly in Python, and answered 5 consecutive rounds to capture the flag.

## Weak signals (single source — treat as hints, not rules)
- Tropical min-plus matrix-vector multiplication (`ct_i = min_j(K[i][j] + p_j)`) inverted via Galois residuation `p_j = max_i(ct_i - K[i][j])`. [ev: 9551c4]
- Lattice iCE40 FPGA bitstream unpacked with IceStorm (`iceunpack`, `icebox_vlog`) to extract S-box ROM from `SB_RAM256x16` bit-interleaved INIT parameters. [ev: 45596d]
- 16-bit MS-DOS real-mode floppy disk image decompiled in Ghidra using segment `0x07C0:0x0000` to find a 20-bit seed LFSR keystream. [ev: 5e0808]
- Multi-key AVR flash-to-SRAM copying: Arduino firmware copying `.data` from flash to SRAM across multiple distinct 10-byte XOR loops. [ev: 24aecd]
- Huge stripped ELF binaries (>1 GB) trimmed with custom scripts (`trim_elf.py`) and isolated inside Docker PID namespaces to prevent exit code 144 crashes. [ev: ddafb0]
- GBA ROM ARM7TDMI DMA timing and register injection using mGBA / Unicorn with Z3 button press solving. [ev: a83e1b]
- IOCCC-style C obfuscation embedding LEB128 bytecode interpreters inside RISC-V 64-bit binaries. [ev: b6c778]
