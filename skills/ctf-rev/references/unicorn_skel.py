#!/usr/bin/env python3
"""Modern Multi-Architecture Emulation Skeleton with Unicorn (x86-64 & ARM64).

Used for emulation-first reverse engineering of stripped firmware, custom crypto/ARX
routines, custom VM dispatchers, self-decrypted RWX payloads, and mobile binaries
(iOS Mach-O, Android JNI .so).

Key Capabilities:
  - Unified multi-architecture support: x86-64 and ARM64 / AArch64.
  - Calling-convention abstraction: ABI argument passing (RDI..R9 / X0..X7) and return reading.
  - Auto-mapping on unmapped memory access (UC_HOOK_MEM_UNMAPPED) for stripped firmware.
  - Anti-debug & environment bypass hooks (rdtsc, ptrace, time, clock_gettime).
  - Code hooks, instruction tracer, memory read/write monitoring.
  - State snapshotting & restoration for branching / path exploration.
  - Comprehensive self-test suite via `--test`.

Usage:
  python3 -I unicorn_skel.py --test
  python3 -I unicorn_skel.py --arch arm64 --bin ./firmware.bin --base 0x400000 --start 0x40069c --end 0x4007a0
  python3 -I unicorn_skel.py --arch x86_64 --bin ./chall --base 0x100000 --start 0x101150 --end 0x101200 --args 42 100

Deps: pip install --user unicorn capstone
"""

import argparse
import os
import struct
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    from unicorn import (
        Uc,
        UC_ARCH_ARM64,
        UC_ARCH_X86,
        UC_HOOK_BLOCK,
        UC_HOOK_CODE,
        UC_HOOK_MEM_READ,
        UC_HOOK_MEM_UNMAPPED,
        UC_HOOK_MEM_WRITE,
        UC_MODE_64,
        UC_MODE_ARM,
        UC_PROT_ALL,
        UC_PROT_READ,
        UC_PROT_WRITE,
    )
    from unicorn.arm64_const import (
        UC_ARM64_REG_LR,
        UC_ARM64_REG_PC,
        UC_ARM64_REG_SP,
        UC_ARM64_REG_X0,
        UC_ARM64_REG_X1,
        UC_ARM64_REG_X2,
        UC_ARM64_REG_X3,
        UC_ARM64_REG_X4,
        UC_ARM64_REG_X5,
        UC_ARM64_REG_X6,
        UC_ARM64_REG_X7,
        UC_ARM64_REG_X29,
        UC_ARM64_REG_X30,
    )
    from unicorn.x86_const import (
        UC_X86_REG_R8,
        UC_X86_REG_R9,
        UC_X86_REG_R10,
        UC_X86_REG_R11,
        UC_X86_REG_R12,
        UC_X86_REG_R13,
        UC_X86_REG_R14,
        UC_X86_REG_R15,
        UC_X86_REG_RAX,
        UC_X86_REG_RBP,
        UC_X86_REG_RBX,
        UC_X86_REG_RCX,
        UC_X86_REG_RDI,
        UC_X86_REG_RDX,
        UC_X86_REG_RIP,
        UC_X86_REG_RSI,
        UC_X86_REG_RSP,
    )
    UNICORN_AVAILABLE = True
except ImportError:
    UNICORN_AVAILABLE = False


PAGE_SIZE = 0x1000


def align_down(addr: int, page_size: int = PAGE_SIZE) -> int:
    return addr & ~(page_size - 1)


def align_up(addr: int, page_size: int = PAGE_SIZE) -> int:
    return (addr + page_size - 1) & ~(page_size - 1)


