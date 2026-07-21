# Pakkemaskin Skriver

<img src="skaak_logo_vektor.png" height="55" alt="Skjåk Trelast AS"/>

**Passive RS-232 tap for legacy industrial timber sorting systems — automatic package label capture to CSV and Excel.**

A Raspberry Pi listens silently on the serial line between a Telemecanique TSX PLC and an OKI Microline dot-matrix printer. Every package label is parsed and stored automatically — no manual data entry, no data loss even if the printer is off.

Built for [Skjåk Trelast AS](https://www.skjaaktrelast.no), a Norwegian sawmill running a Telemecanique TSX 47-30 sorting system from the late 1980s.

---

## How it works

```
TSX PLC  ──── original cable ────  40 cm tap cable  ──── OKI Microline printer
                                          │
                                    WAGO clamps
                                    (pin 2 TX + pin 7 GND only)
                                          │
                                   StarTech USB-RS232
                                          │
                                   Raspberry Pi Zero WH
                                          │
                              pakkelapper.csv + pakkelapper.xlsx
```

The 40 cm DB25 male-to-female cable is inserted **in series** between the original PLC cable and the printer. Only pins 2 (TX) and 7 (GND) are tapped mid-cable via WAGO 221-412 clamps — the system is **physically incapable of injecting signals back into the PLC**. Signal integrity to the printer is unaffected.

---

## Features

- **Passive tap** — read-only by design, zero risk to PLC or printer
- **Real-time capture** at 9600 baud (< 1 kB/s), handles any print rate
- **Duplicate detection** — double-pressing the confirmation button stores the package only once
- **Gap detection** — non-sequential package numbers logged to `mangler.csv`
- **Rollover handling** — counter resets (9999 → 0) detected automatically; deduplication and gap detection scoped per round
- **Season tracking** — `rå` (green/unseasoned) / `tørr` (kiln-dried), set via CLI to match the physical toggle switch on the machine
- **Manual registration** — register a package number when the label never printed
- **Excel export** — one sheet per sort category, frozen headers, autofilter, per-dimension summary, bar/line/pie charts for daily/monthly/yearly production
- **Dual write** — SD card (master) + USB flash drive (secondary with automatic gap-filling on reconnect)
- **Robust ESC sequence handling** — full Epson/IBM escape code table, unknown sequences logged rather than silently corrupting data
- **systemd service** — starts automatically at boot, restarts on failure

---

## Label format

Labels are printed over RS-232 with form-feed (0x0C) as separator:

```
   644                      75X 150       ← package number · dimension
   2026/ 6/19                5            ← date · sort digit
                            FURU          ← timber species (FURU=pine, GRAN=spruce)
   2          7                      1
   5          2                      3    ← length histogram (ignored)
  13          4
              84            0             ← board count
             357,8          0,0           ← total length (running metres)
             4,025          0,000         ← volume (m³)
              42            0,0           ← average length (dm)
```

The parser anchors on **decimal values** (3-decimal = cubic metres, 1-decimal = running metres) rather than fixed column positions, making it robust to whitespace variation across different package types.

### Sort digit mapping

| Digit | Category | Notes |
|-------|----------|-------|
| 5 | 5Sort (finest) | Default when lever untouched — high volume |
| 1 | Krok (hook/bent) | High volume |
| 4 | Gulv (floor grade) | High volume; rarely also B.L by operator choice |
| 6 | Krok / Hogges | Krok and høgg share this digit; høgg is hand-marked on the physical bundle |
| 3 | Hogges (reject) | Rare in practice from automation |
| 2 | Unknown | Possibly B.L in edge cases |
| 0 | Not used | Confirmed |

---

## Hardware

| Component | Source | Notes |
|-----------|--------|-------|
| Raspberry Pi Zero WH | RS Components | Pre-soldered GPIO headers |
| StarTech ICUSB232DB25 | RS Components | USB to DB25 RS-232 adapter |
| 4-port USB hub (micro-USB) | RS Components | For adapter + flash drive |
| Lexar Industrial microSDHC | RS Components | Industrial-grade storage |
| Kingston USB flash drive | RS Components | Daily data retrieval |
| RS PRO IP54 enclosure | RS Components | Protection from sawdust |
| WAGO 221-412 clamps | RS Components | Signal tap, no soldering |
| DB25 male-to-female 40 cm | AliExpress | Active tap cable (in-series) |
| Micro-USB OTG adapter | AliExpress | For USB hub on Pi Zero |
| SSD1306 OLED 0.96" (optional) | AliExpress | Status display |

---

## Installation

### Requirements

```bash
pip install pyserial openpyxl
# For Excel logo embedding (optional):
pip install cairosvg pillow
```

### Quick start

```bash
# Clone and enter directory
git clone https://github.com/YOUR_USERNAME/pakkemaskin-skriver.git
cd pakkemaskin-skriver

# Install as systemd service (Raspberry Pi)
bash installer.sh

# Or run manually
python3 les_pakkelapp_fikset.py --port /dev/ttyUSB0
```

### First run — verify format before committing to live capture

```bash
# Capture raw data without saving anything
python3 les_pakkelapp_fikset.py --bare-fangst --port /dev/ttyUSB0
```

Compare the terminal output against the physical printed label. If you see garbled characters (`6´´ ·5Ø ±50` instead of `645 75X 150`), the PLC likely uses 7E1 framing:

```bash
python3 les_pakkelapp_fikset.py --bare-fangst --paritet E --databits 7
```

---

## Usage

```bash
# Set season (match physical toggle switch on machine)
python3 les_pakkelapp_fikset.py --sett-sesong rå
python3 les_pakkelapp_fikset.py --sett-sesong tørr

# Live capture (daily operation)
python3 les_pakkelapp_fikset.py --port /dev/ttyUSB0

# Export to Excel (with charts and summary sheet)
python3 les_pakkelapp_fikset.py --eksporter-xlsx

# Daily summary in terminal
python3 les_pakkelapp_fikset.py --oppsummering

# Per-dimension summary
python3 les_pakkelapp_fikset.py --oppsummering-dimensjon

# Manually register a package (label never printed)
python3 les_pakkelapp_fikset.py --registrer 1234

# Find USB port
python3 les_pakkelapp_fikset.py --list-porter

# Simulate from file (no PLC needed — for testing)
python3 les_pakkelapp_fikset.py --simuler eksempel.txt
```

---

## Output files

| File | Content |
|------|---------|
| `pakkelapper.csv` | One row per unique package; no duplicates |
| `utskrift.txt` | Full raw capture with timestamps — nothing ever lost |
| `mangler.csv` | Gap log: package numbers not seen (possible missed confirmations) |
| `sesong.txt` | Current season: `rå` or `tørr` |
| `pakkelapper.xlsx` | Excel workbook: Sammendrag (summary + charts) + one sheet per sort category + per-dimension overview |

### CSV columns

```
tid_fanget, dato, pakkenr, dimensjon, treslag, sort, sort_navn,
antall_plank, sum_lengde_lm, kubikk_m3, snittlengde_m,
sesong, runde, status, raa
```

`sum_lengde_lm` is the **sum** of all board lengths in the package (running metres).  
`snittlengde_m` is the **average** board length (metres). They are different values.

---

## Simulation and acceptance testing

A complete 6-month synthetic dataset is included for local testing without a PLC:

```bash
# Run acceptance test (expected: 7 packages, 1 duplicate dropped,
# 1 gap at package #2, automatic rollover at 9999→0)
python3 les_pakkelapp_fikset.py --simuler strom_A.bin
```

The simulation covers:
- Normal packages with correct field parsing
- Duplicate button press (stored only once)
- Counter rollover 9999 → 0 (new round started, dedup/gap scoped correctly)
- Gap detection (package #2 missing → logged to `mangler.csv`)
- ESC sequences with printable parameter bytes (robustness test)
- 7E1 vs 8N1 parity mismatch (documented symptom)

---

## Architecture

```
Serial line (RS-232, 9600 8N1)
    │
rens()          Strip ESC sequences (full Epson/IBM table), normalise CR/LF
    │
parse_lapp()    Extract fields anchored on decimal values (not fixed positions)
    │
Register        Dedup + gap detection, scoped per round
    │
append_csv()    Atomic append to pakkelapper.csv
    │
utskrift.txt    Raw backup (always written, even for duplicates)
```

Excel export (`eksporter_xlsx`) runs **only on demand** — never during live capture — keeping the Pi Zero's CPU free for serial reading.

---

## Known limitations

- **Krok vs. Hogges (sort digit 6):** Both share digit 6 on the label. Hogges (reject) is the minority — sorters hand-write "HOGGES" directly on the physical bundle. This hand annotation is invisible to the RS-232 tap. The app assumes Krok as default for digit 6. This is a confirmed, accepted workflow at Skjåk Trelast.
- **B.L / B.BL sort codes:** Confirmed digit not yet established (operator-dependent). Currently routes to Gulv (digit 4) or Uavklart.
- **Label format verified from photos only**, not yet from live byte stream. First `--bare-fangst` run on the actual line will confirm or require minor parser adjustments.

---

## Project status

- [x] Core capture and parsing
- [x] Duplicate detection
- [x] Gap detection and round/rollover handling
- [x] Season tracking
- [x] Excel export with charts and summary sheet
- [x] Robust ESC sequence handling (Epson/IBM table)
- [x] Simulation test suite
- [ ] Live line verification (`--bare-fangst` on actual PLC)
- [ ] Physical installation on site
- [ ] B.L / B.BL sort digit confirmation

---

## License

MIT — see [LICENSE](LICENSE)

---

*Built with Python 3, pyserial, openpyxl. Tested on Raspberry Pi Zero WH running Raspberry Pi OS Lite.*
