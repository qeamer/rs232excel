# Wiring

<img src="img/passive-rs232-tap.png" width="100%" alt="PLC DB25 male → breakout → printer; screws 2+7 → USB–DB25 → Pi"/>

## Simple chain (recommended)

1. **PLC DB25 male** plugs straight into the **breakout** (female side).
2. From breakout **male** → extension → **OKI**.
3. From breakout **screw 2 (TX)** and **screw 7 (GND)** → new **USB–DB25** adapter (**RX** + **GND**).
4. USB–DB25 → **USB hub** → Pi DATA (via OTG).

No cutting. Not GPIO. Signal → `/dev/ttyUSB0`.

### Pins — what maps where

On the **plant breakout** (PLC↔printer), screw number = DB25 pin:

| Breakout screw | Line signal | Meaning |
|----------------|-------------|---------|
| **2** | TX | Data PLC → printer (tap here) |
| **7** | GND | Signal ground (tap here) |
| 3 | RX | Printer→PLC — **do not tap** for listen |
| others | — | pass 1:1 only |

On the **listen adapter** (USB–DB25, typically DTE like a PC port):

| Adapter pin | Signal | From plant breakout |
|-------------|--------|---------------------|
| **3** | **RX** (listen in) | ← breakout screw **2** (TX) |
| **7** | **GND** | ← breakout screw **7** |
| 2 | TX out from adapter | **do not connect** (leave open) |

```text
PLANT (breakout)               LISTEN ADAPTER (USB–DB25)
────────────────               ────────────────────────
screw 2  TX  ────────────────→  pin 3  RX
screw 7  GND ───────────────→  pin 7  GND
```

**How into the listen adapter (pick one):**

1. **Best:** separate DB25-female screw breakout. Plug USB–DB25 **male** into it. Wire plant screw 2 → listen screw **3**, plant screw 7 → listen screw **7**.
2. **DuPont DB25 female** on the adapter male: use leads labeled **3** and **7** to plant 2 and 7.
3. Not GPIO. Don’t cut the hub cable.

TX → RX — never TX to TX. No data? Try swapping 2↔3 **on the listen end only** (some adapters are DCE).

## Parts

| Part | Role |
|------|------|
| **DB25 M↔F breakout** w/ screws | Pass-through PLC↔printer + tap point |
| **USB–DB25** (new, for Pi) | RS-232 levels → USB on the hub |
| DB25 extension | Breakout → OKI |
| Pi OTG | micro-USB **male** → USB-A **female** |
| USB hub | male into OTG; keyboard + stick + USB–DB25 |

If you already have StarTech ICUSB232DB25 (DB9 + DB25 adapter), it fills the USB–DB25 role.

## USB to Pi

<img src="img/usb-chain-complete.png" width="100%" alt="USB chain"/>

```text
Pi DATA ── OTG (USB-A FEMALE) ← hub (USB-A MALE)
                              ├── keyboard
                              ├── flash → /media/usb0
                              └── USB–DB25 → /dev/ttyUSB0
                                    ↑
                         breakout screws 2+7 (TX→RX, GND)
```

PWR IN (corner): 5V / ≥2.5 A. Not the DATA port.

## More detail

- Steps A/B (breakout vs WAGO): [tap-step-by-step.png](img/tap-step-by-step.png)
- Breakout focus: [tap-recommended-breakout.png](img/tap-recommended-breakout.png)

*Norwegian: [docs/no/wiring.md](../no/wiring.md)*
