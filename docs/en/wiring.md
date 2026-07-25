# Wiring

<img src="img/passive-rs232-tap.png" width="100%" alt="Correct: DB25-MG center, null modem, Pi DATA"/>

## Center piece: DB25-MG (not a loose gender-changer block)

You have **DB25-MG Ver 1.1**: green board with **FEMALE + MALE + screw terminals 1–25**.
That is both pass-through and tap.

```text
PLC DB25 MALE  --mated-->  DB25-MG FEMALE
                                │
                                ├── all pins 1:1 --> DB25-MG MALE --> extension --> OKI
                                │
                                └── screw 2 (TX) + screw 7 (GND) --wires--> listen end
```

## Listen end

USB→DB25 **male** **null modem** plugs into a **DB25 female**. Wires from MG screws 2 and 7 into that female (pins per table). USB-A → hub → OTG female → Pi **DATA** (middle micro-USB).

| | MG screw | → | USB–DB25 |
|--|----------|---|----------|
| **A first** | 2 TX | → | pin **2** |
| | 7 GND | → | pin **7** |
| **B if no data** | 2 TX | → | pin **3** |
| | 7 GND | → | pin **7** |

PWR IN = power only. Never GPIO. No fantasy side-jab wires into connector shells.

*Norwegian: [docs/no/wiring.md](../no/wiring.md)*
