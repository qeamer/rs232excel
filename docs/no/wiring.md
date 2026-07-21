# Kobling

Sett inn **40 cm DB25 hann→hunn skjøtekabel** mellom eksisterende PLS-kabel og OKI-skriverens port.

Midt på kabelen klippes **kun** lederne for:

| Pinne | |
|:--|:--|
| **2** | Datalinja (PLS → skriver) |
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
