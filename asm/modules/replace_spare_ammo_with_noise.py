"""
INPLACE

Duplicated from replace_spare_ammo_with_lag, but we have to do some conversion
"""

from lib.version_constants import MemoryAddress

class NoiseForSpareAmmo:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):

        """
        Entire EXTRA AMMO if branch which we can overwrite, 7 instructions
        7f069fbc 8f a4 00 60     lw         a0,local_8(sp)
        7f069fc0 1d a0 00 05     bgtz       t5,LAB_7f069fd8
        7f069fc4 00 00 00 00     _nop
        7f069fc8 0f c1 78 2d     jal        testGunAccuracyDataFlag
        7f069fcc 3c 05 00 40     _lui       a1,0x40
        7f069fd0 10 40 00 23     beq        v0,zero,LAB_7f06a060
        7f069fd4 00 00 00 00     _nop
        """

        IF_ADDR = {
            "NTSC-U" : 0x9eaec,
            "NTSC-J" : 0x9f118,
        }[api.VERSION]

        SET_A1_ADDR = {
            "NTSC-U" : 0x9eb68,
            "NTSC-J" : 0x9f194,
        }[api.VERSION]

        # Nop the normal setting of A1
        api.asm(hex(SET_A1_ADDR), "mfc1 a1, f0")

        # Clear the if
        for i in range(7):
            api.nop_quietly(hex(IF_ADDR + i*4))

        # Use it to set A1, which will persist
        # t6 - t8 all fine to use
        # f0 presumably (common return parameter), and f16 we see used later for a float constant.
        instrs = [
            "lui t6, 0x42c8",   # 10 is 0x4120, 100 is 0x42c8
            "mtc1 t6, f16",
            "jal 0xf067174",    # uses t6,t7,t8 (all fine) to get noise to f0
            "li a0, 0",     # right gun
            "mul.S f0, f0, f16",
            "nop",
            "nop",  # can't convert him back yet?

            "jal 0x0004514",    # PRESERVED
            "cvt.w.S f0, f0",   # was a nop
        ]
        
        for i, instr in enumerate(instrs):
            api.asm(hex(IF_ADDR + i*0x4), instr)

