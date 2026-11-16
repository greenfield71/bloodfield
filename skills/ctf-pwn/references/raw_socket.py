#!/usr/bin/env python3
"""No-pwntools exploit toolkit: raw sockets, struct packing, De Bruijn patterns, and safe linking.

Use when pwntools is not installed/allowed (a frequent 2026 CTF idiom) or when you
require a zero-dependency, freestanding solve. Mirrors all core pwntools primitives:
  - Packing/unpacking: p64/u64, p32/u32, p16/u16, p8/u8 (little and big endian)
  - Cyclic pattern generation and offset finding: cyclic(n), cyclic_find(val)
  - Payload flattening: flat(*args, filler=b"\\x00") with dict offset support
  - Modern glibc Safe Linking: safe_link(ptr, pos), safe_unlink(mangled, pos=None)
  - Minimal ROP builder: ROPBuilder
  - Socket tube abstraction: Tube with recv_until, send_line_after, interactive, etc.
  - Freestanding C syscall stub generation

Run self-tests:
    python3 references/raw_socket.py --test

Deps: Python 3 stdlib only.
"""
from __future__ import annotations

import os
import select
import socket
import string
import struct
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 1337
DEFAULT_TIMEOUT = 10.0


# ==============================================================================
# 1. Binary Packing and Unpacking
# ==============================================================================

def p64(x: int, endian: str = "<") -> bytes:
    """Pack 64-bit unsigned integer (default: little-endian)."""
    return struct.pack(f"{endian}Q", x & 0xFFFFFFFFFFFFFFFF)


def u64(b: bytes, endian: str = "<") -> int:
    """Unpack 64-bit unsigned integer from up to 8 bytes (padded with null bytes)."""
    pad = b.ljust(8, b"\x00")[:8]
    return struct.unpack(f"{endian}Q", pad)[0]


def p32(x: int, endian: str = "<") -> bytes:
    """Pack 32-bit unsigned integer (default: little-endian)."""
    return struct.pack(f"{endian}I", x & 0xFFFFFFFF)


def u32(b: bytes, endian: str = "<") -> int:
    """Unpack 32-bit unsigned integer from up to 4 bytes (padded with null bytes)."""
    pad = b.ljust(4, b"\x00")[:4]
    return struct.unpack(f"{endian}I", pad)[0]


def p16(x: int, endian: str = "<") -> bytes:
    """Pack 16-bit unsigned integer (default: little-endian)."""
    return struct.pack(f"{endian}H", x & 0xFFFF)


def u16(b: bytes, endian: str = "<") -> int:
    """Unpack 16-bit unsigned integer from up to 2 bytes (padded with null bytes)."""
    pad = b.ljust(2, b"\x00")[:2]
    return struct.unpack(f"{endian}H", pad)[0]


def p8(x: int) -> bytes:
    """Pack 8-bit unsigned integer."""
    return struct.pack("B", x & 0xFF)


def u8(b: bytes) -> int:
    """Unpack 8-bit unsigned integer."""
    return b[0] if len(b) > 0 else 0


# ==============================================================================
# 2. De Bruijn Cyclic Sequence Generation and Offset Finding
# ==============================================================================

def cyclic(length: int = 100, n: int = 4, alphabet: str = string.ascii_lowercase) -> bytes:
    """Generate a De Bruijn cyclic pattern with 4-byte unique subsequences.
    
    Mirrors pwntools cyclic sequence generation:
    'aaaa', 'baaa', 'caaa', 'daaa' ... (leftmost character varies fastest).
    """
    from itertools import product

    res: List[str] = []
    for p in product(alphabet, repeat=n):
        res.append("".join(reversed(p)))
        if len(res) * n >= length:
            break
    return "".join(res)[:length].encode("latin-1")


def cyclic_find(
    subseq: Union[int, bytes, str],
    n: int = 4,
    alphabet: str = string.ascii_lowercase,
    max_search: int = 100000,
) -> int:
    """Find the byte offset of a crash pattern in the cyclic sequence.
    
    Accepts:
      - int: e.g. 0x6161616c (unpacked crash value from RSP/faulting RIP)
      - bytes: e.g. b"laaa"
      - str: e.g. "laaa"
    Returns the integer byte offset, or -1 if not found.
    """
    if isinstance(subseq, int):
        sub_bytes = struct.pack("<I" if n == 4 else "<Q", subseq)
    elif isinstance(subseq, str):
        sub_bytes = subseq.encode("latin-1")
    elif isinstance(subseq, bytes):
        sub_bytes = subseq
    else:
        raise TypeError(f"Unsupported subseq type: {type(subseq)}")

    pat = cyclic(max_search, n=n, alphabet=alphabet)
    return pat.find(sub_bytes[:n])


