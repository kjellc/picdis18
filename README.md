# picdis18
A disassembler for PIC18 microcontroller   

### Features and limitations

* Generates MPLAB XC8 compatible assembly file
* Currently uses PIC18F47Q10 SFR and configuration registers definitions. To use other PIC18 family mcu need to modify <regnames18.txt> and <confregs18.txt> files with corresponding definitions
* Analyzes code covarege. By default uses only reset vector (0x0000) as entry point. To add interrupt vectors to code coverage use int1 and int2 option flags
* All uncovered code are replaced by 'db' byte definitions. If known tables are used then comments for these can be added from db definitions file (see example_db.txt as example)
* It tries to find and replace table pointer registers loading code with table address labels. This feature is experimental. It's tested and works for COWBASIC generated code
* Does not support extended instruction set and indexed literal addressing mode.
* If address calculation or address lookup tables are used for branching or table pointers then dissassembler will not work correctly

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
