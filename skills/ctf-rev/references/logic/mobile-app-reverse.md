# Mobile Application Reversing (Android and iOS)

> category: rev · slug: mobile-app-reverse · evidence: 16 writeups from 10 events · strength: strong

**When this applies (recognition, first 5 minutes):**
- Archive packaging or file signature indicates an Android package (`.apk`, `.aab`, unzips into `classes.dex`, `AndroidManifest.xml`, `lib/`, `res/`) or mobile Mach-O ARM64 binary. [ev: e26e67, 841073, d02322, 062442, 467425]
- Decompiled Java/Kotlin source in JADX contains `System.loadLibrary(...)` loading a bundled `.so` file with `public native` method declarations bridging user input to native code. [ev: 64f78e, e26e67, 4127d2, d02322, 062442]
- Decompiled Java exposes static flag getters or reflection handles (`Vault.get_flag()`, `Method.invoke`) paired with client-side root/tamper checks (`detectRoot()`, `isDeviceRooted()`). [ev: 84932b, 3d3586, e3c4b0, 4127d2, 6c0727]
- Application package bundles internal native libraries (`lib/arm64-v8a/*.so`, `lib/x86_64/*.so`) or SQLite databases in `assets/` / `res/raw/` containing encrypted blobs. [ev: 64f78e, e26e67, 2762f0]
- Challenge description, prompt text, or strings explicitly reference Android/mobile concepts (activities, intents, JNI, Smali, Dalvik, or mobile frameworks like MNN FlatBuffers). [ev: 84932b, 64f78e, a0a66d, 2762f0]

## Opening sequence (do in this order)
1. **Unpack and inspect package manifest** — extract APK using `unzip -q` or inspect with `file` and JADX; inspect `AndroidManifest.xml` for launchable activities, exported components, and permissions; time-box 2 min. Why: identifies the true execution entry point, registered native libraries, and whether challenge logic resides in Java, resources, or native `.so`. [ev: e26e67, 841073, d02322, 062442, 467425]
2. **Decompile Java layer and locate validation entry point** — open package in `jadx` to audit activity lifecycle (`onCreate`), UI button listeners (`onClick`), and flag validation dispatch; check if validation is pure Java or calls `System.loadLibrary`; time-box 5 min. Why: reveals whether you can solve statically in Java, need to invoke an un-obfuscated getter, or must pivot to native disassembly. [ev: 84932b, 3d3586, e3c4b0, 6c0727, ff8049]
3. **Audit native library exports and strings** — if a native library exists (`lib/**/*.so`), inspect with `strings`, `readelf -s`, and load into `Ghidra` or `IDA Pro`; locate JNI entry points (`Java_<package>_<class>_<method>`) or `JNI_OnLoad`; time-box 5 min. Why: separates simple static constant/arithmetic comparisons from complex state machines or cryptographic engines early. [ev: 841073, 7e13c5, 062442, d02322]
4. **Evaluate dynamic instrumentation vs static extraction** — test whether flag-generating methods can be statically reversed in <10 minutes vs invoked via Frida or Smali patch; time-box 3 min. Why: setting up an emulator/AVD and Frida server is costly; avoid it if static inversion or Smali patching is trivial. [ev: 84932b, 7e13c5, 3d3586, 4127d2]
5. **Inspect resources and asset directories** — check `res/raw/`, `res/drawable/`, and `assets/` for encrypted databases (`.db`), configuration tables, or layered vector drawables before reversing complex algorithms; time-box 3 min. Why: challenges frequently store encrypted payloads or camouflage flag graphics in asset XMLs rather than bytecode. [ev: 64f78e, e26e67, ff8049, 062442]

