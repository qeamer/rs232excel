# Kobling

<img src="img/passiv-rs232-tapp.png" width="100%" alt="Passiv RS-232-tapp"/>

Sett inn **40 cm DB25 hann→hunn skjøtekabel** mellom eksisterende PLS-kabel og OKI-skriverens port.

**Åpne kappen** midt på skjøten — **klipp ikke hele kabelen over**. Trekk ut og klipp **kun** disse to lederne (andre ledere urørt):

| Pinne | |
|:--|:--|
| **2** | Datalinja / TX (PLS → skriver) |
| **7** | Jord (GND) |

**WAGO 221** — tre ledninger i hver klemme:

```
PLS-side ──┐
           ├── WAGO ── skriver-side
Pi-gren ───┘
```

Koble Pi-grenen til StarTech ICUSB232DB25:

| Fra WAGO | Til adapter |
|:--|:--|
| Data (pin 2) | **RX** |
| GND (pin 7) | **GND** |

Fest skjøten i kabelrenna. La aldri WAGO henge løst.

*English: [docs/en/wiring.md](../en/wiring.md)*
