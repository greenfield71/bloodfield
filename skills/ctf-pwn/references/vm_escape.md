# Custom VM & Interpreter Escapes: Deep-Dive Methodology

In 2025–2026 CTF competitions, authors increasingly deploy bespoke bytecode interpreters
and custom virtual machines (e.g. LattiaVM, Piet/Piet 2, modified Lua 5.5.0, and WebAssembly
sandboxes) to defeat automated analysis. The central vulnerability archetype in these targets
is **Out-of-Bounds (OOB) indexing from the virtual machine's operand stack into the native
host stack frame**, enabling leakless control flow hijacking.

---

## 1. The Anatomy of a Custom Virtual Machine

Most CTF bytecode interpreters declare their execution context as a native C struct located
either on the native thread stack or the heap:

```c
typedef struct {
    uint8_t   *bytecode;     /* Pointer to executable instruction stream */
    size_t     pc;           /* Program counter */
    int32_t    sp;           /* Virtual stack pointer / depth index */
    int32_t    stack[256];   /* Virtual operand stack array */
    int64_t    regs[8];      /* General-purpose virtual registers */
    uint32_t   flags;        /* Condition codes / VM state */
} VMState;
```

### Dispatch Loop Patterns
1. **Switch Dispatch**: A central loop around `switch (bytecode[pc++])` with cases for each opcode.
2. **Direct Threading / Computed Goto**: An array of `void *dispatch_table[256]` with `goto *dispatch_table[op]`.
3. **Function Pointer Jump Table**: An array of function pointers `void (*handlers[256])(VMState *)`.

In Ghidra/radare2, locate the main execution loop, identify the table of jump targets or handlers,
and document each opcode's stack delta (`pop_count`, `push_count`).

---

## 2. Memory Layout: The Virtual-to-Native Stack Boundary

When `VMState` or the VM's operand stack array is allocated as a local variable within a native
function (e.g., `vm_exec()` or `main()`), the virtual operand stack sits directly adjacent to
native stack variables, saved frame pointers (`saved_rbp`), and the native return address (`saved_rip`).

### Memory Layout Diagram (x86-64 Native Stack Frame)

```
Higher Addresses (Caller Stack Frame)
+-------------------------------------------------------------+
| ... Caller's Local Variables / Caller Saved Registers       |
+-------------------------------------------------------------+
| Native Return Address (saved RIP)                          |  <-- Primary Hijack Target
+-------------------------------------------------------------+
| Native Saved Frame Pointer (saved RBP)                     |  <-- Stack Pivot Target
+-------------------------------------------------------------+
| Native Compiler Stack Canary (if enabled)                  |
+-------------------------------------------------------------+
| Native Local Variables (e.g., loop counters, state flags)   |
+-------------------------------------------------------------+
| vm.sp (Virtual Stack Pointer / depth)                       |  <-- SP Aliasing Target
+-------------------------------------------------------------+
| vm.stack[255]                                               |
| vm.stack[254]                                               |
| ...                                                         |
| vm.stack[1]                                                 |
| vm.stack[0]                                                 |  <-- Lower Boundary
+-------------------------------------------------------------+
| Stale native stack data from previous libc / main calls     |  <-- Stale Pointer Leak Source
+-------------------------------------------------------------+
Lower Addresses (Top of Stack, RSP points here)
```

### Critical Boundaries
- **Positive Overflow (`vm.sp >= 256`)**:
  Accessing `vm.stack[256]` or beyond writes directly into `vm.sp` (if adjacent), the native
  canary, `saved_rbp`, and `saved_rip`.
- **Negative Underflow (`vm.sp < 0` or negative indexing)**:
  Accessing `vm.stack[-N]` reads or modifies memory allocated before `vm.stack`, including stale
  pointers left on the stack by `__libc_start_main`, runtime initialization, or previous functions.

---

## 3. Exploit Methodology 1: Stack Bounds Elision & SP Aliasing (LattiaVM)

### The Vulnerability Pattern
The VM implements stack operations without validating the upper boundary, or performs an
insufficient boundary check:

