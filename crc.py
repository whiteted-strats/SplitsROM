import argparse

def getTrueChecksum(romData):
    # Goldeneye (hopefully)
    in_lo = 0xF8CA4DDB
    rom_ptr = 0x400 + 0xc00

    # Init
    xs = in_lo + 1
    lowPrev = xs
    hs = xs
    x = xs
    y = xs
    ss = xs

    for i in range(0, 0x100000, 4):
        romVal = int.from_bytes(romData[rom_ptr:rom_ptr+4], "big")

        ls = (lowPrev + romVal) & 0xFFFFFFFF
        if (ls < lowPrev):
            hs = (hs + 1) & 0xFFFFFFFF  # safety first
        
        roll = romVal & 0x1f    # v1
        low = (romVal >> (0x20 - roll)) # t8
        high = ((romVal << roll) & 0xFFFFFFFF)  # t6
        shiftedRomVal = low | high

        x = x ^ romVal
        ss = (ss + shiftedRomVal) & 0xFFFFFFFF

        if (xs < romVal):
            shiftedRomVal = ls ^ romVal
        
        xs = shiftedRomVal ^ xs
        rom_ptr = rom_ptr + 4

        y = ((romVal ^ ss) + y) & 0xFFFFFFFF
        lowPrev = ls


    A = ls ^ hs ^ x     # a3, t2, t3
    B = ss ^ xs ^ y     # s0, a2, t4
    A,B = [i.to_bytes(4,"big") for i in [A,B]]
    checksum = A + B

    return checksum


def main(romFp):
    with open(romFp, "rb") as fs:
        romData = fs.read()

    if (
        romData[0x066C:0x0670] == bytes(4) or
        romData[0x0678:0x067C] == bytes(4)
    ):
        print("[!] Warning - CIC check disabled in BOOT")

    trueChecksum = getTrueChecksum(romData)
    romChecksum = romData[0x10:0x18]

    if romChecksum == trueChecksum:
        print("[+] Good checksum - no action")
        return

    print(f"[ ]  Rom checksum is: {romChecksum.hex()}")
    print(f"[ ] True checksum is: {trueChecksum.hex()}")

    with open(romFp, "wb") as fs:
        fs.write(romData[:0x10])
        fs.write(trueChecksum)
        fs.write(romData[0x18:])
    print("[+] Checksum corrected in file")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("rom")
    args = p.parse_args()
    main(args.rom)