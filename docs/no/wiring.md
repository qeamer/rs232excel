# Kobling

<img src="img/tapp-dine-deler.png" width="100%" alt="Handlekurv: USB–DB25 nullmodem, DuPont, hunn-breakout, pigtail"/>

<img src="img/passiv-rs232-tapp.png" width="100%" alt="Passiv tapp med dine deler"/>

## Det du kjøper (handlekurv)

| # | Del | Rolle |
|---|-----|--------|
| 1 | **USB→DB25 hann** (FTDI, **null modem** / krysset) | Lytteadapter på huben → `/dev/ttyUSB0` |
| 2 | **DuPont F–F** 10 cm | Midlertidig/kort kobling mellom skruer / hoder |
| 3 | **DB25 hunn-breakout** m/skruer | PLS DB25 **hann** plugges rett inn; tapp på skrue 2 og 7 |
| 4 | **DB25 hunn-pigtail** → nakne ledere | Alternativ vei til å finne/feste ledere (pin 2/3/7) |

## Viktig: det som fortsatt mangler for skriveren

Breakouten i kurven er **bare hunn** — den er **ikke** M↔F pass-through.  
PLS hann → breakout gir deg skruer, men **signalet går ikke videre til OKI av seg selv**.

Du trenger fortsatt én av:

- eksisterende skjøtekabel / Y som lar skriveren få signal **og** at du tapper, **eller**
- **DB25 M↔F breakout** (hann+hunn på samme board), **eller**
- DB25 **hann**-utgang (hann-pigtail / skjøt) fra skruene 1:1 til OKI (alle pinner, ikke bare 2 og 7)

## Lyttekobling (med null modem)

På anleggs-breakout (PLS-linja):

| Skrue | Signal |
|-------|--------|
| **2** | TX (data PLS→skriver) — tapp |
| **7** | GND — tapp |
| 3 | RX andre veien — **ikke** tapp til Pi |

USB–DB25 er merket **null modem** (TX/RX krysset inne i kabelen). Derfor:

| Prøv | Breakout | → | USB–DB25 hann |
|------|----------|---|----------------|
| **A (først)** | skrue **2** (TX) | → | pin **2** |
| | skrue **7** (GND) | → | pin **7** |
| **B (hvis null data)** | skrue **2** (TX) | → | pin **3** |
| | skrue **7** (GND) | → | pin **7** |

Bruk DuPont F–F eller pigtail-ledere inn i skruene. **Ikke GPIO.**

## USB til Pi

```text
Pi DATA ── OTG (USB-A HUNN) ← hub (USB-A HANN)
                              ├── tastatur
                              ├── minnepenn → /media/usb0
                              └── USB→DB25 (null modem) → /dev/ttyUSB0
```

PWR IN (hjørne): 5V / ≥2,5 A.

Test:

```bash
python3 read_package.py --raw-capture --port /dev/ttyUSB0
```

*English: [docs/en/wiring.md](../en/wiring.md)*
