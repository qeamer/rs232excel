# Wiring

<img src="img/passive-rs232-tap.png" width="100%" alt="Listen: MG screws 2+7 → female breakout → FTDI null modem → Pi"/>

## Your plan — yes

```text
PLC DB25 MALE → DB25-MG (F+M+screws) → ribbon 1:1 → OKI
                     screws 2 (TX) + 7 (GND)
                              ↓
              DB25 FEMALE terminal adapter (solder-free)
                              ↓ mated
              FTDI USB→DB25 MALE (null modem) → hub → Pi DATA
```

Prefer tapping from **MG screws 2 and 7** (same signals as in the ribbon — don’t cut the ribbon).

Null modem: try MG 2 → listen screw **2**, 7→7 first; if no data use listen screw **3** for TX. Leave other listen screws empty.

PWR IN = power only. DATA = OTG → hub. Not GPIO.

*Norwegian: [docs/no/wiring.md](../no/wiring.md)*
