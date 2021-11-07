"""
INPLACE
"""

# Decent little helper
def floatRepForInt(n):
    if n == 0:
        return 0
    signBit = "0" if n >= 0 else "1"
    n = abs(n)
    bs = bin(n)[2:]
    assert bs[0] == "1"
    bs = bs[1:]
    exp = len(bs) + 127

    if len(bs) > 7:
        assert bs[7:] == "0" * (len(bs) - 7), "can't represent {} in just the top 2 bytes".format(n)
        bs = bs[:7]

    s = signBit + bin(exp)[2:].zfill(8) + bs + "0" * (7-len(bs))
    assert len(s) == 16
    return int(s,2)


class FarRun:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):
        """ ORIGINAL NTSC-U
        32 random bits -> [0,1)
        
        [A] rand value to co processor
        7f02a5cc 44 82 20 00     mtc1       v0,f4

        [B] Load 200 into f0
        7f02a5d0 3c 01 43 48     lui        at,0x4348
        7f02a5d4 44 81 00 00     mtc1       at,f0

        [C] Instructions dealing with negative values (which we'll cut)
        ! though note that we still need to convert!
        7f02a5d8 04 41 00 05     bgez       v0,LAB_7f02a5f0
        7f02a5dc 46 80 21 a0     _cvt.s.W   f6,f4
        7f02a5e0 3c 01 4f 80     lui        at,0x4f80
        7f02a5e4 44 81 40 00     mtc1       at,f8
        7f02a5e8 00 00 00 00     nop
        7f02a5ec 46 08 31 80     add.S      f6,f6,f8

        [D] Loads 2^-32, push our rand to [0,1)
        7f02a5f0 3c 01 2f 80     lui        at,0x2f80
        7f02a5f4 44 81 50 00     mtc1       at,f10
        7f02a5f8 00 00 00 00     nop
        7f02a5fc 46 0a 34 02     mul.S      f16,f6,f10
        7f02a600 00 00 00 00     nop

        [E] * 200 then + 200, we'll replace with our 2 custom instrs
        7f02a604 46 00 84 82     mul.S      f18,f16,f0
        7f02a608 0c 00 29 14     jal        RAND
        7f02a60c 46 00 95 00     _add.S     f20,f18,f0

        """

        TWEAK_ADDR = {
            "NTSC-U" : 0x5F0FC,
        }[api.VERSION]

        # Standard values are 200 and 200
        BASE_RUN = 350
        RANDOM_RUN = 50

        flt_base_run = floatRepForInt(BASE_RUN)
        flt_random_run = floatRepForInt(RANDOM_RUN)

        ##print("lui at,0x{:x}".format(flt_base_run))
        ##print("lui at,0x{:x}".format(flt_random_run))

        instrs = [
            # Ditch the sign bit, copy over to f4
            "srl v0, v0, 1",
            "mtc1 v0, f4",

            # Load our constants
            "lui at,0x{:x}".format(flt_base_run),
            "mtc1 at,f0",
            "lui at,0x{:x}".format(flt_random_run),
            "mtc1 at,f8",
            "nop",

            # Convert to float, then push into [0,1)
            "cvt.s.W f6, f4",
            "lui at,0x3000",    # 2 ^ -31
            "nop",              # necessary? Pads anyway
            "mtc1 at,f10",
            "nop",
            "mul.S f16,f6,f10",
            "nop",

            # [0,1) * RAND_RUN + BASE_RUN
            "mul.S f18,f16,f8",

            # [!] Unchanged!
            # 7f02a608 0c 00 29 14     jal        RAND
            # 7f02a60c 46 00 95 00     _add.S     f20,f18,f0
        ]

        for i, instr in enumerate(instrs):
            api.nop_quietly(hex(TWEAK_ADDR+i*4))
        for i, instr in enumerate(instrs):
            api.asm(hex(TWEAK_ADDR+i*4), instr)

