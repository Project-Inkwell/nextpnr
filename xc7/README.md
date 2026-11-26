# xc7

Project Inkwell's branch of nextpnr for the Xilinx 7-series: openXC7's
himbaechel `xilinx` uarch, its chipdb timed in every speed grade from
[Project Inkwell's xc7 timing database](https://github.com/Project-Inkwell/xc7)
instead of X-Ray's delays, and a blinky for the Numato Neso
(xc7a100tcsg324-1) through to its flash.

What this branch adds to openXC7's `main`:

- `himbaechel_dbgen/chip.py` writes a node's timing in the order nextpnr
  reads it, capacitance before resistance. With the order swapped, the load
  a node's resistance puts on each pip out of it is lost, and a chipdb timed
  with loads (as the xc7 database is) underestimates high-fanout nets.
- `examples/neso`: the Neso's blinky, its constraints, and `flash.py`, which
  writes a bitstream into the Neso's SPI flash over its FT2232H and boots it.
- `xc7/`: the environment it all builds in, and its Makefile.

## Building

`xc7/Containerfile` is everything but nextpnr: yosys v0.69, nextpnr's build
dependencies, prjxray-db (the Artix-7) at `$PRJXRAY_DB`, X-Ray's tools at
`$PRJXRAY`, and the xc7 timing database at `$XC7_TIMING`. The checkout is
mounted at `/src` and built there, so a change to nextpnr needs no new
image. It needs podman, and openXC7's `meta` submodule, which the chipdb's
generator reads:

    git clone -b xc7 https://github.com/Project-Inkwell/nextpnr.git
    cd nextpnr && git submodule update --init himbaechel/uarch/xilinx/meta

    xc7/run.sh                              a shell in it
    xc7/run.sh make -f xc7/Makefile         nextpnr-himbaechel with the
                                            xc7a100t's chipdb, timed, in
                                            build/xc7/
    xc7/run.sh make -f xc7/Makefile neso    the Neso's blinky through to
                                            build/xc7/neso/blinky.bit
    make -f xc7/Makefile neso-flash         into the Neso's flash, booted

A device without a directory in the timing database keeps X-Ray's delays;
`--device xc7a100tcsg324-1` picks the grade, `1`, from the part's suffix.

`neso-flash` runs on the host the Neso is plugged into, with libftdi's
Python bindings (`python3-ftdi1`) and access to its USB device (2a19:1005),
header P2 at its factory setting (the flash). The blinky's four outputs, on
header P5 pins 37 to 40, toggle at about 6, 3, 1.5 and 0.75 Hz from the
100 MHz oscillator, with VADJ (switch J3) at 2.5 V.
