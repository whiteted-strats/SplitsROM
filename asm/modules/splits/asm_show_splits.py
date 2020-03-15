"""
Replaces the hit statistics on the final screen with our splits, supporting scrolling.
Requires Word bank 0x9C (Ltitle) and 0x98 (Lgun) compacted.
"""

# MEMORY LAYOUT:
#   [-0x10] - delta mode (0/1)
#   [-0xc]  - follower of 067CA4, the input
#   [-0x8]  - displayIndex (reset to 0)
#   [-0x4]  - max index     (reset to 0)
#   [ 0x0]  - splitsBuffer

#   [?]  - namesBuffer[4*64]


from lib.version_constants import MemoryAddress

class ShowSplitsPatch:

    # The API offers [VERSION, MemConst, InstrConst, asm, getScratchSpaceAddr, virtualise]
    @classmethod
    def apply_patch(cls, api):
        
        funcAddr = api.getScratchSpaceAddr()

        formatStr = MemoryAddress({
            "NTSC-U" : 0x8005180C,
            "NTSC-J" : 0x8005183C,
            "PAL" : 0x80047934,
        }[api.VERSION])

        format_calls = {
            "NTSC-U" : [0x4c11c, 0x4c250, 0x4c38c, 0x4c4d8],
            "NTSC-J" : [0x4c20c, 0x4c340, 0x4c47c, 0x4c5c8],    # + 0xF0
            "PAL" : [0x49f38, 0x4a06c, 0x4a1a8, 0x4a2f4]
        }[api.VERSION]

        strFormatVirtualAddr = {
            "NTSC-U" : 0x0000ac94,
            "NTSC-J" : 0x0000aca4, # +0x10
            "PAL" : 0x0000a0f4, # acf4 physical
        }[api.VERSION]


        # Inject into the 'prelude's to the 4 calls to the string formatting function
        # Each has the same form (BEFORE our edit):
        """
            lui a1 0x8005/4
            addiu a1,a1, X
            addiu a0,sp, 0xa8
            mfc1 a3,fY
            jal        (string format)@7000ac94
            [set a2]
        """

        # We fix X to pick our string format,
        #   and replace the 2 instructions before the jal with a call to our function
        for i, jal_addr in enumerate(format_calls):
            instrs = [
                formatStr.lui_instr("a1"),  
                "addiu a1,a1,{}".format(hex(formatStr.low)),    # a1 = formatStr
                "jal 0x{:x}".format(api.virtualise(funcAddr)),
                "li a0, 0x{:x}".format(i),
                                    # <- jal_addr points here
                "jal 0x{:x}".format(strFormatVirtualAddr),    # call the format function (no change) (7 implied)
                "nop",              # don't write over our a2 thankyouverymuch
            ]

            # Nop the area then assembly it
            for addr in range(jal_addr - 0x10, jal_addr + 0x8, 0x4):
                api.nop_quietly("{:x}".format(addr))
            
            for addr, instr in zip(range(jal_addr - 0x10, jal_addr + 0x8, 0x4), instrs):
                api.asm("{:x}".format(addr), instr)

        

        # Memory addresses that we're going to need
        deltaMode = api.splitsBuffer - 0x10
        inputFollower = api.splitsBuffer - 0xc
        displayIndex = api.splitsBuffer - 0x8
        maxIndex = api.splitsBuffer - 0x4

        # Check all of these share the same HIGH
        assert deltaMode.lui_instr("r") == api.splitsBuffer.lui_instr("r")

        wordBank9C_ptr = api.MemConst.wordBankTable + 0x9c

        # For unrolling the copy:
        assert api.namesBuffer.lui_instr("r") == (api.namesBuffer + 0xc).lui_instr("r")

        # (3) Write our function
        #   INPUT:  a0 = 0,1,2,3 the call
        #   OUTPUT: a2,a3
        #       Preserves everyone else (except ra)

        MOVE_UP = 49    # 34
        MOVE_DOWN = 56  # 41
        UPDATE_STRING = 62  # 47
        DRAW_TIMES = 104
        funcInstrs = [
            # PREFIX, save t0,t1,t2,t3,t4
            "addiu sp, sp, -0x14",
            "sw t0, 0x0(sp)",
            "sw t1, 0x4(sp)",
            "sw t2, 0x8(sp)",
            "sw t3, 0xc(sp)",
            "sw t4, 0x10(sp)",


            #  ==== Read the display index, and update it if we're the 1st call ====
            displayIndex.lui_instr("t3"),
            "lw t0, {}".format(displayIndex.offset_term("t3")),  
            "bne a0, zero, 0x{:x}".format(funcAddr + 0x4*UPDATE_STRING),    # kills t3
            api.MemConst.p1_input.lui_instr("t2"),

            "lw t1, {}".format(inputFollower.offset_term("t3")),            # t1 = Follower of the input
            "lw t2, {}".format(api.MemConst.p1_input.offset_term("t2")),     # t2 = Input
            "li t3, -0x1",                                                  # t3 = 0xFFFFFFFF, just used to bitflip
            "xor t1, t1, t3",       # ~
            "and t1, t1, t2",       # t1 = Pressed this time and not previously

            

            # ==== DELTA VERSION ADDITION - updates Delta mode ====
            # t3 usable, t2 we restore
            # .DBC: dpad, bumpers, cbuttons: we want the low 2 bits of each of those nibbles
            "srl t2, t1, 16",   # C-buttons
            "srl t3, t1, 20",
            "or t2, t2, t3",    # OR on the bumpers
            "srl t3, t1, 24",
            "or t2, t2, t3",    # OR on D-pad
            "srl t3, t2, 1",
            "or t2, t2, t3",    # OR these 2 bits. Higher bits killed below

            deltaMode.lui_instr("t3"),                      
            "lw t3, {}".format(deltaMode.offset_term("t3")),    # Read existing delta mode
            "xor t2, t2, t3",                                   # Flip low bit if a button has been pressed
            "andi t2, t2, 0x1",                                 # Kill other bits
            deltaMode.lui_instr("t3"),
            "sw t2, {}".format(deltaMode.offset_term("t3")),    # Store

            api.MemConst.p1_input.lui_instr("t2"),
            "lw t2, {}".format(api.MemConst.p1_input.offset_term("t2")),     # Restore t2 = Input




            # ==== Handle the Up / Down button presses ====
            #       & update the input follower
            ## .D.C ....
            ## Down is 4, Up is 8
            ## So shifts are:
            ##  18 = C-down
            ##  19 = C-up   = +1
            ##  26 = D-down = +7
            ##  27 = D-up   = +1
            "srl t1, t1, 18",
            "andi t3, t1, 0x1",
            "bnel t3, zero, 0x{:x}".format(funcAddr + 0x4*MOVE_DOWN),
            inputFollower.lui_instr("t1"),

            "srl t1, t1, 1",
            "andi t3, t1, 0x1",
            "bnel t3, zero, 0x{:x}".format(funcAddr + 0x4*MOVE_UP),
            inputFollower.lui_instr("t1"),

            "srl t1, t1, 7",
            "andi t3, t1, 0x1",
            "bnel t3, zero, 0x{:x}".format(funcAddr + 0x4*MOVE_DOWN),
            inputFollower.lui_instr("t1"),

            "srl t1, t1, 1",
            "andi t3, t1, 0x1",
            "bne t3, zero, 0x{:x}".format(funcAddr + 0x4*MOVE_UP),
            inputFollower.lui_instr("t1"),   # bne not bnel, so set regardless

            # Neither up nor down - still update the follower!
            "sw t2, {}".format(inputFollower.offset_term("t1")),
            "b 0x{:x}".format(funcAddr + 0x4*UPDATE_STRING),
            "nop",

            # MOVE_UP
            # t0 = index, t1 = High(inputFollower), t2 = input
            "sw t2, {}".format(inputFollower.offset_term("t1")),    # Update the input follower
            "sltiu t3, t0, 0x1",     # 1 if t0 = 0
            "xori t3, t3, 0x1",      # 0 if t0 = 0 else 1
            "subu t0, t0, t3",
            "sw t0, {}".format(displayIndex.offset_term("t1")),

            "b 0x{:x}".format(funcAddr + 0x4*UPDATE_STRING),
            "nop",

            # MOVE_DOWN
            "sw t2, {}".format(inputFollower.offset_term("t1")),    # Update the input follower
            "lw t2, {}".format(maxIndex.offset_term("t1")),   # Read the MAX INDEX
            "addiu t3, t0, 0x3",
            "sltu t3, t3, t2",      # t3 = curr + 4 <= max, i.e. if we can advance
            "addu t0, t0, t3",      # so add this
            "sw t0, {}".format(displayIndex.offset_term("t1")),




            # ================ UPDATE_STRING ===================
            # Find our string as index 6D + a0 in word bank at offset 9C from the table at 8008C640 (NTSC-U)
            "addu t0, t0, a0",
            wordBank9C_ptr.lui_instr("t1"),
            "lw t1, {}".format(wordBank9C_ptr.offset_term("t1")),   # t1 = word bank 9C
            "sll t3, a0, 1",        # Was 2
            "addu t3, t1, t3",      
            "lhu t2, 0xdc(t3)",     # read offset 6D + a0. Offset was 1B4, was lw
            "addu t1, t1, t2",      # t1 = word address

            # '[00 -] [text..' so our 2 digits are at the start of the 1st 32 bit word
            # Store in t2 : we do need to remove the 00 because they may not actually be 00
            "li t3, 10",
            "div t0, t3",
            "mflo t2",  # div, assume < 10
            "mfhi t3",  # mod

            "sll t4, t2, 24",
            "sll t3, t3, 16",
            "lw t2, 0x0(t1)",
            "andi t2, t2, 0xFFFF",       # Clear the upper 2 bytes
            "addu t2, t2, t4",  # Add div * 256^3, to add to the earlier 0
            "addu t2, t2, t3",  # Add mod to add to the final 0
            "lui t3, 0x3030",   # t3 reg is freed up now
            "addu t2, t2, t3",  # Add the '00' : this isn't interpreted as negative
            "sw t2, 0x0(t1)",

        
            # Also copy in the desired text string, to a max fixed length
            # t0 needs to be preserved
            # t1 is our string bank, which we'll skip the first 4 of
            # t2 we set to our source
            "sll t2, t0, 4", # 16 bytes for each
            api.namesBuffer.lui_instr("t3"),
            "addu t2, t2, t3",

            # Unrolled copying ;) 
            # .. of 4 words, for 5 total, so there must be room in these text entries.
            "lw t3, {}".format((api.namesBuffer + 0x0).offset_term("t2")),
            "sw t3, 0x4(t1)",
            "lw t3, {}".format((api.namesBuffer + 0x4).offset_term("t2")),
            "sw t3, 0x8(t1)",
            "lw t3, {}".format((api.namesBuffer + 0x8).offset_term("t2")),
            "sw t3, 0xc(t1)",
            "lw t3, {}".format((api.namesBuffer + 0xc).offset_term("t2")),
            "sw t3, 0x10(t1)",



            # ==== GET TIME ====
            # Find the statistic, store it into t0
            api.splitsBuffer.lui_instr("t1"),
            "sll t2, t0, 2",
            "addu t1, t1, t2",
            "lw t0, {}".format(api.splitsBuffer.offset_term("t1")),



            # ==== DELTA VERSION ADDITION - delta mode ====
            "beq zero, t2, 0x{:x}".format(funcAddr + 0x4*DRAW_TIMES),       # If our index was 0, skip
            deltaMode.lui_instr("t3"),
            "beq zero, t0, 0x{:x}".format(funcAddr + 0x4*DRAW_TIMES),       # If our split is 0:00, skip. This is generally a fail split.
            "lw t3, {}".format(deltaMode.offset_term("t3")),                # t3 <- Delta mode
            "beq zero, t3, 0x{:x}".format(funcAddr + 0x4*DRAW_TIMES),       # Skip if delta mode = 0
            "lw t1, {}".format((api.splitsBuffer - 0x4).offset_term("t1")), # Load the previous split
            "sub t0, t0, t1",   # Update t0 to the difference.



            # ============= DRAW TIMES ==============
            # divmod by 60 or 50!
            "li t3, 0x{:x}".format(50 if api.VERSION == "PAL" else 60),
            "div t0, t3",

            # Get the results (after a short sleep)
            "mflo a2",  # / 50 or 60, SET a2
            "mfhi t1",  # % 50 or 60

            # Do something useful before we divide again:
            # Set t3 = 3 for our next operation
            # and multiply t1 by 5 into t2 using shifts
            "li t3, 0x3",
            "sll t2, t1, 0x2",
            "addu t2, t1, t2",

            # IF NTSC Divide by 3, completing the move from 0-59 -> 0-98
            # IF PAL ignore t2 and just double t1 into a3, 0-49 -> 0-98
            "nop" if api.VERSION == "PAL" else "div t2, t3",
            "sll a3, t1, 0x1" if api.VERSION == "PAL" else "mflo a3",  # SET a3

            # SET a0 = (sp + 0x14) + 0xA8
            # This is to replicate the a0 = sp + 0xA8 that we wrote over..
            # But accounting for the fact we've taken off 0x14 !
            "addiu a0, sp, 0xbc",

            # a1 preserved so we're all done

            # SUFFIX, restore t0,t1,t2,t3,t4
            "lw t0, 0x0(sp)",
            "lw t1, 0x4(sp)",
            "lw t2, 0x8(sp)",
            "lw t3, 0xc(sp)",
            "lw t4, 0x10(sp)",
            "jr  ra",
            "addiu sp, sp, 0x14",
        ]


        for i in range(len(funcInstrs)):
            api.nop_quietly(hex(funcAddr + i*4))

        for i, instr in enumerate(funcInstrs):
            api.asm(hex(funcAddr+i*4), instr)