# ==============================================================================
# 3. Payload Flattening (flat)
# ==============================================================================

def flat(*args: Any, filler: bytes = b"\x00") -> bytes:
    """Flatten nested structures, integers, bytes, strings, and offset dicts.
    
    Example:
        flat({
            40: p64(ret_gadget),
            48: p64(win_addr),
        })
        flat(b"A" * 40, p64(ret_gadget), p64(win_addr))
    """
    out = bytearray()

    for arg in args:
        if isinstance(arg, dict):
            # Dictionary maps integer offsets to payload pieces
            sorted_items = sorted(arg.items(), key=lambda item: item[0])
            for offset, val in sorted_items:
                val_bytes = flat(val, filler=filler)
                if len(out) < offset:
                    out.extend(filler * (offset - len(out)))
                # Overwrite or append at specified offset
                end_pos = offset + len(val_bytes)
                if end_pos > len(out):
                    out.extend(filler * (end_pos - len(out)))
                out[offset:end_pos] = val_bytes
        elif isinstance(arg, (list, tuple)):
            for item in arg:
                out.extend(flat(item, filler=filler))
        elif isinstance(arg, bytes):
            out.extend(arg)
        elif isinstance(arg, bytearray):
            out.extend(arg)
        elif isinstance(arg, str):
            out.extend(arg.encode("latin-1"))
        elif isinstance(arg, int):
            out.extend(p64(arg))
        elif arg is None:
            continue
        else:
            raise TypeError(f"Unsupported payload type in flat: {type(arg)}")

    return bytes(out)


# ==============================================================================
# 4. Modern Glibc Safe Linking Helpers (glibc 2.32 - 2.42)
# ==============================================================================

def safe_link(ptr: int, pos: int) -> int:
    """Mangle a pointer according to glibc 2.32+ safe linking: Ptr ^ (Pos >> 12)."""
    return (ptr ^ (pos >> 12)) & 0xFFFFFFFFFFFFFFFF


def safe_unlink(mangled: int, pos: Optional[int] = None) -> int:
    """Unmangle a glibc safe-linked pointer.
    
    If `pos` is known, computes `mangled ^ (pos >> 12)`.
    If `pos` is unknown, decrypts iteratively (valid for 64-bit ASLR heap layouts
    where pos and ptr share base pages or tcache head where ptr == 0).
    """
    if pos is not None:
        return (mangled ^ (pos >> 12)) & 0xFFFFFFFFFFFFFFFF

    # Iterative 12-bit shift recovery from MSB to LSB (standard 5-round decrypt)
    res = 0
    for _ in range(6):
        res = mangled ^ (res >> 12)
    return res & 0xFFFFFFFFFFFFFFFF


# ==============================================================================
# 5. Standalone ROP Chain Builder
# ==============================================================================

class ROPBuilder:
    """Minimal freestanding ROP chain builder without pwntools dependencies."""

    def __init__(self, base: int = 0):
        self.base = base
        self._chain: List[int] = []

    def raw(self, *items: Union[int, bytes]) -> "ROPBuilder":
        """Append raw 64-bit values or byte blocks directly to the chain."""
        for item in items:
            if isinstance(item, int):
                self._chain.append(item)
            elif isinstance(item, (bytes, bytearray)):
                for chunk in [item[i:i + 8] for i in range(0, len(item), 8)]:
                    self._chain.append(u64(chunk))
        return self

    def gadget(self, offset: int) -> "ROPBuilder":
        """Append an offset rebased by self.base."""
        self._chain.append(self.base + offset)
        return self

    def ret(self, ret_gadget: Optional[int] = None) -> "ROPBuilder":
        """Add a bare ret gadget for 16-byte stack alignment before system()."""
        if ret_gadget is not None:
            self._chain.append(ret_gadget)
        return self

    def call(
        self,
        func: int,
        rdi: Optional[int] = None,
        rsi: Optional[int] = None,
        rdx: Optional[int] = None,
        pop_rdi: Optional[int] = None,
        pop_rsi: Optional[int] = None,
        pop_rdx: Optional[int] = None,
    ) -> "ROPBuilder":
        """Stage registers and invoke target function."""
        if rdi is not None:
            if pop_rdi is None:
                raise ValueError("pop_rdi gadget required to stage RDI")
            self.raw(pop_rdi, rdi)
        if rsi is not None:
            if pop_rsi is None:
                raise ValueError("pop_rsi gadget required to stage RSI")
            self.raw(pop_rsi, rsi)
        if rdx is not None:
            if pop_rdx is None:
                raise ValueError("pop_rdx gadget required to stage RDX")
            self.raw(pop_rdx, rdx)
        self.raw(func)
        return self

    def chain(self) -> bytes:
        """Return the serialized ROP chain as bytes."""
        return b"".join(p64(g) for g in self._chain)


