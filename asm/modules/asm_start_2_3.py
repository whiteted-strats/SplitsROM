"""
Sets PlayerData + 0x2a58 = 06 when Frig (0xA) loads
This hook is achieved by making the code that initialises some player data more compact
"""

class Start2_3Patch:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):

        funcAddr = api.getScratchSpaceAddr()

        initCodeAddr = {
            "NTSC-U" : 0x00039ca0,
            "NTSC-J" : 0x00039d00,
        }[api.VERSION]
        v1_increment = {
            "NTSC-U" : -0x5f4c,
            "NTSC-J" : -0x5edc,
        }[api.VERSION]

        SUFFIX = 0x6
        funcInstrs = [
            # Initially t5 = current mission, t6 = 0xA
            
            "bne t5, t6, 0x{:x}".format(funcAddr + 0x4 * SUFFIX),
            "nop",

            # *t5 = playerData, t6 = 2.3
            api.MemConst.playerDataPtr.lui_instr("t5"),
            "li t6, 0x06",
            "lw t5, {}".format(api.MemConst.playerDataPtr.offset_term("t5")),
            "sw t6, 0x2a58(t5)",

            # SUFFIX
            "jr ra",
            "nop",
        ]
        
        for i, instr in enumerate(funcInstrs):
            api.nop_quietly(hex(funcAddr + i*4))
        for i, instr in enumerate(funcInstrs):
            api.asm(hex(funcAddr+i*4), instr)


        # Was interspersed, now this is only at the end of the compacted code below
        # Using t5 & t6 only
        hook_code = [
            api.MemConst.currentMission.lui_instr("t5"),
            "lw t5, {}".format(api.MemConst.currentMission.offset_term("t5")),
            "jal 0x{:x}".format(api.virtualise(funcAddr)),
            "li t6, 0xA",   # Frig
        ]

        # Tweaked, compacted code & shell code
        blockInstrs = [
            "sw         zero ,0x7fc (t4)",
            "lw t0,0x0 (s0)",               # Set t0 early instead of t5
            "or         t4,v1,zero",
            "sw zero ,0x800 (t0)",          # Use t0, not t5
            # [0], was setting t9
            "sw zero ,0x804 (t0)",          # Use t0, not t9
            "lw         t8,0x0 (s0)",
            "sw         a1,0x2a44 (t8)",
            # [1], was setting t0
            "addiu      t8,v1,0x3a8",
            "sw         a1,0x2a48 (t0)",
            # [2], was setting t7
            "or         t0,v1,zero",
            "lui        v1,0x8008",
            "sw zero ,0x2a50 (t0)",         # Use t0, not t7
            # [3], was setting t6
            "addiu      v1,v1,{}".format(hex(v1_increment)),
            "sw zero ,0x2a54 (t0)",         # Use t0, not t6
            hook_code[0],
            hook_code[1],
            hook_code[2],
            hook_code[3],                                             
        ]
        # Following line is
        # lw    t1, 0x0(s0)


        # t5,t6,t7,t9 are all reset afterwards without their values being used.
        # Briefly checked for NTSC-J too

        for i, instr in enumerate(blockInstrs):
            api.nop_quietly(hex(initCodeAddr + i*4))
        for i, instr in enumerate(blockInstrs):
            api.asm(hex(initCodeAddr+i*4), instr)

