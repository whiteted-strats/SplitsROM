import sys, json, base64, zlib, re, argparse
from itertools import count
from rom import load as loadRom
from util import *

def main():

    # Parse arguments
    parser = argparse.ArgumentParser(description="Dumps out the compressed setup files and title text")
    parser.add_argument("output_dirc", help="The directory to dump the files to")
    parser.add_argument("input_rom", help="input rom to dump")
    args = parser.parse_args()
    print("")

    # Load the rom
    rom, version_char = loadRom(args.input_rom)
    rom.loadMainDataFile()
    rom.loadFileNames()
    
    
    # Get the files
    setup_file_ids = rom.getSetupFileIds()
    lang_title_file_id = rom.fileIdForName["Ltitle" + rom.LANG_CHAR]
    lang_gun_file_id = rom.fileIdForName["Lgun" + rom.LANG_CHAR]

    # Dump the setups
    for file_id in setup_file_ids:
        short_fn = rom.fileNames[file_id]
        storage_fn = "{}.{}.set.1172".format(short_fn, version_char)
        fp = os.path.join(args.output_dirc, storage_fn)
        print("Dumping {} ..".format(short_fn))
        with open(fp, "wb") as fs:
            fs.write(rom.getFile(file_id))

    # Dump the title file
    print("\nDumping title language..")
    storage_fn = "{}.{}.lng.1172".format("Ltitle" + rom.LANG_CHAR, version_char)
    with open(os.path.join(args.output_dirc, storage_fn), "wb") as fs:
        fs.write(rom.getFile(lang_title_file_id))

    # Dump the gun file
    print("Dumping gun language..")
    storage_fn = "{}.{}.lng.1172".format("Lgun" + rom.LANG_CHAR, version_char)
    with open(os.path.join(args.output_dirc, storage_fn), "wb") as fs:
        fs.write(rom.getFile(lang_gun_file_id))

    print("Done.")

if __name__ == "__main__":
    main()