# Kobling — bruksanvisning

<img src="img/passiv-rs232-tapp.png" width="100%" alt="Bruksanvisning A–G med steg 1–5"/>

<img src="img/bruksanvisning-tapp-foto.png" width="100%" alt="Foto-versjon A–G"/>

## Deler (bokstaver)

| | Gjenstand | Hva det er |
|--|-----------|------------|
| **A** | DB25-MG | Hunn + hann + skruer 1–25 (anlegg) |
| **B** | Båndkabel DB25 M↔F | 1:1 skjøt A → OKI |
| **C** | DB25 **hunn** terminal | Lytte-hunn med skruer (én hunn-kontakt) |
| **D** | FTDI USB→DB25 **hann** | Null modem → hub |
| **E** | 2× DuPont F–F | Kun to ledninger (TX + GND) |
| **F** | USB-hub + OTG | Hub hann → OTG hunn → Pi DATA |
| **G** | Pi Zero WH + 5V | PWR IN = strøm · DATA = midt |

Ingen andre adaptere i lyttegreinen.

## Steg

1. **Anlegg:** PLS-hann → **A**-hunn. **A**-hann → **B** → OKI.  
2. **Tapp:** **E1** på **A**-skrue **2**. **E2** på **A**-skrue **7**.  
3. **Lytte-hunn:** **E1** → **C**-skrue **2**. **E2** → **C**-skrue **7**. (Ingen andre skruer på C.)  
4. **FTDI:** **D** DB25-hann rett inn i **C** hunn.  
5. **Pi:** 5V i **G** PWR IN. **F** OTG i **G** DATA. **D** USB-A i hub.

Null data? Flytt **E1** på **C** fra skrue 2 til skrue **3**.

## Kabeltabell

| Kabel | Fra | Til |
|-------|-----|-----|
| PLS-kabel | PLS · DB25 hann | **A** · hunn |
| **B** | **A** · hann | OKI |
| **E1** | **A** · skrue 2 | **C** · skrue 2 (eller 3) |
| **E2** | **A** · skrue 7 | **C** · skrue 7 |
| **D** DB25 | **D** · hann | **C** · hunn |
| **D** USB | **D** · USB-A | **F** · hub |
| **F** | hub hann | OTG → **G** DATA |
| PSU | 5V | **G** PWR IN |

Test: `python3 read_package.py --raw-capture --port /dev/ttyUSB0`

*English: [docs/en/wiring.md](../en/wiring.md)*
