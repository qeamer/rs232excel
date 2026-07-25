<p align="center">
  <a href="https://www.skjak-trelast.no">
    <img src="skaak_logo_vektor.png" height="80" alt="Skjåk Trelast AS"/>
  </a>
</p>

<p align="center">
  <a href="README.md" style="font-size: 1.45em; font-weight: 700">← Norsk Readme (hovedversjon)</a>
</p>

<h1 align="center">rs232excel</h1>

<p align="center" style="font-size: 1.1em">
  <b>Passive serial tap · Telemecanique TSX → OKI Microline → CSV & Excel</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3572A5"/>
  <img src="https://img.shields.io/badge/platform-Raspberry%20Pi%20Zero%20WH-C7053D"/>
  <img src="https://img.shields.io/badge/serial-RS--232%209600%208N1-555"/>
  <img src="https://img.shields.io/badge/license-MIT-1B4D3E"/>
</p>

<p align="center" style="font-size: 1.05em">
  <b>🇬🇧 English translation</b> — the project is built and maintained primarily for
  <a href="README.md"><b>Scandinavian sawmills (Norwegian version →)</b></a>
</p>

<p style="font-size: 1.05em">
A Raspberry Pi listens silently on the RS-232 line between a Telemecanique TSX PLC and an OKI Microline 280. Every timber package label is parsed to CSV/Excel — no manual entry.
<strong>No knife, no WAGO.</strong> StarTech straight: screw <b>2 → VARE2 C3 → pin 3 (RX)</b>
(no data? try C2).
</p>

<img src="docs/en/img/tap-mated.png" width="100%" alt="Step-by-step passive RS-232 tap, StarTech straight 2→3"/>

<img src="docs/en/img/db25-correct-pins.png" width="100%" alt="DB25 correct pins: pin 2=TX, pin 7=GND, StarTech RX=pin 3"/>

The tap is **physically read-only**: only TX+GND from DIN-rail breakout screws 2/7 to solder-free female **C3**/C7 → StarTech **ICUSB232DB25** pin 3 RX (straight; fallback C2). On the DB25: **pin 2 = TX**, **pin 7 = GND** (plant); StarTech **pin 3 = RX**. Signal to `/dev/ttyUSB0`, not GPIO. The printer keeps printing as before. Guide: [docs/en/wiring.md](docs/en/wiring.md) · [HANDOFF-CLAUDE.md](docs/no/HANDOFF-CLAUDE.md).

---

## Daily use on the Pi

After the Norwegian production install (`python/no`), HDMI shows a number menu (no login). Same actions work as one-word commands over SSH.

**First time / after rewiring** — confirm hardware before saving:

1. **USB** — hub, keyboard, stick, and serial adapter visible? Stick mounted?
2. **Sjekk** — dry-run one package through the plant (shown on screen, **not** saved).
3. **Logg** — once capture is running: live messages (**Ctrl+C** returns to the menu).

**Normal shift** — keep the service running:

5. **Start** — save packages (SD + mirror to stick)  
6. **Stopp** — end of shift / before troubleshooting  
7. **Restart** — if the service hangs, or after swapping USB cable/adapter  
8. **Excel** — optional “refresh now” (Excel is also mirrored automatically)

```bash
usb            # list USB + integrity check (SD ↔ stick)
integritet     # verify / heal flash drive from SD master
start   stopp   restart   status
logg           # live log — Ctrl+C to stop
sjekk          # dry run (does not save)
excel          # refresh Excel now
```

Yearly files on SD/stick: `pakkelapperYYYY.csv` + `.xlsx` (updated in place; new year → new names).  
Primary docs: **[README.md](README.md)** · **[docs/no/INSTALLATION.md](docs/no/INSTALLATION.md)** · **[CHANGELOG.md](CHANGELOG.md)**

---

## Quick start

**Production (Skjåk / appliance CLI, USB mirror, yearly files):** use [`python/no/`](python/no/) — see Norwegian README.

**English script mirror** (`python/en/` — flags in English; USB appliance tooling lives in `python/no/`):

```bash
git clone https://github.com/qeamer/rs232excel.git
cd rs232excel/python/en
pip install -r requirements.txt
python3 read_package.py --port /dev/ttyUSB0
python3 read_package.py --export-xlsx
```

📖 **[Installation guide (English) →](docs/en/INSTALLATION.md)** · **[Installasjonsguide (norsk) →](docs/no/INSTALLATION.md)**

---

## What you get

