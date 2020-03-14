"""
Adapted from Ryan Dwyer's Function Explorer
https://gitlab.com/ryandwyer/gepd-function-explorer/-/blob/master/extractor/lib/Rom.py
"""


import zlib, re
from itertools import count

"""
Identify the ROM game and version based on the CRC and instantiate the
appropriate Rom class.
"""
def load(filename):
    fs = open(filename, 'rb')

    fs.seek(0x20)
    assert fs.read(0x10) == b"GOLDENEYE       "

    fs.seek(0x3b)
    VERSION = fs.read(4)

    if VERSION == b"NGEJ":
        rom = GeJapFinalRom()
    elif VERSION == b"NGEE":
        rom = GeNtscFinalRom()
    elif VERSION == b"NGEP":
        rom = GePalFinalRom()
    else:
        print('Unrecognised ROM version')
        exit(1)

    rom.setFp(fs)
    return rom, VERSION.decode()[-1].lower()


class Rom:
    fp = None
    mdf = None

    def setFp(self, fp):
        self.fp = fp
        return self

    def getGame(self):
        return self.GAME

    """
    Read and extract the 0x21990 (GE) or 0x39850 (PD) data file and store it in
    self.mdf.
    """
    def loadMainDataFile(self):
        self.fp.seek(self.MDF_ROM_ADDRESS)
        buffer = self.fp.read(200000)       # Overlarge, deflate knows where the end
        self.mdf = self.inflate(buffer)

    """
    Read and return the common functions and stage-specific functions.
    We just return the functions as a block of bytes and don't try to read the
    individual instructions here.
    """
    def getFunctions(self):
        self.loadMainDataFile()
        functions = self.readFunctions(self.mdf, self.GLOBAL_FUNCTIONS_ADDRESS, self.MDF_MEM_ADDRESS, 0)
        for index, file_id in enumerate(self.SETUP_FILE_IDS):
            setup_file = self.getFile(file_id)
            functions = functions + self.readStageFunctions(setup_file, index + 1)  # stage_id is just added to the json output
        return functions

    """
    Look up the file ID in the MDF's file list, then return a buffer containing
    the file data. The file may be compressed.
    """
    def getFile(self, file_id):
        start_address, end_address = self.findFile(file_id)
        self.fp.seek(start_address)
        return self.fp.read(end_address - start_address)

    def findFile(self,file_id):
        offset = self.FILELIST_ADDRESS + file_id * self.FILE_ENTRY_LENGTH + self.FILE_ENTRY_OFFSET
        nxt = offset + self.FILE_ENTRY_LENGTH
        start_address = int.from_bytes(self.mdf[offset:offset+4], 'big')
        end_address = int.from_bytes(self.mdf[nxt:nxt+4], 'big')

        return start_address, end_address

    def fileSize(self, file_id):
        s,e = self.findFile(file_id)
        return e-s

    """
    Returns the virtual address which will point to our name.
    """
    def fileNameVirtualAddr(self, file_id):
        offset = self.FILELIST_ADDRESS + file_id * self.FILE_ENTRY_LENGTH + self.VIRT_LOAD_OFFSET
        return int.from_bytes(self.mdf[offset:offset+4], 'big')

    """
    Takes a new position for each file, writes it to a copy of the existing filelist,
    which is returned
    """
    def writeNewFilePositions(self,position):
        newMDF = bytearray(self.mdf)
        assert len(position) == len(self.fileNames)
        for file_id, new_pos in enumerate(position):
            offset = self.FILELIST_ADDRESS + file_id * self.FILE_ENTRY_LENGTH + self.FILE_ENTRY_OFFSET
            newMDF[offset:offset+4] = new_pos.to_bytes(4, "big")

        return newMDF

    def readStageFunctions(self, setup_file, stage_id):
        setup_file = self.inflate(setup_file)
        offset = self.SETUP_FUNCTIONS_OFFSET
        table_address = int.from_bytes(setup_file[offset:offset+4], 'big')
        return self.readFunctions(setup_file, table_address, 0, stage_id)

    """
    Read functions out of a buffer and return them as an array.

    table_address is expected to be a buffer-local address where the functions
    table starts. The table consists of entries of 8 bytes each. 4 bytes for the
    address and 4 bytes for the function ID.

    For stage functions, the address will be buffer-local. For the common
    functions, the address will be a memory address, so we subtract the
    data_offset argument to translate it into a buffer-local address.
    """
    def readFunctions(self, buffer, table_address, data_offset, stage_id):
        pairs = []
        while True:
            offset = int.from_bytes(buffer[table_address:table_address+4], 'big')
            function_id = int.from_bytes(buffer[table_address+4:table_address+8], 'big')
            if offset == 0:
                break
            pairs.append((function_id, offset))
            table_address += 8
        pairs = sorted(pairs, key=lambda x:x[1])
        functions = []
        for index, pair in enumerate(pairs):
            start = pair[1] - data_offset
            end = table_address if index == len(pairs) - 1 else pairs[index + 1][1]
            end -= data_offset
            functions.append({
                'id': pair[0],
                'stage_id': stage_id,
                'raw': buffer[start:end],
            })
        return functions


    """
    Return the list of file names.
    Both the setup editor & ourselves keep a contigious run of file_ids, probably because it's required.
    We can just deserialise the blob of the names
    """
    def loadFileNames(self):
        addr = self.NAMES_OFFSET
        self.fileNames = []
        while True:
            currName = bytearray()
            while self.mdf[addr] != 0:
                currName.append(self.mdf[addr])
                addr += 1
            
            currName = currName.decode()
            self.fileNames.append(currName)

            if currName == "ob/ob_end.seg":
                break

            while self.mdf[addr] == 0:
                addr += 1

        self.fileIdForName = dict(zip(self.fileNames, count()))

    """
    Returns all the file IDs of foreign language
    """
    def getForeignLangFileIds(self):
        return self.getLangFileIds(True)

    def getLangFileIds(self, foreign):
        foreignTextIds = []
        lang_re = re.compile("L.*([A-Z])")

        for file_id, name in enumerate(self.fileNames):
            m = lang_re.match(name)
            if not m:
                continue
            
            langChar, = m.groups(1)
            if (langChar == self.LANG_CHAR) ^ (foreign):
                foreignTextIds.append(file_id)

        return foreignTextIds

    def getSetupFileIds(self):
        setup_re = re.compile("Usetup.*")
        l = []
        for file_id, name in enumerate(self.fileNames):
            if setup_re.match(name):
                l.append(file_id)

        return l

    def inflate(self, buffer):
        return zlib.decompress(buffer[self.ZLIB_HEADER_LENGTH:], wbits=-15)

