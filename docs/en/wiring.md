# Wiring

<img src="img/passive-rs232-tap.png" width="100%" alt="Passive RS-232 tap — DB9 middle / DB25 ends"/>

## What you have

| Part | Connector |
|------|-----------|
| PLC and OKI | **DB25** |
| Extension (middle) | Often a **DB9** cable with **DB25 adapters** on each end |
| Pi OTG | micro-USB **male** (into Pi) → USB-A **female** (hub male plugs in) |
| Pi listen | USB–RS232: USB-A **male** (into hub) → DB9 **female** → DB25 adapter → WAGO |

The signals to tap are still **DB25 pin 2 (TX)** and **pin 7 (GND)** at the PLC/printer.  
In the DB9 middle section that maps to:

| Signal | DB25 (PLC/OKI / adapter) | DB9 (conductor in middle) |
|--------|--------------------------|---------------------------|
| TX (data PLC→printer) | **2** | **3** |
| GND | **7** | **5** |

## Wire colors — do not trust them

Cheap extensions use **different colors**. There is no reliable “red = TX” rule.

**Find the conductors with a continuity tester:**

1. Insert the extension (or hold the DB25 adapter).
2. Probe **metal pin 2** on the DB25 end (TX).
3. Probe the thin conductors mid-cable (jacket opened) — the one that beeps is **TX**.
4. Repeat with **pin 7** → that is **GND**.
5. Mark both with tape before cutting.

## Tap (two conductors only)

**Slit the jacket** on the DB9 middle — **do not cut the whole cable through**.  
Cut **only** the two conductors you verified (TX + GND). Leave all others intact.

**WAGO 221** — three ends in each clamp:

```
PLC side ──┐
           ├── WAGO ── printer side
Pi branch ─┘
```

## On to USB–RS232 (separate branch — not into PLC/OKI)

The extension’s **DB25** ends go only into the PLC and printer.  
The listen adapter is a separate branch:

```text
Pi ── micro-USB MALE ── OTG ── USB-A FEMALE
                                    ↑
                              hub (USB-A FEMALE ports)
                                    ↑
              USB-A MALE ── USB-RS232 ── DB9 FEMALE ── DB25 adapter ── WAGO
```

| From WAGO | To listen adapter (serial end) |
|-----------|-------------------------------|
| TX (DB25 pin 2 / DB9 pin 3) | **RX** |
| GND (DB25 pin 7 / DB9 pin 5) | **GND** |

TX → RX — never TX to TX. → `/dev/ttyUSB0`.

Secure the splice in the cable tray. Never leave a WAGO hanging loose.

*Norwegian: [docs/no/wiring.md](../no/wiring.md)*
