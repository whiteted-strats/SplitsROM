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
            "PAL" : 0x000ac14c,
        }[api.VERSION]

        # Initialise to 0x3f800000, which has definitely built full speed.
        api.asm(hex(resetAddr), "swc1 f2,0x17c(t5)")    


        # [2] 1.X?, now in place :)
        onePointTwoAddr = {
            "NTSC-U" : 0x000b7e34,
            "NTSC-J" : 0x000b8484,  # should work fine
            "PAL" : 0x000b5d98, # heavily inferred
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

        

        # [3] We've come back to 2.x ..
        twoPointThreeAddr = {
            "NTSC-U" : 0x000b7d14,
            "NTSC-J" : 0x000b8364,
            "PAL" : 0x000b5c78,
        }[api.VERSION]
        
        """
        [TEST]
        000b7d14 29 a1 00 3d     slti       at,t5,0x3d
        000b7d18 54 20 00 09     bnel       at,zero,LAB_000b7d40
        000b7d1c 8e 0f 00 00     _lw        t7,0x0(s0)

        [ELSE]
        000b7d20 8e 08 00 00     lw         t0,0x0(s0)
        000b7d24 3c 18 80 05     lui        t8,0x8005
        000b7d28 8f 18 83 74     lw         t8,-0x7c8c(t8)=>DAT_80048374
        000b7d2c 8d 0c 01 7c     lw         t4,0x17c(t0)
        000b7d30 01 98 70 21     addu       t6,t4,t8
        000b7d34 10 00 00 03     b          LAB_000b7d44
        000b7d38 ad 0e 01 7c     _sw        t6,0x17c(t0)

        000b7d3c UNREACHABLE

        [IF]
                             LAB_000b7d40                                    XREF[1]:     000b7d18(j)  
        000b7d40 ad e0 01 7c     sw         zero,0x17c(t7)

        [FINALLY]
                             LAB_000b7d44                                    XREF[1]:     000b7d34(j)  
        000b7d44 8e 08 00 00     lw         t0,0x0(s0)

        """

        BLOCK_END = 12
        
        instrs = [
            #[EXTRA TEST]
            api.MemConst.mission_timer.lui_instr("t7"),
            "lw  t7, {}".format(api.MemConst.mission_timer.offset_term("t7")),
            "beq t7, zero, 0x{:x}".format(twoPointThreeAddr + 0x4*BLOCK_END),
            "lw  t0, 0x0(s0)",  #  [FINALLY]

            #[TEST]
            "slti at, t5, 0x3d",
            "bnel at, zero, 0x{:x}".format(twoPointThreeAddr + 0x4*BLOCK_END),
            "sw zero, 0x17c(t0)",  #[IF]

            #[ELSE unchanged, but generalised]
            api.MemConst.global_timer_delta.lui_instr("t8"),
            "lw  t8, {}".format(api.MemConst.global_timer_delta.offset_term("t8")),
            "lw         t4,0x17c(t0)",
            "addu       t6,t4,t8",
            "sw         t6,0x17c(t0)",

            # -> BLOCK_END
            # One to spare
            "nop",
        ]
    
    
        for i, instr in enumerate(instrs):
            api.nop_quietly(hex(twoPointThreeAddr + i*0x4))
        for i, instr in enumerate(instrs):
            api.asm(hex(twoPointThreeAddr + i*0x4), instr)