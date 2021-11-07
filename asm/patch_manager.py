from binascii import hexlify
from lib.api import API
from lib.version_constants import MemoryAddress

acceptable_versions = [
    "NTSC-U",
    "NTSC-J",
    "PAL",  # :) 
]

in_fn = r"GE_p_unlocked.z64"
out_fn = r"GE_P_splits_asm.z64"

# Deduce the VERSION
with open(in_fn, "rb") as fs:
    fs.seek(0x3b)
    VERSION = fs.read(4)

VERSION = {
    b"NGEE" : "NTSC-U",
    b"NGEJ" : "NTSC-J",
    b"NGEP" : "PAL",
}.get(VERSION, VERSION)

assert VERSION in acceptable_versions, "Unsupported version {}".format(VERSION)

print("Version recognised as {}".format(VERSION))

# =================================================

api = API(VERSION, currentProgram)

# Lazily extend api with our splits buffer & name buffer
# Our buffers are in the compressed LgunE and LtitleE files
splitsBuffer = {
    "NTSC-U" : 0x802AC1C0,
    "NTSC-J" : 0x802AC140,
    "PAL" : 0x8029C1C0  # [-U] -0x10000 + 0x0
}[VERSION] + 0x10   # Note the + 0x10
namesBuffer = {
    "NTSC-U" : 0x802AD160,
    "NTSC-J" : 0x802AD170,
    "PAL" : 0x8029D180 # [-U] -0x10000 + 0x20 (more items of text)
}[VERSION]

api.splitsBuffer = MemoryAddress(splitsBuffer)
api.namesBuffer = MemoryAddress(namesBuffer)


# =================================================

##from modules.asm_CIC_checks import NoCicCheckPatch
from modules.asm_fast_pause_patch import FastPausePatch
from modules.asm_start_2_3 import Start2_3Patch
from modules.asm_ammo_shows_fullspeed import AmmoWithFullspeedPatch
from modules.initial_full_speed import InitialFullSpeed
from modules.replace_ammo import ReplaceAmmoDisplay

from modules.splits.asm_zero_splits import ZeroSplitsPatch
from modules.splits.asm_split_command import SplitCommandPatch
from modules.splits.asm_show_splits import ShowSplitsPatch

from modules.condensed_text import CondensedTextPatch


## SELECT which modules to apply

modules = [
    ## NoCicCheckPatch,     # Repairing the CRC properly now
]

## Splits rom
modules.extend([
    ZeroSplitsPatch,
    SplitCommandPatch,
    ShowSplitsPatch,
    CondensedTextPatch
])

for m in modules:
    m.apply_patch(api)

api.commit(out_fn, in_fn)