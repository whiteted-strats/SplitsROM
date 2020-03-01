"""
INPLACE

Makes the code that initialises the hits statistics more compact,
This leaves room for code which zeros all our splits and the 3 values before it.
  It also zeros the first 17 names. Even with 32 splits it's only necessary to zero the first 4 anyway. 
"""

# Ghidra-Python is a bit weird..
from lib.version_constants import MemoryAddress

class ZeroSplitsPatch:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):


        # Patch this very sparse initialisation code.
        initCodeAddr = {
            "NTSC-U" : 0x39D7C,
            "NTSC-J" : 0x39DDC,
        }[api.VERSION]
        # initCodeAddr -> +0x3c are identical in NTSC-J & -U

        # Including the 3 words before
        fullBuffer = api.splitsBuffer - 0xc
        assert api.namesBuffer.lui_instr("r") == fullBuffer.lui_instr("r")

        instrs = [
            # Compress some initialisation
            "or a0, zero, zero",
            "li t0, 0x1c",
            "addiu t0, t0, -0x4",
            "addu t1, t4, t0",
            "bne t0, zero, 0x{:x}".format(initCodeAddr + 0x08),
            "sw zero, 0x0(t1)",

            # Use our well earned space to zero all our splits, and the string pointers
            fullBuffer.lui_instr("t1"),
            "addiu t1, t1, 0x10C", # Zero up to the 64th split (only using 32 max atm), and 16 names (we only need to zero 4)
            "addiu t1, t1, -0x4",
            "sw zero, {}".format(fullBuffer.offset_term("t1")),
            "sw zero, {}".format(api.namesBuffer.offset_term("t1")),
            "andi t2, t1, 0xFFFF",
            "bne t2, zero, 0x{:x}".format(initCodeAddr + 0x20),
            "nop",
        ]

        for i in range(len(instrs)):
            api.nop_quietly(hex(initCodeAddr+i*4))

        for i, instr in enumerate(instrs):
            api.asm(hex(initCodeAddr+i*4), instr)


        


