# Wiring

Insert **40 cm DB25 hann→hunn** between the existing PLC cable and the OKI printer port.

Mid-cable, cut **only** the conductors for:

| Pin | |
|:--|:--|
| **2** | Data line (PLC → printer) |
| **7** | Ground |

**WAGO 221** — three wires in each clamp:

```
PLS side ──┐
           ├── WAGO ── printer side
Pi branch ─┘
```

Connect Pi branch to StarTech ICUSB232DB25:

| From WAGO | To adapter |
|:--|:--|
| Data (pin 2) | **RX** |
| GND (pin 7) | **GND** |

Secure the splice in the cable tray. Never leave WAGO hanging loose.

Illustrations: see project `illustrasjoner/` folder locally, or open `kobling-side7.html` / `kobling-side8.html`.
