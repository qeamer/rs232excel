# Source code — Norwegian and English versions

This directory contains the capture software in two languages:

## `/en/` — English (GitHub default)

- `read_package.py` — Main capture script (English)
- `install.sh` — Installation script
- `read-package.service` — systemd unit file
- `requirements.txt` — Python dependencies

All code, comments, command-line arguments, CSV columns, Excel headers, and terminal output are in English.

```bash
python3 read_package.py --port /dev/ttyUSB0 --raw-capture
python3 read_package.py --set-season raw
python3 read_package.py --export-xlsx
```

## `/no/` — Norwegian (Skjåk Trelast original)

- `read_package.py` — Main capture script (Norwegian)
- `installer.sh` — Installation script
- `pakkemaskin-skriver.service` — systemd unit file
- `requirements.txt` — Python dependencies

All code, comments, command-line arguments, CSV columns, Excel headers, and terminal output are in Norwegian.

```bash
python3 read_package.py --port /dev/ttyUSB0 --bare-fangst
python3 read_package.py --sett-sesong rå
python3 read_package.py --eksporter-xlsx
```

---

## Installation

Clone the repo and choose the language:

```bash
# For English (GitHub default)
cd rs232excel/python/en
bash install.sh

# For Norwegian (Skjåk Trelast)
cd rs232excel/python/no
bash installer.sh
```

Both versions are identical in functionality — only the human-readable strings differ.
