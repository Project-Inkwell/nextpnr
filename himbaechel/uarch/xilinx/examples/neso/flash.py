"""The Numato Neso's SPI flash through its FT2232H, channel B, with header P2
set to the flash (factory): BDBUS0 SCK, 1 MOSI, 2 MISO, 3 CS#, and BDBUS7
driving PROGRAM_B through an inverter (U11), so BDBUS7 high holds the FPGA in
reset and off the flash's pins. Releasing it lets the FPGA load from flash.

    flash.py id
    flash.py write <file.bit>          erase, program, verify, then boot
"""
import sys
import time

import ftdi1 as ftdi

VID, PID = 0x2A19, 0x1005
DIR = 0x8B  # SCK, MOSI, CS#, BDBUS7 out; MISO in
IDLE, SELECT = 0x88, 0x80  # CS# high / low, BDBUS7 high (FPGA held)


class Flash:
    def __init__(self):
        self.ctx = ftdi.new()
        ftdi.set_interface(self.ctx, ftdi.INTERFACE_B)
        if ftdi.usb_open(self.ctx, VID, PID) < 0:
            sys.exit("open: " + ftdi.get_error_string(self.ctx))
        ftdi.usb_reset(self.ctx)
        ftdi.set_latency_timer(self.ctx, 1)
        ftdi.set_bitmode(self.ctx, 0, ftdi.BITMODE_RESET)
        ftdi.set_bitmode(self.ctx, 0, ftdi.BITMODE_MPSSE)
        ftdi.tcioflush(self.ctx)
        # 60 MHz base, no divide-by-5, no adaptive or 3-phase clocking: 10 MHz.
        self.send(bytes([0x8A, 0x97, 0x8D, 0x86, 2, 0, 0x80, IDLE, DIR]))
        time.sleep(0.01)

    def send(self, data):
        if ftdi.write_data(self.ctx, data) != len(data):
            sys.exit("write: " + ftdi.get_error_string(self.ctx))

    def receive(self, n):
        out = b""
        deadline = time.time() + 5
        while len(out) < n and time.time() < deadline:
            ret, chunk = ftdi.read_data(self.ctx, n - len(out))
            if ret < 0:
                sys.exit("read: " + ftdi.get_error_string(self.ctx))
            out += chunk[:ret]
        if len(out) < n:
            sys.exit(f"read: {len(out)} of {n} bytes")
        return out

    def command(self, out, n_in=0):
        """CS# low, clock `out` then `n_in` bytes in, CS# high (SPI mode 0)."""
        cmd = bytes([0x80, SELECT, DIR])
        cmd += bytes([0x11, (len(out) - 1) & 0xFF, (len(out) - 1) >> 8]) + out
        if n_in:
            cmd += bytes([0x20, (n_in - 1) & 0xFF, (n_in - 1) >> 8])
        cmd += bytes([0x80, IDLE, DIR, 0x87])
        self.send(cmd)
        return self.receive(n_in) if n_in else b""

    def wait(self):
        while self.command(b"\x05", 1)[0] & 1:
            pass

    def read(self, addr, n):
        out = b""
        while len(out) < n:
            k = min(0x10000, n - len(out))
            a = addr + len(out)
            out += self.command(bytes([0x03, a >> 16, (a >> 8) & 0xFF, a & 0xFF]), k)
        return out

    def release(self):
        """BDBUS7 low: PROGRAM_B released, the FPGA loads from flash."""
        self.send(bytes([0x80, 0x08, DIR]))
        time.sleep(0.01)
        ftdi.set_bitmode(self.ctx, 0, ftdi.BITMODE_RESET)
        ftdi.usb_close(self.ctx)


def bitstream(path):
    """A .bit's configuration data: from the sync preamble (FF..FF AA995566)."""
    data = open(path, "rb").read()
    sync = data.find(b"\xaa\x99\x55\x66")
    start = sync
    while start > 0 and data[start - 1] == 0xFF:
        start -= 1
    return data[start:]


def main():
    f = Flash()
    jedec = f.command(b"\x9f", 3)
    print("JEDEC id %02x %02x %02x" % tuple(jedec))
    if sys.argv[1] == "write":
        data = bitstream(sys.argv[2])
        size = (len(data) + 0xFFFF) & ~0xFFFF
        print(f"{len(data)} bytes, erasing {size >> 16} blocks of 64 KiB")
        for a in range(0, size, 0x10000):
            f.command(b"\x06")
            f.command(bytes([0xD8, a >> 16, (a >> 8) & 0xFF, 0]))
            f.wait()
        for a in range(0, len(data), 256):
            f.command(b"\x06")
            f.command(bytes([0x02, a >> 16, (a >> 8) & 0xFF, 0]) + data[a:a + 256])
            f.wait()
        back = f.read(0, len(data))
        if back != data:
            first = next(i for i in range(len(data)) if back[i] != data[i])
            sys.exit(f"verify failed at 0x{first:06x}")
        print("verified")
    f.release()


main()
