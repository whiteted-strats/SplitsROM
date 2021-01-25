"""
INPLACE

Replaces the 2 ammo values with arbitrary memory reads
These are set to the global delta and the fac guard's frames to update

TODO have them come in as args if we want to reuse this

"""

from lib.version_constants import MemoryAddress

class ReplaceAmmoDisplay:

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


        ##BRANCH_ADDR = {
        ##    "NTSC-U" : 0x9ea5c,
        ##}[api.VERSION]

        CURRENT_AMMO_SET_A1 = {
            "NTSC-U" : 0x9eac0,
        }[api.VERSION]

        CURRENT_AMMO_DRAW_CALL = {
            "NTSC-U" : 0x9eadc
        }[api.VERSION]

        IF_ADDR = {
            "NTSC-U" : 0x9eaec,
        }[api.VERSION]

        EXTRA_AMMO_SET_A1 = {
            "NTSC-U" : 0x9eb68,
        }[api.VERSION]

        JMP_OVER_EXTRA_AMMO = {
            "NTSC-U" : 0x9eb90,
        }[api.VERSION]


        guardDelayMem = MemoryAddress(0x801DB33C + 0x008)  # guard_0x15.frames_until_update in adjusted setup
        guardDelayLoad = "lb"

        api.MemConst.global_timer_delta.offset_term("reg")


        # [2] Correct extra ammo first
        # Clear the if
        for i in range(7):
            api.nop_quietly(hex(IF_ADDR + i*4))
        
        # Use just the last to set up our a1..
        # It moves very fast so we may divide it.. we end up with 3 nops above this so we have room
        api.asm(hex(IF_ADDR + 0x6 * 0x4), guardDelayMem.lui_instr("a1"))

        # .. then finish it off where they actually set a1
        api.asm(hex(EXTRA_AMMO_SET_A1), "{} a1, {}".format(guardDelayLoad, guardDelayMem.offset_term("a1")))


        # [1]
        # Set up the a1 where they set it ..
        api.asm(hex(CURRENT_AMMO_SET_A1), api.MemConst.global_timer_delta.lui_instr("a1"))

        """
        End of CURRENT_AMMO section precedes the EXTRA_AMMO if statement
        We need to make a bit more space
        7f069fac 0f c1 a7 23     jal        FUN_7f069c8c                                     undefined FUN_7f069c8c()
        7f069fb0 00 00 38 25     _or        a3,zero,zero
        7f069fb4 af a2 00 68     sw         v0,local_res0(sp)
        7f069fb8 8f ad 00 50     lw         t5,extraAmmo(sp)

        """

        instrs = [
            # .. then make room to finish it off
            "lw   a1, {}".format(api.MemConst.global_timer_delta.offset_term("a1")),
            "jal  0xf069c8c",
            "or   a3,zero,zero",
            "sw   v0, 0x68(sp)",
            # lw t5 bumped off
        ]

        for i, instr in enumerate(instrs):
            api.asm(hex(CURRENT_AMMO_DRAW_CALL + i*0x4), instr)
        

        # Now tidy up the if statement - restore the extraAmmo > 0 test for safety
        instrs = [
            "lw   t5, 0x50(sp)",
            "lw   a0, 0x60(sp)",
            "blez t5, 0x{:x}".format(JMP_OVER_EXTRA_AMMO),
            "nop",
            "nop",
            "nop",
            # guardDelayMem.lui_instr("a1")
        ]
        
        for i, instr in enumerate(instrs):
            api.asm(hex(IF_ADDR + i*0x4), instr)

