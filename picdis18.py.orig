"""PICDIS18.PY -- a disassembler for PIC18 microcontroller code v0.5
Claudiu.Chiculita@ugal.ro    http://www.ac.ugal.ro/staff/ckiku/software/

picdis18.py  [-h] [-l] [-int1] [-int2] [-d dbfile] [-o outputfile] file.hex

file.hex   input .HEX file in Intel format
file_.asm  default output file, containing the assembly instructions, SFR names
           directives, branch/call labels, callers of procedures, comments
-o      save result to the specified file
-h      0xHH syle for hex numbers (default is: HHh)
-l      lists addresses and binary code of instructions
--int1  dissasembly interrupt 1 entry point
--int2  dissasembly interrupt 2 entry point
-d      use specified db definitions file (see example_db.txt for details)
-j file Use jump-table definition file
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
listing = 0    # =1 => only 1 asm line per each addr. ( -empty +nil )
hexstyle = 0   # 0 = 0NNh, 1 = 0xNN - kjc: changed default
dbstyle = 1    # 0 = hex, 1 = dec

code = {}       # key=(even addresses),  value=Instruction(s)
eeprom = {}
configuration = {}
covered = {}
max_addr = 0    # top address loaded by the hex file
stack = []      # store addresses for code coverage analyze
conf_regs = {}  # key = config address, value = config register name

table_defs = []  # store TableDef's

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

class StackItem:
    def __ini__(self):
        self:addr = 0
        self:bank = 0

class TableDef:
    def __init__(self):
        self.comment = ''
        self.data = []

###################################################################
def hexc(nr):            #custom hex()
    if (hexstyle):
        if (nr < 10):
            return str(int(nr))
        return '0x%X' % int(nr)    # C syle
    else:
        if (nr < 10):
            return str(int(nr))    # ASM style
        t = '%Xh' % int(nr)
        if (t[0] in string.ascii_letters):
            t = '0' + t
        return t

## kjc: custom hex v2
def hexc2(nr):
    if (hexstyle):
        if (nr < 10):
            return str(int(nr))
        return '0x%02X' % int(nr)    # C syle
    else:
        t = '%Xh' % int(nr)
        if (t[0] in string.ascii_letters):
            t = '0' + t
        return t

###################################################################
def makelabel(nr):
    s = '%X' % int(nr)
    return 'p' + s.rjust(6).replace(' ', '_')

###################################################################
def maketablelabel(nr):
    s = '%X' % int(nr)
    return 't' + s.rjust(6).replace(' ', '_')

###################################################################
# Reads an Intel HEX file into the `code` dictionary
# the keys are addresses and code[].bin has the object code
#
def read_object_code(objectfile):
    global code, conf_regs
    exta = '0000'                          # prefix for extended addr
    for x in objectfile.readlines():
        if debug:
            print(x[:-1])
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

            # dd = one row from hex file, data bytes
            #print(conf_regs)

            while dd:

                if (ad in conf_regs):
                    configuration[ad] = int(dd[0:2], 16)

                if ((ad & 1) == 0):
                    d = int(dd[0:2], 16), int(dd[2:4], 16)    # convert 2 bytes
                    teco[ad & ~1] = Instruction()             # add a new key = address
                    teco[ad & ~1].bin = (d[1] << 8) + d[0]    # write a word in code

                cks += int(dd[0:2], 16)                       # update checksum
                ad += 1                                       # bump the code address
                dd = dd[2:]                                   # drop one byte

            if ((int(x[-2:], 16) + cks) & 0xFF != 0):         # verify the checksum
                raise ValueError((hexc(-cks), hexc(int(x[-2:], 16))))

            if (ad < 0x300000):
                code.update(teco)
            if ((ad >= 0x310000) and (ad < 0x3f0000)):
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
        if (x == ""):
            continue
        a, b = x.split(' ')
        regn[int(a, 16)] = b
    f.close()
    return regn

###################################################################
def read_conf_regs():
    global conf_regs
    # Provide symbolic names for all config words
    f = open('confregs18.txt', "r");
    conf_regs = {}
    rn = f.readlines()

    for x in rn:
        x = x.strip()
        if (x == ""):
            continue
        a, b = x.split(' ')
        conf_regs[int(a, 16)] = b
    f.close()

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
    global code, stack, bank

    cod = code[addr]
    w = cod.bin
    opc = matching_opcode(w)       # get the right assembly template
    t = opc.template
    #print (t)
    af = w & 0x100
    code[addr].bytes = 2          # 2 bytes by default
    code[addr].stop = opc.stop    # stop coverage analyze after goto, return, branch
    if (opc.skip):
        sti = StackItem()
        sti.addr = addr + 4
        sti.bank = bank
        stack.append(sti)
    if (debug):
        print(hexc(w), t)
    s = []                        # init the return value
    for c in t:                   # for each character in the template
        if (c == 'F'):            # insert a register-file address
            q = w & 0xFF
            if (af != 0):         # banked, calculate and search for SFR name, add it to comment if found
                reg_name = reg_names.get(q | (bank << 8), '')
                if (reg_name):
                    code[addr].comment += ' ' + reg_name
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
            sti = StackItem()
            sti.addr = dest
            sti.bank = bank
            stack.append(sti)
            lookup_adr(dest).calls.append(addr)
        elif (c == 'M'):            # insert a rcall/bra relative +- 1023
            q = w & 0x7FF
            if q < 0x400:
                dest = addr + 2 + (q * 2)
            else:
                dest = addr + 2 - ((0x800 - q) * 2)
            s.append(makelabel(dest))
            sti = StackItem()
            sti.addr = dest
            sti.bank = bank
            stack.append(sti)
            lookup_adr(dest).calls.append(addr)
        elif (c == 'A'):            # access bank = 0 implicit
            if ((w & 0x100) != 0):
                s.append('b') # 'BANKED'
            elif s[-3:] == [',', 'f', ',']:# do not show:    ,f,0
                s = s[:-3]
            elif s[-1] == ',':    # do not show:    ,0
                del s[-1]
            if ((w & 0x100) == 0):
                s.append(',a') # ',ACCESS'
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
            sti = StackItem()
            sti.addr = dest
            sti.bank = bank
            stack.append(sti)
            code[addr].bytes = 4
            if ((w & 0x300) ^ 0x100) == 0:    # only if its a 'call' and 's' is set
                s.append(',FAST')
        elif (c == 'Z'):            # dword    lfsr
            w2 = lookup_adr(addr + 2).bin
            s.append(str((w & 0x30) >> 4) + ',' + hexc(((w & 0xF) << 8) | (w2 & 0xFF)))
            code[addr].bytes = 4
        elif (c == 'X'):            # insert the hex version of the whole word
            s.append('DW ' + hexc(w) + '\t\t;WARNING: unknown instruction!')
        else:                    # insert this source-code character
            if (c == ' '):
                while (len(s) < 7):
                   s.append(' ')
            else:
                s.append(c)

    # tracking bank
    if (t == 'movlb C'):
        bank = w & 0xF

    code[addr].asm = ''.join(s)
    #print(code[addr].asm)

###############################################################
def eep_cfg_txt():                    # generate text for the eeprom and configuration words
    txt = ''
    for x in configuration:
        if listing:
            txt += '%06X %04X' % (int(x), int(configuration[x]))
            txt += '\tCONFIG %s = %s\n' % ((conf_regs[x] if (x in conf_regs) else hexc(x)), hexc(configuration[x]))
        else:
            txt += '\t\tCONFIG %s = %s\n' % ((conf_regs[x] if (x in conf_regs) else hexc(x)), hexc(configuration[x]))
    if eeprom:
        txt += '\t\t;eeprom:\n'
        for x in eeprom:            # hopefully the hex will have very fey eeprom location defined
            if listing:
                txt += '%06X %04X\n' % (x, eeprom[x].bin)
            else:
                txt += '\t\tORG %s\n\t\tdw %s\n' % (hexc(x), hexc(eeprom[x].bin))
    if txt:
        txt += '\n\n'
    return txt

###############################################################
def analyze_coverage():

    global code, covered, stack, bank

    while (len(stack) > 0):
        #print ('stack len %d' % len(stack))
        sti = stack.pop()
        addr = sti.addr;
        bank = sti.bank;
        #print (addr)
        if (addr in covered):
            continue
        stop = False
        while (not stop):
            covered[addr] = True
            if (addr in code):
                #print ('addr in code')
                assembly_line(addr)
                stop = code[addr].stop
                addr += code[addr].bytes
            else: # word is not programmed read as 0xffff (nil)
                #print ('addr not in code')
                addr += 2
            addr = addr & 0xfffff # 20 bit address space
            stop = stop or (addr in covered) # stop if address is already covered

###############################################################
def is_movwf_tblptrx(bin):
    return (bin == 0x6EF6) or (bin == 0x6EF7) or (bin == 0x6EF8)

###############################################################
def is_code(addr):
    #global code, covered
    return (addr in code) and (addr in covered)

###############################################################
def analyze_table_pointers():
    addr_tblptrl = 0
    addr_tblptrh = 0
    addr_tblptru = 0

    addr = max_addr

    #print("max_addr = %s" % max_addr)

    while (addr >= 0):
        if (is_code(addr)):

            if (is_movwf_tblptrx(code[addr].bin)):

                # backward serach for tblptr loading opcodes
                paddr = addr

                l_found = False
                h_found = False
                u_found = False

                l_op_addr = 0
                h_op_addr = 0
                u_op_addr = 0

                while (paddr >= 0) and (paddr > (addr - 100)) and (is_code(paddr)) and ((not l_found) or (not h_found) or (not u_found)):

                    if (not l_found and (code[paddr].bin == 0x6EF6)): #tblptrl
                        addr_tblptrl = paddr;
                        code[paddr].comment += ' tblptrl '
                        laddr = paddr - 2
                        while ((laddr >= 0) and (laddr > (paddr - 20)) and is_code(laddr) and not is_movwf_tblptrx(code[laddr].bin)):
                            if ((code[laddr].bin == 0x0F01) and is_code(laddr - 2) and (code[laddr - 2].bin == 0xB0D8)):
                                laddr = laddr - 4
                                continue
                            if ((code[laddr].bin & 0xfe00) == 0x0e00):
                                code[laddr].comment += ' L ADDR '
                                l_op_addr = laddr
                                l_found = True
                                break
                            laddr = laddr - 2

                    if (not h_found and (code[paddr].bin == 0x6EF7)): #tblptrh
                        addr_tblptrh = paddr;
                        code[paddr].comment += ' tblptrh '
                        laddr = paddr - 2
                        while ((laddr >= 0) and (laddr > (paddr - 20)) and is_code(laddr) and not is_movwf_tblptrx(code[laddr].bin)):
                            if ((code[laddr].bin == 0x0F01) and is_code(laddr - 2) and (code[laddr - 2].bin == 0xB0D8)):
                                laddr = laddr - 4
                                continue
                            if ((code[laddr].bin & 0xfe00) == 0x0e00):
                                code[laddr].comment += ' H ADDR '
                                h_op_addr = laddr
                                h_found = True
                                break
                            laddr = laddr - 2

                    if (not u_found and (code[paddr].bin == 0x6EF8)): #tblptru
                        addr_tblptru = paddr;
                        code[paddr].comment += ' tblptru '
                        laddr = paddr - 2
                        while ((laddr >= 0) and (laddr > (paddr - 20)) and is_code(laddr) and not is_movwf_tblptrx(code[laddr].bin)):
                            if ((code[laddr].bin == 0x0F01) and is_code(laddr - 2) and (code[laddr - 2].bin == 0xB0D8)):
                                laddr = laddr - 4
                                continue
                            if ((code[laddr].bin & 0xfe00) == 0x0e00):
                                code[laddr].comment += ' U ADDR '
                                u_op_addr = laddr
                                u_found = True
                                break
                            laddr = laddr - 2

                    paddr = paddr - 2

                if (l_found and h_found and u_found):

                    # calculate table address
                    table_addr = ((code[u_op_addr].bin & 0xff) << 16) | ((code[h_op_addr].bin & 0xff) << 8) | (code[l_op_addr].bin & 0xff)

                    if (table_addr not in code):
                        print("Invalid table address found!!! %s" % table_addr)
                        code[u_op_addr].comment += ' INVALID !!!'
                        code[h_op_addr].comment += ' INVALID !!!'
                        code[l_op_addr].comment += ' INVALID !!!'
                    else:
                        # add label to table
                        code[table_addr].label = maketablelabel(table_addr)
                        #print("Table label added %s" % code[table_addr].label)

                        # replace pointer loading opcodes with (low LABEL, high LABEL, upper LABEL)
                        code[u_op_addr].asm = ('movlw' if ((code[u_op_addr].bin & 0xff00) == 0x0e00) else 'addlw') + '  low highword ' + maketablelabel(table_addr)
                        code[h_op_addr].asm = ('movlw' if ((code[h_op_addr].bin & 0xff00) == 0x0e00) else 'addlw') + '  high ' + maketablelabel(table_addr)
                        code[l_op_addr].asm = ('movlw' if ((code[l_op_addr].bin & 0xff00) == 0x0e00) else 'addlw') + '  low ' + maketablelabel(table_addr)

                    addr = min(addr_tblptrl, addr_tblptrh, addr_tblptru)

        addr = addr - 2

###############################################################
def ascii_char(code):
    if ((code < 32) or (code > 126)):
        return '.'
    else:
        return chr(code)

###############################################################
def fix_line_wrap(s):
    return (s if (not s or (s[-1] != '\\')) else s + '.')

###############################################################
def read_table_defs(file):
    global table_defs

    tmp_table_def = TableDef()

    for s in file.readlines():
        if (s[0] == ';'):
            #print("Table comment found = %s" % s[1:])

            #store previous tmp_table_def into table_defs
            if (len(tmp_table_def.data) > 0):
                table_defs.append(tmp_table_def)
                tmp_table_def = TableDef()

            tmp_table_def.comment = s[1:].strip()

        elif re.match(r'(\d+\D+)+', s):
            for b in re.findall(r'\d+', s):
                tmp_table_def.data.append(int(b))

    file.close()

    # store the last one
    if (len(tmp_table_def.data) > 0):
        #store tmp_table_def into table_defs
        table_defs.append(tmp_table_def)

    #for t in table_defs:
    #   print('"%s" %s' % (t.comment, len(t.data)))

###############################################################

def read_jumptable_defs(file):

    for s in file.readlines():
        if (len(s) <= 1):
            continue
        if (s[0] == ';'):
            #print("JumpTable comment found = %s" % s[1:])
            continue
        start, stop = s.split(',')
        start_addr = int(start, 16)
        stop_addr = int(stop, 16)
        #print('jumptable: ', start, stop)
        if (start_addr <= stop_addr):
            while (start_addr <= stop_addr):
                sti = StackItem()
                sti.bank = 0
                sti.addr = start_addr
                stack.append(sti)
                start_addr += 2
        else:
            print("Bad syntax, jumptable file: %s > %s" % (start, stop))

    file.close()

###############################################################
def search_table_def_matched():

    global code, covered, table_defs

    waddrs = list(code.keys())
    waddrs.sort()

    for t in table_defs:

        #print('Sarching for %s' % t.comment)
        #print('len(t.data) = %s' % len(t.data))
        #print('max_addr = %s' % max_addr)

        byte_addr = 0

        while (byte_addr <= (max_addr + 1)):

            # word address for searching
            waddr = byte_addr & ~1
            if ((waddr not in code) or (waddr in covered)):
                byte_addr = byte_addr + 1
                continue

            matching = True
            offset = 0

            while (matching):

                waddr2 = (byte_addr + offset) & ~1

                if ((waddr2 not in code) or (waddr2 in covered)):
                    matching = False
                    break

                if ((byte_addr + offset) & 0x01):
                    byte = code[waddr2].bin >> 8
                else:
                    byte = code[waddr2].bin & 0xff

                if (offset < len(t.data)):
                    if (byte != t.data[offset]):
                        matching = False
                        break

                else: # all bytes compared, matching is found
                    break

                offset = offset + 1

            if (matching): # pattern found, add prefixline
                #print(" Pattern found at %s" % waddr)
                code[waddr].prefixline = code[waddr].prefixline + ('\n' if (code[waddr].prefixline) else '') + '\n' + (8 * ' ') + ';' + t.comment + \
                    (' (with offset +1) ' if (byte_addr & 1) else '') + '\n'

            byte_addr = byte_addr + 1

###############################################################
# main entry to the program
###############################################################
if __name__ == '__main__':

    table_defs_file = ''
    jumptable_defs_file = ''
    use_interrupt1 = False
    use_interrupt2 = False

    try:

        opts, args = getopt.getopt(sys.argv[1:], "hlo:d:j:", ["int1", "int2"])

        input_file = args[0]
        output_file = input_file[:-4] + '_.asm'

        for o, v in opts:
            if (o == '-o'):    # user-supplied output path
                output_file = v
            elif (o == '-l'):
                listing = 1
            elif (o == '-h'):
                hexstyle = 1    # 0xNNN
            elif (o == '-d'):
                table_defs_file = v
            elif (o == '-j'):
                jumptable_defs_file = v
            elif (o == '--int1'):
                use_interrupt1 = True
            elif (o == '--int2'):
                use_interrupt1 = True
    except:
        print(__doc__)
        sys.exit(2)

    if (table_defs_file != ''):
        print('Reading table defs file...', os.path.abspath(table_defs_file))
        try:
            read_table_defs(open(table_defs_file, "r"))
        except OSError as e:
            print(f"Unable to open {table_defs_file}: {e}", file=sys.stderr)
            sys.exit(2)

    if (jumptable_defs_file != ''):
        print('Reading jump-table table defs file...', os.path.abspath(jumptable_defs_file))
        try:
            read_jumptable_defs(open(jumptable_defs_file, "r"))
        except OSError as e:
            print(f"Unable to open {jumptable_defs_file}: {e}", file=sys.stderr)
            sys.exit(2)

    print('Building tables...')
    operand_table = make_operand_table()
    reg_names = read_registry_names()

    print('Reading config regs names...')
    read_conf_regs()

    print('Reading object file...', os.path.abspath(input_file))
    try:
        read_object_code(open(input_file, "r"))
    except OSError as e:
            print(f"Unable to open {input_file}: {e}", file=sys.stderr)
            sys.exit(2)

    print('Disassemble...')

    tempk = list(code.keys())
    tempk.sort()

    max_addr = max(tempk);
    #print('max_addr = %d' % int(max_addr))

    # set start condition
    sti = StackItem()
    sti.addr = 0
    sti.bank = 0
    stack.append(sti)

    print('Analyze code coverage...')
    analyze_coverage()

    ##### Interrupt vectors #########################

    if (use_interrupt1 and (0x0008 in code)):
        sti = StackItem()
        sti.addr = 0x0008;
        sti.bank = 0
        stack.append(sti)

        print('Analyze Interrupt vector 1...')
        analyze_coverage();

        code[0x0008].prefixline += '; Interrupt vector 1 \n'

    if (use_interrupt2 and (0x0018 in code)):

        sti = StackItem()
        sti.addr = 0x0018;
        sti.bank = 0
        stack.append(sti)

        print('Analyze Interrupt vector 2...')
        analyze_coverage();

        code[0x0018].prefixline += '; Interrupt vector 2 \n'

    #################################################

    print('Analyze table pointers...')
    analyze_table_pointers()

    print('Searching for table definitions matches...');
    search_table_def_matched()

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
            cod.prefixline += '\n\t\tORG %s \n' % (hexc(wadr))
            #print(' ORG', "%s" % (hexc(wadr)))

        if (wadr not in covered):
            cod.asm = '%s%s,%s' % ('db'.ljust(5, ' '), hexc2(cod.bin & 0xff), hexc2((cod.bin >> 8) & 0xff))
            cod.comment = ';%s%s' % (ascii_char(cod.bin & 0xff), ascii_char(cod.bin >> 8))
            cod.bytes = 2
            next_wadr = wadr + 2
            while (cod.bytes < 16): # upto 16 bytes in one db
                if (next_wadr not in code):
                    break # break if there is no code
                if (next_wadr in covered):
                    break # break is db finishes
                if ((len(code[next_wadr].calls) > 0) or code[next_wadr].label.strip() or code[next_wadr].prefixline):
                    break # break if db has label or comment or prefixline
                next_bin = code[next_wadr].bin
                cod.asm += ',%s,%s' % (hexc2(next_bin & 0xff), hexc2((next_bin >> 8) & 0xff))
                cod.comment += '%s%s' % (ascii_char(next_bin & 0xff), ascii_char(next_bin >> 8))
                cod.bytes += 2
                next_wadr += 2

    print('Writing...', os.path.abspath(output_file))
    otf = open(output_file, "w")
    tempk = list(code.keys())
    tempk.sort()
    otf.write(';Generated by PICDIS18, Claudiu Chiculita, 2003.  http://www.ac.ugal.ro/staff/ckiku/software\n')
    otf.write(';Select your processor\n')
    otf.write('PROCESSOR 18F47Q10; modify this\n')
    otf.write('\n')
    otf.write('#include <xc.inc>\n')
    otf.write('\n')
    otf.write(eep_cfg_txt())
    otf.write('PSECT RESETVEC, abs\n');
    otf.write('RESETVEC:\n\n');

    skip_till_addr = 0;
    for addr in tempk:
        if (addr < skip_till_addr):
            continue
        if (listing):
            otf.write(code[addr].prefixline) # kjc: added prefixline
            otf.write('%05X %04X\t' % (int(addr), int(code[addr].bin)))
        else:
            otf.write(code[addr].prefixline)

        comment_spacing = ''
        if (code[addr].comment):
            # use spaces before comment
            comment_spacing = (' ' * int(((72 if (code[addr].asm.startswith('db')) else 32) + 3 - (2 + len(code[addr].asm.expandtabs(tabsize)))) / 1))
        else:
            comment = ''

        otf.write('%s%s%s%s\n' % ((code[addr].label + (':' if code[addr].label.strip() else '')).ljust(10), code[addr].asm, comment_spacing, fix_line_wrap(code[addr].comment)))
        skip_till_addr = addr + code[addr].bytes;

    otf.write('END RESETVEC')
    otf.close()
    print('Done.')
