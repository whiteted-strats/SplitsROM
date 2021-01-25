"""
Contains the API class which we instatiate a single member of.
This provides access to the assembler & version-dependent differences
  In particular it manages the scratch space for extra functions
"""

from version_constants import MemoryConst, InstructionConst
from ghidra.app.plugin.assembler import Assemblers
import array # jython

# Add support for a label system? Keep the system we've got anyway

unsign = lambda x: x if x >= 0 else 256 + x

class API:
    def __init__(self, VERSION, currentProgram):
        self.VERSION = VERSION
        self._changes = dict()

        # Fetch the constants based on the version
        self.MemConst = MemoryConst(VERSION)
        self.InstrConst = InstructionConst(VERSION)

        # Determine where our free space is going to start
        self._scratchSpaceStart = {
            "NTSC-U" : 0x107450,
            "NTSC-J" : 0x108170,
            "PAL" : 0x0c39d4,   # PAL lacks the spectrum emulator and the debug menu section is very small.
                                # We overwrite the single function "handle_cheats_turned_on" in the "cheat_buttons" module
                                # THIS MEANS YOU CAN'T SET ANY CHEATS
                                # It is size 0x8d4 
        }[VERSION]

        self._asmer = Assemblers.getAssembler(currentProgram)
        self._ram = currentProgram.getAddressFactory().getAddressSpace("ram")
        self._mem = currentProgram.getMemory()

    def asm(self, hexOffset, statement):
        try:
            r = self._asmer.assemble(self._ram.getAddress(hexOffset), statement)
        except:
            print("Unable to assemble: {} at {}".format(statement, hexOffset))
            return
        
        b = bytearray([
                unsign(self._mem.getByte(self._ram.getAddress(int(hexOffset,16)+i))) for i in range(4)
        ])

        self.store_directly(hexOffset, b)

    def store_directly(self, hexOffset, b):
        # Advance self._scratchSpaceStart if we write over it.
        #  -> writes to the scratch space must be contigious
        if int(hexOffset, 16) == self._scratchSpaceStart:
            self._scratchSpaceStart += 4
        assert hexOffset not in self._changes
        self._changes[hexOffset] = b

    def nop_quietly(self, hexOffset):
        r = self._asmer.assemble(self._ram.getAddress(hexOffset), "nop")
        assert hexOffset not in self._changes


    def virtualise(self, addr):
        # The 7 at the front is implied by the section remember
        return 0xf000000 + addr - self.MemConst.virtual_offset

    def getScratchSpaceAddr(self):
        # Add atleast 1 nop to align our position

        pad = (16 - (self._scratchSpaceStart % 16))

        # This will add 4 to _scratchSpaceStart each iteration
        for offset in range(0,pad,4):
            self.asm("{:x}".format(self._scratchSpaceStart), "nop")

        # Log
        print("Scratch space provided at 0x{:x}".format(self._scratchSpaceStart))

        return self._scratchSpaceStart

    def getChanges(self):
        return self._changes

    def shift(self, startAddr, endAddr, shift):
        # Doesn't respect scratch space - why would you shift there
        # BEWARE - reads from db

        assert shift < 0
        w = array.array('b', '\x00\x00\x00\x00' )
        for addr in range(startAddr, endAddr, 4):
            # Read the 4 signed bytes and unsigned them
            # Don't write them because we have the issues of noping it first & telling ghidra it's still asm
            self._mem.getBytes(self._ram.getAddress(addr), w, 0, 4)
            ##self._mem.setBytes(ram.getAddress(addr + shift), w)
            unsigned = [unsign(w[0]), unsign(w[1]), unsign(w[2]), unsign(w[3])]

            # Add the changes - after shifting
            hexAddr = "{:x}".format(addr + shift)
            assert hexAddr not in self._changes
            self._changes[hexAddr] = unsigned



    def commit(self, out_fn, in_fn):
        with open(in_fn, "rb") as fs:
            data = bytearray(fs.read())

        for addr, bs in self._changes.items():
            addr = int(addr, 16)
            assert len(bs) == 4
            data[addr:addr+4] = bs

        with open(out_fn, "wb") as fs:
            fs.write(data)