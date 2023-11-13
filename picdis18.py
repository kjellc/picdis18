"""PICDIS18.PY -- a disassembler for PIC18 microcontroller code v0.4
Claudiu.Chiculita@ugal.ro    http://www.ac.ugal.ro/staff/ckiku/software/

picdis18.py  [-h] [-l] [-o outputfile] file.hex

file.hex   input .HEX file in Intel format
file_.asm  default output file, containing the assembly instructions, SFR names
           directives, branch/call labels, callers of procedures, comments
-o    save result to the specified file
-h    0xHH syle for hex numbers (default is: HHh)
-l    lists addresses and binary code of instructions
Can be loaded into MPLAB and reassembled immediatedly without any problems!
although the processor type should be changed (default 18F47Q10)
"""
# The assigned labels contain the hex address of the instruction
# ToDo: + clean code + bitnames
#------------------History---------------------------
#
#
#----------------------------------------------------

#The starting point for this program was:
#DISPIC16.PY
#Copyright (C) 2002 by Mel Wilson  mailto://mwilson@the-wire.com .
#Free for any use providing this notice is retained in the code.
#Use this code at your own risk.

import getopt, os, sys, string, re

debug = 0
tabsize = 4
listing = 0   # =1 => only 1 asm line per each addr. ( -empty +nil )
hexstyle = 0  # 0NNNh
dbstyle = 1   # 0 = hex, 1 = dec

code = {}     # key=(even addresses),  value=Instruction(s)
eeprom = {}
configuration = {}
covered = {}
max_addr = 0   # top address loaded by the hex file
stack = []     # store addresses for code coverage analyze

class Instruction:
    def __init__(self):
        self.bin = 0        # taken from hex
        self.dummy = 0      # strange jumps, ORGs
        self.calls = []     # list of callers/(jumpers)
        self.asm = ''
        self.label = '    '
        self.prefixline = ''
        self.comment = ';'
        self.bytes = 0      # operand length in bytes (2, 4 or 16 for db's)
        self.stop = False

class Opcode:
    def __init__(self):
        self.template = 'X'
        self.value = 0
        self.mask = 0
        self.skip = False
        self.stop = False

###################################################################
def hexc(nr):            #custom hex()
    if hexstyle:
        return '0x%X' % int(nr)    # C syle
    else:
        if (nr < 10):
            return str(int(nr))    # ASM style
        t = '%Xh' % int(nr)
        if (t[0] in string.ascii_letters):
            t = '0' + t
        return t

###################################################################
def makelabel(nr):
    s = '%X' % int(nr)
    return 'p' + s.rjust(6).replace(' ', '_')

###################################################################
# Reads an Intel HEX file into the `code` dictionary
# the keys are addresses and code[].bin has the object code
#
def read_object_code(objectfile):
    global code
    exta = '0000'                          # prefix for extended addr
    for x in objectfile.readlines():
        if x[0] == ':':                    # Intel form        :CCAAAATTllhhllhh....rr
            x = x.strip()
            nb = int(x[1:3], 16)           # number of bytes this record
            ad = int(exta + x[3:7], 16)    # starting word address this record + extended linear
            ty = int(x[7:9], 16)           # record type
            if debug:
                print(string.rjust(hexc(ad),8), ty, x)
            if ty == 0:
                pass
            elif ty == 1:
                break                       # end of record
            elif ty == 4:                   # extended linear, only :02000004aaaa  supported
                exta = x[9:13];
                continue
            else:
                print("Not a data record")
                continue                    # not a data record - ignore it
            teco = {}                       # temporary code
            cks = nb + (ad & 0xFF) + ((ad >> 8) & 0xFF) + ty    # init checksum
            dd = x[9:-2]                    # isolate the data
            ad /= 2                         # convert byte to word address
            while dd:
                d = int(dd[0:2], 16), int(dd[2:4], 16)   # convert 2 bytes
                teco[ad * 2] = Instruction()             # add a new key = address
                teco[ad * 2].bin = (d[1] << 8) + d[0]    # write a word in code
                cks += d[0] + d[1]                       # update checksum
                ad += 1                                  # bump the code address
                dd = dd[4:]                              # drop old data
            if ((int(x[-2:], 16) + cks) & 0xFF != 0):    # verify the checksum
                raise ValueError((hexc(-cks), hexc(int(x[-2:], 16))))
            if (ad < (0x300000 / 2)):
                code.update(teco)
            elif (ad < (0xF00000/2)):
                configuration.update(teco)
            else:
                eeprom.update(teco)
        else:
            print("Ignoring line: ", x)                    # ignore anything else

