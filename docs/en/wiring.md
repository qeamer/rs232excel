# Wiring — assembly guide

See Norwegian lettered guide (source of truth): [docs/no/wiring.md](../no/wiring.md)

Parts: **A** DB25-MG · **B** ribbon · **C** female screw breakout · **D** FTDI USB–DB25 null modem · **E** two DuPont · **F** hub+OTG · **G** Pi.

Steps: (1) PLC→A→B→OKI (2) E from A screws 2+7 (3) E into C screws 2+7 (4) D male into C (5) D USB→hub→G DATA; 5V→G PWR IN.

Null modem: try C screw 2 first, else 3. GND stays 7.
