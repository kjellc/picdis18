# picdis18
A disassembler for PIC18 microcontroller   

picdis18.py  [-h] [-l] [-o outputfile] file.hex   

file.hex   input .HEX file in Intel format   
file_.asm  default output file, containing the assembly instructions, SFR names directives, branch/call labels, callers of procedures, comments   
-o	save result to the specified file   
-h	0xHH syle for hex numbers (default is: HHh)   
-l	lists addresses and binary code of instructions   

* Can be loaded into MPLAB and reassembled immediatedly without any problems.   
* Currently supported chip is PIC18F47Q10. For other PIC18 family mcu need to modify the code and INC file with SFR definitions must be replaced.
* Does not support extended instruction set and indexed literal addressing mode.

#Original author   
#Copyright (C) 2002 by Mel Wilson  mailto://mwilson@the-wire.com.  
#Free for any use providing this notice is retained in the code.  
#Further code modifications covered by included GNU General Public License v3.0
