# Installasjonsguide

Komplett gjennomgang — fra tom SD-kort til fangst i produksjon på høvleriet. Ca. 45 minutter, ingen programmeringserfaring nødvendig.

## Allerede installert? Bruk bare dette

På HDMI: **ingen login** — tallmeny direkte.

```text
1  Porter     2  Sjekk     3  Logg     4  Status
5  Start      6  Stopp     7  Restart   8  Excel
```

Oppdater / fiks hengende login (kjør via **SSH** — HDMI-login kan henge):

```bash
ssh pi@192.168.1.53
cd ~/rs232excel
git pull origin cursor/pakkemaskin-cli-ef03
cd python/no
bash fiks-login.sh
```

(`fiks-login.sh` skrur av cloud-init, maskerer login, starter meny, rebooter.)

Resten av denne siden er **første gangs installasjon** (SD-kort → kabler → verifisering).

---

<img src="img/signal-flow.png" width="100%" alt="Systemarkitektur"/>

Skriveren fortsetter å skrive fysiske pakkelapper **helt som før**. Tappen lytter bare — den sender aldri — så skriver og PLS oppfører seg likt uansett om Pi-en er påslått eller ikke.

---

## 1 · Deler

| # | Del | Kilde | Formål |
|---|-----|-------|--------|
| 1 | Raspberry Pi Zero WH | RS 2858711 | Hoveddatamaskin, ferdig loddet header |
| 2 | StarTech ICUSB232DB25 | RS 1238049 | USB → RS-232 DB25 adapter |
| 3 | RS PRO 4-port USB-hub | RS 2206492 | Serieadapter + minnepenn samtidig |
| 4 | Lexar 32GB Industrial microSDHC | RS 2676402 | Systemdisk — fasiten |
| 5 | 2× Kingston 64GB USB-minnepenn | RS 0622158 | Sanntidsspeiling av CSV + Excel |
| 6 | RS PRO IP54 kapsling 60×190×110 | RS 1959122 | Støvbeskyttelse |
| 7 | WAGO 221-412 klemmer, 10-pk | RS 8837544 | Verktøyfri avgrening |
| 8 | DB25 hann→hunn skjøtekabel 40 cm | AliExpress | **AKTIV** tapp-kabel |
| 9 | DB25 hann→hunn skjøtekabel 50 cm | AliExpress | Reserve — merk med tape |
| 10 | Micro-USB OTG adapter | AliExpress | Pi Zero → hub |
| 11 | SSD1306 0,96" OLED, I2C, 4-pin | AliExpress | Statusskjerm (valgfritt) |
| 12 | Dupont hopperledninger F-F | AliExpress | 4 av 40 brukes (OLED) |

I tillegg: **5V / minst 2,5 A** micro-USB strømforsyning (helst 3 A), tynn ledning til WAGO-grenen.

> **Strøm er kritisk på Pi Zero.** For lite ampere → «mystiske» feil: tastatur som ikke svarer,
> USB-enheter som forsvinner, hengende konsoll. Bruk godkjent vegglader (**5,0–5,1 V, ≥ 2,5 A**),
> ikke svak telefonlader. HDMI + hub + tastatur + minnepenn trekker mer enn Pi-en alene.

---

## 2 · Flash SD-kortet (på Windows/Mac)

