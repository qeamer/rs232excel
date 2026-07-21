# Installation Guide

Complete walkthrough — from empty SD card to a live passive tap running on the sawmill floor. Roughly 45 minutes, no programming experience required.

<img src="img/signal-flow.png" width="100%" alt="System architecture"/>

The printer keeps printing physical labels **exactly as before**. The tap only listens — it never transmits — so the printer and PLC behave identically whether the Pi is powered or not.

---

## 1 · Parts list

| # | Part | Source | Purpose |
|---|------|--------|---------|
| 1 | Raspberry Pi Zero WH | RS 2858711 | Main computer, pre-soldered headers |
| 2 | StarTech ICUSB232DB25 | RS 1238049 | USB → RS-232 DB25 adapter |
| 3 | RS PRO 4-port USB hub | RS 2206492 | Serial adapter + flash drive together |
| 4 | Lexar 32GB Industrial microSDHC | RS 2676402 | System drive — the master copy |
| 5 | 2× Kingston 64GB USB flash | RS 0622158 | Live CSV mirror, pull anytime |
| 6 | RS PRO IP54 enclosure 60×190×110 | RS 1959122 | Sawdust protection |
| 7 | WAGO 221-412 clamps, 10-pack | RS 8837544 | Tool-free wire tap |
| 8 | DB25 M-F extension 40 cm | AliExpress | **ACTIVE** tap cable |
| 9 | DB25 M-F extension 50 cm | AliExpress | Spare — mark with tape |
| 10 | Micro-USB OTG adapter | AliExpress | Pi Zero → hub |
| 11 | SSD1306 0.96" OLED, I2C, 4-pin | AliExpress | Status screen (optional) |
| 12 | Dupont jumper wires F-F | AliExpress | 4 of 40 used (OLED) |

Also needed: 5V/2A+ micro-USB power supply, thin hookup wire for the WAGO branch.

---

## 2 · Flash the SD card (on your Windows/Mac PC)

