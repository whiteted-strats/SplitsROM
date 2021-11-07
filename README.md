# SplitsROM
Tools for adding split statistics and other tweaks to Goldeneye -U, -J and PAL roms
Also now the proper home of the compiled splits roms and the relevant setups.

Born in the fires of Runway 21 and Frigate 2.3 development, these modular assembly edits & tools allow you to replace the hit statistics in the endscreen with scrollable splits, and add a few QOL changes. It probably would have been easier to do using the decomp project, but assembly hacking is very fun.

## Compiling splits roms
1. Take selected projects from files/all_projects and copy their contents into include_setups.
2. Compress all these files, and move the 1172 files into the 1172 folder.
3. Be sure to include your versions' Ltitle.cmpr and Lgun.cmpr files - including all 6 is fine, get these from /files/gun_and_title_texts if they aren't already there
4. Run the injector i.e:
  py -3 sl\injector.py files\splits_roms\NTSC_U_splits_echo.z64 files\splits_roms\u.mdf files\base_roms\splits_asm_base\GE_U_splits_asm.z64 files\include_setups\1172
5. Hopefully there was enough space (if not, what did you do :O). Compress the mdf file (u.mdf in this example) using the setup editor (tools -> compress file) as instructed.
6. Copy the compressed mdf file into the rom at the address which was specified at the end of step 4. I cba to write a script to do this. If it's shorter then write some zeros after it. Be sure not to extend the size of the rom. If using HxD, use ctrl-B.
7. Run crc.py on the file to fix the checksum


## Mechanics

The setup editor [https://github.com/carnivoroussociety/GoldEditor#downloads] can be used to add game scripts to setup files (for any version). These scripts include the AD command, which is normally a comment that is ignored by the GE rom. We hook this code to add our own command with comments:

*!cmd split N(N) [Split name]*

i.e. *!cmd split 09 Split #10*

when executed will store the current mission time to the 10th split, and call it "Split #10"

Names & splits are stored to 2 separate buffers. Originally I thought I could just find some memory somewhere but I had a lot of crashes on console (though emu doesn't mind :) ). So I've added support for a more compact text file (asm/modules/condensed_text.py). The Lgun & Ltitle text files must be compacted, and their zero buffers must be hardcoded into patch_manager.py. The existing values shouldn't need changing provided you only edit setups & level text files.

In the endscreen, the correct splits are dynamically copied to entries 0x6D to 0x70 of Ltitle. Note that these are length 20, and the 3rd & 4th characters are never overwritten. I've set them to " -" so that the splits read "03 - My split text". Both split buffers are zeroed when the level loads. Up to 32 splits can be stored.

## Broad structure
* **asm**
* **asm/lib**
* **asm/lib/api.py** interfaces with modules, i.e. by offering the "getScratchSpaceAddr" function for edits which need extra code space
* **asm/lib/version_constants.py** sets useful memory addresses. These have .lui_instr(reg) and .offset_term(reg) functions for modules to use
* **asm/modules** contains all of the assembly edits. /splits has the more substantial ones
* **asm/patch_manager.py** run me in *ghidra* after hardcoding in_fn and out_fn. Select which modules you want to apply.
* **setup_logistics**
* **sl/rom.py** adapted from [https://gitlab.com/ryandwyer/gepd-function-explorer/-/blob/master/extractor/lib/Rom.py], gives access to how files are stored inside the different ROM versions.
* **sl/dumper.py** gets files out of all ROM versions.
* **sl/compare.py** is a helper for comparing hashes. Most but not all -J & -U setups are identical.
* **sl/injector.py** is the main function for injecting editted files
* **sl/text_compactor** compacts text! Needs the text_condenser module (eh the names are similar) else GE will try to access well beyond the end of the text file and crash. This module still supports normal text :)  
* **/files/** 
* **/files/base_roms/** has unlocked carts (with good crcs) and "splits base" roms which have been created using the patch_manager here, adding just the splits tweaks.
* **/files/gun_and_title_texts** are specially tweaked files used by the splits rom, and much be included when injecting.
* **/files/all_projects** contains a folder for each 'project' which has been made - usually creating splits for a single difficulty
* **/files/include_setups/** copy your selected setup files (and any text files) into here when creating the rom
* **/files/include_setups/1172** compress said files into here - and be sure to include Ltitle and Lgun files
* **/files/splits_roms/** final output files :)

## Nuances
* the setup editor only supports the NTSC-U rom, but the setup files are version-free. It's text editor is kinda handy but it garbles japanese text so you have to do some copy & paste to restore them. 
* patch_manager.py must be run as a ghidra script on the appropriate ROM. It was easier to develop the edits here, though feel free to add support for keystone if you like.
* injector.py shrinks all foreign language text files to size 0 (rather than actually delete them), and once it's done this once it will forget about any extra free space that it has. So inject all your files in one go please :)
* when importing scripts, the setup editor will silently redirect functions calls to 0001 if the function that was being called doesn't exist. This caught me out when moving Statue to NTSC-J.
* probably some I've forgotten about
* do all your compression using the setup editor
* you currently can't use any cheats on splits, since the function which is called when activating a cheat is used as scratch space by modules (including the splits modules)