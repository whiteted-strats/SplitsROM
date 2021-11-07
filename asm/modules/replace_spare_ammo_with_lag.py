"""
INPLACE

Duplicated from show_cinema_length - replaces spare ammo with the global delta
"""

from lib.version_constants import MemoryAddress

class LagForSpareAmmo:

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

        # PAL addresses not really checked
        IF_ADDR = {
            "NTSC-U" : 0x9eaec,
            "NTSC-J" : 0x9f118,
            "PAL" : 0x9d140,
        }[api.VERSION]

        SET_A1_ADDR = {
            "NTSC-U" : 0x9eb68,
            "NTSC-J" : 0x9f194,
            "PAL" : 0x9d1bc,
        }[api.VERSION]

        # Nop the normal setting of A1
        api.asm(hex(SET_A1_ADDR), "nop")

        # Clear the if
        for i in range(7):
            api.nop_quietly(hex(IF_ADDR + i*4))

        # Use it to set A1, which will persist
        # Can use a0, a1, t5 and v0.. but we don't need it.
        instrs = [
            api.MemConst.global_timer_delta.lui_instr("t5"),
            "lw a1, {}".format(api.MemConst.global_timer_delta.offset_term("t5")),
            "nop",
            "nop",
            "nop",
            "nop",
            "nop",
        ]
        
        for i, instr in enumerate(instrs):
            api.asm(hex(IF_ADDR + i*0x4), instr)

