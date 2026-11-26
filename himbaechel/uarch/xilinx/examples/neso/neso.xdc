# Numato Neso (xc7a100tcsg324): the 100 MHz oscillator on CLK1 (F4, bank 35 at
# VADJ, set by switch J3; here 2.5 V), and header P5 pins 37, 38, 39 and 40
# (bank 14, 3.3 V).
set_property PACKAGE_PIN F4 [get_ports clk]
set_property IOSTANDARD LVCMOS25 [get_ports clk]
set_property PACKAGE_PIN L18 [get_ports {blink[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {blink[0]}]
set_property PACKAGE_PIN M18 [get_ports {blink[1]}]
set_property IOSTANDARD LVCMOS33 [get_ports {blink[1]}]
set_property PACKAGE_PIN R12 [get_ports {blink[2]}]
set_property IOSTANDARD LVCMOS33 [get_ports {blink[2]}]
set_property PACKAGE_PIN R13 [get_ports {blink[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {blink[3]}]
