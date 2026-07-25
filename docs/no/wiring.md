# Kobling — bruksanvisning A–G

<img src="img/bruksanvisning-tapp-foto.png" width="100%" alt="AI-foto bruksanvisning A–G"/>

<img src="img/passiv-rs232-tapp.png" width="100%" alt="Skjema bruksanvisning A–G"/>

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

1. **Anlegg:** PLS-hann → **A** (DB25-MG)-hunn. **A**-hann → **B** (bånd) → OKI.  
2. **Tapp på A = DB25-MG:** **E1** i skrue **2**, **E2** i skrue **7**.  
3. **Inn på C = DB25 hunn-terminal (lytte):** **E1** → skrue **2**, **E2** → skrue **7**.  
4. **D = FTDI** DB25-hann rett inn i **C** sin hunn-front (ledningene blir sittende i C-skrue 2 og 7).  
5. **Pi G:** 5V → **PWR IN** (høyre). **F** OTG → **DATA** (midt). **D** USB → hub.

Null data? Flytt **E1** på **C** fra 2 til **3**.

Test: `python3 read_package.py --raw-capture --port /dev/ttyUSB0`

*English: [docs/en/wiring.md](../en/wiring.md)*