Last ned **Raspberry Pi Imager** fra [raspberrypi.com/software](https://www.raspberrypi.com/software/), sett inn SD-kortet, og konfigurer som vist:

<img src="img/pi-imager-setup.png" width="100%" alt="Raspberry Pi Imager"/>

Hovedvalg: **Device** = Raspberry Pi Zero **WH** · **OS** = Raspberry Pi OS **Lite (32-bit)** · **Storage** = Lexar-kortet. Trykk tannhjul (eller Ctrl+Shift+X) for tilpasningsskjermen, deretter **Write** (~5 min).

> **Hvorfor Lite (32-bit)?** Pi Zero WH har ARMv6 — 64-bit OS støttes ikke. Uten skrivebord: raskere oppstart, mindre slitasje på SD-kortet, alt gjøres over SSH uansett.

---

## 3 · Første oppstart og SSH

1. Sett SD-kortet i Pi-en. Koble strøm til porten merket **PWR IN**.
2. Vent 1–2 minutter (grønt LED roer seg).
3. Fra PC-en på samme nettverk:

```bash
ssh pi@pakkemaskin.local
# eller IP fra ruteren:
ssh pi@192.168.1.42
```

Windows uten ssh? [PuTTY](https://putty.org) eller WSL.

> **Login på HDMI henger / tastaturet «virker ikke» ved `login:`?**  
> Det er ofte en sen boot-melding som ødelegger prompten — ikke dødt tastatur.  
> Trykk **Alt+F2** for en ny, ren login på tty2. (Tilbake til første skjerm: **Alt+F1**.)  
> Eller SSH: `ssh pi@192.168.x.x` (IP vises ofte over login-linjen).

---

## 4 · Installer programvaren

Lim inn disse blokkene én om gangen i SSH:

```bash
# Systemoppdatering (~5 min)
sudo apt update && sudo apt upgrade -y

# Klon repoet
git clone https://github.com/qeamer/rs232excel.git
cd rs232excel/python/no

# Avhengigheter og autostart (+ kommandoen «pakkemaskin»)
bash installer.sh
```

Etter dette fungerer `start`, `stopp`, `logg`, `sjekk`, osv. fra hvor som helst.

Valgfri OLED-skjerm:

```bash
pip3 install --break-system-packages luma.oled
sudo raspi-config      # Interface Options → I2C → Enable → reboot
python3 vis_status.py  # kjører uavhengig av fangst
```

---

## 5 · Fysisk tapping

**Stopp maskinen før du rører kabler.** Originalkabelen endres aldri — 40 cm skjøtekabelen settes **i serie** ved skriveren og kan fjernes på sekunder.

Se også: [wiring.md](wiring.md)

<img src="img/passiv-rs232-tapp.png" width="100%" alt="Passiv RS-232-tapp pin 2 og 7"/>

> Ignorer AI-illustrasjoner som viser GPIO, parallellport (D0–D7) eller 40-pinners LCD — signalet går til **USB–RS232 → `/dev/ttyUSB0`**.

Steg for steg:

1. **Sett inn 40 cm skjøtekabel** mellom skriverens DB25 og eksisterende kabel fra sorteringsanlegget. Ta bilde av originaltilkoblingen først.
2. **Åpne kappen** midt på skjøten (klipp **ikke** hele kabelen over). Finn lederne for **pinne 2 (TX)** og **pinne 7 (GND)**. Fotografer fargekoding før klipping.
3. **Klipp kun disse to lederne** — alle andre ledere urørt, så skriveren fortsatt får hele signalet.
4. **WAGO: tre ender per klemme** — PLS-side + skriver-side (signalet går ubrutt) + ny tynn ledning til USB-serieadapter.
5. **Fest skjøten** med strips i kabelrenna — la aldri WAGO henge løst. Merk aktiv kabel med tape.

> ⚠ **Retning teller:** pinne 2 fra skriversiden er **TX** (signalkilden). Den kobles til adapterens **RX**. TX→TX fanger ingenting.

### USB-kjede

<img src="img/usb-kjede-komplett.png" width="100%" alt="USB-kjede: WAGO-tapp → ICUSB232DB25 → hub"/>

OTG-adapteren **må** i **data**-porten midt på Pi Zero — hjørneporten er kun strøm (**PWR IN**).

**Anbefalt produksjonsoppsett (tastatur + minnepenn + serieadapter samtidig):**

```text
PWR IN (hjørne) ─── 5V / ≥2,5 A vegglader (helst 3 A)

USB midt ─── OTG ─── USB-hub (gjerne med egen strøm)
                         ├── USB-tastatur
                         ├── minnepenn      → /media/usb0 (CSV+Excel)
                         └── RS-232-adapter → /dev/ttyUSB0
```

- SD-kortet er alltid fasiten (fangst fortsetter uten minnepenn).
- Minnepennen speiler **CSV + Excel** automatisk som **årets** filer, f.eks. `pakkelapper2026.csv` + `pakkelapper2026.xlsx` på `/media/usb0`. Samme filer oppdateres på stedet (ikke nye kopier hver gang). Ved årsskifte startes nye `…2027…`-filer.
- USB-skriving bruker **fsync** og ved korrupt/avvik **atomisk omskriving** fra SD. Kommando `integritet` (eller meny **1 USB**) sjekker/helbreder pennen etter hard yank uten trygg utløsing.
- Menyvalg **8 Excel** / kommando `excel` er valgfri «oppdater nå»; Wi‑Fi-henting kan komme senere.
- Passiv hub uten ekstra strøm fungerer ofte med 2,5–3 A vegglader; ved ustabilitet: **hub med egen PSU**.
- Tastatur med innebygd hub: OK — sett minnepenn/serieadapter i den, eller bruk separat hub.

### OLED statusskjerm (valgfritt)

<img src="img/oled-i2c-korrekt.png" width="80%" alt="OLED I2C fire ledninger"/>

Fire hopperledninger (I2C), helt uavhengig av USB-kjeden. Eget program (`vis_status.py`) — krasjer den, påvirkes ikke fangsten. **Ikke** 40-pinners LCD-HAT.

---

## 6 · Verifiser før produksjon

**Test 1 — bare fangst, ingenting lagres.** Kjør en pakke gjennom anlegget:

```bash
cd ~/rs232excel/python/no
python3 read_package.py --bare-fangst --port /dev/ttyUSB0
```

Sammenlign med den trykte lappen. Rart tegn (`6´´ ·5Ø ±50` i stedet for `645 75X 150`)? PLS bruker sannsynligvis 7E1:

```bash
python3 read_package.py --bare-fangst --paritet E --databits 7
```

Ingenting i det hele tatt? Prøv `--baud 4800`, `2400`, eller `19200`, og sjekk pin 2/7-skjoeten.

**Test 2 — ekte fangst.** Produksjonskommando:

```bash
python3 read_package.py --port /dev/ttyUSB0 --usb-sti /media/usb0
```

<img src="img/terminal-capture.png" width="100%" alt="Sanntidsfangst"/>

Kjør 2–3 pakker, sjekk `pakkelapperYYYY.csv` mot papirlappene, trekk ut minnepennen midt i kjøring (fangst fortsetter), sett den inn igjen (manglende rader synkes).

**Produksjon.** Tjenesten fra steg 4 starter automatisk ved boot:

```bash
start
logg     # live logg
```

> Etter install skriver du bare `start`, `stopp`, `restart`, `status`, `logg`, `sjekk`, `excel`.
> Ved kræsj eller etter kabelbytte: `restart`

---

## 7 · Resultatet

`--eksporter-xlsx` lager en merket arbeidsbok: **Sammendrag**-ark med totaler per sort, per dag/måned/år, pluss grafer — deretter ett ark per sortkategori og **Rådata**-ark. Alle summer er formler mot rådata.

<p align="center">
<img src="img/excel-summary.png" width="49%" alt="Excel Sammendrag"/>
<img src="img/excel-charts.png" width="42%" alt="Excel grafer"/>
</p>

Trekk ut minnepennen når som helst — årets `pakkelapperYYYY.csv` og `pakkelapperYYYY.xlsx` ligger klare på pennen (samme filer oppdateres under fangst; nytt år = nye filnavn).

---

## 8 · Sjekkliste

- [ ] Alle deler mottatt (SD-kort sendes separat!)
- [ ] 40 cm kabel merket AKTIV, 50 cm merket RESERVE
- [ ] Tap skjøtet: pin 2+7 WAGO, festet med strips
- [ ] USB-kjede: Pi **data-port** → OTG → hub → adapter + minnepenn
- [ ] OLED på GPIO 1/3/5/6, I2C aktivert (hvis brukt)
- [ ] `--bare-fangst` viser lesbar lappetekst
- [ ] Live kjøring verifisert mot papirlapper
- [ ] Minnepenn ut/inn → rader synket
- [ ] systemd-tjeneste aktivert → overlever strømbrudd
- [ ] Excel-eksport med Sammendrag, grafer og logo

---

*Spørsmål eller koblingsbilde som ikke stemmer? Åpne en issue.*

*English version: [docs/en/INSTALLATION.md](../en/INSTALLATION.md)*
