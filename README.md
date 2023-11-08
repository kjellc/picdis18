# picdis18
A disassembler for PIC18 microcontroller   

picdis18.py  [-h] [-l] [-o outputfile] file.hex   

file.hex   input .HEX file in Intel format   
file_.asm  default output file, containing the assembly instructions, SFR names   
           directives, branch/call labels, callers of procedures, comments   
-o	save result to the specified file   
-h	0xHH syle for hex numbers (default is: HHh)   
-l	lists addresses and binary code of instructions   
Can be loaded into MPLAB and reassembled immediatedly without any problems!   
although the processor type should be changed (default 18F252)   


#The starting point for this program was:  
#DISPIC16.PY  
#Copyright (C) 2002 by Mel Wilson  mailto://mwilson@the-wire.com .  
#Free for any use providing this notice is retained in the code.  
#Use this code at your own risk.  
#Free for any use providing this notice is retained in the code.  