## Decision points
- **IF** the APK is small or self-contained with one opaque asset/blob and flag-shaped literals in strings or notes **THEN** within minutes dump dex/native strings, find the key-derivation recipe (hash/concatenation of literals), try it on the asset with XOR/AES, and treat flag-shaped literals as decoys; do full component reading only if this fails **ELSE** follow the JNI/export route. [ev: 64f78e, 062442, 7e13c5, e26e67]
- **IF** the target method `get_flag()` is a self-contained static method or exports an unauthenticated getter **THEN** bypass root check and invoke it directly via Frida dynamic call (`Java.use(...).get_flag()`) or Smali bytecode patch into `onCreate` **ELSE** decompile the native library check routine. [ev: 84932b, 3d3586, e3c4b0, 6c0727]
- **IF** native routine performs simple byte-wise arithmetic/XOR against a static array in `.rodata` **THEN** extract bytes from ELF and invert algorithm directly with Python without launching an emulator **ELSE** inspect complex state updates for mathematical invertibility or model transitions in Z3. [ev: 841073, 7e13c5, 062442, d02322, 2762f0]
- **IF** JADX fails to decompile complex obfuscated Java bytecode (instruction limit exceeded or heavy reflection) but the method signature is clean **THEN** hook or invoke dynamically using Frida **ELSE** extract strings and reconstruct algorithm statically. [ev: 3d3586, e3c4b0, 6c0727]
- **IF** native binary enforces runtime anti-tamper or root detection (`check_root()`) returning an error string **THEN** hook the root check function with `Interceptor.replace` to force a clean return (e.g. return 1 or false) before calling the getter **ELSE** extract and decrypt embedded payloads directly from `.rodata`. [ev: 3d3586, 4127d2, 7e13c5]
- **IF** execution flow is driven by rolling hashes or multi-step state machine split across Java and native libraries **THEN** extract constraint matrices / state tables statically and solve via Z3 or meet-in-the-middle search **ELSE** use dynamic tracing / logging. [ev: e26e67, 2762f0]
- **IF** the APK unzips to reveal secondary encrypted assets or packed ELF shared libraries (`assets/*.bin` or encrypted `.so`) **THEN** recover AES key/IV parameters or decryption routines from the Java startup lifecycle (`onCreate`) to unpack the inner payload **ELSE** analyze the primary `.so` directly. [ev: 64f78e, e26e67]
- **IF** dynamic emulator or Frida setup encounters persistent environment friction (architecture mismatch, crashes, or root detection) **THEN** abandon dynamic execution and pivot to static bytecode patching via `apktool` or standalone Python emulation **ELSE** proceed with dynamic runtime hooks. [ev: 84932b, 7e13c5, e26e67]
- **IF** the app enforces emulator evasion or root detection via known checks (e.g. checking `/system/bin/su` or `RootBeer`) **THEN** override the boolean check dynamically in Frida or patch out the abort/exit branch in Smali **ELSE** let the app run natively under a standard AVD or local test runner. [ev: 84932b, 3d3586, 4127d2]

## Pivot triggers (the "aha" signals that cracked these challenges)
- `Vault.get_flag()` or parameterless method present in Java/Smali despite heavy internal obfuscation → static bytecode analysis is a decoy; invoke method directly via Frida or patch `MainActivity.onCreate` with `invoke-static` to log flag on startup. [ev: 84932b, 3d3586, e3c4b0, 6c0727]
- JNI function compares user input against transformed buffer derived from fixed `.rodata` offsets (`(table[i] - 7) >> 2` or XOR key) → routine does not validate via dynamic runtime state or remote servers; invert transformation statically in a 10-line Python script. [ev: 841073, 7e13c5, 062442, d02322]
- Root detection triggers error message ("Root detected - flag unavailable") during dynamic execution → locate `check_root` / `detectRoot` boolean export in Ghidra or JADX and overwrite return value with Frida `Interceptor.replace` or `implementation` override. [ev: 3d3586, 4127d2]
- State machine operations (modular multiplication by odd constant, bit rotations, XORs) are 100% bijective / mathematically invertible → avoid brute-forcing the entire search space; split the sequence in half with a meet-in-the-middle hash table or symbolize in Z3. [ev: e26e67, 2762f0]
- Prompt or source mentions "cache", "database", or secondary storage → search `assets/` and `res/raw/` for SQLite databases or encrypted blobs; cross-reference table schemas with native key derivation functions. [ev: 64f78e, e26e67]
- UI presents distractor checks (trivial button click counts, fake flags in strings, or audio tone checks) → verify whether UI callbacks feed directly into cryptographic decryption or are completely disconnected from flag output. [ev: 47c602, 64f78e, ff8049]

