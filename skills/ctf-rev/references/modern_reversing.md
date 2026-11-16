# Modern Reverse Engineering Reference (CTF 2025–2026+)

A comprehensive reference for cutting-edge CTF reverse engineering paradigms: Unicorn emulation-first workflows, exotic dispatchers (SIGILL/ud2 exception VMs, functional/lambda-calculus VMs), OLLVM/MBA deobfuscation, mobile (iOS Mach-O, Android JNI) and on-device machine learning (MNN FlatBuffers).

---

## 1. Emulation-First Reverse Engineering with Unicorn

### Rationale: Emulate over Reimplementation
In modern CTFs (e.g., UIUCTF `GODMODE//999`, Kali Team `Whispering Feather`), authors introduce subtle customizations into standard algorithms:
- Custom SHA-256 initialization vectors or altered padding.
- Non-standard ARX (Add-Rotate-Xor) rounds with customized constants.
- Bespoke AEAD / ChaCha20 variants.
Attempting to rewrite the algorithm in Python often wastes hours on tiny endianness or constant discrepancies. **The emulation-first approach runs the actual compiled machine code** in a controlled sandbox:
1. Map memory pages (code, stack, data, MMIO).
2. Write binary bytes extracted from the target (`objdump`, `dd`, or raw file read).
3. Set input arguments in architecture-specific ABI registers.
4. Execute the exact function range.
5. Extract output buffer / return register directly.

### Multi-Architecture Register Reference
| Architecture | Arg Registers (in order) | Return Register | Stack Pointer | Instruction Pointer |
| :--- | :--- | :--- | :--- | :--- |
| **x86-64 (System V)** | `RDI`, `RSI`, `RDX`, `RCX`, `R8`, `R9` | `RAX`, `RDX` | `RSP` | `RIP` |
| **ARM64 / AArch64** | `X0`, `X1`, `X2`, `X3`, `X4`, `X5`, `X6`, `X7` | `X0`, `X1` | `SP` | `PC` (`LR`/`X30` link) |

### Firmware ROM Mapping & Ranked Disk Replay
When given a raw firmware blob and an image disk (e.g. `GODMODE//999`):
```python
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_PROT_ALL
from unicorn.arm64_const import UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_SP

ROM_BASE = 0x00000000
RAM_BASE = 0x40000000
RAM_SIZE = 0x10000000

mu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
# Map ROM and load raw firmware
with open("firmware.bin", "rb") as f:
    firmware_data = f.read()
mu.mem_map(ROM_BASE, (len(firmware_data) + 0xFFF) & ~0xFFF, UC_PROT_ALL)
mu.mem_write(ROM_BASE, firmware_data)

# Map RAM and initialize stack
mu.mem_map(RAM_BASE, RAM_SIZE, UC_PROT_ALL)
mu.reg_write(UC_ARM64_REG_SP, RAM_BASE + 0x800000)

# Call real firmware AEAD routine at 0x1240
# int firmware_decrypt(void *out_buf, const void *in_buf, size_t len, const void *key)
mu.reg_write(UC_ARM64_REG_X0, RAM_BASE + 0x1000) # out
mu.reg_write(UC_ARM64_REG_X1, RAM_BASE + 0x2000) # in
# ... set up input data in RAM, run routine, read decrypted output ...
```

### Anti-Debug Bypassing in Unicorn
Hook instruction addresses where detection occurs and advance the instruction pointer:
```python
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RAX, UC_X86_REG_RIP

def bypass_hook(uc, address, size, user_data):
    if address == 0x401234: # Target check (e.g. ptrace / rdtsc / /proc check)
        uc.reg_write(UC_X86_REG_RAX, 0)     # Simulate success (no debugger)
        uc.reg_write(UC_X86_REG_RIP, 0x401240) # Skip to next instruction block

mu.hook_add(UC_HOOK_CODE, bypass_hook)
```

### Self-Decrypted RWX Payloads
In binaries with self-unpacking/decrypting stages (Kali `Whispering Feather`):
1. Identify the comparison or execution handoff address in Ghidra (e.g. `0x40069C`).
2. Run emulation up to that exact comparison instruction.
3. Read the stack or heap buffer where the decrypted data resides (e.g., `mu.mem_read(sp + 0x220, 64)`).
4. Ignore decoy flags embedded in static `.rodata`.

