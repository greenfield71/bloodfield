# Packed, Self-Modifying, and In-Memory Loaders

> category: rev · slug: `packed-self-modifying-loader` · evidence: 16 writeups from 12 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Unusual section headers: sections with `SizeOfRawData == 0` (e.g. `.text`, `UPX0`), sections marked writable and executable (WX), or substantial appended overlays beyond the section header table. [ev: 9f74f1, 7ba241, 56662d]
- Static disassembly displays truncated entry points, XOR decryption loops, or dynamic memory-allocation and protection APIs (`mprotect`, `VirtualProtect`, `memfd_create`) directly preceding execution transfer. [ev: 0ffc7b, 76e27c, 305d06]
- Architecture mode-switch instructions in 32-bit Windows binaries (`PUSH 0x33; ...; RETF` or far calls switching to segment selector `0x33` for WOW64 Heaven's Gate). [ev: 0ffc7b, 860e13, db25e2]
- Multi-layer droppers or onion unpackers writing nested PE/ELF files into temporary directories, cache paths, or anonymous in-memory file descriptors. [ev: 9f74f1, fbedf0, f05c62, 38e970]
- Statically visible flag-checking routines referenced in `.data` contain uncalled dead ends, while pre-main `.init_array` constructors or dynamic hooks redirect function pointers at runtime. [ev: 76e27c, fbedf0, 56662d]

## Opening sequence (do in this order)
1. **Triage container & section headers** — inspect section names, raw sizes, entropy, and standard packer signatures (`UPX`, PyInstaller `MEI`, VMProtect); time-box 3 min. Why: determines whether the outer wrapper can be stripped immediately with standard unpackers (`upx -d`), carved via static overlays, or decompressed offline. [ev: 9f74f1, 7ba241, 56662d]
2. **Audit dynamic drops and memory syscalls** — monitor dropped files in `/tmp` or `%LOCALAPPDATA%`, and trace allocations (`memfd_create`, `VirtualAlloc`) via `strace`, Wine debug channels, or PLT hooks on `memcpy`; time-box 5 min. Why: droppers frequently extract clean, uncompressed inner binaries to memory or disk; carving them avoids analyzing the complex outer loader. [ev: 9f74f1, 76e27c, fbedf0]
3. **Audit constructors and runtime pointer initialization** — inspect `.init_array` entries, TLS callbacks, and function pointer initialization in `.data`/`.bss` before reversing `main`; time-box 5 min. Why: loaders often initialize pointers to complex honeypot routines statically and swap them to the real checking logic in constructors. [ev: 76e27c, 56662d]
4. **Identify mode switches and signal dispatchers** — search disassembly for `retf` with selector `0x33` (Heaven's Gate) or signal handler registrations (`SIGTRAP`, `SIGSEGV`); time-box 5 min. Why: standard 32-bit decompilers corrupt 64-bit shellcode, and debuggers fail or crash when encountering signal-driven JIT loaders unless carved or intercepted. [ev: 0ffc7b, 860e13, 305d06, db25e2]
5. **Locate runtime instruction unsealers & dispatch loops** — look for decryption routines executed immediately prior to control transfer (e.g. self-modifying loops, custom VM `vm_execute` loops, or trap dispatchers); time-box 5 min. Why: hooking or dumping memory after the unsealer executes yields the true unprotected instructions and avoids analyzing the protective cryptography. [ev: 0ffc7b, 305d06, 2b52b8]

## Decision points
- **IF** file size far exceeds the end of the last loadable segment/section, a custom trailer magic sits near EOF, or a MEI/`PAYLOAD_START`-style marker is present **THEN** treat the file as a self-extracting package: measure segment end vs file size, carve the overlay or parse the trailer, or run under `strace -f -e trace=openat,write,unlink` and copy dropped temp files before they are deleted, then analyze the inner binary as the real target **ELSE** analyze the outer file in place. [ev: b03ebc, aa5f98, 9f74f1, d7a46d]
- **IF** layered blobs (PE resources, appended payloads, evolving generations) are XOR-masked **THEN** enumerate containers first (resource table, overlay), recover the key from known plaintext (`MZ`/ELF magic, flag prefix), script the peel until nothing remains, and log every layer's key and any marker left in each layer **ELSE** carve by signature. [ev: 465bca, 7ba241, 06267e, 9f74f1]
- **IF** the binary transitions CPU modes via Heaven's Gate (`retf` with segment `0x33`) **THEN** carve the payload starting past the `RETF` and analyze it in a dedicated 64-bit disassembler or 64-bit Unicorn emulator **ELSE** continue single-architecture static analysis. [ev: 0ffc7b, 860e13, db25e2]
- **IF** the outer executable unpacks an inner payload to disk or memory (`memfd_create`, zlib/LZMA streams, temporary files) **THEN** carve the inner binary/shared library and analyze it directly **ELSE** analyze the loader in-place. [ev: 9f74f1, 76e27c, fbedf0, 16c799]
- **IF** payload blocks or inner stages are encrypted with recognizable cryptographic algorithms (AES tables, RC4 KSA/PRGA, Speck ARX constants) **THEN** extract the static keys and ciphertext directly from `.rodata` or dynamic registers rather than reversing the cryptographic implementation **ELSE** invert custom mathematical mixing functions. [ev: 9f74f1, fbedf0, 2b52b8, 2d00be]
- **IF** self-modifying code executes in small chained stages (<= 16-bit key per stage) **THEN** snapshot memory state and brute-force the keys sequentially via in-process execution or masked bytecode pattern matching **ELSE** invert the terminal transformation algebraically. [ev: f05c62, 38e970]
- **IF** anti-debugging checks (TracerPid, RDTSC) or signal traps (SIGTRAP) interfere with debugger tracing **THEN** bypass debugging via `LD_PRELOAD` library hooks or static key derivation in Python **ELSE** use dynamic breakpoints to dump memory. [ev: 76e27c, 305d06, 56662d]
- **IF** a flag-checking function is reached via a global pointer stored in `.data` **THEN** inspect `.init_array` constructors for runtime pointer overwrites before reversing the pointed function **ELSE** reverse the statically referenced routine directly. [ev: 76e27c, 56662d]

## Pivot triggers (the "aha" signals that cracked these challenges)
- Segment selector `0x33` loaded before `retf` → Heaven's Gate 32-bit to 64-bit mode transition → carved the post-`retf` byte stream and disassembled it as x86_64, converting garbled 32-bit instructions into clean logic. [ev: 0ffc7b, 860e13]
- Static sections have `SizeOfRawData == 0` with a preceding `PACKER_INFO` table of RVA pairs or zlib/LZMA compression headers → packed payload can be extracted statically without battling dynamic anti-debug traps → wrote offline Python extraction script to decompress clean payload. [ev: 9f74f1, 16c799]
- `.init_array` constructor overwrites global function pointer `g_check_fn` before `main()` → the complex statically visible flag checker is an elaborate honeypot decoy → redirected analysis to the dynamic pointer target. [ev: 76e27c, 56662d]
- Each self-modifying segment consumes only 2 bytes (65,536 space) before decrypting the next layer → irreversible mathematical obfuscation cannot prevent brute force on 16-bit slices → built in-process snapshot/rollback runner using `mprotect` or masked instruction matching to solve all stages in seconds. [ev: f05c62, 38e970]
- VM dispatcher (`vm_execute`) or instruction unsealer logs operands/decrypted instructions directly in memory → custom VM lifting and bytecode decryption reversing are unnecessary → hooked the decoder/dispatcher at runtime to log decrypted instructions and cryptographic state. [ev: 2b52b8, 305d06]

## Dead ends & stop-loss
- Reversing complex decoy modules inside multi-layer droppers (e.g. bundled GameBoy emulators, font ligature parsers, network beaconing) — abandon when static xrefs from `main` lead to dead ends or `.init_array` constructor overrides exist; it failed because authors intentionally embed complex open-source or custom parsers as time-sink honeypots. [ev: 9f74f1, 76e27c, fbedf0, 56662d]
- Decompiling Heaven's Gate 64-bit shellcode inside a 32-bit decompiler view or debugging it in a 32-bit debugger — abandon immediately upon seeing `retf 0x33`; it failed because decompilers misinterpret stack offsets (ESP vs RSP) and 32-bit debuggers crash or lose control upon CPU mode switch. [ev: 0ffc7b, 860e13, db25e2]
- Dynamic debugging with GDB/strace against binaries with silent anti-debug state corruption (RDTSC, TracerPid) or SIGTRAP handlers — abandon when decrypted payloads crash or fail checksums; it failed because anti-debug logic silently corrupts decryption keys instead of exiting immediately. [ev: 76e27c, 305d06, 56662d]
- Attempting simultaneous full-binary static decompilation or heavy symbolic execution (angr `entry_state()`) on multi-stage/onion loaders — abandon within 10 minutes if constraints explode; it failed because chained SMC accumulates runtime mutations, and symbolic execution stalls on glibc initialization or AVX2 SIMD operations. [ev: 76e27c, f05c62, 38e970]
- Writing a full standalone bytecode emulator/lifter for layered VM loaders when execution tracing is available — abandon when lifting takes > 30 minutes; it failed because layered bytecode cannot be disassembled statically until earlier stages decrypt it, whereas tracing register states at the dispatcher yields the operations directly. [ev: f05c62, 2b52b8]
- Relying on short (2-3 byte) opcode prefixes to validate brute-forced self-modifying stages — abandon when false positives occur; it failed because 16-bit keys produce spurious collisions that corrupt downstream execution states unless validated by a longer masked pattern. [ev: 0ffc7b, 38e970]

## Author tricks / decoys seen
- Fake flag strings planted in static data sections or `.note` sections (`CTF{example_flag}`, fake build IDs) that do not match competition prefixes or are never referenced by real validation logic. [ev: 7ba241, 56662d]
- Elaborate decoy parsers (e.g., OpenType font GSUB ligature tables, embedded GameBoy ROM emulators) statically wired to global function pointers but swapped out at runtime by `.init_array` hooks. [ev: 76e27c, fbedf0, 56662d]
- Silent anti-debug key poisoning: instead of terminating with a message, checks against `TracerPid` or `RDTSC` silently XOR cryptographic keys (e.g. `^ 0x80`), causing decryption to yield garbage. [ev: 76e27c, 56662d]
- Dual-mode polyglot code where opcode bytes (like `0x48`) execute as distinct valid instructions in 32-bit (`DEC EAX`) versus 64-bit (`REX.W`) modes to branch control flow unexpectedly across Heaven's Gate calls. [ev: 0ffc7b, db25e2]
- Multi-layer droppers hiding true payloads behind innocent system filenames (e.g., `svchost`, hidden icon caches) or disguised as passive data containers. [ev: 9f74f1, fbedf0]
- Unreachable decoy VM interpreters bundled alongside droppers (e.g. an emulator function with an immediate `RET` instruction at entry) to waste time reversing dead VM handlers. [ev: 9f74f1, fbedf0]

## Verify before submitting
- Feed the candidate flag into the original binary natively or under Wine and confirm it outputs the official success string (e.g. "Access Granted", "[+] correct!", "The gods are pleased"). [ev: 0ffc7b, 76e27c, db25e2, 305d06]
- Verify flag normalization, casing, and padding: check whether pre-normalization (e.g., `toupper`) or PKCS#7 padding was applied, ensuring raw input matches exact hash/cipher expectations. [ev: 0ffc7b, 9f74f1, 305d06]
- Ensure the candidate string adheres strictly to the target event's flag wrapper specification (e.g. `psctf{...}`, `Securinets{...}`, `kalmar{...}`) rather than generic decoy strings. [ev: 9f74f1, 7ba241, 56662d]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| python3 | Offline payload decryption, LZMA/zlib decompression, brute-force scripting | 12 |
| IDA Pro | Static analysis, entry point decryptor triage, `.init_array` hook inspection | 7 |
| Ghidra | Decompiling carved 64-bit shellcode, static analysis of multi-stage binaries | 5 |
| file | Initial file format triage, architecture bitness, and stripping status | 5 |
| gdb | Runtime register inspection, dynamic black-box state probing | 4 |
| gcc | Compiling native C snapshot runners and `LD_PRELOAD` shared object hooks | 3 |
| strings | Rapid initial triage, identifying output prompts, detecting decoy flags | 3 |
| objdump / readelf | Analyzing section tables, detecting raw size discrepancies and overlays | 3 |
| LD_PRELOAD | Intercepting `memcpy` to carve in-memory ELFs, hooking decrypted buffers | 2 |
| ndisasm | Disassembling carved raw 64-bit shellcode buffers lacking object headers | 2 |
| Wine | Executing and tracing Windows PE binaries and dropper behaviors on Linux | 2 |
| upx | Decompressing UPX-packed binaries (`upx -d`) | 1 |

## Worked micro-traces
- `[ev: 0ffc7b]` Given a 32-bit Windows Lazarus GUI PE checking a 40-character flag, initial analysis revealed strings obfuscated with XOR 0x57 leading to self-modifying code decrypted via `flag_data[i] ^= input[i % 7] ^ 0x57`. The solver initially attempted to decompile the entire binary in Ghidra's 32-bit view and was misled by an all-uppercase polynomial validation table. Observing `PUSH 0x33; ...; RETF` immediately signaled Heaven's Gate; carving the 64-bit payload past the `RETF` into a separate x86_64 project revealed 7 independent chunked FNV-1a hash checks. The solver inverted the hashes via meet-in-the-middle over alphanumeric characters to reconstruct the true mixed-case flag and confirm the success prompt.
- `[ev: 76e27c]` Given an ELF challenge that decrypted a secondary ELF on the GPU using Vulkan compute shaders and executed it via `memfd_create`, initial analysis showed static pointers to an elaborate font ligature table checker. Naive symbolic execution with angr crashed during glibc startup, and running under GDB triggered TracerPid/RDTSC anti-debug checks that silently corrupted key derivation. The solver discovered an `.init_array` constructor `_specter_hook` dynamically overwritten `g_check_fn` to the real checking function, and noticed AVX2/Salsa operations had zero inter-byte diffusion. Recognizing the byte-independence, the solver bypassed complex symbolic math by treating the binary as a black-box oracle in GDB, recovering all 48 flag bytes in ~330 dynamic executions in 2 seconds.
- `[ev: 38e970]` Given an ELF binary implementing 256 chained self-modifying code stages, each consuming 2 input bytes to decrypt subsequent code, whole-binary static analysis stalled due to path explosion and accumulated state mutations. An initial brute-force attempt using only a 3-byte instruction prefix to identify successful decryptions caused false-positive key matches that broke the chain. The solver pivoted by observing that every decrypted stage shared a 17-byte instruction sequence with only a 4-byte RIP-relative displacement varying. By capturing an exact memory snapshot and matching against the masked 17-byte bytecode pattern across 65,536 keys per stage, the solver sequentially peeled all stages to extract the complete flag.

## Weak signals (single source — treat as hints, not rules)
- Kernel module binary format loaders: when provided a companion `.ko` alongside an encrypted flat file, inspect `init_module` for `register_binfmt` / `insert_binfmt` to extract the decryption cipher and mapping base. [ev: 2d00be]
- Transformer weights memorizing compressed payloads: when given an autoregressive model (`infer.py`), perform continuous greedy decoding from seed tokens rather than prompt-response restarts to extract embedded gzip archives. [ev: 69dcf9]
- Dual-mode polyglot branching: byte `0x48` decodes as `DEC EAX` in 32-bit mode but `REX.W` prefix in 64-bit mode, allowing a single function to diverge control flow across Heaven's Gate invocations. [ev: db25e2]
- Dynamic backdoor gate patching: complex validation engines guarded by signal handlers may contain developer test gates (e.g. route projection window) that can be forced open by patching data segment constants. [ev: 33f3ef]
- GPU compute shader unpacking: loaders can offload decryption routines to Vulkan/SPIR-V compute pipelines to hide decryption keys and logic from standard CPU debuggers. [ev: 76e27c]