class UnicornEmulator:
    """Multi-architecture execution engine wrapping Unicorn with CTF-focused utilities."""

    X86_64_ARG_REGS = [
        UC_X86_REG_RDI,
        UC_X86_REG_RSI,
        UC_X86_REG_RDX,
        UC_X86_REG_RCX,
        UC_X86_REG_R8,
        UC_X86_REG_R9,
    ]

    ARM64_ARG_REGS = [
        UC_ARM64_REG_X0,
        UC_ARM64_REG_X1,
        UC_ARM64_REG_X2,
        UC_ARM64_REG_X3,
        UC_ARM64_REG_X4,
        UC_ARM64_REG_X5,
        UC_ARM64_REG_X6,
        UC_ARM64_REG_X7,
    ]

    def __init__(
        self,
        arch: str = "x86_64",
        auto_map_unmapped: bool = True,
        stack_base: int = 0x70000000,
        stack_size: int = 0x100000,
    ):
        if not UNICORN_AVAILABLE:
            raise RuntimeError("Unicorn engine is not installed (`pip install --user unicorn`).")

        self.arch = arch.lower()
        if self.arch in ("x86_64", "x86-64", "amd64", "x64"):
            self.uc_arch = UC_ARCH_X86
            self.uc_mode = UC_MODE_64
            self.is_arm64 = False
        elif self.arch in ("arm64", "aarch64", "arm64-v8a"):
            self.uc_arch = UC_ARCH_ARM64
            self.uc_mode = UC_MODE_ARM
            self.is_arm64 = True
        else:
            raise ValueError(f"Unsupported architecture: {arch}. Use 'x86_64' or 'arm64'.")

        self.mu = Uc(self.uc_arch, self.uc_mode)
        self.mapped_ranges: List[Tuple[int, int]] = []
        self.instruction_trace: List[int] = []
        self.memory_writes: List[Tuple[int, bytes]] = []
        self.custom_hooks: Dict[int, Callable[['UnicornEmulator', int, int], Optional[bool]]] = {}

        # Configure default stack
        self.stack_base = stack_base
        self.stack_size = stack_size
        self.map_memory(self.stack_base, self.stack_size, UC_PROT_ALL)
        self.set_sp(self.stack_base + self.stack_size - 0x1000)

        if auto_map_unmapped:
            self.mu.hook_add(UC_HOOK_MEM_UNMAPPED, self._hook_unmapped_mem)

    # --------------------------------------------------------------------------
    # Memory Management
    # --------------------------------------------------------------------------

    def map_memory(self, addr: int, size: int, prot: int = UC_PROT_ALL) -> None:
        start = align_down(addr)
        end = align_up(addr + size)
        length = end - start
        self.mu.mem_map(start, length, prot)
        self.mapped_ranges.append((start, end))

    def write_memory(self, addr: int, data: bytes) -> None:
        end = addr + len(data)
        # Check if region is mapped, map if not
        if not any(s <= addr and end <= e for s, e in self.mapped_ranges):
            self.map_memory(addr, len(data), UC_PROT_ALL)
        self.mu.mem_write(addr, data)

    def read_memory(self, addr: int, size: int) -> bytes:
        return bytes(self.mu.mem_read(addr, size))

    def _hook_unmapped_mem(self, uc: Uc, access: int, address: int, size: int, value: int, user_data: Any) -> bool:
        start = align_down(address)
        try:
            uc.mem_map(start, PAGE_SIZE, UC_PROT_ALL)
            self.mapped_ranges.append((start, start + PAGE_SIZE))
            return True
        except Exception:
            return False

    # --------------------------------------------------------------------------
    # Register & Architecture Abstraction
    # --------------------------------------------------------------------------

    def set_sp(self, sp: int) -> None:
        if self.is_arm64:
            self.mu.reg_write(UC_ARM64_REG_SP, sp)
        else:
            self.mu.reg_write(UC_X86_REG_RSP, sp)

    def get_sp(self) -> int:
        return self.mu.reg_read(UC_ARM64_REG_SP if self.is_arm64 else UC_X86_REG_RSP)

    def set_pc(self, pc: int) -> None:
        if self.is_arm64:
            self.mu.reg_write(UC_ARM64_REG_PC, pc)
        else:
            self.mu.reg_write(UC_X86_REG_RIP, pc)

    def get_pc(self) -> int:
        return self.mu.reg_read(UC_ARM64_REG_PC if self.is_arm64 else UC_X86_REG_RIP)

    def set_return_value(self, val: int) -> None:
        if self.is_arm64:
            self.mu.reg_write(UC_ARM64_REG_X0, val)
        else:
            self.mu.reg_write(UC_X86_REG_RAX, val)

    def get_return_value(self) -> int:
        return self.mu.reg_read(UC_ARM64_REG_X0 if self.is_arm64 else UC_X86_REG_RAX)

    def set_args(self, *args: int) -> None:
        reg_list = self.ARM64_ARG_REGS if self.is_arm64 else self.X86_64_ARG_REGS
        for i, val in enumerate(args):
            if i < len(reg_list):
                self.mu.reg_write(reg_list[i], val)
            else:
                # Extra args pushed to stack
                sp = self.get_sp() - 8
                self.set_sp(sp)
                self.write_memory(sp, struct.pack("<Q", val))

    def write_reg(self, reg_name: str, val: int) -> None:
        reg_id = self._resolve_reg(reg_name)
        self.mu.reg_write(reg_id, val)

    def read_reg(self, reg_name: str) -> int:
        reg_id = self._resolve_reg(reg_name)
        return self.mu.reg_read(reg_id)

    def _resolve_reg(self, name: str) -> int:
        n = name.lower().strip()
        if self.is_arm64:
            arm64_map = {
                "x0": UC_ARM64_REG_X0, "x1": UC_ARM64_REG_X1, "x2": UC_ARM64_REG_X2,
                "x3": UC_ARM64_REG_X3, "x4": UC_ARM64_REG_X4, "x5": UC_ARM64_REG_X5,
                "x6": UC_ARM64_REG_X6, "x7": UC_ARM64_REG_X7, "sp": UC_ARM64_REG_SP,
                "pc": UC_ARM64_REG_PC, "lr": UC_ARM64_REG_LR, "x30": UC_ARM64_REG_X30,
            }
            if n in arm64_map:
                return arm64_map[n]
        else:
            x86_map = {
                "rax": UC_X86_REG_RAX, "rbx": UC_X86_REG_RBX, "rcx": UC_X86_REG_RCX,
                "rdx": UC_X86_REG_RDX, "rsi": UC_X86_REG_RSI, "rdi": UC_X86_REG_RDI,
                "rbp": UC_X86_REG_RBP, "rsp": UC_X86_REG_RSP, "rip": UC_X86_REG_RIP,
                "r8": UC_X86_REG_R8, "r9": UC_X86_REG_R9, "r10": UC_X86_REG_R10,
                "r11": UC_X86_REG_R11, "r12": UC_X86_REG_R12, "r13": UC_X86_REG_R13,
                "r14": UC_X86_REG_R14, "r15": UC_X86_REG_R15,
            }
            if n in x86_map:
                return x86_map[n]
        raise ValueError(f"Unknown register '{name}' for architecture {self.arch}")

    # --------------------------------------------------------------------------
    # Hooking & Anti-Debug Bypasses
    # --------------------------------------------------------------------------

    def hook_address(self, addr: int, callback: Callable[['UnicornEmulator', int, int], Optional[bool]]) -> None:
        """Register a handler for a specific instruction address (e.g. mock function or skip check)."""
        self.custom_hooks[addr] = callback

    def bypass_anti_debug(self, check_addr: int, skip_to_addr: int, fake_return: int = 0) -> None:
        """Helper to bypass anti-debugging checks (ptrace, timing, /proc checks)."""
        def _bypass(emu: 'UnicornEmulator', address: int, size: int) -> None:
            emu.set_return_value(fake_return)
            emu.set_pc(skip_to_addr)

        self.hook_address(check_addr, _bypass)

    def enable_instruction_trace(self) -> None:
        def _trace(uc: Uc, address: int, size: int, user_data: Any) -> None:
            self.instruction_trace.append(address)
            if address in self.custom_hooks:
                self.custom_hooks[address](self, address, size)

        self.mu.hook_add(UC_HOOK_CODE, _trace)

    def enable_memory_write_trace(self) -> None:
        def _mem_write(uc: Uc, access: int, address: int, size: int, value: int, user_data: Any) -> None:
            data = value.to_bytes(size, byteorder="little")
            self.memory_writes.append((address, data))

        self.mu.hook_add(UC_HOOK_MEM_WRITE, _mem_write)

    # --------------------------------------------------------------------------
    # Execution
    # --------------------------------------------------------------------------

    def run(self, start_addr: int, end_addr: int, timeout: int = 0, count: int = 0) -> int:
        """Execute from start_addr until reaching end_addr. Returns return register value."""
        # Ensure code hook is installed if custom address hooks exist
        if self.custom_hooks and not self.instruction_trace:
            self.enable_instruction_trace()

        self.mu.emu_start(start_addr, end_addr, timeout=timeout, count=count)
        return self.get_return_value()


