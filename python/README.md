# Programvare — norsk og engelsk

<table>
<tr><td bgcolor="#1B4D3E" align="center">
<p style="font-size: 18px; color: white; margin: 12px">
<b>🇳🇴 Hovedversjon: <code>python/no/</code> — for skandinaviske sagbruk</b><br>
<span style="font-size: 15px">Norsk CLI, CSV-kolonner, Excel-ark og terminaloutput</span>
</p>
</td></tr>
</table>

## `/no/` — Norsk produksjonsversjon ⭐

- `read_package.py` — fangst, parsing, CSV, Excel
- `installer.sh` — systemd-tjeneste
- `pakkemaskin-skriver.service` — autostart
- `vis_status.py` — valgfri OLED-skjerm
- `eksempel.txt` — testlapper for `--simuler`

```bash
cd rs232excel/python/no
bash installer.sh
python3 read_package.py --port /dev/ttyUSB0 --usb-sti /media/usb0
python3 read_package.py --eksporter-xlsx
```

## `/en/` — Engelsk speilversjon (oversettelse)

- `read_package.py` — same logic, English strings
- `install.sh` — installation script
- `read-package.service` — systemd unit

```bash
cd rs232excel/python/en
bash install.sh
python3 read_package.py --port /dev/ttyUSB0 --usb-mirror /media/usb0
python3 read_package.py --export-xlsx
```

Begge versjoner er funksjonelt like — kun språk skiller dem.
