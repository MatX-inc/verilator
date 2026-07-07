// DESCRIPTION: Verilator: Verilog Test module
//
// This file ONLY is placed under the Creative Commons Public Domain.
// SPDX-FileCopyrightText: 2026 Wilson Snyder
// SPDX-License-Identifier: CC0-1.0

interface Intf;
   logic [3:0] value;
endinterface

module Leaf (
   input clk,
   output logic [7:0] cnt
);
   always @(posedge clk) cnt <= cnt + 8'd1;
endmodule

module MidNoInline (
   input clk,
   output wire [7:0] out
);
   /* verilator no_inline_module */
   wire [7:0] c0;
   wire [7:0] g0;
   wire [7:0] g1;
   Leaf u_leaf (.clk(clk), .cnt(c0));
   for (genvar g = 0; g < 2; ++g) begin : gen_blk
      wire [7:0] gcnt;
      Leaf u_gleaf (.clk(clk), .cnt(gcnt));
   end
   assign g0 = gen_blk[0].gcnt;
   assign g1 = gen_blk[1].gcnt;
   assign out = c0 ^ g0 ^ g1;
endmodule

module ParamMod #(
   parameter W = 8
) (
   input clk,
   output logic [W-1:0] value
);
   always @(posedge clk) value <= value + 1;
endmodule

module t (
   input clk
);
   wire [7:0] o;
   wire [15:0] pv;
   int cyc = 0;

   MidNoInline u_mid (.clk(clk), .out(o));
   ParamMod #(.W(16)) u_param (.clk(clk), .value(pv));
   Intf the_intf ();

   always @(posedge clk) begin
      cyc <= cyc + 1;
      the_intf.value <= cyc[3:0];
      if (cyc > 10) begin
         if (o == 8'hff && pv == 16'hffff) $write("impossible\n");
         $write("*-* All Finished *-*\n");
         $finish;
      end
   end
endmodule
