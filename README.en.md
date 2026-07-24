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
A Raspberry Pi listens silently on the RS-232 line between a 1980s Telemecanique TSX PLC and an OKI Microline 280 dot-matrix printer at a Norwegian sawmill. Every timber package label is parsed and stored automatically — dimension, species, grade, board count, volume. No manual entry. No data loss, even when the printer is off.
</p>

<img src="docs/en/img/signal-flow.png" width="100%" alt="System architecture"/>

The tap is **physically read-only**: slit the jacket on the 40 cm extension and cut **only** the conductors for pin 2 (TX) and pin 7 (GND) — not the whole cable. WAGO three-way join; TX → adapter **RX**. Signal to `/dev/ttyUSB0`, not GPIO. The printer keeps printing as before.

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

Raspberry Pi Zero WH · StarTech ICUSB232DB25 · WAGO 221 · 40 cm DB25 extension ·
USB hub + keyboard + flash drive · optional SSD1306 OLED.
Full parts list in the [installation guide](docs/en/INSTALLATION.md).

<p style="font-size: 15px; margin-bottom: 0.4em"><b>1 · Passive tap</b> — slit the jacket; cut <b>only</b> pin 2 (TX) and pin 7 (GND) conductors. Not the whole cable. WAGO, TX→RX. Not GPIO.</p>
<img src="docs/en/img/passive-rs232-tap.png" width="100%" alt="Passive RS-232 tap"/>

<p style="font-size: 15px; margin-bottom: 0.4em"><b>2 · USB chain</b> — WAGO tap → <b>ICUSB232DB25</b> → hub (with keyboard + stick). PWR IN = power (≥2.5 A); data port → OTG → hub.</p>
<img src="docs/en/img/usb-chain-complete.png" width="100%" alt="USB chain with WAGO and ICUSB232DB25"/>

<p style="font-size: 15px; margin-bottom: 0.4em"><b>3 · OLED (optional)</b> — 0.96" SSD1306 I2C, four wires. Rotates day/year, last package, sort mix.</p>
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
