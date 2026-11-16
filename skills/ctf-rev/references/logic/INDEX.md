# ctf-rev logic playbooks: routing index

How to use:
1. Finish the first-10-minutes triage in `SKILL.md` (Solver Mindset), then match what you saw to a signal row below.
2. Open that playbook and follow its "Opening sequence" in order; respect the time-boxes.
3. If two rows match (e.g. a VM inside a packed loader), handle the outer layer first. [ev: 0ffc7b, 76e27c, f05c62]
4. Stuck > 20 min: re-read `meta_reasoning.md` and the playbook's "Decision points", then pivot.
5. Strength = evidence base of the playbook (writeups / events). Tool commands live in `SKILL.md` and `../modern_reversing.md`.

| Signal (minute 0-10) | Archetype | Playbook | Strength |
|---|---|---|---|
| Switch-case or jump table looping over a byte array with a virtual PC; `SIGILL`/`ud2` handler acting as interpreter [ev: 2742bf, a4b4b0, c1b450, 73fc0d] | Custom Bytecode Virtual Machine | [custom-bytecode-vm.md](custom-bytecode-vm.md) | strong (33 writeups / 19 events) |
| Sequential unrolled loops of bitwise transforms ending in `memcmp` against a constant buffer [ev: 2e3f9e, 2bd3ec, ae10f0, 4dd429] | Invertible Transform Pipeline | [invertible-transform-pipeline.md](invertible-transform-pipeline.md) | strong (60 / 32) |
| Multi-variable coupled equations or dense bitwise logic circuits [ev: ac0a19, 70d6ff, f9927d, dcce7e] | Coupled Constraint System and SMT Solving | [constraint-system-smt.md](constraint-system-smt.md) | strong (19 / 14) |
| High entropy (>7.2), W^X sections, `memfd_create`, decryptor loop before a jump [ev: 0ffc7b, 9f74f1, 76e27c, f05c62] | Packed, Self-Modifying, and In-Memory Loaders | [packed-self-modifying-loader.md](packed-self-modifying-loader.md) | strong (16 / 12) |
| Flat CFG backbone with a state-variable dispatcher, MBA expressions, or `SIGILL`/`ud2` control flow [ev: 1d2e38, 84932b, 067aaa, 465bca] | Obfuscated Control Flow (CFF and MBA) | [obfuscated-control-flow.md](obfuscated-control-flow.md) | strong (30 / 19) |
| Managed runtime metadata: .NET, JVM, Python `.pyc`/PyInstaller, WASM, AppleScript [ev: 274017, 512c78, 34526b, cd0145] | Managed Runtime Decompilation | [managed-runtime-decompile.md](managed-runtime-decompile.md) | strong (25 / 17) |
| APK with JNI native library (`lib*.so`) and Java UI; iOS app bundle [ev: 84932b, 3d3586, e26e67, a0a66d] | Mobile Application Reversing | [mobile-app-reverse.md](mobile-app-reverse.md) | strong (16 / 10) |
| Freestanding non-x86 ELF loading at `0x80000000`, no interpreter, MMIO/HTIF [ev: 2e3f9e, 142c04, f9c26a, 24aecd] | Non-Standard Architecture and Firmware | [non-standard-arch-firmware.md](non-standard-arch-firmware.md) | strong (17 / 12) |
| Repeated `srand`/`rand` calls, LFSR feedback, bounded 32-bit or `time()` seeds [ev: 4ed234, d0934a, 6c0ca7, 1f8a0b] | PRNG State and Seed Recovery | [prng-and-seed-recovery.md](prng-and-seed-recovery.md) | strong (10 / 7) |
| WASD/directional input, maze map, state machine, or game engine assets [ev: 91681a, 142c04, 4ed234, c3763c] | Interactive Game and State Machine | [interactive-game-and-state-machine.md](interactive-game-and-state-machine.md) | strong (22 / 15) |
| Kernel module (`.ko`), `ioctl` commands, `/dev/` nodes, Intel AMX tiles or other special CPU features [ev: 91681a, f9927d, cd395d, 0ec1db] | Kernel Modules, Drivers, and Hardware Interfaces | [system-kernel-and-hardware-interface.md](system-kernel-and-hardware-interface.md) | strong (14 / 11) |
| Corrupted ELF headers, stripped Go binary with `pclntab`, or a single `jz` gate [ev: f63cee, dcce7e, 69c2e0, 4529d2] | Triage Shortcuts, Repair, and Binary Patching | [triage-shortcuts-and-binary-patching.md](triage-shortcuts-and-binary-patching.md) | strong (18 / 12) |

Extra routing (round-A lessons): root-required/debugger-hostile with tiny main -> system-kernel; file size >> segments or trailer magic -> packed loader (carve first); fork+ptrace/SIGILL stream -> obfuscated-control-flow (tracer is VM); easy crackme with exact length -> invertible-transform; small APK + opaque asset -> mobile (strings-first); asset-only game map -> triage (visual first). [ev: 647312, b03ebc, 0180b1, 467425, 64f78e, 17ee43]

Cross-cutting discipline (loop, hypotheses, stop-loss, decoys, AI failure modes, verification): [meta_reasoning.md](meta_reasoning.md).
- Decompiler output unreadable or crashing: drop to `objdump -d` / `radare2` and targeted xrefs. [ev: b03ebc, 48b12d, 4ff5d8]
