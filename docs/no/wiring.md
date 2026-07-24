# Kobling

<img src="img/passiv-rs232-tapp.png" width="100%" alt="Passiv RS-232-tapp DB9 midt / DB25 ender"/>

## Hva du har

| Del | Kontakt |
|-----|---------|
| PLS og OKI | **DB25** |
| Skjøtekabel (midt) | Ofte **DB9**-kabel med **DB25-adapter** i hver ende |
| Pi-lytting | **StarTech ICUSB232DB25** (USB → DB25) |

Signalet som skal tappes er fortsatt **DB25 pin 2 (TX)** og **pin 7 (GND)** på PLS/OKI-siden.  
I DB9-midten tilsvarer det:

| Signal | DB25 (PLS/OKI / adapter) | DB9 (leder midt i skjøten) |
|--------|--------------------------|----------------------------|
| TX (data PLS→skriver) | **2** | **3** |
| GND | **7** | **5** |

## Farger — ikke stol på dem

Billige skjøter bruker **ulike farger**. Det finnes ingen pålitelig «rød = TX»-regel.

**Finn lederne slik (multimeter / pipetest):**

1. Sett skjøten inn (eller hold DB25-adapteren i hånden).
2. Sett den ene Proben på **metallpinne 2** i DB25-enden (TX).
3. Pip deg gjennom de tynne lederne midt i kabelen (kappen åpnet) — den som piper er **TX**.
4. Gjenta med **pinne 7** → det er **GND**.
5. Merk de to lederne med tape før du klipper.

## Tapp (kun to ledere)

**Åpne kappen** midt på DB9-delen — **klipp ikke hele kabelen over**.  
Klipp **kun** de to lederne du har verifisert (TX + GND). Alle andre urørt.

**WAGO 221** — tre ender i hver klemme:

```
PLS-side ──┐
           ├── WAGO ── skriver-side
Pi-gren ───┘
```

## Videre til ICUSB232DB25

| Fra WAGO | Til StarTech ICUSB232DB25 |
|----------|---------------------------|
| TX (fra DB25 pin 2 / DB9 pin 3) | **RX** |
| GND (fra DB25 pin 7 / DB9 pin 5) | **GND** |

TX → RX — aldri TX til TX. USB-enden av StarTech i huben → `/dev/ttyUSB0`.

Fest skjøten i kabelrenna. La aldri WAGO henge løst.

*English: [docs/en/wiring.md](../en/wiring.md)*