class GeRom(Rom):
    GAME = 'ge'
    ZLIB_HEADER_LENGTH = 2
    SETUP_FUNCTIONS_OFFSET = 0x14
    FILE_ENTRY_LENGTH = 0x0c
    VIRT_LOAD_OFFSET = 0x04
    FILE_ENTRY_OFFSET = 0x08
    SETUP_FILE_IDS = [
        0x0270, # Dam
        0x026a, # Facility
        0x0276, # Runway
        0x0279, # Surface 1
        0x0278, # Bunker 1
        0x027b, # Silo
        0x0272, # Frigate
        0x027a, # Surface 2
        0x0277, # Bunker 2
        0x027c, # Statue
        0x0269, # Archives
        0x0275, # Streets
        0x0271, # Depot
        0x027d, # Train
        0x0273, # Jungle
        0x026d, # Control
        0x026c, # Caverns
        0x026e, # Cradle
        0x026b, # Aztec
        0x026f, # Egypt
        0x0274, # Credits
    ]

"""
MDF_ROM_ADDRESS = address in ROM where the main data file starts
MDF_MEM_ADDRESS = address in N64 memory where the main data file is placed
FILELIST_ADDRESS = offset in the MDF where the file table starts
GLOBAL_FUNCTIONS_ADDRESS = offset in the MDF where the global functions list starts
"""

class GeJapFinalRom(GeRom):
    MDF_ROM_ADDRESS = 0x219d0
    MDF_MEM_ADDRESS = 0x80020dd0
    FILELIST_ADDRESS = 0x252b4
    GLOBAL_FUNCTIONS_ADDRESS = 0x166ac

    NAMES_OFFSET = 0x38010  # = NTSC-U
    LANG_CHAR = "J"

class GeNtscFinalRom(GeRom):
    MDF_ROM_ADDRESS = 0x21990
    MDF_MEM_ADDRESS = 0x80020d90
    FILELIST_ADDRESS = 0x252c4
    GLOBAL_FUNCTIONS_ADDRESS = 0x166bc

    NAMES_OFFSET = 0x38010
    LANG_CHAR = "E" # != version char


class GePalFinalRom(GeRom):
    MDF_ROM_ADDRESS = 0x1f850
    MDF_MEM_ADDRESS = 0x8001ec50
    FILELIST_ADDRESS = 0x1fe74
    GLOBAL_FUNCTIONS_ADDRESS = 0x138ac

    NAMES_OFFSET = 0x2eba0
    LANG_CHAR = "P" # Interesting :) 