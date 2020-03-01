import os
from itertools import count

"""
'UsetupdestZ.j.1172' -> 'UsetupdestZ', rather than including the '.j' to return the whole stem
This is useful because we can have
  .1172 for the editor to recognise,
  .j for the user to recognise
and the filename for the rom to recognise.
"""
def getFilenamePrefix(filename):
    index = filename.find(".")
    if index == -1:
        return filename
    return filename[:index]


def getInjectionFiles(setup_dirc):
    injection_files = dict()
    for fn in os.listdir(setup_dirc):
        fp = os.path.join(setup_dirc, fn)
        if not os.path.isfile(fp):
            continue

        with open(fp, "rb") as fs:
            data = fs.read()
            if data[:2] != b"\x11\x72":
                print("  '{}' is not 1172 compressed. Ignoring..".format(fn))
                continue

            data += bytes(-len(data) % 16)
            assert len(data) % 16 == 0

            injection_files[getFilenamePrefix(fn)] = data

    return injection_files

def sieveInjectionFiles(rom, injection_files):
    fileNamesSet = set(rom.fileNames)

    reqSpace = 0
    for fn in list(injection_files.keys()):

        if fn not in fileNamesSet:
            print("  '{}' not present in current rom. Ignoring..".format(fn))
            del injection_files[fn]
            continue

        else:
            # Add the new file, remove existing
            reqSpace += len(injection_files[fn])
            reqSpace -= rom.fileSize(rom.fileIdForName[fn])

    return reqSpace

def collateNewFiles(rom, FILES_START, foreignLangFileIds, injection_files):
    
    newPositionForID = [0]
    contents = [b""]    # start
    curr_pos = FILES_START

    for file_id, fn in zip(count(1), rom.fileNames[1:-1]):

        newPositionForID.append(curr_pos)

        if file_id in foreignLangFileIds:
            contents.append(b"")
            curr_pos += 0

        elif fn in injection_files:
            contents.append(injection_files[fn])
            curr_pos += len(injection_files[fn])
        
        else:
            data = rom.getFile(file_id)
            contents.append(data)
            curr_pos += len(data)

    newPositionForID.append(curr_pos) # ob/ob_end.seg

    return b"".join(contents), newPositionForID