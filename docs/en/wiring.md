# Wiring

<img src="img/passive-rs232-tap.png" width="100%" alt="PLC DB25 male → breakout → printer; screws 2+7 → USB–DB25 → Pi"/>

## Simple chain (recommended)

1. **PLC DB25 male** plugs straight into the **breakout** (female side).
2. From breakout **male** → extension → **OKI**.
3. From breakout **screw 2 (TX)** and **screw 7 (GND)** → new **USB–DB25** adapter (**RX** + **GND**).
4. USB–DB25 → **USB hub** → Pi DATA (via OTG).

No cutting. Not GPIO. Signal → `/dev/ttyUSB0`.

| From breakout | To USB–DB25 |
|---------------|-------------|
| Screw **2** (TX) | **RX** |
| Screw **7** (GND) | **GND** |

TX → RX — never TX to TX.

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