###################################################################
def read_registry_names():
    # Provide symbolic names for all special file registers
    f = open('regnames18.txt', "r");
    regn = {}
    rn = f.readlines()
    for x in rn:
        x = x.strip()
        if x == "":
            continue
        a, b = x.split(' ')
        regn[int(a, 16)] = b
    f.close()
    return regn

###################################################################
# Read a specially-formatted string to build the opcode-identification table.
# Each line in the master string contains
# - an assembly statement template in lowercase with 'magic' uppercase characters
#   denoting operands to be filled in
# - skip '0'/'1' - if this is conditional skip operand
# - stop '0'/'1' - if code execution does not continue after this instructino (e.g. goto, bra, return, ...)
# - a binary instruction word template containing '1's and '0's in critical positions
#   and with any other non-blanks indicating "don't care" bit positions
# Each entry in the opcode-identification table contains:
# - an assembly template string
# - a binary value
# - a binary mask
# - skip, boolean
# - stop, boolean
# see the `matching_opcode` and `assembly_string` functions for the
# examples of the use of this table
#
def make_operand_table():
    f = open('opcodes18.txt', "r");
    oplist = []
    opcode_templates = f.readlines()
    for x in opcode_templates:#.split('\n'):
        x = x.strip()
        if (x == ""):
            continue
        # split into (asm, skip, stop, binary template)
        asm, skip, stop, template = (re.split(' \s+', x))
        cv = cm = 0                    # init code_value, code_mask
        for ch in template:            # for each character in the bit template
            if (ch == '0'):
                cv = (0 | (cv << 1))   # set the bit value 0
                cm = (1 | (cm << 1))   # set mask to compare this bit
            elif (ch == '1'):
                cv = (1 | (cv << 1))   # set the bit value 1
                cm = (1 | (cm << 1))   # set mask to compare this bit
            elif (ch != ' '):
                cv = (0 | (cv << 1))   # value 0 to ignore this bit position
                cm = (0 | (cm << 1))   # mask  0 to ignore this bit position

        opc = Opcode()
        opc.template = asm        # Eg: 'addwf F, D, A'
        opc.value = cv            # Eg: 0x4800
        opc.mask = cm             # Eg: 0xfc00
        opc.skip = (skip != '0')  # Eg: False
        opc.stop = (stop != '0')  # Eg: False

        oplist.append(opc)

    f.close()
    return oplist

###################################################################
# Return the assembly-language template string
# that matches a given binary instruction word
#
def matching_opcode(w):
    global operand_table

    for opc in operand_table:
        if ((w & opc.mask) == opc.value):
            return opc
    return Opcode()                         # return dummy opcode 'X' unidentifiable binary -- punt

###################################################################
def lookup_adr(addr):
    global code
    if (addr in code):
        return code[addr]
    else:                            # exceptional case: a jump to a location not defined in hexfile
        x = Instruction()            #                    or a missing second word in a dword instr
        x.dummy = 1
        x.bin = 0xffff
        x.bytes = 2
        code[addr] = x
        return x

