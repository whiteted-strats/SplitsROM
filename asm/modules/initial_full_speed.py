"""
INPLACE now

Only 1.X is supported by this module, whereas our old script had 2.X too (though not inplace).
To be extended.

"""

class InitialFullSpeed:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):
            
        # [1] the reset
        resetAddr = {
            "NTSC-U" : 0x000ae20c,
            "NTSC-J" : 0x000ae83c,
        }[api.VERSION]

        # Initialise to 0x3f800000, which has definitely built full speed.
        api.asm(hex(resetAddr), "swc1 f2,0x17c(t5)")    


        # [2] 1.X?, now in place :)
        onePointTwoAddr = {
            "NTSC-U" : 0x000b7e34,
            ##"NTSC-J" : 0x000b8484,
        }[api.VERSION]

        """
            7f0832ec 8e 08 00 00     lw         t0,0x0(s0)=>PTR_8007a0b0                       
            ..
            [A] - 8 instructions
            7f083304 8f aa 01 9c     lw         t2,0x19c(sp)
            7f083308 57 20 00 06     bnel       t9,zero,LAB_7f083324
            7f08330c 8f ad 01 54     _lw        t5,0x154(sp)
            7f083310 55 40 00 04     bnel       t2,zero,LAB_7f083324
            7f083314 8f ad 01 54     _lw        t5,0x154(sp)
            7f083318 8e 0b 00 00     lw         t3,0x0(s0)=>PTR_8007a0b0    -> got on                     
            7f08331c ad 60 01 7c     sw         zero,0x17c(t3)
            7f083320 8f ad 01 54     lw         t5,0x154(sp)

            -> branches to here
        """

        LAST_INSTR = 7  # at the end of the if, avoiding repeated delay slot calls
        instrs = [
            "bne t9, zero, 0x{:x}".format(onePointTwoAddr + 0x4*LAST_INSTR),
            "lw   t2, 0x19c(sp)",
            "bne t2, zero, 0x{:x}".format(onePointTwoAddr + 0x4*LAST_INSTR),
            api.MemConst.mission_timer.lui_instr("t5"),
            "lw   t5, {}".format(api.MemConst.mission_timer.offset_term("t5")),
            "bnel t5, zero, 0x{:x}".format(onePointTwoAddr + 0x4*LAST_INSTR),
            "sw   zero, 0x17c(t0)",

            # LAST_INSTR
            "lw   t5, 0x154(sp)",
        ]

        for i, instr in enumerate(instrs):
            api.nop_quietly(hex(onePointTwoAddr + i*0x4))
        for i, instr in enumerate(instrs):
            api.asm(hex(onePointTwoAddr + i*0x4), instr)

        

        # [3] We'll leave 2.x for another time
        """
        twoPointThreeAddr = {
            "NTSC-U" : "000b7d40",
            "NTSC-J" : "000b8390",
        }[VERSION]
        """
    

    