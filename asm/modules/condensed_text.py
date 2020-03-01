"""
INPLACE
Support more condensed text files. Remove stupid & unused functionality that returns a nullptr
Might be of interest for general ROM hacks.
"""

class CondensedTextPatch:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):

        initCodeAddr = {
            "NTSC-U" : 0x0f6908,
            "NTSC-J" : 0X0f75f8,
        }[api.VERSION]

        # Clean and trim the main text function,
        #   adding a call to our function to support the more compressed text files
        # NOTE that this function returns a pointer to the text.
        UNCOND = 12
        COMMON = 15
        mainBlock = [
            "sra        t6,a0,0xa",
            "sll        t6,t6,0x2",     # bank offset, top 6 bits
            api.MemConst.wordBankTable.lui_instr("v0"), #"lui        v0,0x8009",
            "addu       v0,v0,t6",
            "lw         v0,{}".format(api.MemConst.wordBankTable.offset_term("v0")),   # => Bank, "-0x39c0 (v0)"

            # TEST
            "lb         t7, 0x0(v0)",
            "beq        zero, t7, 0x{:x}".format(initCodeAddr + 0x4*UNCOND),
            "andi       t8,a0,0x3ff",

            # CONDENSED
            "sll    t9,t8,0x1", # *2
            "addu   t0,v0,t9",
            "b  0x{:x}".format(initCodeAddr + 0x4*COMMON),
            "lhu    v1,0x2(t0)", # Skip the first 2 bytes, the 'header'. Read a half word instead
            
            # UNCONDENSED
            "sll        t9,t8,0x2",     # * 4
            "addu       t0,v0,t9",
            "lw         v1,0x0 (t0)",   # Read full word, no header

            # COMMON
            "addu       a0,v1,v0",
            "jr         ra",
            "or         v0,a0,zero",
        ]

        for i, instr in enumerate(mainBlock):
            api.asm(hex(initCodeAddr+i*4), instr)

