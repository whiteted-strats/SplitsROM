import sys, json, base64, zlib, re, argparse
from itertools import count
from rom import load as loadRom
from util import *



def main():

    # Parse arguments
    parser = argparse.ArgumentParser(description="Injects replacement setup files into a rom, deleting foreign text to create extra room.")
    parser.add_argument("output_rom", help="output rom with updated files, but out-of-date '21990' file")
    parser.add_argument("output_mdf", help="new decompressed '21990' file. Compress it via GE editor.")
    parser.add_argument("input_rom", help="input rom to inject")
    parser.add_argument("setup_dirc", help="input setup files directory")
    args = parser.parse_args()
    print("")

    # Load the rom
    rom, version_char = loadRom(args.input_rom)
    rom.loadMainDataFile()
    rom.loadFileNames()
    FILE_COUNT = len(rom.fileNames)

    # Get all the injection files, {name -> compressed_data}
    injection_files = getInjectionFiles(args.setup_dirc)
    print("{} files discovered in the supplied directory.".format(len(injection_files)))


    # Filter out unrecognised filenames, and compute the extra space that we'll need
    # Some of the new files may be smaller, and we do benefit from this
    reqSpace = sieveInjectionFiles(rom, injection_files)
    print("")

    
    # Calculate the available space from removing foreign text (~33KB)
    # More for PAL because it has E, J and P text (bizarre)
    foreignLangFileIds = set(rom.getForeignLangFileIds())
    availableSpace = sum([rom.fileSize(file_id) for file_id in foreignLangFileIds])
    

    print("{} extra space required, {} available from removing foreign text.".format(reqSpace, availableSpace))
    if reqSpace > availableSpace:
        print("NOT ENOUGH SPACE.")
        return

    print("Proceeding..")


    # Compute the new positions, and collate the new files
    # Note that we can't read ob/ob_end.seg
    FILES_START = rom.findFile(0)[1]
    FILES_END = rom.findFile(FILE_COUNT - 1)[0]
    newFilesBuffer, newPositionForID = collateNewFiles(rom, FILES_START, foreignLangFileIds, injection_files)


    # Output
    newMDF = rom.writeNewFilePositions(newPositionForID)

    with open(args.output_mdf, "wb") as fs:
        fs.write(newMDF)

    with open(args.output_rom, "wb") as ofs:
        rom.fp.seek(0)
        data = rom.fp.read(FILES_START)
        data += newFilesBuffer
        data += bytes(availableSpace - reqSpace)
        assert len(data) == FILES_END
        rom.fp.seek(len(data))
        data += rom.fp.read()

        ofs.write(data)


    print("\nDone.")
    print("Compress the mdf '21990' file and write it to 0x{:x}".format(rom.MDF_ROM_ADDRESS))


if __name__ == "__main__":
    main()