## Dead ends & stop-loss
- Spending hours setting up an Android AVD/emulator, rooting it, and troubleshooting Frida server connections when the native `.so` logic is self-contained — abandon when static disassembly reveals fixed `.rodata` buffers and deterministic logic; write a standalone Python solver or Smali patch instead. [ev: 84932b, 7e13c5, e26e67]
- Reversing obfuscated Java bytecode inside utility/vault classes line-by-line when reflection or Frida dynamic invocation is available — abandon when JADX skips instructions or classes are heavily obfuscated; call the method directly in the running VM. [ev: 3d3586, e3c4b0, 6c0727]
- Grepping raw binaries for flag prefix strings (`FLAG{`, `0xV01D{`) without analyzing validation code — abandon when initial hits yield multiple fake/decoy flags; verify how the candidate string is actually referenced. [ev: 64f78e, ff8049]
- Interacting with client-side UI gimmicks (tapping buttons repeatedly, playing audio pitch into mic, completing game achievements) — abandon when UI code has no cryptographic connection to flag decryption; inspect event handlers and intent dispatchers in JADX directly. [ev: 47c602, ff8049]
- Brute-forcing large multi-step state spaces or running slow emulator test harnesses when state updates are mathematically reversible — abandon after finding invertible operations; implement meet-in-the-middle or Z3 constraint models instead. [ev: e26e67, 2762f0]
- Spending time analyzing non-essential audio or media assets (`pop.mp3`, standard image assets) for steganography — abandon after 3 minutes if spectral or binwalk scans show standard format data without anomalies. [ev: 062442, ff8049]

## Author tricks / decoys seen
- Decoy flag strings embedded in `.rodata` or resources intended to mislead naive `grep` / `strings` sweeps. [ev: 64f78e, ff8049]
- Challenge prompt or title baiting players into dynamic Frida/emulator setups when a 5-minute static script or Smali patch solves it instantly. [ev: 84932b, 7e13c5, 062442]
- Distractor UI mechanics (game achievement counters, audio pitch detection, dummy buttons) that execute no security validation. [ev: 47c602, ff8049]
- Hybrid multi-tier logic hiding state updates inside native JNI `.so` while displaying validation checks in Java to derail single-layer static analysis. [ev: e26e67, 2762f0]
- Secondary payload encryption or dynamic library loading designed to obscure the true native binary from top-level APK triage. [ev: 64f78e, e26e67]

## Verify before submitting
- Re-run the standalone Python solver or verify the reconstructed key against the validation condition (e.g., AES-GCM tag verification or length check). [ev: 64f78e, e26e67, 2762f0]
- Execute the candidate string through the native binary / patched runner or observe the output in `adb logcat` / Frida console to confirm genuine acceptance. [ev: 84932b, 3d3586, e26e67, 4127d2]
- Confirm the decrypted string strictly matches the challenge flag regex format and contains coherent leetspeak/English words. [ev: 7e13c5, d02322, 062442]

