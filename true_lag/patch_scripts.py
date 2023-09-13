import struct
from cmd_lengths import instructionSizes
import os
from binascii import unhexlify
import json
import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("script_dirc")
    p.add_argument("write_fp")
    args = p.parse_args()

    with open(os.path.join(args.script_dirc, "script_seg_info.json"), "r") as fs:
        script_seg_info = json.load(fs)

    scriptInstrs = {}
    scriptLocs = {}

    # Read the scripts in
    for sc_fp in os.listdir(args.script_dirc):
        _, ext = os.path.splitext(sc_fp)
        if ext != ".act":
            assert ext == ".json"
            continue

        instrs = []

        with open(os.path.join(args.script_dirc, sc_fp), "r") as fs:
            n = sc_fp[:-4]

            for ln in fs:
                ln = ln.strip()
                if ln == "END":
                    instrs.append((0x4, bytes()))
                    continue

                if ln == "":
                    continue    # allow ourselves some blank lines
                
                cmd = int(ln[:2], 16)
                if cmd == 0xad:
                    data = bytes(ln[2:].replace("*", "\n") + "\x00","ascii")
                else:
                    data = unhexlify(ln[2:])
                    assert len(data) == instructionSizes[cmd] - 1
                instrs.append((cmd, data))
            
            assert instrs[-1][0] == 0x4, f"{sc_fp} missing terminator"
            scriptInstrs[n] = instrs

    ##assert set(scriptInstrs.keys()) == set(scriptOrder)

    # Start injecting
    with open(args.write_fp, "r+b") as fs:
        # Set script footer start
        fs.seek(0x14)
        SCRIPT_FOOTER_START = int.from_bytes(fs.read(0x4), "big")

        # Clear
        fs.seek(script_seg_info['SCRIPT_DATA_START'])
        fs.write(bytes(script_seg_info['SCRIPT_FOOTER_END'] - script_seg_info['SCRIPT_DATA_START']))

        # Write each of the scripts, recording position
        fs.seek(script_seg_info['SCRIPT_DATA_START'])
        for sn in scriptInstrs.keys():
            scriptLocs[sn] = fs.tell()
            for cmd, data in scriptInstrs[sn]:
                fs.write(bytes([cmd]) + data)
            p = fs.tell()
            fs.write(bytes(-p % 4))

        # We could probably relocate the footer but for now we won't
        spareDataSpace = SCRIPT_FOOTER_START - fs.tell()
        assert spareDataSpace >= 0, f"Need {-spareDataSpace} bytes more space"
        print(f"0x{spareDataSpace:x} bytes spare script data space")
        fs.seek(SCRIPT_FOOTER_START)
        
        # Write the footer, in ascending order
        footerScriptOrder = [int(sn,16) for sn in scriptInstrs.keys()]
        footerScriptOrder.sort()
        for isn in footerScriptOrder:
            sn = f"{isn:04X}"
            l = scriptLocs[sn]
            fs.write(struct.pack(">ii", l, isn))
            ##print(f"Wrote {sn} to header..")

        fs.write(bytes(8))
        spareFooterSpace = script_seg_info['SCRIPT_FOOTER_END'] - fs.tell()
        assert spareFooterSpace >= 0
        print(f"{spareFooterSpace // 8} spare functions in footer")

    print("[+] Injected")


if __name__ == "__main__":
    main()