```c
/* Vulnerable handler: push without capacity check */
void op_push(VMState *vm, int32_t val) {
    vm->stack[vm->sp++] = val; /* Missing: if (vm->sp >= 256) error(); */
}

/* Vulnerable DUP: check against max_elements off by one */
void op_dup(VMState *vm) {
    int32_t val = vm->stack[vm->sp - 1];
    vm->stack[vm->sp++] = val; /* If sp == 256, writes into vm->sp! */
}
```

### Exploit Steps
1. **SP Aliasing**:
   - Push 256 values until `vm.sp == 256`.
   - The next push or `DUP` writes its operand directly into the memory location occupied by
     `vm.sp` itself.
   - By controlling the pushed value, you overwrite `vm.sp` with an arbitrary integer index.
2. **Relocating the Virtual Stack Pointer**:
   - Set `vm.sp` so that `vm.stack[vm.sp]` aliases `saved_rip` (e.g. index `258` or `260`
     depending on struct alignment and canary placement).
3. **Constrained R/W via SWAP / DUP**:
   - If direct arbitrary write opcodes are absent, use `SWAP` to exchange values between the
     relocated SP index and existing stack values.
   - Use `ADD` or `SUB` opcodes to adjust addresses in-place on the native stack without needing
     a full memory leak.
4. **Triggering Execution**:
   - Issue a VM halt / exit opcode. The native function returns, popping your crafted `saved_rip`
     into native `$rip`.

---

## 4. Exploit Methodology 2: Negative Indexing & Stack Pivoting (Piet / Piet 2)

### The Vulnerability Pattern
Interpreter operations like `roll` or `pop` check lower bounds incorrectly:

```c
/* Vulnerable roll handler in Piet interpreter */
void piet_roll(VMState *vm) {
    int32_t count = pop(vm);
    int32_t depth = pop(vm);
    if (depth <= 0) return; /* Checks depth <= 0, BUT fails to check depth <= vm->depth! */
    
    /* Result: index = vm->sp - depth becomes NEGATIVE! */
    int32_t val = vm->stack[vm->sp - depth];
    // ...
}
```

### Exploit Steps
1. **Negative Index Reading (Stale Pointer Recovery)**:
   - Drive the virtual stack index negative (`vm.stack[-K]`).
   - Read stale libc pointers (e.g. `__libc_start_main_ret` or `_IO_2_1_stdout_`) left on the
     native stack by earlier runtime execution.
   - In leakless environments, calculate relative offsets directly in VM registers or stack slots.
2. **Partial Overwrite of Saved RBP**:
   - Target the native `saved_rbp` located just before `saved_rip`.
   - Overwrite only the least-significant byte (1-byte write) or low 16 bits of `saved_rbp` to
     repoint RBP into the attacker-controlled VM operand stack buffer.
   - If ASLR randomizes the stack page, a 4-bit (1-nibble) brute force (1/16 chance) allows
     reliably landing RBP in your buffer.
3. **Stack Pivot Execution**:
   - When the interpreter function executes `leave; ret` (equivalent to `mov rsp, rbp; pop rbp; ret`),
     `$rsp` is shifted directly into your VM operand stack.
   - The subsequent `ret` pops the first gadget of your ROP chain from the VM stack.

---

## 5. Exploit Methodology 3: Bytecode Type Confusion & Tag Stripping (Lua 5.5.0)

### The Vulnerability Pattern
In modified Lua runtimes (e.g. UIUCTF Firefly):
1. The bytecode verifier stub (`luai_verifycode`) is gutted or left empty, allowing `string.dump`
   and `load()` of arbitrary raw bytecode.
2. Opcode execution handlers (such as `OP_FORLOOP` or custom instructions) lack type validation,
   while helper macros like `chgivalue` mutate values while preserving type tags.

```c
/* Lua TValue representation */
typedef struct {
    Value value_;
    lu_byte tt_;   /* Type tag: LUA_TNUMINT, LUA_TSTRING, LUA_TTABLE, etc. */
} TValue;
```

