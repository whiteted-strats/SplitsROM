"""
USES 4 WORDS SCRATCH SPACE
-> could be avoided if the function isn't used elsewhere, but eh :)

80052528 is J's commandAddress
"""

class ImproveCmds72And73:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):

        """
        3 word function at 7f0bfc40 currently returns the global timer as a float
        We only need 4 instructions and could steal 1 extra but the function may be used elsewhere.
        Called at 7f037b30, 7f037b90, so just call our new function instead
        """

        JAL_ADDRS = {
            "NTSC-U" : [0x6c660, 0x6c6c0],  # 7f037b30, 7f037b90 the virtuals
            "NTSC-J" : [0x6c9A0, 0x6ca00]
        }[api.VERSION]

        # a0, a1, at, f0 useable
        instrs = [
            api.MemConst.mission_timer.lui_instr("at"),
            "lwc1 f0, {}".format(api.MemConst.mission_timer.offset_term("at")),
            "nop",
            "nop",
            "jr ra",
            "cvt.s.W f0, f0",   # get it the right way around!
        ]

        # Write to scratch space
        funcAddr = api.getScratchSpaceAddr()
        for i, _instr in enumerate(instrs):
            api.nop_quietly(hex(funcAddr + i*0x4))
        
        for i, instr in enumerate(instrs):
            api.asm(hex(funcAddr + i*0x4), instr)


        # Patch calls
        for jal_addr in JAL_ADDRS:
            api.asm(hex(jal_addr), "jal 0x{:x}".format(api.virtualise(funcAddr)))