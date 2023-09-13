import struct
from cmd_lengths import instructionSizes
import os
from binascii import unhexlify
from glob import glob
import json
import argparse

def readScript(fs):
    instrs = []

    while True:
        cmd = fs.read(1)[0]

        if cmd == 0xad:
            byte = cmd
            chars = []
            while byte != 0:
                byte = fs.read(1)[0]
                chars.append(byte)
            data = bytes(chars)

            
        else:
            assert cmd < 0xfd
            data = fs.read(instructionSizes[cmd] - 1)

        instrs.append((cmd, data))
        
        if cmd == 0x4:
            break

    return instrs

def readAllScripts(fs, scriptLocs, scriptInstrs, script_footer_start):
    scriptRanges = []

    for n, start in scriptLocs.items():
        fs.seek(start)
        scriptInstrs[n] = readScript(fs)

        end = fs.tell()
        end += (-end) % 4

        scriptRanges.append((start, end))

    # The scripts don't necessarily form a block..
    # .. we have to discover hidden scripts within :)
    hidden_script_count = 0

    scriptRanges.sort()
    for s1,s2 in zip(scriptRanges, scriptRanges[1:] + [(script_footer_start,)]):
        if s1[-1] == s2[0]:
            continue

        pos = s1[-1]
        gap_end = s2[0]
        print(f"Gap discovered 0x{pos:x} -> 0x{gap_end:x}")

        while pos < gap_end:
            n = f"_hidden_{hidden_script_count}"
            scriptLocs[n] = pos
            fs.seek(pos)
            scriptInstrs[n] = readScript(fs)

            pos = fs.tell()
            pos += (-pos) % 4
            hidden_script_count += 1
        
        assert pos == gap_end

    if hidden_script_count > 0:
        print(f"[!] Found {hidden_script_count} 'hidden' extra scripts")

    SCRIPT_DATA_START = scriptRanges[0][0]
    return SCRIPT_DATA_START

def main_dump(read_fp, script_dirc, includeComments=True):
    os.makedirs(script_dirc)

    with open(read_fp, "rb") as fs:
        scriptLocs = {}
        scriptInstrs = {}

        fs.seek(0x14)
        script_footer_start = int.from_bytes(fs.read(0x4), "big")

        # Read the locations of the scripts
        fs.seek(script_footer_start)
        while True:
            p, n = struct.unpack(">ii", fs.read(8))
            if p == 0:
                assert n == 0
                break
            scriptLocs[f"{n:04X}"] = p

        # Print the odd order that they're in
        scriptOrder = sorted(scriptLocs.keys(), key=lambda k:scriptLocs[k])
        print("Reading scripts: " + ', '.join([f"'{n}'" for n in scriptOrder]))

        # Read the scripts, checking that all the data forms a single block
        SCRIPT_FOOTER_END = fs.tell()
        SCRIPT_DATA_START = readAllScripts(fs, scriptLocs, scriptInstrs, script_footer_start)
        print(f"Script data confirmed blob 0x{SCRIPT_DATA_START:x} -> 0x{script_footer_start:x} -> 0x{SCRIPT_FOOTER_END:x}")
        with open(os.path.join(script_dirc, "script_seg_info.json"), "w") as fs:
            json.dump({
                "SCRIPT_DATA_START" : SCRIPT_DATA_START,
                "SCRIPT_FOOTER_END" : SCRIPT_FOOTER_END,
            }, fs)

        # Dump the script in GE editor style
        for sn, si in scriptInstrs.items():
            with open(os.path.join(script_dirc, f"{sn}.act"), "w") as fs:
                for cmd, data in si:
                    if cmd == 0xad:
                        if includeComments:
                            s = data[:-1].decode().replace("\n", "*")
                            fs.write("AD" + s + "\n")
                    elif cmd == 0x4:
                        fs.write("END")
                    else:
                        fs.write(f"{cmd:02X}" + data.hex().upper() + "\n")

        print("[+] Dumped scripts")
        
def main():
    p = argparse.ArgumentParser()
    p.add_argument("setups_folder")
    p.add_argument("dumps_folder")
    args = p.parse_args()

    # For each setup in the folder..
    for setup_fp in glob(f"{args.setups_folder}/*.set"):
        i = setup_fp.index(os.sep)
        script_dirc = setup_fp[i+1:-4].replace(".","_")
        print(setup_fp, script_dirc)
        main_dump(setup_fp, os.path.join(args.dumps_folder, script_dirc))
        print("\n\n")

if __name__ == "__main__":
    main()