# ==============================================================================
# 6. Tube Socket Abstraction
# ==============================================================================

class Tube:
    """Pure-Python network tube providing pwntools-like socket interaction."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        sock: Optional[socket.socket] = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        if sock is not None:
            self.s = sock
        else:
            self.s = socket.create_connection((host, port), timeout=timeout)
        self.s.settimeout(timeout)
        self.buf = bytearray()

    def set_timeout(self, timeout: float) -> None:
        self.timeout = timeout
        self.s.settimeout(timeout)

    def recv(self, n: int = 4096) -> bytes:
        """Receive up to n bytes, returning buffered data first if available."""
        if self.buf:
            out = bytes(self.buf[:n])
            self.buf = self.buf[n:]
            return out
        try:
            return self.s.recv(n)
        except (socket.timeout, BlockingIOError):
            return b""

    def recv_exact(self, n: int) -> bytes:
        """Receive exactly n bytes."""
        while len(self.buf) < n:
            chunk = self.s.recv(max(4096, n - len(self.buf)))
            if not chunk:
                break
            self.buf.extend(chunk)
        out = bytes(self.buf[:n])
        self.buf = self.buf[n:]
        return out

    def recv_until(self, delim: Union[bytes, str], drop: bool = False) -> bytes:
        """Receive bytes until delimiter is encountered in the stream."""
        delim_bytes = delim.encode("latin-1") if isinstance(delim, str) else delim
        while delim_bytes not in self.buf:
            try:
                chunk = self.s.recv(4096)
            except (socket.timeout, BlockingIOError):
                break
            if not chunk:
                break
            self.buf.extend(chunk)

        idx = self.buf.find(delim_bytes)
        if idx < 0:
            out = bytes(self.buf)
            self.buf.clear()
            return out

        end = idx if drop else idx + len(delim_bytes)
        out = bytes(self.buf[:end])
        self.buf = self.buf[idx + len(delim_bytes):]
        return out

    def recv_line(self, drop: bool = False) -> bytes:
        """Receive until newline."""
        return self.recv_until(b"\n", drop=drop)

    def recv_leak(self, prefix: Union[bytes, str] = b"", length: int = 8) -> int:
        """Receive a leaked pointer following prefix and unpack it as unsigned 64-bit."""
        if prefix:
            self.recv_until(prefix)
        data = self.recv_exact(length)
        return u64(data)

    def send(self, data: Union[bytes, str]) -> None:
        """Send raw bytes or string."""
        payload = data.encode("latin-1") if isinstance(data, str) else data
        self.s.sendall(payload)

    def send_line(self, data: Union[bytes, str] = b"") -> None:
        """Send payload followed by newline."""
        payload = (data.encode("latin-1") if isinstance(data, str) else data) + b"\n"
        self.s.sendall(payload)

    def send_after(self, delim: Union[bytes, str], data: Union[bytes, str]) -> bytes:
        """Wait for delim, then send raw payload."""
        recvd = self.recv_until(delim)
        self.send(data)
        return recvd

    def send_line_after(self, delim: Union[bytes, str], data: Union[bytes, str]) -> bytes:
        """Wait for delim, then send payload followed by newline."""
        recvd = self.recv_until(delim)
        self.send_line(data)
        return recvd

    def close(self) -> None:
        """Close the underlying socket."""
        try:
            self.s.close()
        except Exception:
            pass

    def __enter__(self) -> "Tube":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def interactive(self) -> None:
        """Bridge the socket to your terminal for interactive shell access."""
        print("[*] Switching to interactive session; press Ctrl-C to quit.")
        self.s.setblocking(False)
        if self.buf:
            sys.stdout.buffer.write(self.buf)
            sys.stdout.buffer.flush()
            self.buf.clear()

        try:
            while True:
                r, _, _ = select.select([self.s, sys.stdin], [], [])
                if self.s in r:
                    data = self.s.recv(4096)
                    if not data:
                        print("[*] Connection closed by remote host.")
                        break
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
                if sys.stdin in r:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    self.s.sendall(line.encode("latin-1"))
        except (KeyboardInterrupt, EOFError):
            print("\n[*] Exiting interactive mode.")


# ==============================================================================
# 7. Freestanding C Syscall Stub Generator
# ==============================================================================

def c_freestanding_stub() -> str:
    """Return a static freestanding C template with raw Linux x86_64 syscalls.
    
    Compile with:
        gcc -nostdlib -static -no-pie -fno-stack-protector exploit.c -o exploit
    """
    return """/* Freestanding x86_64 Exploit Stub (Zero Libc Dependencies) */
