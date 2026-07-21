<p align="center">
  <img src="skaak_logo_vektor.png" width="300" alt="Skjåk Trelast AS"/>
</p>

<p align="center">
  <strong>rs232excel</strong><br/>
  Passive serial tap · package labels → CSV & Excel
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Raspberry%20Pi-Zero%20WH-C51A4A?logo=raspberrypi&logoColor=white" alt="Raspberry Pi"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT"/>
</p>

<br/>

```
  TSX PLC ── orig. cable ── tap cable ── OKI Microline
                              │
                         pin 2 + 7
                              │
                         Raspberry Pi
                              │
                    pakkelapper.csv · .xlsx
```

<br/>

## Quick start

```bash
pip install -r requirements.txt
python3 les_pakkelapp.py --port /dev/ttyUSB0
python3 les_pakkelapp.py --eksporter-xlsx
```

<br/>

## Commands

| Flag | |
|:--|:--|
| `--bare-fangst` | Test live stream, no files |
| `--sett-sesong rå` | Match machine season toggle |
| `--simuler eksempel.txt` | Offline test |
| `--registrer 1234` | Manual package entry |
| `--usb-sti /media/usb0` | Mirror CSV to USB stick |

<br/>

## Output

| File | |
|:--|:--|
| `pakkelapper.csv` | One row per package |
| `pakkelapper.xlsx` | Sort sheets + summary |
| `mangler.csv` | Missing package numbers |
| `utskrift.txt` | Raw backup |

<br/>

<details>
<summary><strong>Hardware</strong></summary>

<br/>

40 cm DB25 extension **in series** at the printer. Cut **only** wires for pin **2** (data) and **7** (GND). WAGO 221 — three wires per clamp: PLC side · printer side · Pi branch.

Signal → USB adapter **RX**, not TX→TX. See [`docs/wiring.md`](docs/wiring.md).

</details>

<details>
<summary><strong>Install on Pi</strong></summary>

<br/>

```bash
bash installer.sh          # systemd service
sudo raspi-config          # enable I2C if using OLED
python3 vis_status.py      # optional status screen
```

</details>

<br/>

<p align="center">
  <sub>
    <a href="https://www.skjaaktrelast.no">Skjåk Trelast AS</a> ·
    Telemecanique TSX · OKI Microline · RS-232 9600 8N1
  </sub>
</p>
