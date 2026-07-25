# Kobling — bruksanvisning A–G

<img src="img/passiv-rs232-tapp.png" width="100%" alt="Bruksanvisning: kun E1+E2, Pi PWR til høyre"/>

## Gjenstander

| | Del | |
|--|-----|--|
| **A** | DB25-MG | Anlegg: hunn+hann+skruer |
| **B** | Båndkabel M↔F | A → OKI |
| **C** | DB25 hunn-terminal | Lytte — én hunn + skruer |
| **D** | FTDI USB→DB25 hann | Null modem, plugges i **C** |
| **E1** | Én DuPont | **A**-skrue 2 → **C**-skrue 2 |
| **E2** | Én DuPont | **A**-skrue 7 → **C**-skrue 7 |
| **F** | Hub + OTG | Til **G** DATA |
| **G** | Pi Zero WH | Se porter under |

**Ikke:** ekstra loop-kabler i C · gender-changer på siden av C · WAGO · GPIO.

## Pi Zero porter (langs kanten)

Fra **venstre → høyre**:

1. **HDMI** (helt til venstre)  
2. **DATA / USB** (midt) ← OTG + hub hit  
3. **PWR IN** (helt til **høyre**) ← kun 5V  

## Steg

1. PLS-hann → **A**-hunn. **A**-hann → **B** → OKI.  
2. **E1** i **A**-skrue **2**. **E2** i **A**-skrue **7**.  
3. **E1** → **C**-skrue **2**. **E2** → **C**-skrue **7**. Stopp.  
4. **D**-hann rett i **C**-hunn.  
5. 5V → **G PWR IN** (høyre). **F** OTG → **G DATA** (midt). **D** USB → hub.

Null data? Flytt **E1** på **C** fra 2 til **3**.

Test: `python3 read_package.py --raw-capture --port /dev/ttyUSB0`

*English: [docs/en/wiring.md](../en/wiring.md)*