###################################################################
# F        .... .... ffff ffff
# N        .... .... nnnn nnnn
# M        .... .nnn nnnn nnnn
# C        .... .... .... kkkk
# K        .... .... kkkk kkkk
# B        .... bbb. .... ....
# A        .... ...a .... ....
# D        .... ..d. .... ....
# S        .... .... .... ...s
# W        double  -call,goto
# Y        double  -movff
# Z        double  -lfsr
def assembly_line(addr):
    global code, stack

    cod = code[addr]
    w = cod.bin
    opc = matching_opcode(w)       # get the right assembly template
    t = opc.template
    af = w & 0x100
    code[addr].bytes = 2          # 2 bytes by default
    code[addr].stop = opc.stop    # stop coverage analyze after goto, return, branch
    if (opc.skip):
        stack.append(addr + 4)
    if (debug):
        print(hexc(w), t)
    s = []                        # init the return value
    for c in t:                   # for each character in the template
        if (c == 'F'):            # insert a register-file address
            q = w & 0xFF
            if ((af == 0) and (q >= 0x80)):
                s.append(reg_names.get(q | 0xF00, hexc(q)))
            else:
                s.append(hexc(q))
        elif (c == 'D'):            # insert a ",w" modifier = 0, if appropriate
            if ((w & 0x200) == 0):
                s.append('W')
            else:
                s.append('f')
        elif (c == 'B'):            # insert a bit-number
            s.append('%d' % (((w >> 9) & 0x7)))
        elif (c == 'K'):            # insert an 8-bit constant
            s.append(hexc(w & 0xFF))
        elif (c == 'C'):            # movlb
            s.append(hexc(w & 0xF))
        elif (c == 'N'):            # branch relative +- 127
            q = (w & 0xFF)
            if (q < 0x80):
                dest = addr + 2 + (q * 2)
            else:
                dest = addr + 2 - (0x100 - q) * 2
            s.append(makelabel(dest))
            stack.append(dest)
            lookup_adr(dest).calls.append(addr)
        elif (c == 'M'):            # insert a rcall/bra relative +- 1023
            q = w & 0x7FF
            if q < 0x400:
                dest = addr + 2 + (q * 2)
            else:
                dest = addr + 2 - ((0x800 - q) * 2)
            s.append(makelabel(dest))
            stack.append(dest)
            lookup_adr(dest).calls.append(addr)
        elif (c == 'A'):            # access bank = 0 implicit
            if ((w & 0x100) != 0):
                s.append('BANKED')
            elif s[-3:] == [',', 'f', ',']:# do not show:    ,f,0
                s = s[:-3]
            elif s[-1] == ',':    # do not show:    ,0
                del s[-1]
        elif (c == 'S'):            # =1 restore reg. on ret: retfie/return (implicit 0)
            if (w & 0x1) == 1:
                s.append('FAST')
            elif s[-1] == ',':
                del s[-1]
        elif (c == 'Y'):            # dword    movff
            w2 = lookup_adr(addr + 2).bin
            s.append(reg_names.get(w  & 0xFFF, hexc(w  & 0xFFF)) + ',' +
                     reg_names.get(w2 & 0xFFF, hexc(w2 & 0xFFF)))
            code[addr].bytes = 4
        elif (c == 'W'):            # dword    call/goto
            w2 = lookup_adr(addr + 2).bin
            dest = ((w & 0xFF) | ((w2 & 0xFFF) << 8)) * 2
            lookup_adr(dest).calls.append(addr)
            s.append(makelabel(dest))
            stack.append(dest)
            code[addr].bytes = 4
            if ((w & 0x300) ^ 0x100) == 0:    # only if its a 'call' and 's' is set
                s.append(',FAST')
        elif (c == 'Z'):            # dword    lfsr
            w2 = lookup_adr(addr + 2).bin
            s.append(str((w & 0x30) >> 4) + ',' + hexc(((w & 0xF) << 8) | (w2 & 0xFF)))
            code[addr].bytes = 4
        elif (c == 'X'):            # insert the hex version of the whole word
            s.append('DE ' + hexc(w) + '\t\t;WARNING: unknown instruction!')
        else:                    # insert this source-code character
            if (c == ' '):
                while (len(s) < 6):
                   s.append(' ')
            else:
                s.append(c)

    code[addr].asm = ''.join(s)

###############################################################
def eep_cfg_txt():                    # generate text for the eeprom and configuration words
    txt = ''
    for x in configuration:
        if listing:
            txt += '%06X %04X\n' % (int(x), int(configuration[x].bin))
        else:
            txt += '\t\t__CONFIG %s, %s\n' % (hexc(x), hexc(configuration[x].bin))
    if eeprom:
        txt += '\t\t;eeprom:\n'
        for x in eeprom:            # hopefully the hex will have very fey eeprom location defined
            if listing:
                txt += '%06X %04X\n' % (x, eeprom[x].bin)
            else:
                txt += '\t\tORG %s\n\t\tDE %s\n' % (hexc(x), hexc(eeprom[x].bin))
    if txt:
        txt += '\n\n'
    return txt

###############################################################
def analyze_coverage():

    global code, covered, stack

    while (len(stack) > 0):
        print ('stack len %d' % len(stack))
        addr = stack.pop()
        print (addr)
        if (addr in covered):
            continue
        stop = False
        while (not stop):
            covered[addr] = True
            if (addr in code):
                print ('addr in code')
                assembly_line(addr)
                stop = code[addr].stop
                addr += code[addr].bytes
            else: # word is not programmed read as 0xffff (nil)
                print ('addr not in code')
                addr += 2
            addr = addr & 0xfffff # 20 bit address space
            stop = stop or (addr in covered) # stop if address is already covered

