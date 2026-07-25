# Kobling — bruksanvisning A–G

<img src="img/bruksanvisning-tapp-foto.png" width="100%" alt="AI-foto bruksanvisning A–G"/>

<img src="img/passiv-rs232-tapp.png" width="100%" alt="Skjema bruksanvisning A–G"/>

## Gjenstander

| | Del | |
|--|-----|--|
| **A** | DB25-MG | Anlegg: hunn+hann+skruer |
| **B** | Båndkabel M↔F | A → OKI |
| **C** | DB25 hunn-terminal | Lytte — én hunn + skruer |
| **D** | StarTech USB→serie + DB25-hann (har) | Rett inn i **C** |
| **E1** | Ledning / DuPont | **A**-skrue **2** → **C**-skrue **3** (prøv 2 hvis null data) |
| **E2** | Ledning / DuPont | **A**-skrue **7** → **C**-skrue **7** |
| **F** | Hub + OTG | Til **G** DATA |
| **G** | Pi Zero WH | Se porter under |

**Ikke:** ekstra loop-kabler i C · gender-changer på siden av C · WAGO · GPIO.

## Pi Zero porter (langs kanten)

Fra **venstre → høyre**:

1. **HDMI** (helt til venstre)  
2. **DATA / USB** (midt) ← OTG + hub hit  
3. **PWR IN** (helt til **høyre**) ← kun 5V  

## Steg

1. **Anlegg:** PLS-hann → **A** (DB25-MG)-hunn. **A**-hann → **B** (bånd) → OKI.  
2. **Tapp på A = DB25-MG:** **E1** i skrue **2**, **E2** i skrue **7**.  
3. **Inn på C = DB25 hunn-terminal (lytte):** **E1** → skrue **3** (StarTech/RX; prøv 2 hvis null data), **E2** → skrue **7**.  
4. **D = StarTech** DB25-hann rett inn i **C** sin hunn-front.  
5. **Pi G:** 5V → **PWR IN** (høyre). **F** OTG → **DATA** (midt). **D** USB → hub.

OLED **JMD0.96D-1**: DuPont F–F til pin 1/3/5/6 (valgfritt).

Test: `python3 read_package.py --raw-capture --port /dev/ttyUSB0`

*English: [docs/en/wiring.md](../en/wiring.md)*