### Exploit Steps
1. **Construct Fake TString (Arbitrary Read)**:
   - Create a craftily misaligned integer or userdata whose type tag is coerced to `LUA_TSTRING`.
   - The `TString` pointer points to `(target_address - offsetof(TString, data))`.
   - Reading the string via Lua yields raw process memory at `target_address`.
2. **Construct Fake Table (Arbitrary Write)**:
   - Forge a `Table` structure whose node array or array slice points to target write destinations
     (e.g., GOT table, heap metadata, or function pointers).
   - Assigning `table[key] = val` performs an arbitrary memory write.
3. **Dynamic Linker GOT Hijacking**:
   - In Partial RELRO environments, overwrite `fclose@GOT` with `fflush`.
   - This keeps sensitive file buffers (e.g. `/flag.txt` read buffer) allocated in memory rather
     than closed and cleared, allowing subsequent extraction.

---

## 6. Exploit Methodology 4: WebAssembly / Host Boundary Confusion (Sparxie)

### Architecture
WebAssembly runtimes embedded in native hosts (Wasmtime, Wasmer, Emscripten/V8) isolate guest
linear memory (`wasm_memory`) from host memory, but bridge them via exported host imports.

### Attack Path
1. **Host Import Argument Smuggling**:
   - Locate host-imported functions (e.g., `env.sparxie_redeem(ptr, len)`).
   - If the host trusts guest pointers without validating bounds against linear memory limits,
     pass addresses outside linear memory to achieve host arbitrary read/write.
2. **Guest Deduplication / UAF**:
   - Exploit memory allocator bugs inside guest libc (e.g., chunk deduplication logic omitting
     metadata tags).
   - Corrupt WASM function table indices (`call_indirect`) to redirect control flow to unexpected
     guest export routines or trigger type confusion.

---

## 7. Leakless ROP Construction Cookbook

When PIE or ASLR is enabled and the VM provides no output/print instructions, construct a
compact **leakless ROP chain**:

### Technique A: Register Staging via Stale Stack Values
Stale libc pointers frequently populate registers (`RAX`, `RDX`, `RSI`) or native stack slots.
If `RAX` already points into libc:
```
pop rdi; ret
<offset to "/bin/sh">
add rdi, rax; ret
call system
```

### Technique B: Ultra-Compact 128-Byte Execve Chain
When payload space on the VM operand stack is severely constrained (e.g. L3akCTF LattiaVM):
```assembly
# Gadget 1: pop rax; ret
pop rax
<address_of_system>

# Gadget 2: mov rdi, rsp; call rax; followed by inline command
mov rdi, rsp
call rax
.ascii "pr f*\0"   # Executes "pr f*" (prints flag matching glob)
```
*Note: Using glob patterns like `pr f*` or `sh\0` fits into 8 bytes, eliminating the need
to locate or allocate a separate `/bin/sh` string pointer.*

### Technique C: Two-Byte Partial Overwrite of Saved RIP
- The lowest 12 bits of an address are never randomized by ASLR (page offset is constant).
- Overwriting only the lowest 2 bytes (`uint16_t`) of `saved_rip` redirects execution to any
  instruction in the same page (or 16 possible pages with a 4-bit brute force).
- Target a hidden `win()` function, an existing `call system` gadget, or a `one_gadget`.

---

## 8. GDB / Pwndbg Tracing Workflow for VM Escapes

When debugging a VM binary under GDB with pwndbg:

```bash
# 1. Break at the VM dispatch loop
pwndbg> b *0x401230

# 2. Set a hardware watchpoint on the VM stack pointer variable
pwndbg> watch *(int*)(0x7fffffffdf00 + 0x408)

# 3. Trace bytecode execution step-by-step
pwndbg> display/i $rip
pwndbg> display/16xw $rsp

# 4. Examine VM operand stack vs Native frame boundary
pwndbg> telescope $rsp 32
pwndbg> distance &vm.stack[255] $rbp

# 5. Check stack alignment before calling libc functions
# $rsp must end in 0x0 (16-byte aligned) immediately prior to 'call' instructions
pwndbg> print/x $rsp & 0xf
```
