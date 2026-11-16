# Modern Libc & Musl Exploitation Matrix (2025–2026)

Modern Linux CTF challenges have largely moved beyond legacy heap attacks (`__free_hook`,
unsorted bin attack). Glibc versions **2.34 through 2.42** and **musl 1.2.5** enforce strict
mitigations that require modern exploitation primitives.

---

## 1. Glibc Version Mitigation Matrix

| Glibc Version | Safe Linking | Hook Pointers (`__free_hook`) | Primary Heap Target | Relocation Protections |
| :--- | :--- | :--- | :--- | :--- |
| **2.31** | No | Present (`__free_hook`, `__malloc_hook`) | Hook overwrite via tcache poisoning | Partial / Full RELRO |
| **2.32–2.33** | **Yes** (`ptr ^ (pos >> 12)`) | Present | Hook overwrite + Safe Linking bypass | Full RELRO |
| **2.34** | **Yes** | **REMOVED** | `_IO_FILE` FSOP, `__exit_funcs` | Full RELRO |
| **2.35–2.41** | **Yes** | **REMOVED** | House of Apple 2, House of Emma | Pointer Guard / FSOP |
| **2.42** | **Yes** | **REMOVED** | House of Apple 2 / `_IO_wfile_jumps`, `tls_dtor_list` | Thread Arena changes, Full RELRO |
| **musl 1.2.5** | N/A (no tcache) | **Never existed** | Embedded `FILE->write` function pointer | mallocng metadata validation |

---

## 2. Glibc 2.32–2.42: Safe Linking Mathematics

In glibc 2.32+, tcache and fastbin forward pointers (`fd`) are protected using Safe Linking:
```c
#define PROTECT_PTR(pos, ptr)  ((void *) (((size_t)(pos) >> 12) ^ (size_t)(ptr)))
#define REVEAL_PTR(ptr)         /* Iterative XOR decryption */
```

### Mathematical Properties & Bypasses
1. **Head of Bin Leak (Zero Pointer)**:
   - When a bin is empty and the first chunk is inserted, its forward pointer `ptr` is `NULL` (`0`).
   - The stored mangled value is: `0 ^ (pos >> 12) = (pos >> 12)`.
   - Therefore, reading the `fd` of the single chunk in a tcache bin leaks the **heap base page address** directly!
2. **Deterministic Unmangling (Iterative XOR)**:
   - In 64-bit architectures with standard ASLR, the upper bits (bits 40–63) of `pos >> 12` are 0.
   - The top 12 bits of `mangled` are the unmasked top 12 bits of `ptr`.
   - Iteratively XORing 12-bit windows recovers the full original pointer without knowing `pos`:
     ```python
     def safe_unlink(mangled: int) -> int:
         res = 0
         for _ in range(6):
             res = mangled ^ (res >> 12)
         return res & 0xFFFFFFFFFFFFFFFF
     ```
3. **Arbitrary Chunk Forgery**:
   - To forge a tcache chunk pointing to arbitrary target address `TARGET`:
     ```python
     forged_fd = TARGET ^ (chunk_addr >> 12)
     ```

---

## 3. Glibc 2.34–2.42: FSOP (House of Apple 2)

Since `__free_hook` and `__malloc_hook` were completely removed in glibc 2.34, File Stream
Oriented Programming (FSOP) via `_IO_FILE` structure corruption is the standard method to
hijack execution on modern glibc.

### The Mechanism
In glibc 2.35–2.42, `_IO_wfile_jumps` provides a clean code execution primitive when
`_IO_wdoallocbuf` calls `_wide_data->_wide_vtable->__doallocate`:

```
_IO_wfile_overflow -> _IO_wdoallocbuf -> _wide_data->_wide_vtable->__doallocate(fp)
```

