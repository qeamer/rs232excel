# Wiring

Insert **40 cm DB25 M→F extension** between the existing PLC cable and the OKI printer port.

Mid-cable, cut **only** the conductors for:

| Pin | |
|:--|:--|
| **2** | Data line (PLC → printer) |
| **7** | Ground |

**WAGO 221** — three wires in each clamp:

```
PLC side ──┐
           ├── WAGO ── printer side
Pi branch ─┘
```

Connect Pi branch to StarTech ICUSB232DB25:

| From WAGO | To adapter |
|:--|:--|
| Data (pin 2) | **RX** |
| GND (pin 7) | **GND** |

Secure the splice in the cable tray. Never leave WAGO hanging loose.

*Norwegian: [docs/no/wiring.md](../no/wiring.md)*
