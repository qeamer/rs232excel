# Kobling

<img src="img/passiv-rs232-tapp.png" width="100%" alt="Lytting: MG skrue 2+7 → hunn-breakout → FTDI null modem → Pi"/>

## Din plan — ja, slik

```text
PLS DB25 HANN
      │
      ▼ i inngrep
DB25-MG (hunn + hann + skruer)
      │
      ├── HANN ── båndkabel M↔F (1:1) ──► OKI
      │
      └── skrue 2 (TX) + skrue 7 (GND)
                │
                ▼ DuPont / ledning
DB25 HUNN terminal-adapter (solder free)
      │  kun skrue 2 (eller 3) + skrue 7
      ▼ i inngrep
FTDI USB→DB25 HANN (null modem)
      │
      ▼ USB-A
USB-hub → OTG → Pi DATA
```

**Best:** ta TX/GND fra **MG-skrue 2 og 7** (samme signal som i båndkabelen til skriver).  
Da slipper du å klippe/skjøte i båndkabelen. Båndet får stå urørt 1:1 til OKI.

Å «lytte fra båndkabelen» er elektrisk det samme — men mer rotete (finne farge/leder). Bruk skruene.

## Lytte-hunnen + FTDI

| Del | Rolle |
|-----|--------|
| DB25 **hunn** terminal breakout (solder free) | Tar imot FTDI-hannen; skruer for pin 2/3/7 |
| FTDI USB→DB25 **hann** **null modem** | Plugges i hunnen → hub → Pi |
| DuPont F–F | MG-skrue → lytte-hunn-skrue |

### Null modem

| | Fra MG | → | Lytte-hunn (mot FTDI) |
|--|--------|---|------------------------|
| **A først** | skrue **2** TX | → | skrue **2** |
| | skrue **7** GND | → | skrue **7** |
| **B hvis null data** | skrue **2** TX | → | skrue **3** |
| | skrue **7** GND | → | skrue **7** |

La alle andre skruer på lytte-hunnen stå **tomme** (ikke koble FTDI sin TX ut tilbake til anlegget).

## Pi

| Port | |
|------|--|
| **PWR IN** (hjørne) | 5V / ≥2,5 A |
| **DATA** (midt) | OTG → hub → FTDI (+ evt. minnepenn) |

Ikke GPIO. Test: `python3 read_package.py --raw-capture --port /dev/ttyUSB0`

<img src="img/tapp-deler-korrekt.png" width="100%" alt="Deler-referanse"/>

*English: [docs/en/wiring.md](../en/wiring.md)*
