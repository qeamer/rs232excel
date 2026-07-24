# Kobling

<img src="img/tapp-anbefalt-breakout.png" width="100%" alt="Anbefalt tapp med DB25 breakout — uten å klippe"/>

<img src="img/tapp-steg-for-steg.png" width="100%" alt="Steg-for-steg: metode A breakout / metode B WAGO"/>

## Anbefaling: kjøp breakout — ikke klipp

| | Metode A (anbefalt) | Metode B (fungerer) |
|--|---------------------|---------------------|
| Del | **DB25 hann↔hunn breakout** med skrueterminaler | Kort offer-skjøt + **WAGO 221** |
| Inngrep | Sett boardet inn i skjøten | Åpne kappe, klipp kun TX+GND |
| Reversibelt | Ja — trekk ut boardet | Mindre pent |
| Finn TX/GND | Merkt **pin 2** og **pin 7** på boardet | Pipetest (farger lyver) |
| Søk | `DB25 male female breakout screw terminal` | — |

Kjøp gjerne to breakouts (én i drift, én reservedel). Billige AliExpress/Amazon-varianter holder i skap; DIN-rail (f.eks. Winford) hvis du vil ha mer industrielt.

**Ikke** GPIO. **Ikke** parallellport (STROBE/D0…). **Ikke** 40-pinners LCD-HAT. Signal går til `/dev/ttyUSB0` via USB–RS232.

## Hva du har

| Del | Kontakt |
|-----|---------|
| PLS og OKI | **DB25** |
| Skjøtekabel (midt) | Ofte **DB9**-kabel med **DB25-adapter** i hver ende |
| Pi OTG-skjøtekabel | micro-USB **hann** inn i Pi DATA → USB-A **hunn** ute |
| USB-hub | egen USB-A **hann**-kabel inn i OTG-hunnen |
| StarTech / DB9-kabel | USB-A **hann** inn i hubben → DB9 **hann** + **DB9→DB25-adapter** → DB25 **hann** |

| Signal | DB25 (PLS/OKI / breakout) | DB9 (hvis midtseksjon) |
|--------|---------------------------|------------------------|
| TX (data PLS→skriver) | **2** | **3** |
| GND | **7** | **5** |

## Metode A — breakout (anbefalt)

1. Sett **DB25 M↔F breakout** inn mellom PLS-kabel og OKI (eller midt i kort offer-skjøt). Originalkabel urørt.
2. Alle pinner går 1:1 gjennom boardet.
3. Fra **skrue 2 (TX)** → ledning til lytteadapterens **RX**.
4. Fra **skrue 7 (GND)** → ledning til lytteadapterens **GND**.
5. Fest i kabelrenne. Merk «AKTIV».

## Metode B — WAGO (hvis du ikke bestiller)

**Farger — ikke stol på dem.** Pipetest fra DB25-pinne **2** og **7**.

1. Sett inn kort **offer-skjøt**. Original PLS→OKI røres aldri.
2. Åpne kappen midt på skjøten — **klipp ikke hele kabelen over**.
3. Klipp **kun** TX + GND. Tre ender i hver WAGO 221: PLS | OKI | Pi-gren.
4. Pi-gren: TX → RX, GND → GND.

```
PLS-side ──┐
           ├── WAGO ── skriver-side
Pi-gren ───┘
```

## USB–RS232 (egen grein)

<img src="img/usb-kjede-komplett.png" width="100%" alt="USB-kjede med riktige kjønn"/>

```text
Pi DATA ── micro-USB HANN ── OTG-skjøtekabel ── USB-A HUNN
                                                    ↑
                              hubens USB-A HANN ────┘
                                    │
                         ├── tastatur
                         ├── USB-pinne → /media/usb0
                         └── StarTech / DB9-kabel:
                               USB-A HANN inn i hub
                               → DB9 HANN
                               → DB9→DB25-adapter
                               → DB25 HANN → breakout/WAGO-lytting
                               → /dev/ttyUSB0
```

| Fra tapp (breakout/WAGO) | Til StarTech (serie-ende) |
|--------------------------|---------------------------|
| TX (DB25 pin 2) | **RX** |
| GND (DB25 pin 7) | **GND** |

TX → RX — aldri TX til TX.

Eldre oversiktstegning (WAGO-fokus): [passiv-rs232-tapp.png](img/passiv-rs232-tapp.png)

*English: [docs/en/wiring.md](../en/wiring.md)*