###############################################################
def ascii_char(code):
    if ((code < 32) or (code > 127)):
        return '.'
    else:
        return chr(code)

###############################################################
# main entry to the program
###############################################################
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hlo:")
        input_file = args[0]
        output_file = input_file[:-4] + '_.asm'
        for o, v in opts:
            if (o == '-o'):    # user-supplied output path
                output_file = v
            elif (o == '-l'):
                listing = 1
            elif (o == '-h'):    #ToDo:repair
                hexstyle = 1    # 0xNNN
    except:
        print(__doc__)
        sys.exit(2)

    print('Building tables...')
    operand_table = make_operand_table()
    reg_names = read_registry_names()

    print('Reading object file...', os.path.abspath(input_file))
    read_object_code(open(input_file, "r"))

    print('Disassemble...')

    tempk = list(code.keys())
    tempk.sort()

    max_addr = max(tempk);
    print('max_addr = %d' % int(max_addr))

    print('Analyze code coverage...')
    stack.append(0); # start address
    analyze_coverage()

    print('Arranging...')
    skip_till_wadr = 0;

    for wadr in tempk:
        if (wadr < skip_till_wadr):
            continue
        cod = code[wadr]
        if (len(cod.calls) > 0):                # put labels
            cod.label = makelabel(wadr)
            cod.comment += ' entry from: ' + ','.join(map(hexc, cod.calls))
            if ((not listing) and (len(cod.calls) > 1)):
                cod.prefixline += '\n'
        if (len(cod.comment) < 3):              # remove empty comments
            cod.comment = ''
        if ((wadr - 2) not in code):            # must put an ORG if not contiguous
            cod.prefixline += '\t\tORG %s \n' % (hexc(wadr))

        if (wadr not in covered):
            cod.asm = '%s%s,%s' % ('db'.ljust(5, ' '), cod.bin & 0xff, cod.bin >> 8)
            cod.comment = ';%s%s' % (ascii_char(cod.bin & 0xff), ascii_char(cod.bin >> 8))
            cod.bytes = 2
            next_wadr = wadr + 2
            while (cod.bytes < 16): # upto 16 bytes in one db
                if (listing):
                    break # listing format
                if (next_wadr not in code):
                    break # break if there is no code
                if (next_wadr in covered):
                    break # break is db finishes
                if ((len(code[next_wadr].calls) > 0) or (len(code[next_wadr].calls) > 0)):
                    break # break if db has label or comment
                next_bin = code[next_wadr].bin
                cod.asm += ',%s,%s' % (next_bin & 0xff, next_bin >> 8)
                cod.comment += '%s%s' % (ascii_char(next_bin & 0xff), ascii_char(next_bin >> 8))
                cod.bytes += 2
                next_wadr += 2

    print('Writing...', os.path.abspath(output_file))
    otf = open(output_file, "w")
    tempk = list(code.keys())
    tempk.sort()
    otf.write(';Generated by PICDIS18, Claudiu Chiculita, 2003.  http://www.ac.ugal.ro/staff/ckiku/software\n')
    otf.write('\t\t;Select your processor\n\t\tLIST      P=18F47Q10\t\t; modify this\n\t\t#include "p18F47Q10.inc"\t\t; and this\n\n')
    otf.write(eep_cfg_txt())

    skip_till_addr = 0;
    for addr in tempk:
        if (not listing and (addr < skip_till_addr)):
            continue
        if listing:
            otf.write('%05X %04X\t' % (int(addr), int(code[addr].bin)))
        else:
            otf.write(code[addr].prefixline)

        comment_spacing = 0
        if (code[addr].comment):
            # prefix with tabs
            comment_spacing = ('\t' * int(((72 if (code[addr].asm.startswith('db')) else 32) + 3 - len(code[addr].asm.expandtabs(tabsize))) / tabsize))
        else:
            comment = ''

        otf.write('%s\t%s%s%s\n' % (code[addr].label, code[addr].asm, comment_spacing, code[addr].comment))
        skip_till_addr = addr + code[addr].bytes;

    otf.write('\tEND')
    otf.close()
    print('Done.')