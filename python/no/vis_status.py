#!/usr/bin/env python3
"""
vis_status.py — Pakkemaskin Skriver (Skjåk Trelast)

Liten OLED-skjerm (0,96" SSD1306, I2C) som roterer mellom to
statusvisninger, hver 10. sekund. Kjører som EGET, uavhengig program
— leser bare pakkelapper.csv utenfra og rører aldri fangst-koden.

Skjermer (roterer i denne rekkefølgen):
  1. Dagens og årets oppsummering (antall pakker + kubikk)
  2. Sortfordeling i dag — mini stolpediagram med ANTALL pakker per sort
     (ikke prosent — Kent tenker i faktiske pakketall på gulvet)

Avhengigheter (på selve Pi-en):
    sudo apt install -y python3-pip i2c-tools
    sudo raspi-config   # Interface Options → I2C → Enable
    pip3 install luma.oled --break-system-packages
"""

import csv, datetime, sys, time
from pathlib import Path

CSV_STI = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("pakkelapper.csv")
DATA_OPPDATER_SEK = 3     # hvor ofte vi sjekker CSV-filen for nye pakker
SKJERM_BYTT_SEK = 10      # hvor lenge hver skjerm vises før den bytter


# ── Datainnhenting (ren logikk, testbar uten skjerm-maskinvare) ─────

def les_gyldige_rader(csv_sti: Path):
    if not csv_sti.exists():
        return []
    with csv_sti.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("status") in ("ok", "manuell")]


def rader_for_dato_prefix(rader, prefix: str):
    """Filtrerer på pakkens EGEN dato (fra lappen), ikke tidspunktet Pi-en
    fanget den — mer riktig for dags-/årsstatistikk hvis Pi-en noen gang
    restartes og etterbehandler gamle data."""
    return [r for r in rader if (r.get("dato") or "").startswith(prefix)]


def summer_pakker(rader):
    kubikk = 0.0
    for r in rader:
        try: kubikk += float(str(r.get("kubikk_m3", "")).replace(",", "."))
        except ValueError: pass
    return len(rader), round(kubikk, 1)


def dagens_rader(rader):
    return rader_for_dato_prefix(rader, datetime.date.today().isoformat())


def dagens_oppsummering(rader):
    return summer_pakker(dagens_rader(rader))


def arets_oppsummering(rader):
    return summer_pakker(rader_for_dato_prefix(rader, str(datetime.date.today().year)))


def sortfordeling_i_dag(rader):
    tellere = {}
    for r in dagens_rader(rader):
        navn = r.get("sort_navn") or "?"
        tellere[navn] = tellere.get(navn, 0) + 1
    return tellere


# ── Skjerm-innhold (returnerer liste med tekstlinjer) ────────────────

def skjerm_dag_og_ar(rader):
    dag_antall, dag_kubikk = dagens_oppsummering(rader)
    ar_antall, ar_kubikk = arets_oppsummering(rader)
    return ["I DAG:", f"{dag_antall} pakker  {dag_kubikk}m3",
            "I ÅR:", f"{ar_antall} pakker  {ar_kubikk}m3"]


def skjerm_sortfordeling(rader):
    """Stolpediagram med FAKTISK ANTALL pakker per sort (ikke prosent) —
    lengste stolpe = høyest antall, skalert relativt til den."""
    fordeling = sortfordeling_i_dag(rader)
    if not fordeling:
        return ["SORT I DAG:", "(ingen pakker", "registrert ennå)"]
    linjer = ["SORT I DAG:"]
    maks = max(fordeling.values())
    for navn, ant in sorted(fordeling.items(), key=lambda x: -x[1])[:4]:
        bar_lengde = round((ant / maks) * 8) if maks else 0
        bar = "#" * bar_lengde
        linjer.append(f"{navn[:5]:5}{bar} {ant}")
    return linjer


SKJERMER = [
    skjerm_dag_og_ar,
    skjerm_sortfordeling,
]


# ── Selve skjerm-visningen (krever fysisk maskinvare) ────────────────

def kjor_skjerm():
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import ssd1306
    from PIL import ImageFont

    serial = i2c(port=1, address=0x3C)
    enhet = ssd1306(serial)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
    except OSError:
        font = None

    rader = les_gyldige_rader(CSV_STI)
    sist_data_sjekk = time.time()
    sist_skjerm_bytt = time.time()
    skjerm_idx = 0

    while True:
        na = time.time()
        if na - sist_data_sjekk >= DATA_OPPDATER_SEK:
            rader = les_gyldige_rader(CSV_STI)
            sist_data_sjekk = na
        if na - sist_skjerm_bytt >= SKJERM_BYTT_SEK:
            skjerm_idx = (skjerm_idx + 1) % len(SKJERMER)
            sist_skjerm_bytt = na

        try:
            linjer = SKJERMER[skjerm_idx](rader)
        except Exception as e:
            linjer = ["Feil i skjerm:", str(e)[:20]]

        with canvas(enhet) as draw:
            for i, tekst in enumerate(linjer[:5]):
                draw.text((0, i * 13), tekst, font=font, fill="white")

        time.sleep(0.5)


if __name__ == "__main__":
    try:
        kjor_skjerm()
    except ImportError:
        print("Mangler luma.oled — installer med:")
        print("  pip3 install luma.oled --break-system-packages")
    except KeyboardInterrupt:
        print("Stoppet.")
