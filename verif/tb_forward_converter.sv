// Self-checking testbench for forward_converter.
//  Phase 1: replay golden vectors from ref_model.py (vectors/vec_n<N>.hex).
//  Phase 2 (N <= SWEEP_MAX_N): exhaustive sweep of every 3N-bit input against
//           a behavioural golden model (signed %, independent of the RTL).
// Plusargs: +VEC=<file> +NVEC=<count>
`timescale 1ns / 1ps

module tb_forward_converter;
    parameter integer N = 4;
    parameter integer SWEEP_MAX_N = 8;
    localparam integer W = 6*N + 1;
    localparam integer MAXV = 1 << 22;

    reg  signed [3*N-1:0] x;
    wire [N-1:0] r0, r_minus1;
    wire [N:0]   r1;

    forward_converter #(.N(N)) dut (
        .input_num(x), .r0(r0), .r_minus1(r_minus1), .r1(r1)
    );

    reg [W-1:0] mem [0:MAXV-1];
    reg [1023:0] vec_file;
    integer nvec, i, errors, checked;
    reg [N-1:0] e_rm1, e_r0;
    reg [N:0]   e_r1;

    task automatic compare(input [N-1:0] a_rm1, input [N-1:0] a_r0, input [N:0] a_r1);
        begin
            checked = checked + 1;
            if (r_minus1 !== a_rm1 || r0 !== a_r0 || r1 !== a_r1) begin
                errors = errors + 1;
                if (errors <= 10)
                    $display("FAIL N=%0d x=%0d: got (r-1,r0,r1)=(%0d,%0d,%0d) exp (%0d,%0d,%0d)",
                             N, x, r_minus1, r0, r1, a_rm1, a_r0, a_r1);
            end
        end
    endtask

    function automatic [N:0] smod(input signed [63:0] v, input signed [63:0] m);
        reg signed [63:0] r;
        begin
            r = v % m;
            if (r < 0) r = r + m;
            smod = r[N:0];
        end
    endfunction

    reg signed [63:0] v;

    initial begin
        errors = 0;
        checked = 0;
        if (!$value$plusargs("VEC=%s", vec_file)) begin
            $display("ERROR: +VEC=<file> required");
            $finish;
        end
        if (!$value$plusargs("NVEC=%d", nvec)) begin
            $display("ERROR: +NVEC=<count> required");
            $finish;
        end
        if (nvec > MAXV) begin
            $display("ERROR: NVEC=%0d exceeds MAXV=%0d", nvec, MAXV);
            $finish;
        end
        $readmemh(vec_file, mem, 0, nvec - 1);

        // Phase 1: golden vectors from the Python reference model.
        for (i = 0; i < nvec; i = i + 1) begin
            {x, e_rm1, e_r0, e_r1} = mem[i];
            #1;
            compare(e_rm1, e_r0, e_r1);
        end
        $display("N=%0d vectors: checked=%0d errors=%0d", N, checked, errors);

        // Phase 2: exhaustive sweep with behavioural golden model.
        if (N <= SWEEP_MAX_N) begin
            for (v = -(64'sd1 <<< (3*N-1)); v < (64'sd1 <<< (3*N-1)); v = v + 1) begin
                x = v[3*N-1:0];
                #1;
                compare(smod(v, (64'sd1 <<< N) - 1),
                        smod(v, 64'sd1 <<< N),
                        smod(v, (64'sd1 <<< N) + 1));
            end
            $display("N=%0d sweep done: total checked=%0d errors=%0d", N, checked, errors);
        end

        $display("RESULT N=%0d checked=%0d errors=%0d %s", N, checked, errors,
                 errors == 0 ? "PASS" : "FAIL");
        $finish;
    end
endmodule