---

## 2. Exotic Virtual Machines & Dispatchers

### 2.1 SIGILL / `ud2` Exception-Driven VM (UIUCTF 2026 `vector-cache`)
Instead of an explicit `while(1) { switch(*pc++) }` loop, the program uses the Linux kernel signal subsystem as a stealth dispatcher:
1. The binary installs a signal handler for `SIGILL` (`sigaction(SIGILL, &act, NULL)`).
2. Every virtual instruction is triggered by an intentional illegal opcode: `ud2` (`0x0F 0x0B` on x86-64).
3. Immediate bytes following `ud2` encode the virtual opcode and operands:
   ```
   [0x0f, 0x0b] [opcode: 1 byte] [reg_dst: 1 byte] [reg_src / imm: 4 bytes]
   ```
4. Inside the `SIGILL` signal handler:
   ```c
   void sigill_handler(int sig, siginfo_t *info, void *ucontext) {
       ucontext_t *uc = (ucontext_t *)ucontext;
       uint8_t *pc = (uint8_t *)uc->uc_mcontext.gregs[REG_RIP];
       // pc points directly to 0x0F 0x0B
       uint8_t opcode = pc[2];
       uint8_t dst    = pc[3];
       // Execute virtual instruction...
       uc->uc_mcontext.gregs[REG_RIP] += instruction_length; // advance past ud2 + operands
   }
   ```
5. **Static Analysis Obstacle**: Ghidra and IDA mark `ud2` as `__builtin_trap()` and terminate basic block analysis, creating fragmented control flow graphs.
6. **Dynamic Tracing via GDB**:
   Configure GDB to pass `SIGILL` without stopping:
   ```gdb
   handle SIGILL nostop noprint pass
   set pagination off
   set follow-fork-mode child

   # Break at signal handler to log VM instructions:
   b *sigill_handler
   commands
     silent
     set $uc = (ucontext_t *)$rdx
     set $pc = (unsigned char *)$uc->uc_mcontext.gregs[16] # REG_RIP on Linux x86-64
     printf "VM_OP: 0x%02x, op1: 0x%02x, op2: 0x%02x\n", $pc[2], $pc[3], $pc[4]
     continue
   end
   ```

### 2.2 Functional & Lambda-Calculus Term VMs (UIUCTF 2026 `glyphs`)
Programs compiled from functional languages (Haskell, Scheme, custom compilers) evaluate a term graph instead of an imperative instruction stream:
- **Scott Encoding of Data**:
  - Boolean `True` = $\lambda t. \lambda f. t$
  - Boolean `False` = $\lambda t. \lambda f. f$
  - Pair $(a, b)$ = $\lambda f. f\ a\ b$
  - Tree node `Node(left, val, right)` = $\lambda leaf. \lambda node. node\ left\ val\ right$
- **Term Reducer**: The binary evaluates terms using graph reduction.
- **Solving Strategy**:
  1. Dump the term graph via GDB memory dumps (`dumpterm.gdb`).
  2. Implement an offline call-by-need (Thunk) reducer in Python:
     ```python
     class Thunk:
         def __init__(self, func):
             self.func = func
             self.evaluated = False
             self.val = None
         def get(self):
             if not self.evaluated:
                 self.val = self.func()
                 self.evaluated = True
             return self.val
     ```
  3. Probe individual bits: Send 1-hot bit vectors (`0x000...001`, `0x000...010`) to determine which input bit affects which branch of the term tree.

### 2.3 Bytecode Interpreters & Code-Cave Patching (UIUCTF 2026 `Veil of Evernight`)
Small bytecode VMs (200–500 bytes) embedded inside stripped ELFs often emit output (e.g. PNG files, license files) byte-by-byte:
1. Locate the byte emit handler (typically a `syscall` or memory store).
2. Patch a code cave or hook the `write` syscall in GDB to dump recovered fragment bytes:
   ```gdb
   catch syscall write
   commands
     silent
     dump memory /tmp/dump.bin $rsi ($rsi + $rdx)
     continue
   end
   ```

---

## 3. De-obfuscation Techniques

