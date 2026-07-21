<p align="center">
  <img src="skaak_logo_vektor.png" height="70" alt="Skjåk Trelast AS"/>
</p>

<h1 align="center">rs232excel</h1>

<p align="center">
  <b>Passiv serieport-tapp · Telemecanique TSX → OKI Microline → CSV og Excel</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3572A5"/>
  <img src="https://img.shields.io/badge/platform-Raspberry%20Pi%20Zero%20WH-C7053D"/>
  <img src="https://img.shields.io/badge/serial-RS--232%209600%208N1-555"/>
  <img src="https://img.shields.io/badge/license-MIT-1B4D3E"/>
</p>

En Raspberry Pi lytter passivt på RS-232-linja mellom en Telemecanique TSX PLS fra 1980-tallet og en OKI Microline 280 nåleskriver på Skjåk Trelast. Hver pakkelapp parses og lagres automatisk — dimensjon, treslag, sort, antall plank, kubikk. Ingen manuell registrering. Ingen datatap, selv når skriveren er av.

<img src="docs/no/img/signal-flow.png" width="100%" alt="Systemarkitektur"/>

Tappen er **fysisk skrivebeskyttet**: kun pinne 2 (TX) og pinne 7 (GND) grener av via WAGO midt på kabelen. Skriveren fortsetter helt som før, og ingenting kan sendes tilbake mot PLS-en.

**Språk:** [Norsk](#hurtigstart) · [English](README.md)

---

## Hurtigstart

```bash
git clone https://github.com/qeamer/rs232excel.git
cd rs232excel/python/no
pip install -r requirements.txt
python3 read_package.py --port /dev/ttyUSB0 --usb-sti /media/usb0
python3 read_package.py --eksporter-xlsx
```

📖 **[Installasjonsguide (norsk) →](docs/no/INSTALLATION.md)** · **[Installation guide (English) →](docs/en/INSTALLATION.md)**

---

## Det du får

<p align="center">
<img src="docs/no/img/excel-summary.png" width="49%" alt="Excel Sammendrag"/>
<img src="docs/no/img/excel-charts.png" width="42%" alt="Excel grafer"/>
</p>

En merket Excel-arbeidsbok, generert på kommando fra live CSV:

- **Sammendrag** — totaler per sort, per dag / måned / år, med kake-, stablet søyle- og linjediagram. Alle tall er formler mot rådata.
- **Ett ark per sortkategori** (5Sort / Krok / Gulv / Hogges / Uavklart) — frosne overskrifter, autofilter, mini-oppsummering per dimensjon
- **Rådata** — hver fanget pakke, flat tabell

## Slik fungerer fangsten

<img src="docs/no/img/terminal-capture.png" width="100%" alt="Sanntidsfangst"/>

| Situasjon på gulvet | Hva programmet gjør |
|---|---|
| Operatør trykker kvittering to ganger | **Dedup** — pakke lagres én gang, råkopi i `utskrift.txt` |
| Pakke aldri kvittert | **Hull-deteksjon** — manglende numre i `mangler.csv` |
| Teller nullstilles 9999 → 0 | **Runde** — oppdages automatisk, dedup/hull per runde |
| Skriver av / tom for papir | Data ligger på kabelen uansett — fangst fortsetter |
| Minnepenn trukket ut midt i kjøring | SD-kort er fasit; minnepenn synkes ved ny tilkobling |
| Lapp aldri skrevet ut | `--registrer N` legger inn manuelt |
| PLS sender rare ESC-sekvenser | Full Epson/IBM-tabell; ukjente koder logges, ødelegger ikke data |

## Kommandoer (norsk)

| Flag | Formål |
|---|---|
| `--port /dev/ttyUSB0` | Live fangst (produksjon) |
| `--usb-sti /media/usb0` | Speil CSV til minnepenn i sanntid |
| `--bare-fangst` | Bare vis rådata — verifiser første gang |
| `--sett-sesong rå` / `tørr` | Match fysisk sesongbryter på maskinen |
| `--eksporter-xlsx` | Generer Excel-arbeidsbok |
| `--oppsummering` | Daglige totaler i terminalen |
| `--registrer 1234` | Manuell pakke |
| `--simuler eksempel.txt` | Offline test — uten PLS |

Engelske flagg (`--raw-capture`, `--export-xlsx`, …): se [`python/en/read_package.py`](python/en/read_package.py).

## Hardware

<img src="docs/no/img/wiring-tap.png" width="100%" alt="Kobling"/>

Raspberry Pi Zero WH · StarTech ICUSB232DB25 · WAGO 221-412 · 40 cm DB25 skjøtekabel i serie · IP54 kapsling · valgfri SSD1306 OLED. Full delerliste i [installasjonsguiden](docs/no/INSTALLATION.md).

## Lappformat

```
   645                      75X 150     ← pakkenr · dimensjon
   2026/ 6/22                5          ← dato · sort-siffer
                            FURU        ← treslag (FURU=furu, GRAN=gran)
              25            0           ← antall plank
             108,7          0,0         ← sum lengde (løpemeter)
             1,223          0,000       ← kubikk (m³)
              43            0,0         ← snittlengde (dm)
```

Parseren forankrer seg på desimalmønstre (3 des = m³, 1 des = meter) — robust mot avstandsforskyvning på ulike lapptyper.

## Prosjektstruktur

```
docs/
  en/          installation guide + wiring (English)
  no/          installasjonsguide + kobling (norsk)
python/
  en/          read_package.py, install.sh, read-package.service
  no/          read_package.py, installer.sh, pakkemaskin-skriver.service
```

## Lisens

MIT

---

<p align="center">
  <sub><a href="https://www.skjaaktrelast.no">Skjåk Trelast AS</a> · Telemecanique TSX · OKI Microline · RS-232 9600 8N1</sub>
</p>
