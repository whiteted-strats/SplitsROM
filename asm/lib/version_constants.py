"""
All these values are constant addresses but we split them into
  MemoryConst & InstructionConst.
MemoryConst contains mostly MemoryAddress instances, which have lui_instr & offset_term functions.
InstructionConst contains the physical addresses as ints
"""

class MemoryAddress:
    def __init__(self, i):
        self.i = i

        # Process the low/high portions for lui & an offset in [-0x8000, 0x7FFF]
        self.low = int(i & 0xFFFF)
        self.high = int(i >> 16)
        if self.low >= 0x8000:
            self.high += 1
            self.low -= 0x10000

    def __add__(self, off):
        return MemoryAddress(self.i + off)

    def __sub__(self, off):
        return MemoryAddress(self.i - off)

    def lui_instr(self, out_reg):
        return "lui {}, {}".format(out_reg, hex(self.high))

    def offset_term(self, reg):
        return "{}({})".format(hex(self.low), reg)


class MemoryConst:
    def __init__(self, VERSION):
        if VERSION == "NTSC-U":
            self.virtual_offset = 0x34b30
            
            self.mission_timer = MemoryAddress(0x80079a20)    # no introduction required
            self.p1_input = MemoryAddress(0x80067CA4)         # 1st 2 bytes are flags for buttons, last 2 are analogues
            self.playerDataPtr = MemoryAddress(0x80079EE0)    # -> PlayerData
            self.wordBankTable = MemoryAddress(0x8008c640)
            self.shotStatistics = MemoryAddress(0x80079EF0)
            self.settingsData = MemoryAddress(0x800409D0)     # values set in the pause are here. = FFFFFFFF
            self.currentMission = MemoryAddress(0x8002A8F8)
            self.ost_frames_float = MemoryAddress(0x80030af0)
            
            # NTSC-U only for now
            self.global_timer_delta = MemoryAddress(0x80048374) # float version follows

        elif VERSION == "NTSC-J":
            self.virtual_offset = 0x34b70

            self.mission_timer = MemoryAddress(0x80079a60)    # + 0x40
            self.p1_input = MemoryAddress(0x80067CE4)         # + 0x40
            self.playerDataPtr = MemoryAddress(0x80079F50)    # + 0x70
            self.wordBankTable = MemoryAddress(0x8008c6b0)    # + 0x70
            self.shotStatistics = MemoryAddress(0x80079F60)   # "
            self.settingsData = MemoryAddress(0x80040A00)     # + 0x30
            self.currentMission = MemoryAddress(0x8002A938)   # + 0x40
            self.ost_frames_float = MemoryAddress(0x80030b30)


        elif VERSION == "PAL":
            self.virtual_offset = 0x0329f0

            self.mission_timer = MemoryAddress(0x80068500)
            self.p1_input = MemoryAddress(0x80057cc4)
            self.playerDataPtr = MemoryAddress(0x800689F0)
            self.wordBankTable = MemoryAddress(0x80073a20)
            self.shotStatistics = MemoryAddress(0x80068A00)
            self.settingsData = MemoryAddress(0x8003a620)
            self.currentMission = MemoryAddress(0x80025e48)


# NOTE most instruction differences are stored in the specific modules rather than here,
#  because they don't have very interesting names.

class InstructionConst:
    def __init__(self, VERSION):
        if VERSION == "NTSC-U":
            # In particular, this is called when executing the comment
            self.script_cmd_length = 0x6952c
        elif VERSION == "NTSC-J":
            self.script_cmd_length = 0x6986c
        elif VERSION == "PAL":
            self.script_cmd_length = 0x6742c