### 3.1 OLLVM Control-Flow Flattening (CFF)
OLLVM transforms a standard function control-flow graph into a flat state machine:
- **Dispatcher Block**: A large switch statement (`switch(state)`) enclosed in a `while(1)` loop.
- **Backbone Blocks**: Select and jump to relevant cases.
- **Relevant Blocks**: Original execution blocks, terminating in an assignment `state = NEXT_STATE` and jumping back to the dispatcher.

#### Automated Deflattening Workflow:
1. **Locate Dispatcher & State Variable**:
   The dispatcher is the basic block with the highest in-degree and out-degree. The state variable is loaded at the entry to the switch.
2. **Recover Transitions via Symbolic / Concrete Execution**:
   For each relevant block $B_i$:
   - Initialize execution at the entry of $B_i$.
   - Emulate execution until the state variable is overwritten or the dispatcher is reached.
   - Record $(B_i, state_{in}) \to (B_j, state_{out})$.
3. **Patch Control Flow**:
   Replace the jump from $B_i$ to the dispatcher with a direct `jmp B_j` (or `jcc` for conditional branches).

### 3.2 Mixed Boolean-Arithmetic (MBA) Simplification
Mixed Boolean-Arithmetic tangles simple integer arithmetic (`+`, `-`) with bitwise operations (`&`, `|`, `^`, `~`).

#### Linear MBA Truth-Table Solver
Every bitwise function of 2 variables can be expressed as a linear combination of the 4 basis functions: $\{1, x, y, x \land y\}$.
Use [`references/mba_deobfuscator.py`](mba_deobfuscator.py) to automatically simplify expressions:
```bash
python3 -I references/mba_deobfuscator.py --expr "(x ^ y) + 2 * (x & y)"
# Output: x + y
python3 -I references/mba_deobfuscator.py --expr "(x | y) - (x & ~y)"
# Output: y
```

#### CTF MBA Cheat-Sheet
| Obfuscated Expression | Canonical Equivalent |
| :--- | :--- |
| `(x ^ y) + 2 * (x & y)` | `x + y` |
| `(x \| y) + (x & y)` | `x + y` |
| `(x \| y) - (x & ~y)` | `y` |
| `(x \| y) - (~x & y)` | `x` |
| `(x ^ y) - 2 * (~x & y)` | `x - y` |
| `(x \| y) - (x ^ y)` | `x & y` |
| `(x & ~y) + (x & y)` | `x` |
| `(x & y) - (x \| y)` | `-(x ^ y)` |
| `(x ^ ~y) + 2 * (x \| y)` | `x - y - 1` |

### 3.3 Multi-Stage In-Memory Loaders (RITSEC 2026 `Buried Treasure`)
Malware-style CTF binaries unpack secondary and tertiary stages directly into anonymous memory:
- Syscalls: `memfd_create("payload", MFD_CLOEXEC)`, `write(fd, payload, size)`, `execveat(fd, ...)` or `/proc/self/fd/3`.
- **Extraction Recipe**:
  ```bash
  # Catch memfd writes and dump ELF binaries
  gdb -q ./chall
  (gdb) catch syscall memfd_create
  (gdb) run
  (gdb) catch syscall write
  (gdb) continue
  # Inspect buffer at $rsi
  (gdb) x/4bx $rsi
  # 0x7f 'E' 'L' 'F' -> carve with dump:
  (gdb) dump memory stage2.elf $rsi ($rsi + $rdx)
  ```

---

## 4. Mobile & On-Device ML Reverse Engineering

### 4.1 iOS ARM64 Mach-O Reversing (D^3CTF 2026 `PacMan`)
1. **Mach-O Structure**:
   Parse load commands (`LC_SEGMENT_64`):
   - `__TEXT`: Executable code, `__objc_methname` (selector strings), `__cstring`.
   - `__DATA`: Objective-C metadata (`__objc_const`, `__objc_data`).
2. **Swift & Objective-C Demangling**:
   ```bash
   # Demangle Swift function names
   swift-demangle < mangled_symbol
   # Inspect ObjC selectors and class names
   rabin2 -M ./MachO_Binary | grep -i 'flag\|verify\|score'
   ```
3. **Isolated Game-State VM Emulation**:
   Mach-O binaries often contain isolated state-machine validation routines independent of UI/Metal graphics. Map `LC_SEGMENT_64` sections into Unicorn ARM64, initialize registers, and run the VM steps directly to derive decryption keys (e.g., SplitMix64 PRNG seed -> RC4 key).