## Tools that actually got used
| tool | used for | in N writeups |
|---|---|---|
| Python (with pycryptodome / z3) | Inverting native byte transforms, AES-GCM decryption, MITM and Z3 constraint solving | 11 writeups [ev: 64f78e, e26e67, a0a66d, 841073, 7e13c5, 2762f0, 062442, d02322, ff8049, 467425] |
| jadx / jadx-gui | Java/Kotlin decompilation, AndroidManifest inspection, and JNI bridge tracking | 9 writeups [ev: 3d3586, 64f78e, e26e67, 47c602, e3c4b0, 4127d2, 6c0727, 2762f0, d02322] |
| Ghidra | Native shared library (.so) disassembly, decompiler analysis, and JNI function mapping | 8 writeups [ev: 64f78e, 47c602, a0a66d, 4127d2, 7e13c5, 062442, d02322, 467425] |
| Frida / frida-server | Dynamic instrumentation, hooking root checks, and direct method invocation in live VM | 5 writeups [ev: 3d3586, e3c4b0, 4127d2, 6c0727, ff8049] |
| adb | Device connection, APK deployment, and reading logcat output | 6 writeups [ev: 84932b, 3d3586, e3c4b0, 4127d2, 6c0727, ff8049] |
| apktool | Resource unpacking, Smali bytecode disassembly, patching, and rebuilding | 5 writeups [ev: 84932b, 64f78e, a0a66d, 062442, ff8049] |
| unzip / file / strings | Initial APK extraction, file typing, and quick static string scanning | 6 writeups [ev: e26e67, 841073, 7e13c5, 062442, d02322, 467425] |
| IDA Pro | Native binary analysis and control-flow graph mapping | 3 writeups [ev: 47c602, 2762f0, 062442] |
| Android Studio AVD | Emulating target Android environment for dynamic testing | 3 writeups [ev: 3d3586, e3c4b0, 4127d2] |

## Worked micro-traces
- `[ev: 84932b]` Given an APK nudging dynamic Frida instrumentation to defeat root checks, the solver decompiled Smali with `apktool` and found parameterless static method `Vault.get_flag()`. Rather than fighting emulator setup or anti-root scripts, the solver patched `MainActivity.onCreate` in Smali to call `Vault.get_flag()` directly and print the returned string to Android logcat. Rebuilt the package with `apktool`, re-signed with `apksigner`, launched on an emulator, and extracted the flag `HERO{D1D_Y0U_U53_0BJ3C71ON?}` via `adb logcat`.
- `[ev: e26e67]` Given an APK with an encrypted native library (`libnative-lib.so`), the solver unzipped the package, recovered AES key/IV from Java in JADX, and decrypted the secondary ELF. Initial attempt to run a 27-step forward DFS in emulator was intractable and too slow. The solver recognized that all three native state transformations (modular multiplication by 0x83, rotation, checkpoint XOR) were mathematically invertible, pivoted to a meet-in-the-middle search meeting at step 13, and validated candidate `BKISC{4nd0rid_m4z3_s0lving}` under `qemu-aarch64-static`.
- `[ev: 4127d2]` Given an APK with native library `libnative-lib.so` exporting `get_flag()`, calling it dynamically returned "Root detected - flag unavailable". The solver loaded the `.so` into Ghidra and located the `check_root()` export called within `get_flag`. Instead of reverse-engineering the native decryption algorithm, the solver wrote a 5-line Frida script replacing `check_root` with `Interceptor.replace` to return 1, invoked `get_flag()`, and received `Hero{F1NAL_57EP_Y0U_KN0W_H0W_TO_R3V3R53_4NDR01D}`.

## Weak signals (single source — treat as hints, not rules)
- Look for visual color-camouflage tricks in Android vector drawable XML resources (`res/drawable/*.xml`) where foreground SVG paths match dynamic background colors. [ev: ff8049]
- Look for on-device machine learning models (e.g. decrypted MNN FlatBuffer files in `assets/`) and evaluate them using the vendor Python runtime with callback hooks rather than static graph parsing. [ev: a0a66d]
- Look for signed integer underflows in JNI memory-offset calculations (`clampedOffset`) allowing IPC/intent-driven arbitrary memory overwrites. [ev: 47c602]
- Look for password strings checked via immediate byte comparisons in Mach-O ARM64 binaries unlocking embedded inverted image payloads. [ev: 467425]
- Look for SQLite cache databases (`cache.db`) storing AES-GCM encrypted blobs with AAD headers where the key is assembled from a shuffled native string table. [ev: 64f78e]