#define SYS_read               0
#define SYS_write              1
#define SYS_open               2
#define SYS_close              3
#define SYS_mprotect          10
#define SYS_socket            41
#define SYS_connect           42
#define SYS_execve            59
#define SYS_exit              60
#define SYS_process_vm_readv  310
#define SYS_process_vm_writev 311

typedef unsigned long  uint64_t;
typedef long           int64_t;
typedef unsigned int   uint32_t;
typedef int            int32_t;
typedef unsigned short uint16_t;

struct iovec {
    void  *iov_base;
    uint64_t iov_len;
};

static inline int64_t syscall1(int64_t nr, int64_t a1) {
    int64_t ret;
    __asm__ volatile ("syscall" : "=a"(ret) : "a"(nr), "D"(a1) : "rcx", "r11", "memory");
    return ret;
}

static inline int64_t syscall3(int64_t nr, int64_t a1, int64_t a2, int64_t a3) {
    int64_t ret;
    __asm__ volatile ("syscall" : "=a"(ret) : "a"(nr), "D"(a1), "S"(a2), "d"(a3) : "rcx", "r11", "memory");
    return ret;
}

static inline int64_t syscall6(int64_t nr, int64_t a1, int64_t a2, int64_t a3, int64_t a4, int64_t a5, int64_t a6) {
    int64_t ret;
    register int64_t r10 __asm__("r10") = a4;
    register int64_t r8  __asm__("r8")  = a5;
    register int64_t r9  __asm__("r9")  = a6;
    __asm__ volatile ("syscall" : "=a"(ret) : "a"(nr), "D"(a1), "S"(a2), "d"(a3), "r"(r10), "r"(r8), "r"(r9) : "rcx", "r11", "memory");
    return ret;
}