### 4.2 Android JNI + OLLVM (D^3CTF 2026 `D3LLVM`)
1. **Decompile APK**:
   ```bash
   jadx -d out app.apk
   ```
2. **Locate JNI Native Methods**:
   Check `System.loadLibrary("native-lib")` and `public native boolean checkFlag(...)`.
3. **Static vs Dynamic JNI Registration**:
   - **Static**: Exported as `Java_com_example_app_MainActivity_checkFlag`.
   - **Dynamic**: Registered inside `JNI_OnLoad` via `env->RegisterNatives(clazz, methods, count)`.
   - In Ghidra: Navigate to `JNI_OnLoad`, find the `JNINativeMethod` struct array:
     ```c
     struct JNINativeMethod {
         char *name;      // "checkFlag"
         char *signature; // "(Ljava/lang/String;)Z"
         void *fnPtr;     // Pointer to native implementation
     };
     ```
4. **Frida Dynamic Hooking**:
   Hook the native check function directly to capture plaintext arguments and return values:
   ```javascript
   Java.perform(function() {
       const nativeAddr = Module.findExportByName("libnative-lib.so", "Java_com_example_app_checkFlag");
       Interceptor.attach(nativeAddr, {
           onEnter: function(args) {
               console.log("[+] JNI checkFlag called with args:", args[2]);
           },
           onLeave: function(retval) {
               console.log("[+] checkFlag returned:", retval);
               retval.replace(1); // Force return true
           }
       });
   });
   ```

### 4.3 On-Device Machine Learning Reversing (MNN / TFLite / FlatBuffers)
Modern CTFs package validation logic inside embedded ML models:
1. **Encrypted Models**:
   The model file (`.mnn`, `.tflite`) inside `assets/` is often encrypted (e.g. AES-128-ECB).
2. **Runtime Key Derivation**:
   In `D3LLVM`, the AES decryption key is derived dynamically:
   - Compute **FNV-1a-64** hash over the runtime MNN 3.6.1 operator names string.
   - Seed a **SplitMix64** PRNG with this hash.
   - Generate 16 bytes for the AES-128 key.
3. **Model Inspection**:
   Once decrypted, inspect the model topology:
   ```bash
   # Visualize layers and weights
   netron model.mnn
   ```
4. **Decision Boundary Inversion**:
   Extract dense layer weights ($W$) and bias ($b$):
   $y = \text{Softmax}(W \cdot x + b)$.
   Solve for input $x$ that maximizes the target class logit via Z3 or linear algebra.

---

## 5. Mathematical Algorithmic Reductions

### 5.1 Power Towers (Tetration) Modulo $M$ (RITSEC 2026 `not_quite_optimal`)
Binaries implementing tetration ($a^{a^{\dots}}$) using arbitrary precision (GMP) and artificial `nanosleep` delays can be solved instantly in Python:
1. **Euler's Totient Reduction**:
   For any modulus $m$, $a^b \pmod m \equiv a^{(b \pmod{\phi(m)}) + \phi(m)} \pmod m$ (for $b \ge \phi(m)$).
2. **Mod 256 Evaluation**:
   Since flag characters are reduced mod 256, tetration exponents collapse after 4–5 iterations because $\phi(256) = 128, \phi(128) = 64, \phi(64) = 32, \phi(32) = 16, \phi(16) = 8, \phi(8) = 4, \phi(4) = 2, \phi(2) = 1$.
3. Compute in Python via built-in `pow(base, exp, mod)` without GMP.

### 5.2 Symmetric Block Cipher Magic Constants
Identify standard ciphers from disassembly constants instead of reversing rounds:
- **XTEA / TEA**: `0x9E3779B9` (delta), `-0x61c88647` (two's complement of delta).
- **RC5 / RC6**: `0xB7E15163` ($P32$), `0x9E3779B9` ($Q32$).
- **MD5**: `0x67452301`, `0xEFCDAB89`, `0x98BADCFE`, `0x10325476`.
- **SHA-256**: `0x6A09E667`, `0xBB67AE85`, `0x3C6EF372`, `0xA54FF53A`.
Once identified, decrypt hardcoded ciphertexts using standard Python libraries (`pycryptodome`).
