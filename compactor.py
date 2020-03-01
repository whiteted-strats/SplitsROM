import argparse
import os.path

# Header (non-zero, any)
header = b"WT"
assert len(header) == 2
assert header[0] != 0

# Parse args
parser = argparse.ArgumentParser(description="Compacts text files, preserving file size but consolidating a contiguous block of zeros.")
parser.add_argument("input_file", help="decompressed text file input")
args = parser.parse_args()


# Read input and parse offsets. These must all fit in 2 bytes for us to compact them.
with open(args.input_file, "rb") as fs:
    data = fs.read()

textStart = int.from_bytes(data[:4], "big")
offsets = [int.from_bytes(data[i:i+4], "big") for i in range(0, textStart, 4)]
assert offsets[-1].bit_length() < 16, "Unable to compact final offset"


# Write output as header | halfwords | zeros | text
stem, ext = os.path.splitext(args.input_file)
output_file = stem + ".cmpr" + ext

halfwords = [(offset).to_bytes(2, "big") for offset in offsets]
with open(output_file, "wb") as fs:
    fs.write(header)
    for hw in halfwords:
        fs.write(hw)

    fs.write(bytes(2*len(offsets) - 2))
    fs.write(data[textStart:])

print("Done.")