<p align="center">
<img src="docs/en/img/excel-summary.png" width="49%" alt="Excel summary"/>
<img src="docs/en/img/excel-charts.png" width="42%" alt="Excel charts"/>
</p>

A branded Excel workbook — in Norwegian production it is built **automatically** during capture and mirrored to the stick (`pakkelapperYYYY.xlsx`). `excel` / `--export-xlsx` is optional “refresh now”:

- **Summary** sheet — totals per sort category, per day / month / year, with pie, stacked-bar, and line charts. All values are live formulas over the raw data.
- **One sheet per sort category** (5th Grade / Crooked / Floor / Rejected / No Category) — frozen headers, autofilter, per-dimension mini-summary
- **Raw data** sheet — every captured package, one flat table

## How the capture works

<img src="docs/en/img/terminal-capture.png" width="100%" alt="Live capture"/>

| Situation on the floor | What the software does |
|---|---|
| Operator presses confirm twice | **Dedup** — package stored once, raw copy kept in `utskrift.txt` / `capture.txt` |
| A package never gets confirmed | **Gap detection** — logged in `manglerYYYY.csv` / `missing.csv`; cleared when the package arrives |
| Counter rolls over 9999 → 0 | **Round** — only if max &gt; 9000 and the new number is low (mid-series reprint does **not** start a new round) |
| Printer is off / out of paper | Data is on the wire anyway — capture continues |
| Flash drive yanked mid-run | SD is master; stick syncs/heals on re-insert (`integritet` / fsync + atomic rewrite) |
| Label never printed at all | `--register N` / `--registrer N` — a later real label upgrades an empty manual row |
| PLC sends odd ESC sequences | Full Epson/IBM escape table; unknown codes logged, never corrupt data |

## Commands (English)

| Flag | Purpose |
|---|---|
| `--port /dev/ttyUSB0` | Live capture (production) |
| `--raw-capture` | Raw capture, nothing saved — first-run verification |
| *(USB mirror / `integritet`)* | Norwegian production: `--usb-sti` in [`python/no/`](python/no/) |
| `--set-season raw` / `kiln-dried` | Match the physical season toggle on the machine |
| `--export-xlsx` | Generate the Excel workbook |
| `--summary` | Daily totals in the terminal |
| `--register 1234` | Manual package entry |
| `--simulate example.txt` | Offline test — no PLC needed |

Norwegian production flags (`--bare-fangst`, `--eksporter-xlsx`, …): see [`python/no/`](python/no/).

## Hardware

Raspberry Pi Zero WH · StarTech ICUSB232DB25 · **DB25-MG** + DB25 female terminal · ribbon ·
USB hub + OTG + keyboard + flash · optional OLED JMD0.96D-1.
Full parts list in the [installation guide](docs/en/INSTALLATION.md).

<p style="font-size: 15px; margin-bottom: 0.4em"><b>1 · Passive tap</b> — A–G guide (image above). No knife/WAGO.</p>

<p style="font-size: 15px; margin-bottom: 0.4em"><b>2 · USB chain</b> — OTG: micro-USB <b>male</b> → USB-A <b>female</b> (hub plugs in). StarTech DB25 <b>male</b> into listen female (C). Hub + keyboard + stick. PWR IN (right) ≥2.5 A · DATA (middle).</p>
<img src="docs/en/img/usb-chain-complete.png" width="100%" alt="USB chain OTG/hub/StarTech"/>

<p style="font-size: 15px; margin-bottom: 0.4em"><b>3 · OLED (optional)</b> — JMD0.96D-1 / SSD1306 I2C, four wires. Rotates day/year, last package, sort mix.</p>
<img src="docs/en/img/oled-i2c-correct.png" width="72%" alt="OLED I2C"/>

## Label format

```
   645                      75X 150     ← package no · dimension
   2026/ 6/22                5          ← date · sort digit
                            FURU        ← species (FURU=pine, GRAN=spruce)
              25            0           ← board count
             108,7          0,0         ← total length (running metres)
             1,223          0,000       ← volume (m³)
              43            0,0         ← avg length (dm)
```

## Project structure

```
docs/no/       ← primary docs (Norwegian)
docs/en/       ← English translation
python/no/     ← production code at Skjåk Trelast
python/en/     ← English mirror for GitHub / international use
```

## License

MIT

---

<p align="center">
  <sub><a href="https://www.skjak-trelast.no">Skjåk Trelast AS</a> · Telemecanique TSX · OKI Microline · RS-232 9600 8N1</sub>
</p>
