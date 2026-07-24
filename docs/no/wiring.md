# Kobling

<img src="img/passiv-rs232-tapp.png" width="100%" alt="PLS DB25 hann → breakout → skriver; skrue 2+7 → USB–DB25 → Pi"/>

## Enkel kjede (anbefalt)

1. **PLS DB25 hann** går rett inn i **breakout** (hunn-siden).
2. Fra breakout **hann** → skjøtekabel → **OKI**.
3. Fra breakout **skrue 2 (TX)** og **skrue 7 (GND)** → ny **USB–DB25**-adapter (**RX** + **GND**).
4. USB–DB25 → **USB-hub** → Pi DATA (via OTG-skjøtekabel).

Ingen kniv i kabel. Ikke GPIO. Signal → `/dev/ttyUSB0`.

| Fra breakout | Til USB–DB25 |
|--------------|--------------|
| Skrue **2** (TX) | **RX** |
| Skrue **7** (GND) | **GND** |

TX → RX — aldri TX til TX.

## Deler

| Del | Rolle |
|-----|--------|
| **DB25 M↔F breakout** m/skruer | Pass-through PLS↔skriver + tapppunkt |
| **USB–DB25** (ny, til Pi) | RS-232-nivå → USB på huben |
| Skjøtekabel DB25 | Breakout → OKI |
| Pi OTG | micro-USB **hann** → USB-A **hunn** |
| USB-hub | hann inn i OTG; tastatur + penn + USB–DB25 |

Har du allerede StarTech ICUSB232DB25 (DB9 + DB25-adapter), kan den brukes som USB–DB25 — samme rolle.

## USB til Pi

<img src="img/usb-kjede-komplett.png" width="100%" alt="USB-kjede"/>

```text
Pi DATA ── OTG (USB-A HUNN) ← hub (USB-A HANN)
                              ├── tastatur
                              ├── minnepenn → /media/usb0
                              └── USB–DB25 → /dev/ttyUSB0
                                    ↑
                         breakout skrue 2+7 (TX→RX, GND)
```

PWR IN (hjørne): 5V / ≥2,5 A. Ikke DATA-porten.

## Mer detalj

- Steg A/B (breakout vs WAGO): [tapp-steg-for-steg.png](img/tapp-steg-for-steg.png)
- Breakout-fokus: [tapp-anbefalt-breakout.png](img/tapp-anbefalt-breakout.png)

*English: [docs/en/wiring.md](../en/wiring.md)*