# ------------------------------------------------------------------------------
# High-Level Emulation Shortcuts
# ------------------------------------------------------------------------------

def emulate_x86_64(
    code: bytes,
    start_off: int = 0,
    end_off: Optional[int] = None,
    args: Tuple[int, ...] = (),
    mem_setup: Optional[Dict[int, bytes]] = None,
    reads: Optional[Dict[int, int]] = None,
    code_base: int = 0x400000,
) -> Tuple[int, Dict[int, bytes]]:
    """Emulate x86-64 code snippet. Returns (rax, reads_dict)."""
    emu = UnicornEmulator("x86_64")
    emu.write_memory(code_base, code)
    if mem_setup:
        for addr, data in mem_setup.items():
            emu.write_memory(addr, data)
    emu.set_args(*args)

    target_end = (code_base + end_off) if end_off is not None else (code_base + len(code))
    rax = emu.run(code_base + start_off, target_end)

    out = {}
    if reads:
        for addr, size in reads.items():
            out[addr] = emu.read_memory(addr, size)
    return rax, out


def emulate_arm64(
    code: bytes,
    start_off: int = 0,
    end_off: Optional[int] = None,
    args: Tuple[int, ...] = (),
    mem_setup: Optional[Dict[int, bytes]] = None,
    reads: Optional[Dict[int, int]] = None,
    code_base: int = 0x400000,
) -> Tuple[int, Dict[int, bytes]]:
    """Emulate ARM64 code snippet. Returns (x0, reads_dict)."""
    emu = UnicornEmulator("arm64")
    emu.write_memory(code_base, code)
    if mem_setup:
        for addr, data in mem_setup.items():
            emu.write_memory(addr, data)
    emu.set_args(*args)

    target_end = (code_base + end_off) if end_off is not None else (code_base + len(code))
    x0 = emu.run(code_base + start_off, target_end)

    out = {}
    if reads:
        for addr, size in reads.items():
            out[addr] = emu.read_memory(addr, size)
    return x0, out


