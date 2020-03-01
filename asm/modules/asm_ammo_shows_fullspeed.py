"""
Overrides the pause menu control which handles showing ammo on screen,
 instead displaying it IFF we've built full speed.
NOTE that it still disappears with the rest of the HUD during damage.

Writes to 'settingsData' + 0xF0
"""

class AmmoWithFullspeedPatch:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):

        # Currently:
        # NTSC-U : 7f083394 = 000b7ec4
        # NTSC-J : 7F0839A4 = 000b8514 
        # 000b7ec4  8d  0f  01  7c    lw         t7,0x17c (t0) 
        # 000b7ec8  29  e1  00  b4    slti       at,t7,0xb4
        # i.e. (_DAT_8007a0b0 + 0x17c) < 0xb4

        injection_address = {
            "NTSC-U" : 0x000b7ec4,
            "NTSC-J" : 0x000b8514,
        }[api.VERSION]

        ammo_on_screen = api.MemConst.settingsData + 0xF0

        funcAddr = api.getScratchSpaceAddr()

        # We put our jump over Both instructions - delay slot
        api.asm("{:x}".format(injection_address + 0x4), "nop")
        api.asm("{:x}".format(injection_address), "jal {}".format(hex(api.virtualise(funcAddr))))

        

        funcInstrs = [
            # t7 coming in as the # frames fullspeed
            # Prefix - save t4, t5
            "addiu sp, sp, -0x8",
            "sw t4, 0x0(sp)",
            "sw t5, 0x4(sp)",

            # Perform the replaced instructions (set t7, at)
            "lw t7, 0x17c(t0)",
            "slti at,t7,0xb4",

            # Do our main work
            ammo_on_screen.lui_instr("t4"),
            "xori t5, at, 0x1",     # flip so we show ammo at fullspeed
            "sw t5, {}".format(ammo_on_screen.offset_term("t4")),

            # Suffix, restore t4, t5
            "lw t4, 0x0(sp)",
            "lw t5, 0x4(sp)",
            "jr  ra",
            "addiu sp, sp, 0x8",
        ]

        for i, instr in enumerate(funcInstrs):
            api.nop_quietly(hex(funcAddr+i*4))

        for i, instr in enumerate(funcInstrs):
            api.asm(hex(funcAddr+i*4), instr)


