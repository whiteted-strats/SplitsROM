"""
INPLACE

A tweak to make the left shoulder always give its mid length animation, rather than either of the other 2
Except we accidentally did it for the death animation oops
May still be useful in the future

"""

class LeftShoulderDeathAnim:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):

        # Rand only touches v0, a0, a1, a2
        # We save storing and restoring a2 by using it (to populate tXs before the call)
        
        """ ORIGINAL NTSC-U
        [A] - 7 instructions
        7f026840 af ab 00 90     sw         t3,0x90(sp)
        7f026844 0c 00 29 14     jal        RAND                                             
        7f026848 af a6 00 30     _sw        a2,0x30(sp)
        7f02684c 8f a6 00 30     lw         a2,0x30(sp)
        7f026850 02 00 20 25     or         a0,s0,zero
        7f026854 8c cc 00 20     lw         t4,0x20(a2)
        7f026858 8c cd 00 1c     lw         t5,0x1c(a2)

        [B] - 5 instructions
        7f02685c 00 4c 00 1b     divu       ptr,t4
        7f026860 00 00 18 10     mfhi       value
        7f026864 00 03 70 c0     sll        t6,value,0x3
        7f026868 01 c3 70 23     subu       t6,t6,value
        7f02686c 00 0e 70 80     sll        t6,t6,0x2
        
        [C] - 3 instructions
        7f026870 15 80 00 02     bne        t4,zero,LAB_7f02687c
        7f026874 00 00 00 00     _nop
        7f026878 00 07 00 0d     break      0x1c00

        """


        TWEAK_ADDR = {
            "NTSC-U" : 0x5b370,
        }[api.VERSION]

        BP_LEFT_UPPER_ARM = 11
        MED_ANIM_INDEX = 0

        MOD = 10
        instrs = [
            # [A] - 7 -> 5 instructions, 2 appended back on
            "lw   t4, 0x20(a2)",
            "lw   t5, 0x1c(a2)",
            "jal  0x000a450",       # drop the 7, implied by section
            "sw   t3, 0x90(sp)",
            "or   a0, s0, zero",

            # bp index is sp + 0x88
            "lw   t6, 0x88(sp)",    # t6 used below, so is useable
            "li   at, {}".format(BP_LEFT_UPPER_ARM), 

            # [C] - 3 instructions, replacing the break
            "bne  t6, at, {}".format(TWEAK_ADDR + 0x4 * MOD),
            "nop",
            "li   v0, {}".format(MED_ANIM_INDEX),

            # MOD
            # [B] unchanged just moved
            "divu v0, t4",
            "mfhi v1",
            "sll  t6,v1,0x3",
            "subu t6,t6,v1",
            "sll  t6,t6,0x2",
        ]

        for i, instr in enumerate(instrs):
            api.nop_quietly(hex(TWEAK_ADDR+i*4))
        for i, instr in enumerate(instrs):
            api.asm(hex(TWEAK_ADDR+i*4), instr)



