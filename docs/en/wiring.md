# Wiring — parts A–G

Source of truth (Norwegian lettered guide): [docs/no/wiring.md](../no/wiring.md) · images: [steg-for-steg-passiv-rs232-tapp.png](../no/img/steg-for-steg-passiv-rs232-tapp.png) · [passiv-rs232-tapp.png](../no/img/passiv-rs232-tapp.png)

| | Part | Role |
|--|------|------|
| **A** | DB25-MG (female+male+screws) | Plant pass-through + tap point |
| **B** | DB25 M↔F ribbon 1:1 | A male → OKI |
| **C** | DB25 female solder-free terminal | Listen female — StarTech male plugs here |
| **D** | StarTech USB→serial + DB25 **male** | Into **C** → hub → Pi |
| **E1** | Wire / DuPont | **A** screw **2** → **C** screw **3** (StarTech RX; try C2 if no data) |
| **E2** | Wire / DuPont | **A** screw **7** → **C** screw **7** |
| **F** | Hub + OTG | To **G** DATA |
| **G** | Pi Zero WH | Ports below |

**Do not:** cut the plant cable · WAGO · extra loop wires on C · GPIO.

## Pi Zero ports (left → right)

1. **HDMI** (far left)  
2. **DATA / USB** (middle) ← OTG + hub  
3. **PWR IN** (far **right**) ← 5V only  

## Steps

1. **Plant:** PLC male → **A** female. **A** male → **B** (ribbon) → OKI.  
2. **Tap on A:** **E1** on screw **2**, **E2** on screw **7**.  
3. **Into C:** **E1** → screw **C3** (= StarTech pin 3 RX). **E2** → **C7**.  
   No data? Try **C2** instead of C3.  
4. **D** DB25 male straight into **C** female.  
5. **Pi G:** 5V → **PWR IN** (right). **F** OTG → **DATA** (middle). **D** USB → hub.

**StarTech = straight:** primary path **A2→C3→pin 3 (RX)**. VARE2/C is 1:1 (screw N = DB25 pin N), so TX must land on **C3**, not C2.

OLED **JMD0.96D-1**: DuPont F–F to pins 1/3/5/6 (optional).

Test: `python3 read_package.py --raw-capture --port /dev/ttyUSB0`
