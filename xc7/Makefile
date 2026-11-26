# What the xc7 branch builds, in its environment (xc7/run.sh):
#
#   xc7/run.sh make -f xc7/Makefile        nextpnr-himbaechel with the chipdbs
#                                          of DEVICES, timed in every speed
#                                          grade from Project Inkwell's xc7
#                                          database (XC7_TIMING), in build/xc7
#   xc7/run.sh make -f xc7/Makefile neso   the Numato Neso's blinky
#                                          (xc7a100tcsg324-1, examples/neso)
#                                          through to a bitstream
#   make -f xc7/Makefile neso-flash        writes that bitstream into the
#                                          Neso's SPI flash and boots it: on
#                                          the host the Neso is plugged into,
#                                          with libftdi's Python bindings
BUILD := build/xc7
JOBS := $(shell nproc)
DEVICES := xc7a100t
NESO := himbaechel/uarch/xilinx/examples/neso

nextpnr:
	cmake -S . -B $(BUILD) -G Ninja -DARCH=himbaechel -DHIMBAECHEL_UARCH=xilinx \
		-DHIMBAECHEL_XILINX_DEVICES="$(DEVICES)" -DHIMBAECHEL_PRJXRAY_DB=$(PRJXRAY_DB) \
		-DHIMBAECHEL_XILINX_TIMING=$(XC7_TIMING) -DBUILD_PYTHON=OFF -DCMAKE_BUILD_TYPE=Release
	cmake --build $(BUILD) -j $(JOBS)

# Its files land in build/xc7/neso/, nextpnr's timing report among them.
neso: nextpnr
	mkdir -p $(BUILD)/neso
	yosys -q -p "synth_xilinx -flatten -abc9 -nobram -arch xc7 -top top; write_json $(BUILD)/neso/blinky.json" $(NESO)/blinky.v
	$(BUILD)/nextpnr-himbaechel --device xc7a100tcsg324-1 -o xdc=$(NESO)/neso.xdc --json $(BUILD)/neso/blinky.json \
		-o fasm=$(BUILD)/neso/blinky.fasm --router router2 --report $(BUILD)/neso/report.json
	himbaechel/uarch/xilinx/examples/bitgen_xray.sh xc7a100tcsg324-1 $(BUILD)/neso/blinky.fasm $(BUILD)/neso/blinky.bit
	ls -l $(BUILD)/neso/blinky.bit

# Header P2 at its factory setting (the flash); needs access to USB 2a19:1005.
neso-flash:
	test -f $(BUILD)/neso/blinky.bit || { echo "no $(BUILD)/neso/blinky.bit: xc7/run.sh make -f xc7/Makefile neso first"; exit 1; }
	python3 $(NESO)/flash.py write $(BUILD)/neso/blinky.bit

.PHONY: nextpnr neso neso-flash
