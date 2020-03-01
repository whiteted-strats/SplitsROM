"""
INPLACE

Bypasses the CIC checks.
This does mean people need to ignore the bad CIC warning / have that disabled. 
"""

class NoCicCheckPatch:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):
            
        # Bypass CIC checks, type 6102-7101-ish
        api.asm("066C", "nop")
        api.asm("0678", "nop")