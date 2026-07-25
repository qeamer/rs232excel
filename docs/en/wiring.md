# Wiring — parts A–G

Source of truth (Norwegian lettered guide): [docs/no/wiring.md](../no/wiring.md) · image: [passiv-rs232-tapp.png](../no/img/passiv-rs232-tapp.png)

**A** DB25-MG · **B** ribbon · **C** female screw breakout · **D** FTDI USB–DB25 male null modem · **E1/E2** two DuPont only · **F** hub+OTG · **G** Pi Zero.

Listen branch = only E1 (A screw 2 → C screw 2) and E2 (A screw 7 → C screw 7), then D into C. No extra loop wires.

Pi Zero ports left→right: **HDMI** · **DATA** (hub/OTG) · **PWR IN** (right, 5V only).