### House of Apple 2 Exploit Recipe
Construct a fake `FILE` structure at a known address (on heap or BSS):
1. **`fp->_flags`**: Set to `0x68732020` (ASCII `"  sh"`) or `0` depending on triggering function.
2. **`fp->_mode`**: Set to `> 0` (e.g. `1`) to force wide character processing.
3. **`fp->_IO_write_base`**: Set to `0`.
4. **`fp->_IO_write_ptr`**: Set to `1` (ensures `_IO_write_ptr > _IO_write_base`).
5. **`fp->_wide_data`**: Point to a controlled fake `struct _IO_wide_data`.
6. **`fake_wide_data->_IO_write_base`**: Set to `0`.
7. **`fake_wide_data->_IO_write_ptr`**: Set to `1`.
8. **`fake_wide_data->_wide_vtable`**: Point to a controlled table where `__doallocate` (offset `0x68`) contains `system`.
9. **`fp->vtable`**: Point to `_IO_wfile_jumps` (found in libc rodata).
10. **Trigger**:
    - Call `exit()` (iterates `_IO_list_all`).
    - Or call `puts()`, `fputs()`, `fclose()` on the corrupted `FILE` pointer.
    - Result: `system("  sh")` is executed.

---

## 4. Glibc Pointer Guard: `tls_dtor_list` and `__exit_funcs`

When attacking process exit handlers without a full `FILE` structure:
- Modern glibc protects exit function pointers and thread-local destructors using a pointer
  guard stored in Thread Local Storage (`fs:[0x30]` on x86-64).
- Formula: `mangled = ROL64(target_func ^ fs:[0x30], 0x11)`.
- If an arbitrary read can leak the TLS pointer guard (or if TLS is located at a predictable
  offset from libc base), you can forge entries in `tls_dtor_list` to call `system("/bin/sh")`
  with attacker arguments upon normal `exit()`.

---

## 5. Musl Libc 1.2.5 Exploitation

Musl libc differs fundamentally from Glibc. It does not use `dlmalloc`/`ptmalloc`, has no
tcache, and has completely different internal structures.

### The Allocator: mallocng
- Introduced in musl 1.2.0, `mallocng` organizes memory into size classes, groups, and slabs.
- All chunk headers reside in-band or out-of-band with strict validation checks.
- Traditional heap poisoning (fastbin/tcache duplicate frees) will abort immediately.

### Primary Target: Musl `FILE` Structure Function Pointers
Unlike Glibc (which uses an external `vtable` pointer validated by `_IO_vtable_check`),
**Musl Libc embeds function pointers directly inside each `FILE` structure**:

```c
/* Musl struct _IO_FILE definition */
struct _IO_FILE {
    unsigned flags;
    unsigned char *rpos, *rend;
    int (*close)(FILE *);
    unsigned char *wend, *wpos;
    unsigned char *mustbezero_1;
    unsigned char *wbase;
    size_t (*read)(FILE *, unsigned char *, size_t);
    size_t (*write)(FILE *, const unsigned char *, size_t); /* DIRECT FUNCTION POINTER! */
    off_t (*seek)(FILE *, off_t, int);
    unsigned char *buf;
    size_t buf_size;
    FILE *prev, *next;
    int fd;
    // ...
};
```

### Exploit Methodology on Musl 1.2.5
1. **Direct Pointer Overwrite**:
   - `stdout->write` is located at offset `+0x28` (or `+0x48` depending on architecture/build).
   - There is **no pointer encryption, no canary, and no vtable validation check**.
   - Overwrite `stdout->write` with the address of `system` or a target function.
2. **Argument Delivery**:
   - When `printf()`, `puts()`, or `exit()` flushes `stdout`, it invokes:
     ```c
     f->write(f, f->wbase, f->wpos - f->wbase);
     ```
   - Notice that the first argument (`RDI` on x86-64) passed to `write` is `f` (the `FILE *` itself!).
   - Place `"/bin/sh\0"` at the beginning of the `stdout` buffer (offset `0x00`).
   - Calling `exit()` or triggering any output executes `system("/bin/sh")` directly!

### RWX Module Mapping & Single-Byte Patch Widening
In modular musl binaries (e.g. L3akCTF Bosh):
- Shell extensions or dynamically loaded modules may be mapped with `RWX` permissions.
- **Instruction Patch Widening**: A constrained 1-byte opcode write can transform an instruction:
  - Byte `0x88` (`mov byte ptr [rdi], cl`) patched to `0x89` (`mov dword ptr [rdi], ecx`).
  - This immediately upgrades a constrained 1-byte write into a 4-byte arbitrary write primitive.
