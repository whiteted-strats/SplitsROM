"""
INPLACE

Originally we accidentally did this for death animations :)
It's pretty much the same here

"""

class ForceInjuryAnim:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):

        # Rand only touches v0, a0, a1, a2
        # We save storing and restoring a2 by using it (to populate tXs before the call)
        # And indeed a2 is overwritten before being used again
        
        """ ORIGINAL NTSC-U
        [A] - 6 instructions
        7f026d8c 0c 00 29 14     jal        RAND                                             
        7f026d90 af a6 00 30     _sw        a2,0x30(sp)        = ??
        7f026d94 8f a6 00 30     lw         a2,0x30(sp)
        7f026d98 02 00 20 25     or         a0,s0,zero
        7f026d9c 8c cc 00 28     lw         t4,0x28(a2)
        7f026da0 8c cd 00 24     lw         t5,0x24(a2)

        [B] - 5 instructions
        7f026da4 00 4c 00 1b     divu       v0,t4
        7f026da8 00 00 28 10     mfhi       a1
        7f026dac 00 05 70 c0     sll        t6,a1,0x3
        7f026db0 01 c5 70 23     subu       t6,t6,a1
        7f026db4 00 0e 70 80     sll        t6,t6,0x2

        [C] - 3 instructions
        7f026db8 15 80 00 02     bne        t4,zero,LAB_7f026dc4
        7f026dbc 00 00 00 00     _nop
        7f026dc0 00 07 00 0d     break      0x1c00
        """

        TWEAK_ADDR = {
            "NTSC-U" : 0x5b8bc,
            "PAL" : 0x59794,
        }[api.VERSION]

        BP_LEFT_SHIN = 2
        BP_RIGHT_SHIN = 5
        ##BP_LEFT_UPPER_ARM = 11
        ##BP_RIGHT_UPPER_ARM = 14
        
        ANIM_INDEX = 1

        MOD = 9
        instrs = [
            # [A] - 6 -> 4 instructions, 2 appended back on
            "lw   t4, 0x28(a2)",
            "jal  0x000a450",       # drop the 7, implied by section
            "lw   t5, 0x24(a2)",
            "or   a0, s0, zero",

            # bp index is sp + 0x88
            # t6, a1 used below, so are useable
            "lw   t6, 0x88(sp)",    
            "li   a1, {}".format(BP_RIGHT_SHIN), 

            # [C] - 3 instructions, replacing the break
            "bne  t6, a1, {}".format(TWEAK_ADDR + 0x4 * MOD),
            "nop",
            "li   v0, {}".format(ANIM_INDEX),

            # MOD
            # [B] unchanged just moved
            "divu v0, t4",
            "mfhi a1",
            "sll  t6,a1,0x3",
            "subu t6,t6,a1",
            "sll  t6,t6,0x2",
        ]

        for i, instr in enumerate(instrs):
            api.nop_quietly(hex(TWEAK_ADDR+i*4))
        for i, instr in enumerate(instrs):
            api.asm(hex(TWEAK_ADDR+i*4), instr)