Download **Raspberry Pi Imager** from [raspberrypi.com/software](https://www.raspberrypi.com/software/), insert the SD card, and configure exactly as shown:

<img src="img/pi-imager-setup.png" width="100%" alt="Raspberry Pi Imager settings"/>

Main screen choices: **Device** = Raspberry Pi Zero 2 W · **OS** = Raspberry Pi OS **Lite** (64-bit) · **Storage** = the Lexar card. Hit the gear icon (or Ctrl+Shift+X) for the customisation screen above, then **Write** (~5 min).

> **Why Lite?** No desktop means faster boot, less SD wear, and everything is done over SSH anyway.

---

## 3 · First boot and SSH

1. Insert the SD card into the Pi. Connect power to the port marked **PWR IN**.
2. Wait 1–2 minutes for first boot (green LED settles down).
3. From your PC, on the same network:

```bash
ssh pi@pakkemaskin.local
# or use the IP address from your router's DHCP list:
ssh pi@192.168.1.42
```

Windows without ssh? Install [PuTTY](https://putty.org) or use WSL.

---

## 4 · Install the software

Paste these blocks one at a time into the SSH session:

```bash
# System update (~5 min)
sudo apt update && sudo apt upgrade -y

# Dependencies
pip3 install --break-system-packages pyserial openpyxl
pip3 install --break-system-packages luma.oled        # only if using the OLED

# Enable I2C for the OLED (skip if no display)
sudo raspi-config      # Interface Options → I2C → Enable → reboot
```

Get the project files onto the Pi — easiest is a USB stick prepared on your PC (`les_pakkelapp.py`, `pakkemaskin-skriver.service`, `installer.sh`, `vis_status.py`), or clone directly:

```bash
git clone https://github.com/qeamer/rs232excel.git pakkemaskin-skriver
cd pakkemaskin-skriver
bash installer.sh      # installs the systemd service for autostart
```

---

## 5 · The physical tap

**Stop the machine before touching any cable.** The original cable is never modified — the 40 cm extension goes **in series** at the printer end and can be removed in seconds.

<img src="img/wiring-tap.png" width="100%" alt="DB25 tap wiring"/>

Step by step:

1. **Insert the 40 cm extension** between the printer's DB25 port and the existing cable from the sorting plant. Take a photo of the original connection first.
2. **Mid-cable, open the jacket** and identify the wires for **pin 2 (TX)** and **pin 7 (GND)**. Photograph the colour coding before cutting.
3. **Cut only those two wires** — never the whole cable.
4. **WAGO-join three ends per clamp**: PLC side + printer side (signal continues unbroken) + one new thin wire out to the USB-serial adapter.
5. **Secure the splice** with cable ties in the same cable tray — never leave a WAGO hanging free; vibration works connections loose over time. Mark the active cable with tape.

> ⚠ **Direction matters:** the printer-side pin 2 is **TX** (the signal source). It connects to the adapter's **RX**. TX→TX captures nothing.

### USB chain

<img src="img/usb-chain.png" width="100%" alt="USB chain"/>

The OTG adapter **must** go in the middle **data** port on the Pi Zero — the corner port is power-only and detects nothing.

### OLED status display (optional)

<img src="img/oled-gpio.png" width="80%" alt="OLED GPIO wiring"/>

Four jumper wires, completely independent of the USB chain. Runs as its own program (`vis_status.py`) — if it ever crashes, capture is unaffected.

---

## 6 · Verify before going live

**Test 1 — raw capture, nothing saved.** Run a package through the plant and watch:

```bash
python3 les_pakkelapp.py --bare-fangst --port /dev/ttyUSB0
```

Compare against the physical printed label. Garbled output (`6´´ ·5Ø ±50` instead of `645 75X 150`)? The PLC likely uses 7E1 framing:

```bash
python3 les_pakkelapp.py --bare-fangst --paritet E --databits 7
```

Nothing at all? Try `--baud 4800`, `2400`, or `19200`, and re-check the pin 2/7 splice.

**Test 2 — real capture with USB mirroring.** This is the production command:

```bash
python3 les_pakkelapp.py --port /dev/ttyUSB0 --usb-sti /media/usb0
```

<img src="img/terminal-capture.png" width="100%" alt="Live capture terminal"/>

Run 2–3 packages, check `pakkelapper.csv` against the paper labels, pull the flash drive mid-run (capture continues), re-insert it (missed rows sync automatically).

**Go live.** The service installed in step 4 autostarts on every boot:

```bash
sudo systemctl start pakkemaskin-skriver
journalctl -u pakkemaskin-skriver -f     # live log
```

---

## 7 · The result

`--eksporter-xlsx` produces a branded workbook: a **Sammendrag** sheet with totals per sort category, per day/month/year, plus live charts — followed by one sheet per sort category and a raw-data sheet. All summary numbers are formulas, so edits to the data recalculate everything.

<p align="center">
<img src="img/excel-summary.png" width="49%" alt="Excel summary sheet"/>
<img src="img/excel-charts.png" width="42%" alt="Excel charts"/>
</p>

Pull the flash drive at any time — the Excel file and CSV are on it, ready to open on any PC.

---

## 8 · Final checklist

- [ ] All parts received (SD card shipped separately!)
- [ ] 40 cm cable marked ACTIVE, 50 cm marked SPARE
- [ ] Tap spliced: pins 2+7 WAGO-joined, splice secured with ties
- [ ] USB chain: Pi **data port** → OTG → hub → adapter + flash drive
- [ ] OLED on GPIO 1/3/5/6, I2C enabled in raspi-config
- [ ] `--bare-fangst` shows readable label text
- [ ] Live run verified against paper labels
- [ ] Flash drive pulled and re-inserted → rows synced automatically
- [ ] systemd service enabled → survives power loss
- [ ] Excel export opens with Sammendrag, charts, and logo

---

*Questions or a wiring photo that doesn't match these drawings? Open an issue.*