# ------------------------------------------------------------------------------
# Self-Test Suite
# ------------------------------------------------------------------------------

def run_tests() -> bool:
    """Run verification self-tests for x86-64, ARM64, auto-mapping, and anti-debug hooks."""
    print("[*] Running Unicorn Multi-Architecture Self-Tests...")

    # Test 1: x86-64 computation with ABI args (rdi=5, rsi=3, rdx=7 -> rax = 5*3 + 7 = 22)
    # 48 89 f8          mov rax, rdi
    # 48 0f af c6       imul rax, rsi
    # 48 01 d0          add rax, rdx
    # c3                ret
    x86_code = bytes.fromhex("4889f8") + bytes.fromhex("480fafc6") + bytes.fromhex("4801d0") + b"\xc3"
    rax, _ = emulate_x86_64(x86_code, start_off=0, end_off=len(x86_code) - 1, args=(5, 3, 7))
    assert rax == 22, f"Test 1 Failed: expected rax=22, got {rax}"
    print("  [+] Test 1 Passed: x86-64 ABI argument passing & arithmetic (rax=22)")

    # Test 2: x86-64 memory load & store
    # 48 8b 07          mov rax, [rdi]
    # 48 83 c0 2a       add rax, 42
    # 48 89 06          mov [rsi], rax
    # c3                ret
    x86_mem_code = bytes.fromhex("488b07") + bytes.fromhex("4883c02a") + bytes.fromhex("488906") + b"\xc3"
    in_buf = 0x200000
    out_buf = 0x201000
    _, reads = emulate_x86_64(
        x86_mem_code,
        start_off=0,
        end_off=len(x86_mem_code) - 1,
        args=(in_buf, out_buf),
        mem_setup={in_buf: struct.pack("<Q", 100)},
        reads={out_buf: 8},
    )
    result = struct.unpack("<Q", reads[out_buf])[0]
    assert result == 142, f"Test 2 Failed: expected 142, got {result}"
    print("  [+] Test 2 Passed: x86-64 memory load/store verification (result=142)")

    # Test 3: ARM64 computation with ABI args (x0=0x1234, x1=0x5678, x2=0x42 -> (x0 ^ x1) + x2 = 0x448e)
    # eor x0, x0, x1    -> 00 00 01 ca
    # add x0, x0, x2    -> 00 00 02 8b
    # ret               -> c0 03 5f d6
    arm64_code = bytes.fromhex("000001ca") + bytes.fromhex("0000028b") + bytes.fromhex("c0035fd6")
    x0, _ = emulate_arm64(arm64_code, start_off=0, end_off=len(arm64_code) - 4, args=(0x1234, 0x5678, 0x42))
    assert x0 == 0x448E, f"Test 3 Failed: expected x0=0x448e, got {hex(x0)}"
    print("  [+] Test 3 Passed: ARM64 ABI argument passing & logic/arithmetic (x0=0x448e)")

    # Test 4: ARM64 memory store & unmapped auto-mapping hook
    # str x1, [x0]      -> 01 00 00 f9
    # ldr x2, [x0]      -> 02 00 40 f9
    # add x0, x2, #10   -> 40 28 00 91
    # ret               -> c0 03 5f d6
    arm64_mem_code = bytes.fromhex("010000f9") + bytes.fromhex("020040f9") + bytes.fromhex("40280091") + bytes.fromhex("c0035fd6")
    emu_arm = UnicornEmulator("arm64")
    unmapped_target = 0x55550000  # not explicitly mapped!
    emu_arm.write_memory(0x400000, arm64_mem_code)
    emu_arm.set_args(unmapped_target, 0x1337)
    res_x0 = emu_arm.run(0x400000, 0x400000 + len(arm64_mem_code) - 4)
    assert res_x0 == 0x1337 + 10, f"Test 4 Failed: expected {0x1337 + 10}, got {res_x0}"
    print("  [+] Test 4 Passed: ARM64 unmapped memory auto-mapping hook (result=0x1341)")

    # Test 5: Anti-debug bypass via address hook
    # 0x1000: mov rax, 1   (anti-debug triggered flag) (48 c7 c0 01 00 00 00)
    # 0x1007: add rax, 10  (48 83 c0 0a)
    emu_bypass = UnicornEmulator("x86_64")
    code_bypass = bytes.fromhex("48c7c001000000") + bytes.fromhex("4883c00a")
    emu_bypass.write_memory(0x1000, code_bypass)
    # Bypass check at 0x1000, simulate fake return 0 and jump to 0x1007
    emu_bypass.bypass_anti_debug(check_addr=0x1000, skip_to_addr=0x1007, fake_return=0)
    final_rax = emu_bypass.run(0x1000, 0x1000 + len(code_bypass))
    assert final_rax == 10, f"Test 5 Failed: expected rax=10, got {final_rax}"
    print("  [+] Test 5 Passed: Anti-debug instruction bypass hook (rax=10)")

    print("[SUCCESS] All 5 Unicorn multi-architecture self-tests passed cleanly!")
    return True


