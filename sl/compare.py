"""
Looks at the SHA1s of compressed setups for NTSC-U/J, to see which don't require porting.
"""

from os import listdir
from os.path import isfile, join
from hashlib import sha256

j_dirc = r"ntsc_j_dumped\comp_setups"
u_dirc = r"ntsc_u_dumped\comp_setups"

for j_f in listdir(j_dirc):
    if not isfile(join(j_dirc, j_f)):
        continue

    u_f = j_f.replace(".j.", ".e.")
    try:
        with open(join(u_dirc, u_f), "rb") as fs:
            u_hash = sha256(fs.read()).hexdigest()
    except:
        print("  {} not found in NTSC-U directory".format(u_f))
        continue

    with open(join(j_dirc, j_f), "rb") as fs:
        j_hash = sha256(fs.read()).hexdigest()
    
    fn = j_f[:j_f.find(".")]
    if j_hash != u_hash:
        print("{} differs".format(fn))




