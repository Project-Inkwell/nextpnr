// Four outputs toggling at about 6, 3, 1.5 and 0.75 Hz from the 100 MHz
// oscillator: an LED, a multimeter or a scope on header P5 shows them.
module top (input clk, output [3:0] blink);
    reg [26:0] count = 0;
    always @(posedge clk) count <= count + 1'b1;
    assign blink = count[26:23];
endmodule
