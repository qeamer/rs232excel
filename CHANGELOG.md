# Endringslogg — rs232excel / Pakkemaskin Skriver

Norsk produksjonssti: `python/no/`. Datoer i lokal tid (CEST) der annet ikke er oppgitt.

---

## 2026-07-24 — Pi-apparat, USB-speiling og datasikkerhet

Første fulle driftsdag på hostname `pakkemaskin`: HDMI-meny, minnepenn, årsfiler, bugfikser og trygg kopiering fra penn.

### Trygg for kopier (USB / PC)

Du kan trekke ut minnepennen og kopiere filene til en annen PC. Det som ligger på pennen skal være **hele, konsistente filer** — ikke halvskrevne CSV/Excel.

| Garanti | Hvordan |
|--------|---------|
| SD er fasit | Fangst skriver alltid til SD først |
| Penn speiler SD | `pakkelapperYYYY.csv` + `.xlsx` på `/media/usb0` |
| fsync | Append flush’es til disk før neste steg |
| Atomisk omskriving | Ved korrupt/avvik: tmp → fsync → `rename` → fsync mappe |
| Sjekk/helbred | `integritet` (eller meny **1 USB**) verifiserer SD ↔ penn |
| Hard yank | Neste innsetting (eller `integritet`) bygger pennen på nytt fra SD |
| Årsfiler | Samme to filer hele året — ikke mange tidsstemplede kopier |

**Anbefalt før viktig kopi:** kjør `integritet` — skal svare f.eks. `OK — N rader speilet trygt på minnepenn`.

Kommandoer:

```bash
integritet          # sjekk/helbred SD ↔ penn
usb                 # list USB + samme sjekk
restart             # last inn ny kode i tjenesten
```

### Årsfiler (ikke filkaos)

- `pakkelapper2026.csv` / `pakkelapper2026.xlsx` / `mangler2026.csv`
- Oppdateres **på stedet** hele året
- Ved årsskifte: nye `…2027…`-filer (gamle beholdes på SD som arkiv)
- Gamle `pakkelapper.csv` migreres automatisk til årets navn

### Auto-Excel

- Excel bygges i bakgrunnen under fangst (blokkerer ikke serieporten)
- Speiles til pennen — meny **8** / `excel` er valgfri «oppdater nå»
- Bakgrunnseksport leser CSV-**snapshot** (ikke midt i append)

### Kritiske fangstfikser (Bug D–H)

| ID | Problem | Fiks |
|----|---------|------|
| **D** | Reprint (805→650) startet falsk «ny runde» + hundrevis av falske hull | Nullstilling kun når `maks > 9000` og nytt nr er lavt |
| **E** | Flush midt i lapp → fragment tolket som pakke | Flush krever «komplett» lapp (kubikk m.m.) |
| **F** | Manuell registrering, så ekte lapp = duplikat | Oppgraderer tom manuell rad |
| **H** | Hull i `mangler` ble stående for alltid | Friskmeldes som `funnet` når pakken kommer |

Tester: `cd python/no && python3 -m unittest test_register.py`

### USB-kjede og strøm

- Pi DATA → OTG-skjøtekabel (USB-A **hunn**) ← hub (USB-A **hann**)
- StarTech DB25 **hann** → C (hunn-terminal) ← ledninger fra A (DB25-MG)
- **Anbefalt tapp:** DB25-MG + hunn-terminal (A–G); WAGO/klipping **utdatert**
- Utdaterte bilder `signal-flow.png` / `wiring-tap.png` erstattet med A–G-bruksanvisning
- Primær plakat: `steg-for-steg-passiv-rs232-tapp.png` (StarTech **straight**, **A2→C3→pin 3**; fallback C2)
- DB25-pinnekart: `db25-rette-pinner.png` — pin **2=TX**, **7=GND**, StarTech **3=RX**
- Steg-bilder + Claude-PDF: `docs/no/rs232excel-2026-07-24-for-claude.pdf`
- Markdown-handoff til Claude (fasit + alle bilder): `docs/no/HANDOFF-CLAUDE.md`
- **PWR IN:** 5V / ≥2,5 A (helst 3 A) vegglader — ikke svak telefonlader
- Auto-mount til `/media/usb0` (`fiks-usb.sh` + udev)
- Hotplug: penn ut/inn synkes ved neste sjekk / pakke

### HDMI-apparat (uten kronglete login)

- Korte kommandoer: `start` `stopp` `restart` `status` `logg` `sjekk` `excel` `usb` `integritet` `meny`
- Autologin → nummerert meny (agetty, ikke rå TTY-service)
- cloud-init dempet (fikset «død» login / tastatur)
- Bluetooth bevisst av i apparatmodus — **USB-tastatur** anbefalt

### Oppsett på Pi (etter `git pull`)

```bash
cd ~/rs232excel && git pull
cd python/no
sudo cp pakkemaskin meny /usr/local/bin/
sudo ln -sf /usr/local/bin/pakkemaskin /usr/local/bin/integritet
sudo ln -sf /usr/local/bin/pakkemaskin /usr/local/bin/usb
bash fiks-usb.sh    # første gangs mount-regler
restart
integritet
```

### Commit-logg (denne dagen, eldst → nyest)

| Commit | Tema |
|--------|------|
| `58d07e5` | `pakkemaskin` CLI for daglig bruk |
| `4c5c2af`–`ea70780` | Dokumentasjon av kommandoer øverst i docs |
| `ed53c10` | Tydelig Ctrl+C i live logg |
| `d26392c` | Ettords-kommandoer i PATH |
| `fa7daf9` | Quiet boot, autologin, nummer-meny |
| `453195a`–`7c26fcb` | Fikse kilde HDMI-login / cloud-init |
| `4793f17` | Direkte konsollmeny |
| `4aaf5ad` | `fiks-login` crash (UTF-8 variabel) |
| `14b9363` | agetty → meny (tastatur virker) |
| `7321cdc`–`73fe0a5` | Strøm + USB-hub-kjede i docs |
| `2024485` | Auto-mount minnepenn `/media/usb0` |
| `5fa684c` | Menyvalg USB + hotplug-remount |
| `34cd450` | Auto-speil Excel til penn |
| `10e8d99` | Årsfiler `pakkelapperYYYY.*` |
| `929130d`–`e004ddf` | Bug D–H + dokumentasjon |
| `4d59686` | Trygg USB-integritet (`skriv_trygt` / `integritet`) |

PR: https://github.com/qeamer/rs232excel/pull/3 (`cursor/pakkemaskin-cli-ef03`)

---

### Illustrasjoner (korrigert etter Gemini)

Nye norske diagrammer i `docs/no/img/` (erstatter misvisende AI-bilder):

| Fil | Innhold |
|-----|---------|
| `bruksanvisning-tapp-foto.png` / `passiv-rs232-tapp.png` | A–G breakout (DB25-MG); **ingen** kniv/WAGO |
| `usb-kjede-komplett.png` | PWR IN ≥2,5 A, OTG-hub, tastatur+penn+adapter |
| `oled-i2c-korrekt.png` | 0,96" SSD1306 I2C — **ikke** 40-pinners LCD-HAT |
| `docs/en/img/passive-rs232-tap.png` m.fl. | Engelske speilversjoner av samme diagrammer |

---

## Fremtid (ikke i denne releasen)

- Wi‑Fi-opplasting av Excel til intern Trelast-app / ekspedisjon (f.eks. Høvelapp) når Pi får nett
- Minnepenn forblir reserve ved nettbrudd
