# SplitsROM
Tools for adding split statistics to Goldeneye -U, -J and PAL roms.

Born in the fires of Runway 21 and Frigate 2.3 development, these modular assembly edits & tools allow you to replace the hit statistics in the endscreen with scrollable splits, and add a few QOL changes. It probably would have been easier to do using the decomp project, but assembly hacking is very fun.

## Mechanics

The setup editor [https://github.com/carnivoroussociety/GoldEditor#downloads] can be used to add game scripts to setup files (for any version). These scripts include the AD command, which is normally a comment that is ignored by the GE rom. We hook this code to add our own command with comments:
!cmd split N(N) [Split name]
i.e.
!cmd split 09 Split #10
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
* **/files** setups & scripts
    
## Nuances
* the setup editor only supports the NTSC-U rom, but the setup files are version-free. It's text editor is kinda handy but it garbles japanese text so you have to do some copy & paste to restore them. 
* patch_manager.py must be run as a ghidra script on the appropriate ROM. It was easier to develop the edits here, though feel free to add support for keystone if you like.
* injector.py shrinks all foreign language text files to size 0 (rather than actually delete them), and once it's done this once it will forget about any extra free space that it has. So inject all your files in one go please :)
* when importing scripts, the setup editor will silently redirect functions calls to 0001 if the function that was being called doesn't exist. This caught me out when moving Statue to NTSC-J.
* probably some I've forgotten about

    
      