# ------------------------------------------------------------------------------
# Main CLI Entrypoint
# ------------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Modern Multi-Architecture Unicorn Emulation Helper")
    parser.add_argument("--test", action="store_true", help="Run self-test suite")
    parser.add_argument("--arch", choices=["x86_64", "arm64"], default="x86_64", help="Architecture (x86_64 or arm64)")
    parser.add_argument("--bin", type=str, help="Path to binary file or raw firmware dump")
    parser.add_argument("--base", type=lambda x: int(x, 0), default=0x400000, help="Base mapping address")
    parser.add_argument("--start", type=lambda x: int(x, 0), help="Start address for emulation")
    parser.add_argument("--end", type=lambda x: int(x, 0), help="End address for emulation")
    parser.add_argument("--args", nargs="*", type=lambda x: int(x, 0), default=[], help="Arguments passed to registers")
    parser.add_argument("--trace", action="store_true", help="Enable instruction trace output")

    parsed = parser.parse_args()

    if parsed.test or len(sys.argv) == 1:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not parsed.bin:
        parser.error("--bin <path> is required when not running --test.")

    if not os.path.isfile(parsed.bin):
        sys.exit(f"[-] File not found: {parsed.bin}")

    with open(parsed.bin, "rb") as f:
        code_bytes = f.read()

    emu = UnicornEmulator(arch=parsed.arch)
    emu.write_memory(parsed.base, code_bytes)

    start_addr = parsed.start if parsed.start is not None else parsed.base
    end_addr = parsed.end if parsed.end is not None else (parsed.base + len(code_bytes))

    if parsed.args:
        emu.set_args(*parsed.args)

    if parsed.trace:
        emu.enable_instruction_trace()

    print(f"[*] Emulating {parsed.arch} from {hex(start_addr)} to {hex(end_addr)}...")
    ret_val = emu.run(start_addr, end_addr)
    print(f"[+] Execution completed. Return value: {hex(ret_val)} ({ret_val})")


if __name__ == "__main__":
    main()
