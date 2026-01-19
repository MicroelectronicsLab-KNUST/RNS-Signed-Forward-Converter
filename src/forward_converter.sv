module forward_converter #(
    parameter integer N = 4  // Bit width parameter
) (
    input  signed [3*N-1:0] input_num,  // Signed 3n-bit input
    output [N-1:0] r0,                  // Residue mod 2^n
    output [N-1:0] r_minus1,            // Residue mod 2^n - 1
    output [N:0] r1                     // Residue mod 2^n + 1 (widened to N+1 bits)
);
    // Bit-slicing
    wire [N-1:0] N0 = input_num[N-1:0];                   // Low unsigned
    wire [N-1:0] N1 = input_num[2*N-1:N];                 // Middle unsigned
    wire signed [N-1:0] N2 = input_num[3*N-1:2*N];        // High signed
    // r0 = N0 (direct)
    assign r0 = N0;
    // r_{-1} = |N2 + N1 + N0| mod (2^n - 1)
  wire signed [N+2:0] S = N2 + $signed({1'b0,N1}) + $signed({1'b0,N0});  // Sum with signed arithmetic
    wire signed [N+1:0] mod_m1 = (1 << N) - 1;                              // 2^n - 1
    wire cmp1_m1 = (S < 0);                                                 // Flag for range 1
    wire cmp2_m1 = (S < mod_m1);                                            // Flag for range 1+2
    wire cmp3_m1 = (S < 2*mod_m1);                                          // Flag for range 1+2+3
    wire [2:0] flags_m1 = {cmp1_m1, cmp2_m1, cmp3_m1};                     // 3-bit flag vector
    reg [N:0] r_minus1_reg;
    always @(*) begin
        case (flags_m1)
            3'b111: r_minus1_reg = S + mod_m1;                              // Range 1: S < 0 → add mod_m1
            3'b011: r_minus1_reg = S;                                       // Range 2: >=0 and < mod_m1 → no correction
            3'b001: r_minus1_reg = S - mod_m1;                              // Range 3: >= mod_m1 and < 2*mod_m1 → sub mod_m1
            3'b000: r_minus1_reg = S - 2*mod_m1;                            // Range 4: >= 2*mod_m1 → sub 2*mod_m1
            default: r_minus1_reg = 0;                                      // Should not occur
        endcase
    end
    assign r_minus1 = r_minus1_reg[N-1:0];
    // r1 = |N2 - N1 + N0| mod (2^n + 1)
    wire signed [N+1:0] diff_r1 = N0 - N1;                                  // Signed subtraction
    wire signed [N+1:0] T = diff_r1 + N2;                                   // T with signed arithmetic
    wire signed [N+1:0] mod1 = (1 << N) + 1;                                // 2^n + 1
    wire cmp1 = (T < -mod1);                                                // Flag for range 1
    wire cmp2 = (T < 0);                                                    // Flag for range 1+2
    wire cmp3 = (T < mod1);                                                 // Flag for range 1+2+3
    wire [2:0] flags = {cmp1, cmp2, cmp3};                                  // 3-bit flag vector
    reg [N:0] r1_reg;
    always @(*) begin
        case (flags)
            3'b111: r1_reg = T + 2*mod1;                                    // Range 1: T < -(2^n +1) → add 2*mod1
            3'b011: r1_reg = T + mod1;                                      // Range 2: -(2^n +1) <= T < 0 → add mod1
            3'b001: r1_reg = T;                                             // Range 3: 0 <= T < (2^n +1) → no correction
            3'b000: r1_reg = T - mod1;                                      // Range 4: T >= (2^n +1) → sub mod1
            default: r1_reg = 0;                                            // Should not occur
        endcase
    end
    assign r1 = r1_reg;
endmodule
