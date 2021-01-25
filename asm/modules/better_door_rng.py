"""
INPLACE, TRIVIAL

A tweak to make guards consider opening doors every 3 frames rather than 10
This should ensure the facility guard always opens the decoder door when he targets behind it.

"""

class BetterDoorRNG:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):

        tweakAddr = {
            "NTSC-U" : 0x0006689c
        }[api.VERSION]

        instrs = [
            "li   at, 0x3",     # rather than 0xa
        ]

        for i, instr in enumerate(instrs):
            api.nop_quietly(hex(tweakAddr+i*4))
        for i, instr in enumerate(instrs):
            api.asm(hex(tweakAddr+i*4), instr)



