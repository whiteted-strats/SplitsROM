"""
INPLACE

All pauses are of equal speed and that speed is very fast.
Unused by default.
"""

class FastPausePatch:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):

        # Previous instructions have multiplied by 1.1 and compared:
        #000b4408 46  0a  00  3c    c.lt.S     f0,f10
        #000b440c 00  00  00  00    nop

        # We override all this and just store 0x40800000 = 4.0 to 800365a8 / e8
        
        pausing_addr = {
            "NTSC-U" : 0x000b4410,
            "NTSC-J" : 0x000b4a60,
        }[api.VERSION]

        api.asm("{:x}".format(pausing_addr), "lui at, 0x4080")
        api.asm("{:x}".format(pausing_addr + 0x4), "sw  at, 0x0(v0)")
        api.asm("{:x}".format(pausing_addr + 0x8), "lui at, 0x8005")   # restores register at (original set by NTSC-U b43f0)

