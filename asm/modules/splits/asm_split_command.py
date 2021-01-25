"""
Provides for a split command in the game's scripts, accessed by a comment "!cmd split # NAME"
It writes the current mission time to buffer[#]
Change 'storeValue' to store a different value (i.e. global_timer)

Reading the code section is permitted by the N64 :)
"""

# MEMORY LAYOUT:
#   [-0xc]  - follower of 067CA4, the input
#   [-0x8]  - displayIndex (reset to 0)
#   [-0x4]  - max index     (reset to 0)
#   [ 0x0]  - splitsBuffer

#   [?]  - namesBuffer[4*64]


from lib.version_constants import MemoryAddress

class SplitCommandPatch:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):
        
        funcAddr = api.getScratchSpaceAddr()

        # (0) Patch the hit-updater function.. to not update
        # This isn't actually necessary. I was going to use the hit statistics to point to the names / splits buffers.
        hit_function_update = {
            "NTSC-U" : 0x9f258,
            "NTSC-J" : 0x9f884,
            "PAL" : 0x9d8c0,
        }[api.VERSION]
        api.asm("{:x}".format(hit_function_update), "addiu t0, t9, 0x0")    # 0x1 previously
        api.asm("{:x}".format(hit_function_update + 0x4), "nop")            # store previously


        # (1) Patch Cmd ID 0xAD (debug comment)'s little code block,
        #   to jump to our function rather than determining the command length
        # (We'll call the command length function inside ours)
        
        exec_comment_call_to_cmd_length = {
            "NTSC-U" : 0x6d24c,
            "NTSC-J" : 0x6d58c,
            "PAL" : 0x6b14c,
        }[api.VERSION]
        api.asm("{:x}".format(exec_comment_call_to_cmd_length), "jal 0x{:x}".format(api.virtualise(funcAddr)))
        # Delay slot is a1 = s2 in -U & -J & PAL

        
        # Prep relevant memory addresses
        maxIndex = api.splitsBuffer - 0x4
        storeValue = api.MemConst.mission_timer
        assert maxIndex.lui_instr("r") == api.splitsBuffer.lui_instr("r")


        # (2) Write our function
        # OUTPUT:   v0, the output from determine_command_length @ (7)f0349fc [NTSC-U]
        # s1 is available to us, as it's recomputed as s2 + s6
        LOOP_A = 14
        UPDATE_MAX = 32
        STORE = 38
        DO_COPY = 52
        SUFFIX = 61
        DATA = 70
        funcInstrs = [
            # Call the function we replaced.. before we mess with the stack pointer :)
            # Save ra
            "or s1, zero, ra",
            "jal 0x{:x}".format(api.virtualise(api.InstrConst.script_cmd_length)),
            "nop",
            # => The length is now in v0
            

            # PREFIX, store t0-4
            "addiu sp, sp, -0x10",
            "sw t0, 0x0(sp)",
            "sw t1, 0x4(sp)",
            "sw t2, 0x8(sp)",
            "sw t3, 0xc(sp)",


            # --- CHECK COMMENT ---
            # Look to see if the comment begins with "!cmd split"
            # v0 will be added to S2, the script offset, so we know this includes AD and the 00
            # => length 12 + 2 = E
            "sltiu t2, v0, 0xE",
            "bne t2, zero, 0x{:x}".format(funcAddr + 0x4*SUFFIX),
            "addu t0, s2, s6",

            # t0 + 1 the pointer into the comment
            # t1 = *t0
            # t2 the pointer into the 'answer'
            # t3 = *t2
            # Detect the end using t3 == 't'
            # This is reading the data at the end of the code.
            # It's legacy code so don't touch it ;) but it could be a lot cleaner
            "lui t2, 0x{:x}".format( 0x7000 | ( api.virtualise(funcAddr) >> 16 ) ),
            "li t3, 0x{:x}".format((api.virtualise(funcAddr) + 0x4*DATA) & 0xFFFF),
            "addu t2, t2, t3",

            # DO A
            "lb t1, 0x1(t0)",
            "lb t3, 0x0(t2)",
            "bne t1, t3, 0x{:x}".format(funcAddr + 0x4*SUFFIX),
            "addiu t0, t0, 0x1",
            "li t1, 0x{:x}".format(ord('t')),
            "bne t3, t1, 0x{:x}".format(funcAddr + 0x4*LOOP_A),
            "addiu t2, t2, 0x1",


            # --- READ INDEX ---
            # t0 currently points to the 't' in the user comment
            # so skip this and the space to read the values
            # '0' = 0x30 so we reduce both characters to their lower 4 bits
            "lb t1, 0x3(t0)",
            "lb t0, 0x2(t0)",
            "andi t0, t0, 0xF",

            # If t1 is actually \x00 (i.e. "!cmd split 3") or space (i.e. "!cmd split 4 hello") then we're done
            "beq t1, zero, 0x{:x}".format(funcAddr + 0x4*UPDATE_MAX),
            "li t2, 0x20",
            "beq t1, t2, 0x{:x}".format(funcAddr + 0x4*UPDATE_MAX),
            "andi t1, t1, 0xF",

            # t0 = 10 * t0 + t1
            "sll t2, t0, 0x2",  # * 4
            "addu t2, t2, t0",  # + x
            "sll t0, t2, 0x1",  # * 2
            "addu t0, t0, t1",


            # --- UPDATE MAX INDEX ---
            maxIndex.lui_instr("t1"),
            "lw t2, {}".format(maxIndex.offset_term("t1")),
            "sltu t3, t2, t0",  # t3 = (MAX_INDEX < t0)
            "beq t3, zero, 0x{:x}".format(funcAddr + 0x4*STORE),
            storeValue.lui_instr("t2"), 
            "sw t0, {}".format(maxIndex.offset_term("t1")),

            
            # --- STORE SPLIT ---
            "lw t2, {}".format(storeValue.offset_term("t2")),     # = MISSION / GLOBAL TIMER
            "sll t0, t0, 2",
            "addu t1, t1, t0",
            "sw t2, {}".format(api.splitsBuffer.offset_term("t1")),     # Relies on assertion above

            # ==============================================
            # --- STORE STRING POINTER ---
            "sll t0, t0, 2",    # * 4 compared to storing the split
            api.namesBuffer.lui_instr("t2"),
            "addu t0, t0, t2",

            "addu t1, s2, s6",
            "addiu t1, t1, 0xD",    # 1 for [AD] then "!cmd split X"
            "li t2, 0x20",   # Space
            "lb t3, 0x0(t1)",
            "bnel t2, t3, 0x{:x}".format(funcAddr +0x4*(DO_COPY-1)),
            "addiu t1, t1, 0x1",    # Advance if it's not a space

            # t1 now points to just after the split #, whether it was 1 or 2 digits
            # And namesBuffer.offset_term(t0) points to the buffer we want to copy to
            # Copy until we reach a zero or exceed our limit of 14 (total string is length 16)
            "li t3, 0xE",

            # ---- DO_COPY ------------
            "lb t2, 0x0(t1)",   # Read value  
            "sb t2, {}".format(api.namesBuffer.offset_term("t0")),       # Store  
            "beq t2, zero, 0x{:x}".format(funcAddr + 0x4*(SUFFIX)),
            "addiu t3, t3, -0x1",   # Decrement counter
            "beq t3, zero, 0x{:x}".format(funcAddr + 0x4*(SUFFIX-1)),   # Branch to add a zero
            "addiu t0, t0, 0x1",    # Advance dest
            "b 0x{:x}".format(funcAddr + 0x4*DO_COPY),
            "addiu t1, t1, 0x1",    # Advance source

            # Insist that there's a zero on the end
            #   (t0 was advanced before we left)
            "sb zero, {}".format(api.namesBuffer.offset_term("t0")),

            # ===========================================

            # SUFFIX, restore t0,t1,t2,t3
            # And restore ra from s1
            "lw t0, 0x0(sp)",
            "lw t1, 0x4(sp)",
            "lw t2, 0x8(sp)",
            "lw t3, 0xc(sp)",
            "or ra, zero, s1",
            "jr  ra",
            "addiu sp, sp, 0x10",
            "nop",
            "nop",  # KEEP this padding, data below.
        ]

        for i in range(len(funcInstrs)):
            api.nop_quietly(hex(funcAddr+i*4))

        for i, instr in enumerate(funcInstrs):
            api.asm(hex(funcAddr+i*4), instr)

        # Append the data
        cmd = bytearray("!cmd split\x00\x00".encode())
        assert len(cmd) % 4 == 0
        dataAddr = funcAddr + 4*len(funcInstrs)
        for i, word in enumerate([cmd[j:j+4] for j in range(0, len(cmd), 4)]):
            api.store_directly("{:x}".format(dataAddr + i*4), word) # not 0x anymore
        