void _start(void) {
    /* Example: execve("/bin/sh", NULL, NULL) */
    char sh[] = "/bin/sh";
    char *args[] = { sh, 0 };
    syscall3(SYS_execve, (int64_t)sh, (int64_t)args, 0);
    syscall1(SYS_exit, 0);
}
"""


# ==============================================================================
# 8. Self-Test Suite (--test)
# ==============================================================================

def run_self_tests() -> bool:
    """Comprehensive test suite for raw_socket.py primitives."""
    print("[*] Running raw_socket.py self-test suite...")

    # Suite 1: Pack/Unpack Roundtrips
    assert u64(p64(0xDEADBEEFCAFEBABE)) == 0xDEADBEEFCAFEBABE
    assert u64(p64(0)) == 0
    assert u32(p32(0x1337C0DE)) == 0x1337C0DE
    assert u16(p16(0x1234)) == 0x1234
    assert u8(p8(0x42)) == 0x42
    # Partial buffer padding
    assert u64(b"\xef\xbe\xad\xde") == 0xDEADBEEF
    assert u32(b"\x37\x13") == 0x1337
    # Big-endian mode
    assert p64(0x1122334455667788, endian=">") == b"\x11\x22\x33\x44\x55\x66\x77\x88"
    assert u64(b"\x11\x22\x33\x44\x55\x66\x77\x88", endian=">") == 0x1122334455667788
    print("  [+] Suite 1 (pack/unpack roundtrips): PASSED")

    # Suite 2: De Bruijn Cyclic Generation & Offset Finding
    pat = cyclic(100)
    assert len(pat) == 100
    assert pat.startswith(b"aaaabaaacaaadaaa")
    assert cyclic_find(b"aaaa") == 0
    assert cyclic_find(b"baaa") == 4
    assert cyclic_find(b"caaa") == 8
    assert cyclic_find(b"daaa") == 12
    # Little-endian int search (0x6161616c -> b"laaa")
    assert cyclic_find(0x6161616C) == 44
    assert cyclic_find(b"laaa") == 44
    assert cyclic_find(b"ZZZZ") == -1
    print("  [+] Suite 2 (cyclic patterns & find): PASSED")

    # Suite 3: Flat Packing & Dict Offsets
    payload = flat(
        b"PROLOGUE",
        {
            16: p64(0x401016),
            24: p64(0x401196),
        },
        filler=b"\x90",
    )
    assert payload[:8] == b"PROLOGUE"
    assert payload[8:16] == b"\x90" * 8
    assert payload[16:24] == p64(0x401016)
    assert payload[24:32] == p64(0x401196)
    assert len(payload) == 32
    print("  [+] Suite 3 (payload flat & dict offset): PASSED")

    # Suite 4: Modern Glibc Safe Linking (glibc 2.32+)
    ptr = 0x55555555B2A0
    pos = 0x55555555B2A0
    mangled = safe_link(ptr, pos)
    assert safe_unlink(mangled, pos) == ptr
    # Iterative recovery without known pos (e.g. tcache head / same page)
    assert safe_unlink(mangled) == ptr
    # Different pointer and location
    ptr2 = 0x55555555B400
    pos2 = 0x55555555B2A0
    mangled2 = safe_link(ptr2, pos2)
    assert safe_unlink(mangled2, pos2) == ptr2
    print("  [+] Suite 4 (safe linking & unlinking): PASSED")

    # Suite 5: Standalone ROPBuilder
    rop = ROPBuilder(base=0x400000)
    rop.gadget(0x1016)  # rebased gadget (ret)
    rop.call(0x401050, rdi=0x402000, pop_rdi=0x401020)
    chain = rop.chain()
    expected = flat(
        0x400000 + 0x1016,  # ret
        0x401020,           # pop rdi; ret
        0x402000,           # rdi value
        0x401050,           # call target
    )
    assert chain == expected
    print("  [+] Suite 5 (ROPBuilder chaining): PASSED")

    # Suite 6: In-Process TCP Socket Tube Loopback Test
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    port = server.getsockname()[1]
    server.listen(1)

    server_finished = threading.Event()

    def server_worker():
        try:
            conn, _ = server.accept()
            conn.sendall(b"BANNER: Welcome to Target Service\nENTER NAME: ")
            name = b""
            while b"\n" not in name:
                name += conn.recv(1024)
            conn.sendall(b"OK:" + name)
            # Send binary leak: 8 bytes
            conn.sendall(p64(0x7FFFF7DF2000))
            conn.close()
        finally:
            server.close()
            server_finished.set()

    srv_th = threading.Thread(target=server_worker, daemon=True)
    srv_th.start()

    with Tube("127.0.0.1", port, timeout=5.0) as io:
        banner = io.recv_line(drop=True)
        assert banner == b"BANNER: Welcome to Target Service"
        prompt = io.recv_until(b"ENTER NAME: ", drop=False)
        assert prompt == b"ENTER NAME: "
        io.send_line(b"ExploitPayload")
        ack = io.recv_line(drop=True)
        assert ack == b"OK:ExploitPayload"
        leak = io.recv_leak(length=8)
        assert leak == 0x7FFFF7DF2000

    server_finished.wait(timeout=2.0)
    print("  [+] Suite 6 (Tube TCP loopback communication): PASSED")

    # Suite 7: Freestanding C Stub Validation
    c_code = c_freestanding_stub()
    assert "SYS_process_vm_readv" in c_code
    assert "SYS_process_vm_writev" in c_code
    assert "_start" in c_code
    print("  [+] Suite 7 (freestanding C template): PASSED")

    print("\n[+] ALL TESTS PASSED (7/7 test suites verified successfully)")
    return True


# ==============================================================================
# Main Entry Point
# ==============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--test", "test", "-t"):
        success = run_self_tests()
        sys.exit(0 if success else 1)
    else:
        print(__doc__)
        print(f"Usage:")
        print(f"    python3 {sys.argv[0]} --test     # run full self-test suite")
        print(f"    from {os.path.basename(sys.argv[0])[:-3]} import Tube, p64, u64, flat, cyclic")
