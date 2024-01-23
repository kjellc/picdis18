# picdis18
A disassembler for PIC18 microcontroller   

### Features and limitations

* Generates MPLAB XC8 compatible assembly file.
* Currently uses chip PIC18F47Q10 SFR registers. To use other PIC18 family mcu need to modify <regnames18.txt> file with corresponding SFR definitions
* Does not support extended instruction set and indexed literal addressing mode.

### Usage
picdis18.py  [-h] [-l] [--int1] [--int2] [-d dbfile] [-o outputfile] file.hex

file.hex   input .HEX file in Intel format   
file_.asm  default output file, containing the assembly instructions, SFR names directives, branch/call labels, callers of procedures, comments   
-o	save result to the specified file   
-h	0xHH syle for hex numbers (default is: HHh)   
-l	lists addresses and binary code of instructions   
--int1  dissasembly interrupt 1 entry point
--int2  dissasembly interrupt 2 entry point
-d      use specified db definitions file (see example_db.txt for details)

#Original author   
#Copyright (C) 2002 by Mel Wilson  mailto://mwilson@the-wire.com.  
#Free for any use providing this notice is retained in the code.  
#Further code modifications covered by included GNU General Public License v3.0
