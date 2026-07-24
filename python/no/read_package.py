#!/usr/bin/env python3
"""
read_package.py — Pakkemaskin Skriver (Skjåk Trelast)

Raspberry Pi lytter PASSIVT på pakkelapp-strømmen fra sorteringsanlegget
(TSX → OKI Microline) og lagrer hver pakke sikkert.

  • Knapp trykket flere ganger → DEDUP: duplikat droppes
  • Skriver av                 → tapp TX-linja; data ligger på kabelen
  • Pakke aldri kvittert        → HULL-DETEKSJON i pakkenr-rekka
  • Nullstilling (9999 → 0)     → RUNDE: oppdages automatisk, scoper dedup+hull
  • Lapp kom aldri              → MANUELL registrering (--registrer)
  • Sesong                      → rå / tørr (fysisk vribryter på maskinen)

Lappformat (dekodet fra ekte lapper):
  linje 1:  pakkenr            dimensjon (f.eks. 75X 150)
  linje 2:  dato (ÅÅÅÅ/ M/DD)  sort-siffer (5=5s, 6=krok/høgg, 4=gulv; 0 ikke i bruk)
  linje 3:                     treslag (FURU/GRAN)
  histogram (lengdefordeling, tre kolonner med antall)
  bunn:     antall · sum_lengde(1 des) · kubikk(3 des) · snittlengde(dm)
            (høyre kolonne med nuller = ubrukt, ignoreres)

Filer (årsbasert CSV/Excel/mangler — samme fil overskrives hele året):
  pakkelapperYYYY.csv    én rad per ekte pakke (ingen duplikater)
  manglerYYYY.csv        hull i pakkenr-rekka (per runde; friskmeldes ved innkomst)
  pakkelapperYYYY.xlsx   Excel (automatisk + --eksporter-xlsx)
  utskrift.txt           alt råt, kontinuerlig logg (ikke årsrotert)
  oppsummering.csv       daglig oppsummering (--oppsummering)
  sesong.txt             gjeldende sesong: "rå"/"tørr" (ikke årsrotert)

USB-speiling (sanntid, --usb-sti):
  SD-kortet er alltid fasiten — det er der fangsten faktisk skjer, og
  ingen pakke går tapt selv om ingen minnepenn er tilkoblet. Er en
  minnepenn montert på oppgitt sti, speiles CSV i samme øyeblikk, og
  Excel oppdateres automatisk i bakgrunnen (kort debounce, så
  serieporten ikke blokkeres). På pennen ligger typisk bare årets
  to filer (pakkelapperYYYY.csv + .xlsx) — de oppdateres på stedet,
  ikke som nye kopier hver gang. Ved årsskifte startes nye
  YYYY-filer. Trekk ut pennen og åpne på PC — ingen manuell
  «excel»-kommando nødvendig.

Avhengigheter: pip install pyserial openpyxl
"""

import argparse, csv, datetime, glob, os, re, shutil, threading, time
from pathlib import Path

FORMFEED = 0x0C
ESC = 0x1B


def aarsfiler(aar: int | None = None) -> dict:
    """Filnavn for ett kalenderår — samme fil hele året, nytt år = nye navn."""
    aar = aar or datetime.datetime.now().year
    return {
        "aar": aar,
        "csv": f"pakkelapper{aar}.csv",
        "xlsx": f"pakkelapper{aar}.xlsx",
        "mangler": f"mangler{aar}.csv",
    }


def migrer_legacy_aarsfiler(csv_sti: Path, xlsx_sti: Path, mangler_sti: Path):
    """Første gangs oppgradering: pakkelapper.csv → pakkelapperYYYY.csv osv."""
    legacy_csv = Path("pakkelapper.csv")
    if not csv_sti.exists() and legacy_csv.exists() and csv_sti.resolve() != legacy_csv.resolve():
        logg(f"Flytter {legacy_csv.name} → {csv_sti.name} (årsfil)")
        legacy_csv.rename(csv_sti)
    legacy_xlsx = Path("pakkelapper.xlsx")
    if not xlsx_sti.exists() and legacy_xlsx.exists() and xlsx_sti.resolve() != legacy_xlsx.resolve():
        logg(f"Flytter {legacy_xlsx.name} → {xlsx_sti.name} (årsfil)")
        legacy_xlsx.rename(xlsx_sti)
    legacy_mangler = Path("mangler.csv")
    if not mangler_sti.exists() and legacy_mangler.exists() and mangler_sti.resolve() != legacy_mangler.resolve():
        logg(f"Flytter {legacy_mangler.name} → {mangler_sti.name} (årsfil)")
        legacy_mangler.rename(mangler_sti)


def migrer_usb_legacy(usb_mappe: Path | None, csv_navn: str, xlsx_navn: str):
    """Samme på minnepennen — én CSV + én Excel per år, ikke gamle generiske navn."""
    if usb_mappe is None or not usb_mappe.exists():
        return
    for legacy, ny in (("pakkelapper.csv", csv_navn), ("pakkelapper.xlsx", xlsx_navn)):
        old, new = usb_mappe / legacy, usb_mappe / ny
        if old.exists() and not new.exists():
            try:
                old.rename(new)
                logg(f"📀 Minnepenn: {legacy} → {ny}")
            except OSError as e:
                logg(f"⚠  Klarte ikke rename på minnepenn ({e}).")

KOLONNER = ["tid_fanget", "dato", "pakkenr", "dimensjon", "treslag",
            "sort", "sort_navn", "antall_plank", "sum_lengde_lm", "kubikk_m3",
            "snittlengde_m", "sesong", "runde", "status", "raa"]

DATO_RE   = re.compile(r"(\d{4})\s*/\s*(\d{1,2})\s*/\s*(\d{1,2})")
DIM_RE    = re.compile(r"(\d{2,3})\s*[xX]\s*(\d{2,4})")
TRE_RE    = re.compile(r"(FURU|GRAN)", re.I)
FLOAT1_RE = re.compile(r"(?<![\d,])(\d{1,4},\d)(?![\d])")     # nøyaktig 1 desimal
FLOAT3_RE = re.compile(r"(?<![\d,])(\d{1,4},\d{3})(?![\d])")  # nøyaktig 3 desimaler
INT_RE    = re.compile(r"(?<![\d,])(\d{1,5})(?![\d,])")       # heltall (ikke del av desimaltall)

SORT_NAVN = {
    "1": "krok",
    "3": "høgg",              # sjelden — kan forekomme, men se merknad om siffer 6 under
    "4": "gulv",              # vanlig, alltid i produksjon. Sjelden: operatør kan også
                              # bruke 4 (eller 2) for B.L — flagg de tilfellene manuelt.
    "5": "5s",
    "6": "krok",              # krok og høgg deler siffer 6 (samme spakposisjon hos sortøren).
                              # Krok er standard/flertall. Høgg (mindretall) skilles KUN ved
                              # håndskrift direkte på materialpakken — usynlig for RS-232-
                              # tappingen. Ikke et datakvalitetsproblem, bekreftet av Kent.
}

# Faneinndeling i Excel: hver bekreftet sort-kode får sin egen fane (i stedet for
# blandede dimensjoner under hverandre i én tabell). B.L (Bygningslast) og B.BL
# (Bein bygningslast) mangler ennå bekreftet siffer — se README/spør Kent.
# Pakker med ukjent/uavklart sort-siffer (2, 6, og evt. feil i 4-antagelsen) havner
# i "Uavklart" til da.
SORT_FANE = {
    "5": "5Sort",
    "1": "Krok",
    "6": "Krok",   # krok/høgg deler dette sifferet — krok er standard, se merknad i SORT_NAVN
    "3": "Hogges", # sjelden i praksis fra automatikken alene — ekte høgg skilles ved håndskrift
    "4": "Gulv",
    # "2" routes til "Uavklart" — sjeldent brukt, muligens B.L ved operatørvalg.
    # B.L kan i sjeldne tilfeller også vises som "4" — flagg de manuelt (samme
    # prinsipp som håndskrift skiller krok/høgg på siffer 6).
}
FANE_REKKEFØLGE = ["5Sort", "Krok", "Gulv", "Hogges", "B.L", "B.BL", "Uavklart"]

# Pene norske kolonnenavn for Excel (enheter i tittel, ikke gjentatt i hver celle)
KOLONNE_VISNING = {
    "tid_fanget": "Fanget", "dato": "Dato", "pakkenr": "Pakkenr",
    "dimensjon": "Dimensjon", "treslag": "Treslag", "sort": "Sort",
    "sort_navn": "Sortnavn", "antall_plank": "Antall plank",
    "sum_lengde_lm": "Sum lengde (lm)", "kubikk_m3": "Kubikk (m³)",
    "snittlengde_m": "Snittlengde (m)", "sesong": "Sesong", "runde": "Runde",
    "status": "Status", "raa": "Rådata",
    "antall_pakker": "Antall pakker", "sum_plank": "Sum plank",
    "sum_kubikk_m3": "Sum kubikk (m³)",
}


def logg(m): print(f"[{datetime.datetime.now():%H:%M:%S}] {m}", flush=True)


def rens(rabytes: bytes) -> str:
    ut, i = [], 0
    while i < len(rabytes):
        b = rabytes[i]
        if b == ESC:
            i += 2; continue
        if b in (0x0A, 0x0D):
            ut.append("\n")
        elif 0x20 <= b <= 0xFF and b != FORMFEED:
            ut.append(chr(b))
        i += 1
    linjer = [ln.rstrip() for ln in "".join(ut).split("\n")]
    return "\n".join(linjer).strip("\n")


def som_tall(s):
    try: return int(re.sub(r"\D", "", str(s)))
    except (ValueError, TypeError): return None


def _forste_ikke_null(regex, tekst):
    for m in regex.finditer(tekst):
        if float(m.group(1).replace(",", ".")) != 0:
            return m
    return None


# ── sesong ─────────────────────────────────────────────────────────
def gjett_sesong(d): return "rå" if d.month in (12, 1, 2, 3, 4, 5) else "tørr"


def les_sesong(sti: Path):
    if sti.exists():
        v = sti.read_text(encoding="utf-8").strip().lower()
        if v.startswith("rå") or v in ("raa", "ra"):    return "rå"
        if v.startswith("tør") or v in ("torr", "tor"): return "tørr"
    return gjett_sesong(datetime.date.today())


def sett_sesong(verdi, sti: Path):
    v = verdi.strip().lower()
    norm = "rå" if v in ("rå", "raa", "ra") else "tørr" if v in ("tørr", "torr", "tor") else None
    if not norm:
        logg('Bruk: --sett-sesong rå  |  --sett-sesong tørr'); return
    sti.write_text(norm, encoding="utf-8")
    logg(f"Sesong satt til: {norm}  (lagret i {sti.name})")


def parse_lapp(tekst: str, sesong: str) -> dict:
    rad = {k: "" for k in KOLONNER}
    rad["tid_fanget"] = datetime.datetime.now().isoformat(timespec="seconds")
    rad["raa"] = tekst
    rad["sesong"] = sesong

    # dato
    md = DATO_RE.search(tekst)
    if md:
        rad["dato"] = f"{md.group(1)}-{int(md.group(2)):02d}-{int(md.group(3)):02d}"
    else:
        rad["dato"] = datetime.date.today().isoformat()

    # dimensjon
    mdim = DIM_RE.search(tekst)
    if mdim:
        rad["dimensjon"] = f"{int(mdim.group(1))}x{int(mdim.group(2))}"

    # treslag
    mt = TRE_RE.search(tekst)
    if mt:
        rad["treslag"] = mt.group(1).upper()

    # sort = ensifret tall på dato-linja
    if md:
        for linje in tekst.splitlines():
            if md.group(0) in linje:
                ensifret = re.findall(r"(?<!\d)(\d)(?!\d)", DATO_RE.sub(" ", linje))
                if ensifret:
                    rad["sort"] = ensifret[0]
                break
    rad["sort_navn"] = SORT_NAVN.get(rad["sort"], "")

    # pakkenr = første heltall når dato og dimensjon er fjernet
    uten = tekst
    if md:   uten = uten.replace(md.group(0), " ")
    if mdim: uten = uten.replace(mdim.group(0), " ")
    mpk = INT_RE.search(uten)
    if mpk:
        rad["pakkenr"] = mpk.group(1)

    # summeringsblokk, ankret på desimaltall
    m1 = _forste_ikke_null(FLOAT1_RE, tekst)   # sum_lengde (1 desimal)
    m3 = _forste_ikke_null(FLOAT3_RE, tekst)   # kubikk (3 desimaler)
    if m1: rad["sum_lengde_lm"] = m1.group(1).replace(",", ".")
    if m3: rad["kubikk_m3"]    = m3.group(1).replace(",", ".")

    # antall = siste IKKE-NULL heltall før sum_lengde
    if m1:
        før = [t for t in INT_RE.findall(tekst[:m1.start()]) if int(t) != 0]
        if før:
            rad["antall_plank"] = før[-1]
    # snittlengde = første ikke-null heltall etter kubikk (dm → m)
    if m3:
        for t in INT_RE.findall(tekst[m3.end():]):
            if int(t) != 0:
                rad["snittlengde_m"] = f"{int(t)/10:.1f}"
                break
    return rad


# Nullstilling 9999→0: krev at vi faktisk er nær telleslutt, og at nytt
# nummer er nær start. Ellers: reprint av gammel lapp (f.eks. 805→650)
# ble feiltolket som ny runde («Bug D») og genererte hundrevis av falske hull.
NULLSTILL_MIN_MAKS = 9000


class Register:
    """Dedup + hull-deteksjon, scopet per RUNDE. Ny runde oppdages kun ved
    ekte teller-nullstilling nær 9999 → lavt nummer. Rekonstrueres fra CSV."""
    def __init__(self, csv_sti: Path, mangler_sti: Path, terskel: int = 100):
        self.csv_sti, self.mangler_sti, self.terskel = csv_sti, mangler_sti, terskel
        self.runde, self.sett, self.maks = 1, set(), None
        self.manuelle = set()  # pakkenr kun kjent via --registrer (tom rad)
        if csv_sti.exists():
            runder = {}
            manuelle = {}
            with csv_sti.open(encoding="utf-8") as f:
                for rad in csv.DictReader(f):
                    if rad.get("status") not in ("ok", "manuell"):
                        continue
                    r = som_tall(rad.get("runde")) or 1
                    n = som_tall(rad.get("pakkenr"))
                    if n is None:
                        continue
                    runder.setdefault(r, set()).add(n)
                    if rad.get("status") == "manuell":
                        manuelle.setdefault(r, set()).add(n)
                    else:
                        # ekte lapp vinner over tidligere manuell i samme runde
                        manuelle.setdefault(r, set()).discard(n)
            if runder:
                self.runde = max(runder)
                self.sett = runder[self.runde]
                self.maks = max(self.sett)
                self.manuelle = manuelle.get(self.runde, set()) & self.sett
            logg(f"Lastet runde {self.runde}: {len(self.sett)} pakkenr (høyeste {self.maks}).")

    def vurder(self, pakkenr_tekst):
        n = som_tall(pakkenr_tekst)
        if n is None:
            return "ukjent", None, False
        # Ekte nullstilling: maks nær 9999 OG nytt nr nær 0 — ikke vilkårlig hopp bakover
        if (self.maks is not None
                and self.maks > NULLSTILL_MIN_MAKS
                and n <= self.terskel
                and (self.maks - n) > self.terskel):
            return "ok", n, True
        if n in self.sett:
            # Manuell plassholder: la ekte lapp fylle inn («Bug F»)
            if n in self.manuelle:
                return "oppgrader", n, False
            return "duplikat", n, False
        return "ok", n, False

    def ny_runde(self):
        self.runde += 1
        self.sett, self.maks, self.manuelle = set(), None, set()
        logg(f"↻ Ny runde {self.runde} — pakkenr ser nullstilt ut (9999 → 0)")

    def registrer(self, n, manuell: bool = False):
        if self.maks is not None and n > self.maks + 1:
            self._skriv_hull(self.maks + 1, n - 1)
        self.sett.add(n)
        self.maks = n if self.maks is None else max(self.maks, n)
        if manuell:
            self.manuelle.add(n)
        else:
            self.manuelle.discard(n)
        self._friskmeld_hull(n)

    def _skriv_hull(self, fra, til):
        ny = not self.mangler_sti.exists()
        with self.mangler_sti.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if ny: w.writerow(["oppdaget", "runde", "manglende_pakkenr", "merknad", "status"])
            for m in range(fra, til + 1):
                w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), self.runde, m,
                            "mulig hull — sjekk om pakken ble kvittert", "åpen"])
        logg(f"⚠  Mulig hull (runde {self.runde}): pakkenr {fra}–{til} → {self.mangler_sti.name}")

    def _friskmeld_hull(self, n):
        """Når pakken dukker opp: merk åpne hull-rader som funnet («Bug H»)."""
        if not self.mangler_sti.exists():
            return
        try:
            with self.mangler_sti.open(encoding="utf-8") as f:
                rader = list(csv.DictReader(f))
        except OSError:
            return
        if not rader:
            return
        endret = False
        for rad in rader:
            if (str(rad.get("runde") or "") == str(self.runde)
                    and str(rad.get("manglende_pakkenr") or "") == str(n)
                    and (rad.get("status") or "åpen") == "åpen"):
                rad["status"] = "funnet"
                rad["merknad"] = (rad.get("merknad") or "") + " — friskmeldt (pakke kom inn)"
                endret = True
        if not endret:
            return
        felt = ["oppdaget", "runde", "manglende_pakkenr", "merknad", "status"]
        tmp = self.mangler_sti.with_suffix(".tmp.csv")
        try:
            with tmp.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=felt, extrasaction="ignore")
                w.writeheader()
                for rad in rader:
                    if "status" not in rad:
                        rad["status"] = "åpen"
                    w.writerow(rad)
            os.replace(tmp, self.mangler_sti)
            logg(f"✓ Hull friskmeldt: pakkenr {n} (runde {self.runde})")
        except OSError as e:
            logg(f"⚠  Klarte ikke friskmelde hull ({e}).")
            try:
                if tmp.exists():
                    tmp.unlink()
            except OSError:
                pass


def erstatt_manuell_rad(csv_sti: Path, runde, pakkenr, ny_rad: dict) -> bool:
    """Bytter ut tom manuell rad med ekte lapp-data (samme runde+pakkenr)."""
    if not csv_sti.exists():
        return False
    with csv_sti.open(encoding="utf-8") as f:
        rader = list(csv.DictReader(f))
    fant = False
    for i, rad in enumerate(rader):
        if (rad.get("status") == "manuell"
                and str(rad.get("runde") or "") == str(runde)
                and str(rad.get("pakkenr") or "") == str(pakkenr)):
            rader[i] = {k: ny_rad.get(k, "") for k in KOLONNER}
            fant = True
            break
    if not fant:
        return False
    tmp = csv_sti.with_suffix(".tmp.csv")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOLONNER, extrasaction="ignore")
        w.writeheader()
        w.writerows(rader)
    os.replace(tmp, csv_sti)
    return True


def ser_komplett_lapp(tekst: str) -> bool:
    """Unngå at --flush midt i lapp tolkes som ferdig pakke («Bug E»)."""
    if not tekst or not tekst.strip():
        return False
    # Kubikk (3 desimaler) sitter typisk i bunnblokken — uten den er lappen ufullstendig
    return bool(FLOAT3_RE.search(tekst) and INT_RE.search(tekst))


def append_csv(rad, csv_sti: Path):
    """Append til SD (fasit) med flush+fsync — mindre tap ved strømbrudd."""
    ny = not csv_sti.exists()
    with csv_sti.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=KOLONNER, extrasaction="ignore")
        if ny: w.writeheader()
        w.writerow(rad)
        f.flush()
        os.fsync(f.fileno())


def _fsync_dir(sti: Path):
    """fsync på mappen — nødvendig for at rename skal overleve yank på FAT."""
    try:
        fd = os.open(str(sti.parent), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def skriv_trygt(sti: Path, rader, fieldnames=None):
    """Atomisk CSV-skriving: tmp → flush/fsync → replace → fsync dir.

    Brukes på minnepennen slik at en hard yank midt i skriving ikke etterlater
    halv/korrupt pakkelapperYYYY.csv. SD er fortsatt fasiten."""
    fieldnames = fieldnames or KOLONNER
    sti = Path(sti)
    sti.parent.mkdir(parents=True, exist_ok=True)
    tmp = sti.with_name(sti.name + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for rad in rader:
            w.writerow({k: rad.get(k, "") for k in fieldnames})
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, sti)
    _fsync_dir(sti)


# ── USB-speiling (sanntid, med automatisk innhenting) ────────────────
def _usb_tilgjengelig(usb_sti: Path | None) -> bool:
    """Sjekker om minnepennen er montert akkurat nå (kan komme/gå når som helst)."""
    return usb_sti is not None and usb_sti.parent.exists()


def _nokkel(rad) -> tuple:
    """(runde, pakkenr) brukes til å finne ut hvilke rader som allerede
    finnes på minnepennen, slik at vi ikke dupliserer ved synkronisering."""
    return (str(rad.get("runde") or ""), str(rad.get("pakkenr") or ""))


def _les_rader(csv_sti: Path):
    """Les CSV. Returnerer liste, [] hvis mangler, None hvis korrupt/uleselig."""
    if not csv_sti.exists():
        return []
    try:
        with csv_sti.open(encoding="utf-8") as f:
            leser = csv.DictReader(f)
            if not leser.fieldnames:
                return None
            felter = set(leser.fieldnames)
            # Tom/korrupt penn uten våre kolonner → helbred med full omskriving
            if "pakkenr" not in felter or "runde" not in felter:
                return None
            return list(leser)
    except (OSError, csv.Error, UnicodeError) as e:
        logg(f"⚠  Klarte ikke lese {csv_sti}: {e}")
        return None


def _les_nokler(csv_sti: Path) -> set:
    rader = _les_rader(csv_sti)
    if rader is None:
        return set()
    return {_nokkel(rad) for rad in rader}


def sjekk_og_helbred(csv_sti: Path, usb_sti: Path | None) -> dict:
    """Sjekk at minnepennen speiler SD. Ved avvik/korrupt fil: skriv hele CSV
    atomisk fra SD (fasit). Trygt å kalle ofte og via CLI «integritet»."""
    ut = {"ok": False, "helbredt": False, "manglet": 0, "ekstra": 0,
          "rader_sd": 0, "rader_usb": 0, "melding": ""}
    if not _usb_tilgjengelig(usb_sti):
        ut["melding"] = "Minnepenn ikke montert"
        return ut
    if not csv_sti.exists():
        ut["ok"] = True
        ut["melding"] = "Ingen CSV på SD ennå — ingenting å speile"
        return ut

    sd_rader = _les_rader(csv_sti)
    if sd_rader is None:
        ut["melding"] = "SD-CSV uleselig — avbryter (fasit må være lesbar)"
        return ut
    ut["rader_sd"] = len(sd_rader)
    sd_nokler = {_nokkel(r) for r in sd_rader}

    usb_rader = _les_rader(usb_sti) if usb_sti.exists() else []
    korrupt = usb_rader is None
    if korrupt:
        usb_rader = []
    ut["rader_usb"] = len(usb_rader)
    usb_nokler = {_nokkel(r) for r in usb_rader}

    mangler = sd_nokler - usb_nokler
    ekstra = usb_nokler - sd_nokler
    ut["manglet"] = len(mangler)
    ut["ekstra"] = len(ekstra)

    if not korrupt and not mangler and not ekstra and len(sd_rader) == len(usb_rader):
        ut["ok"] = True
        ut["melding"] = f"OK — {len(sd_rader)} rader speilet trygt på minnepenn"
        return ut

    try:
        # Rask sti: friske fil + kun manglende rader → append med fsync
        if not korrupt and mangler and not ekstra:
            for rad in sd_rader:
                if _nokkel(rad) in mangler:
                    append_csv(rad, usb_sti)
            ut["ok"] = True
            ut["helbredt"] = True
            ut["melding"] = (
                f"Helbredt — la til {len(mangler)} manglende rad(er) "
                f"(fsync, {len(sd_rader)} totalt på SD)"
            )
            marker_xlsx_oppdatering()
            return ut

        # Korrupt / ekstra / ulikt antall → full atomisk omskriving fra SD
        skriv_trygt(usb_sti, sd_rader)
        ut["ok"] = True
        ut["helbredt"] = True
        årsak = []
        if korrupt:
            årsak.append("korrupt/uleselig fil")
        if mangler:
            årsak.append(f"{len(mangler)} manglet")
        if ekstra:
            årsak.append(f"{len(ekstra)} ekstra (fjernet)")
        if len(sd_rader) != len(usb_rader) and not mangler and not ekstra:
            årsak.append("ulikt antall rader")
        ut["melding"] = (
            f"Helbredt — skrev {len(sd_rader)} rader atomisk fra SD "
            f"({', '.join(årsak) or 'avvik'})"
        )
        marker_xlsx_oppdatering()
    except OSError as e:
        ut["melding"] = f"Klarte ikke helbrede minnepenn ({e})"
    return ut


def synkroniser_usb(csv_sti: Path, usb_sti: Path | None):
    """Speil SD → minnepenn via sjekk_og_helbred (atomisk ved behov)."""
    if not _usb_tilgjengelig(usb_sti) or not csv_sti.exists():
        return
    r = sjekk_og_helbred(csv_sti, usb_sti)
    if r["helbredt"] and r["manglet"]:
        logg(f"📀 Minnepenn oppdatert — hentet inn {r['manglet']} pakke(r) "
             f"som ble fanget mens den var frakoblet.")
    elif r["helbredt"]:
        logg(f"📀 {r['melding']}")
    elif not r["ok"] and r["melding"]:
        logg(f"⚠  {r['melding']}")


# ── Automatisk Excel (bakgrunn, debounce) ────────────────────────────
# Pi Zero skal ikke blokkere serieporten mens openpyxl bygger arbeidsbok.
_XLSX_DEBOUNCE_S = 12
_xlsx_auto = {
    "lock": threading.Lock(),
    "dirty": False,
    "busy": False,
    "started": False,
    "csv_sti": None,
    "xlsx_sti": None,
    "usb_sti": None,
}


def speil_xlsx_til_usb(xlsx_sti: Path, usb_sti: Path | None):
    """Kopierer ferdig Excel til minnepennen (atomisk replace + fsync)."""
    if not _usb_tilgjengelig(usb_sti) or not xlsx_sti.exists():
        return
    dest = usb_sti.parent / xlsx_sti.name
    tmp = dest.with_name(dest.name + ".tmp")
    try:
        shutil.copy2(xlsx_sti, tmp)
        with tmp.open("rb") as f:
            os.fsync(f.fileno())
        os.replace(tmp, dest)
        _fsync_dir(dest)
        logg(f"📀 Excel speilet til {dest}")
    except OSError as e:
        logg(f"⚠  Klarte ikke speile Excel til minnepenn ({e}).")
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def _xlsx_arbeider():
    while True:
        time.sleep(_XLSX_DEBOUNCE_S)
        with _xlsx_auto["lock"]:
            if not _xlsx_auto["dirty"] or _xlsx_auto["busy"]:
                continue
            _xlsx_auto["dirty"] = False
            _xlsx_auto["busy"] = True
            csv_sti = _xlsx_auto["csv_sti"]
            xlsx_sti = _xlsx_auto["xlsx_sti"]
            usb_sti = _xlsx_auto["usb_sti"]
        snap = None
        try:
            if csv_sti and xlsx_sti and csv_sti.exists():
                # Kopi før lesing — unngår Excel midt i append_csv fra fangst-tråden
                snap = csv_sti.with_suffix(".xlsxsnap.csv")
                shutil.copy2(csv_sti, snap)
                eksporter_xlsx(snap, xlsx_sti)
                speil_xlsx_til_usb(xlsx_sti, usb_sti)
        except Exception as e:
            logg(f"⚠  Automatisk Excel feilet ({e}). Prøver igjen ved neste endring.")
            with _xlsx_auto["lock"]:
                _xlsx_auto["dirty"] = True
        finally:
            if snap is not None:
                try:
                    snap.unlink(missing_ok=True)
                except TypeError:
                    # Python <3.8 fallback (Lite har nyere, men vær trygg)
                    try:
                        if snap.exists():
                            snap.unlink()
                    except OSError:
                        pass
                except OSError:
                    pass
            with _xlsx_auto["lock"]:
                _xlsx_auto["busy"] = False


def start_xlsx_auto(csv_sti: Path, xlsx_sti: Path, usb_sti: Path | None):
    """Starter bakgrunnstråd som bygger/speiler Excel etter CSV-endringer."""
    with _xlsx_auto["lock"]:
        _xlsx_auto["csv_sti"] = csv_sti
        _xlsx_auto["xlsx_sti"] = xlsx_sti
        _xlsx_auto["usb_sti"] = usb_sti
        if _xlsx_auto["started"]:
            return
        _xlsx_auto["started"] = True
        t = threading.Thread(target=_xlsx_arbeider, name="xlsx-auto", daemon=True)
        t.start()


def _oppdater_xlsx_auto_stier(csv_sti: Path, xlsx_sti: Path, usb_sti: Path | None):
    with _xlsx_auto["lock"]:
        _xlsx_auto["csv_sti"] = csv_sti
        _xlsx_auto["xlsx_sti"] = xlsx_sti
        _xlsx_auto["usb_sti"] = usb_sti


def marker_xlsx_oppdatering():
    """Merk at CSV er endret — Excel bygges om etter debounce."""
    with _xlsx_auto["lock"]:
        if not _xlsx_auto["started"]:
            return
        _xlsx_auto["dirty"] = True


def ny_fangst_state(csv_sti: Path, xlsx_sti: Path, mangler_sti: Path,
                    usb_sti: Path | None, terskel: int, aar: int) -> dict:
    """Mutable stier for langkjøring — byttes ved årsskifte."""
    return {
        "aar": aar,
        "csv_sti": csv_sti,
        "xlsx_sti": xlsx_sti,
        "mangler_sti": mangler_sti,
        "usb_sti": usb_sti,
        "terskel": terskel,
    }


def sikr_gjeldende_aar(state: dict, reg: "Register") -> "Register":
    """Ved 1. januar under fangst: nye årsfiler (gamle beholdes på SD)."""
    aar = datetime.datetime.now().year
    if aar == state["aar"]:
        return reg
    filer = aarsfiler(aar)
    logg(f"Nytt år {aar} — starter {filer['csv']} / {filer['xlsx']} "
         f"(forrige års filer beholdes på SD)")
    state["aar"] = aar
    state["csv_sti"] = Path(filer["csv"])
    state["xlsx_sti"] = Path(filer["xlsx"])
    state["mangler_sti"] = Path(filer["mangler"])
    usb_mappe = state["usb_sti"].parent if state["usb_sti"] else None
    state["usb_sti"] = (usb_mappe / filer["csv"]) if usb_mappe else None
    _oppdater_xlsx_auto_stier(state["csv_sti"], state["xlsx_sti"], state["usb_sti"])
    return Register(state["csv_sti"], state["mangler_sti"], state["terskel"])


def skriv_utskrift(tekst, utskrift: Path):
    with utskrift.open("a", encoding="utf-8") as f:
        f.write(f"\n===== {datetime.datetime.now().isoformat(timespec='seconds')} =====\n{tekst}\n")


def behandle(tekst, utskrift, state: dict, reg: Register, sesong, bare_fangst):
    if not tekst: return reg
    reg = sikr_gjeldende_aar(state, reg)
    csv_sti, usb_sti = state["csv_sti"], state["usb_sti"]
    skriv_utskrift(tekst, utskrift)
    if bare_fangst:
        logg("rå lapp fanget"); return reg
    rad = parse_lapp(tekst, sesong)
    pakkenr = rad["pakkenr"]
    status, n, reset = reg.vurder(pakkenr)
    if status == "duplikat":
        logg(f"↺ duplikat pakkenr {pakkenr} — droppet (finnes i utskrift.txt)"); return reg
    if reset:
        reg.ny_runde()
    rad["runde"] = reg.runde
    if status == "oppgrader":
        rad["status"] = "ok"
        reg.registrer(n, manuell=False)
        if erstatt_manuell_rad(csv_sti, reg.runde, n, rad):
            logg(f"✓ Oppgradert manuell → ekte lapp for pakke {n} [r{reg.runde}/{sesong}]")
        else:
            append_csv(rad, csv_sti)
            logg(f"✓ Ekte lapp for tidligere manuell pakke {n} [r{reg.runde}/{sesong}] (ny rad)")
        synkroniser_usb(csv_sti, usb_sti)
        marker_xlsx_oppdatering()
        return reg
    rad["status"] = status
    if status == "ok":
        reg.registrer(n, manuell=False)
    append_csv(rad, csv_sti)                 # SD-kortet — alltid, er fasiten
    synkroniser_usb(csv_sti, usb_sti)         # speiler denne pakken + evt. "hull" fra forrige frakobling, i ett steg
    marker_xlsx_oppdatering()                # Excel på SD (+ penn) i bakgrunnen
    if status == "ukjent":
        logg("? fant ikke pakkenr — lagret med rådata for manuell sjekk")
    else:
        usb_status = " 📀" if _usb_tilgjengelig(usb_sti) else ""
        logg(f"✓ pakke {rad['pakkenr']} [r{reg.runde}/{sesong}]{usb_status} "
             f"{rad['dimensjon'] or '?'} {rad['treslag'] or '?'} "
             f"sort {rad['sort'] or '?'}({rad['sort_navn'] or '?'}), "
             f"{rad['antall_plank'] or '?'} plank, {rad['kubikk_m3'] or '?'} m³")
    return reg


def registrer_manuelt(pakkenr, csv_sti, mangler_sti, sesong, terskel):
    reg = Register(csv_sti, mangler_sti, terskel)
    status, n, reset = reg.vurder(pakkenr)
    if status in ("duplikat", "oppgrader"):
        logg(f"Pakkenr {pakkenr} finnes allerede i runde {reg.runde}. Avbryter."); return
    if n is None:
        logg("Ugyldig pakkenr."); return
    if reset:
        reg.ny_runde()
    reg.registrer(n, manuell=True)
    rad = {k: "" for k in KOLONNER}
    rad.update(tid_fanget=datetime.datetime.now().isoformat(timespec="seconds"),
               dato=datetime.date.today().isoformat(), pakkenr=str(n),
               sesong=sesong, runde=reg.runde, status="manuell", raa="(manuelt registrert)")
    append_csv(rad, csv_sti)
    logg(f"✓ Manuelt registrert pakke {n} [r{reg.runde}/{sesong}]")


def _tid_aggreger(csv_sti):
    """Leser CSV én gang og bøtter ok/manuell-pakker på år, måned (ÅÅÅÅ-MM),
    ISO-uke (ÅÅÅÅ-UNN) og dag. Tar med pakker, plank, kubikk og løpemeter.
    Skiller også på sesong (rå/tørr) per bøtte, for produksjonssammenligning.
    Returnerer (per_ar, per_mnd, per_uke, per_dag) — hver er dict nøkkel->tall."""
    def ny():
        return {"pakker": 0, "plank": 0, "kubikk": 0.0, "lm": 0.0, "rå": 0, "tørr": 0}
    per_ar, per_mnd, per_uke, per_dag = {}, {}, {}, {}
    if not csv_sti.exists():
        return per_ar, per_mnd, per_uke, per_dag
    with csv_sti.open(encoding="utf-8") as f:
        for rad in csv.DictReader(f):
            if rad.get("status") not in ("ok", "manuell"):
                continue
            try:
                d = datetime.date.fromisoformat((rad.get("dato") or "").strip())
            except ValueError:
                continue
            plank = som_tall(rad.get("antall_plank")) or 0
            try: kubikk = float(str(rad.get("kubikk_m3", "")).replace(",", "."))
            except ValueError: kubikk = 0.0
            try: lm = float(str(rad.get("sum_lengde_lm", "")).replace(",", "."))
            except ValueError: lm = 0.0
            sesong = (rad.get("sesong") or "").strip()
            iso = d.isocalendar()
            for bøtte, nøkkel in ((per_ar, str(d.year)),
                                  (per_mnd, f"{d.year}-{d.month:02d}"),
                                  (per_uke, f"{iso[0]}-U{iso[1]:02d}"),
                                  (per_dag, d.isoformat())):
                g = bøtte.setdefault(nøkkel, ny())
                g["pakker"] += 1
                g["plank"] += plank
                g["kubikk"] += kubikk
                g["lm"] += lm
                if sesong in ("rå", "tørr"):
                    g[sesong] += 1
    return per_ar, per_mnd, per_uke, per_dag


def _grupper_rader(csv_sti, nokkel_felter):
    """Leser pakkelapper.csv og grupperer ok/manuell-rader på de gitte feltene.
    Returnerer dict: tuple(nøkkelverdier) -> {pakker, plank, kubikk}."""
    grupper = {}
    if not csv_sti.exists():
        return grupper
    with csv_sti.open(encoding="utf-8") as f:
        for rad in csv.DictReader(f):
            if rad.get("status") not in ("ok", "manuell"):
                continue
            nøkkel = tuple(rad.get(felt) or "ukjent" for felt in nokkel_felter)
            g = grupper.setdefault(nøkkel, {"pakker": 0, "plank": 0, "kubikk": 0.0})
            g["pakker"] += 1
            g["plank"] += som_tall(rad.get("antall_plank")) or 0
            try: g["kubikk"] += float(str(rad.get("kubikk_m3", "")).replace(",", "."))
            except ValueError: pass
    return grupper


def oppsummering(csv_sti, ut_sti):
    if not csv_sti.exists():
        logg(f"Finner ikke {csv_sti}."); return
    grupper = _grupper_rader(csv_sti, ["sesong", "dato"])
    with ut_sti.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sesong", "dato", "antall_pakker", "sum_plank", "sum_kubikk_m3"])
        for (sesong, dato) in sorted(grupper):
            g = grupper[(sesong, dato)]
            w.writerow([sesong, dato, g["pakker"], g["plank"], round(g["kubikk"], 3)])
    logg(f"Oppsummering skrevet til {ut_sti.name}")
    for (sesong, dato) in sorted(grupper):
        g = grupper[(sesong, dato)]
        print(f"   {sesong:5} {dato}:  {g['pakker']} pakker,  {g['plank']} plank,  {round(g['kubikk'],3)} m³")


def oppsummering_dimensjon(csv_sti, ut_sti):
    """Summerer pakker/plank/kubikk gruppert på sesong + dimensjon (uavhengig av dato)."""
    if not csv_sti.exists():
        logg(f"Finner ikke {csv_sti}."); return
    grupper = _grupper_rader(csv_sti, ["sesong", "dimensjon"])
    if not grupper:
        logg("Ingen pakker å summere ennå."); return
    with ut_sti.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sesong", "dimensjon", "antall_pakker", "sum_plank", "sum_kubikk_m3"])
        for (sesong, dim) in sorted(grupper):
            g = grupper[(sesong, dim)]
            w.writerow([sesong, dim, g["pakker"], g["plank"], round(g["kubikk"], 3)])
    logg(f"Oversikt per dimensjon skrevet til {ut_sti.name}")
    for (sesong, dim) in sorted(grupper):
        g = grupper[(sesong, dim)]
        print(f"   {sesong:5} {dim:>9}:  {g['pakker']} pakker,  {g['plank']} plank,  {round(g['kubikk'],3)} m³")


def list_porter():
    try:
        from serial.tools import list_ports
        porter = [p.device for p in list_ports.comports()]
    except Exception:
        porter = sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*"))
    print("Serieporter funnet:" if porter else "Fant ingen serieporter.")
    for p in porter: print("  ", p)


def les_serie(args, utskrift, state: dict, reg, sesong):
    import serial
    paritet = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN, "O": serial.PARITY_ODD}[args.paritet]
    usb_sti = state["usb_sti"]
    logg(f"Starter. Lytter på {args.port} @ {args.baud} {args.databits}{args.paritet}{args.stoppbits}"
         f"  sesong={sesong}{'  [BARE FANGST]' if args.bare_fangst else ''}"
         f"  filer={state['csv_sti'].name}/{state['xlsx_sti'].name}"
         f"{f'  usb={usb_sti}' if usb_sti else ''}  (Ctrl+C for å stoppe)")
    sist_usb_sjekk = 0.0
    while True:
        try:
            ser = serial.Serial(args.port, args.baud, bytesize=args.databits,
                                parity=paritet, stopbits=args.stoppbits, timeout=args.timeout)
        except serial.SerialException as e:
            logg(f"Får ikke åpnet {args.port} ({e}). Prøver igjen om 5 s …"); time.sleep(5); continue
        logg("Tilkoblet.")
        buf, sist = bytearray(), time.time()
        try:
            while True:
                b = ser.read(1)
                now = time.time()
                if b:
                    if b[0] == FORMFEED:
                        reg = behandle(rens(bytes(buf)), utskrift, state, reg, sesong, args.bare_fangst); buf.clear()
                    else:
                        buf += b
                    sist = now
                elif buf and (now - sist) > args.flush:
                    # Bare flush-tolk hvis lappen ser komplett ut (ellers vent på mer / FF)
                    # — unngår at histogram-tall midt i lapp blir «pakkenr» («Bug E»)
                    tekst = rens(bytes(buf))
                    if args.bare_fangst or ser_komplett_lapp(tekst):
                        reg = behandle(tekst, utskrift, state, reg, sesong, args.bare_fangst)
                        buf.clear()
                    elif (now - sist) > max(args.flush * 4, 15.0):
                        logg("⚠  Ufullstendig lapp etter lang pause — rådump til utskrift, dropper fragment")
                        skriv_utskrift(tekst + "\n[ufullstendig — flush-timeout]", utskrift)
                        buf.clear()
                elif state["usb_sti"] and (now - sist_usb_sjekk) > 15:
                    # Hotplug: penn satt inn midt i skift → synk CSV/Excel uten å vente på neste pakke
                    sist_usb_sjekk = now
                    reg = sikr_gjeldende_aar(state, reg)
                    synkroniser_usb(state["csv_sti"], state["usb_sti"])
        except serial.SerialException as e:
            logg(f"Mistet forbindelsen ({e}). Kobler til igjen om 5 s …")
            try: ser.close()
            except Exception: pass
            time.sleep(5); continue
        except KeyboardInterrupt:
            if buf: behandle(rens(bytes(buf)), utskrift, state, reg, sesong, args.bare_fangst)
            ser.close(); logg("Stoppet."); return


def kjor_simulering(args, utskrift, state: dict, reg, sesong):
    data = Path(args.simuler).read_bytes()
    logg(f"Simulerer fra {args.simuler} …  sesong={sesong}")
    for chunk in data.split(bytes([FORMFEED])):
        reg = behandle(rens(chunk), utskrift, state, reg, sesong, args.bare_fangst)
    logg("Ferdig.")
    return reg


def eksporter_xlsx(csv_sti, xlsx_sti):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    if not csv_sti.exists():
        logg(f"Finner ikke {csv_sti}."); return

    FONT_NAVN = "Calibri"
    TEMA_GRØNN = "1B4D3E"      # tittel/header-bakgrunn — varm, dempet, trelast-aktig
    GRÅ_TEKST = "595959"
    BAND_GRÅ = "F2F2F2"        # svak skygge — markerer ny dimensjon, ikke en sterk farge
    KANT = Side(style="thin", color="D9D9D9")
    RAMME = Border(left=KANT, right=KANT, top=KANT, bottom=KANT)
    TITTEL_FONT = Font(name=FONT_NAVN, size=14, bold=True, color="FFFFFF")
    UNDERTITTEL_FONT = Font(name=FONT_NAVN, size=9, italic=True, color="D9D9D9")
    HEADER_FONT = Font(name=FONT_NAVN, size=10, bold=True, color="FFFFFF")
    HEADER_FILL = PatternFill("solid", fgColor=TEMA_GRØNN)
    TITTEL_FILL = PatternFill("solid", fgColor=TEMA_GRØNN)
    DATA_FONT = Font(name=FONT_NAVN, size=10)
    RAA_FONT = Font(name=FONT_NAVN, size=8, italic=True, color=GRÅ_TEKST)
    SUBTOTAL_FONT = Font(name=FONT_NAVN, size=9, bold=True, color="1B4D3E")
    SUBTOTAL_FILL = PatternFill("solid", fgColor="E8F0EE")

    # Sort: kun brukt i "Uavklart"-fanen (der flere sorter blandes); i de navngitte
    # fanene (5Sort/Krok/Hogges) er sorten allerede gitt av fanenavnet, så fargekode
    # på sort-cellen er overflødig der.
    SORT_FARGER = {
        "5": (PatternFill("solid", fgColor="C6EFCE"), Font(name=FONT_NAVN, size=10, color="2E7D32")),
        "4": (PatternFill("solid", fgColor="BDD7EE"), Font(name=FONT_NAVN, size=10, color="1F4E78")),
        "1": (PatternFill("solid", fgColor="FFEB9C"), Font(name=FONT_NAVN, size=10, color="9C6500")),
        "3": (PatternFill("solid", fgColor="F8CBAD"), Font(name=FONT_NAVN, size=10, color="943126")),
        "6": (PatternFill("solid", fgColor="E0E0E0"), Font(name=FONT_NAVN, size=10, color="595959")),
    }

    NUMMER_FORMAT = {
        "antall_plank": "#,##0", "sum_lengde_lm": "#,##0.0", "kubikk_m3": "0.000",
        "snittlengde_m": "0.0", "runde": "0", "pakkenr": "0",
        "antall_pakker": "#,##0", "sum_plank": "#,##0", "sum_kubikk_m3": "0.000",
    }
    # Bredde = plass til hele overskriften + buffer til nedtrekkspilen fra autofilter,
    # ellers kuttes teksten visuelt bak pilen (f.eks. "Antall pl..").
    KOLONNEBREDDE = {
        "tid_fanget": 18, "dato": 13, "pakkenr": 11, "dimensjon": 13, "treslag": 12,
        "sort": 8, "sort_navn": 14, "antall_plank": 16, "sum_lengde_lm": 18,
        "kubikk_m3": 15, "snittlengde_m": 18, "sesong": 11, "runde": 9,
        "status": 11, "raa": 40,
        "antall_pakker": 16, "sum_plank": 13, "sum_kubikk_m3": 18,
    }

    def skriv_header(ws, kol_start, rad_nr, felter):
        for j, felt in enumerate(felter, start=kol_start):
            c = ws.cell(rad_nr, j, KOLONNE_VISNING.get(felt, felt))
            c.font = HEADER_FONT; c.fill = HEADER_FILL
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[rad_nr].height = 30

    def skriv_dataceller(ws, rad_nr, kol_start, felter, rad, skyggelagt):
        for j, felt in enumerate(felter, start=kol_start):
            verdi = rad.get(felt, "")
            if felt == "dato" and verdi:
                try: verdi = datetime.date.fromisoformat(verdi)
                except ValueError: pass
            elif felt == "tid_fanget" and verdi:
                try: verdi = datetime.datetime.fromisoformat(verdi)
                except ValueError: pass
            elif felt in ("antall_plank", "kubikk_m3", "sum_lengde_lm", "snittlengde_m",
                          "runde", "pakkenr", "antall_pakker", "sum_plank", "sum_kubikk_m3"):
                try: verdi = float(verdi) if verdi != "" else None
                except (ValueError, TypeError): pass
            c = ws.cell(rad_nr, j, verdi)
            c.border = RAMME
            c.font = RAA_FONT if felt == "raa" else DATA_FONT
            if felt == "dato": c.number_format = "DD.MM.YYYY"
            elif felt == "tid_fanget": c.number_format = "DD.MM.YYYY HH:MM"
            elif felt in NUMMER_FORMAT: c.number_format = NUMMER_FORMAT[felt]
            if felt in ("dimensjon", "sesong", "status"):
                c.alignment = Alignment(horizontal="center")
            if felt in ("sort", "sort_navn"):
                c.alignment = Alignment(horizontal="center")
                fyll = SORT_FARGER.get(rad.get("sort"))
                if fyll: c.fill, c.font = fyll
            if skyggelagt and felt != "raa" and not (felt in ("sort", "sort_navn") and rad.get("sort") in SORT_FARGER):
                c.fill = PatternFill("solid", fgColor=BAND_GRÅ)

    def skriv_fane(ws, tittel, felter, rader, vis_dimensjonsoversikt=True):
        n = len(felter)
        bredde_kol = max(n, 5)
        ws.sheet_view.showGridLines = False
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=bredde_kol)
        c = ws.cell(1, 1, tittel); c.font = TITTEL_FONT; c.fill = TITTEL_FILL
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws.row_dimensions[1].height = 26
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=bredde_kol)
        c = ws.cell(2, 1, f"Generert {datetime.datetime.now():%d.%m.%Y %H:%M}  ·  {len(rader)} rader")
        c.font = UNDERTITTEL_FONT; c.fill = TITTEL_FILL
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        for j in range(1, bredde_kol + 1):
            felt_her = felter[j - 1] if j <= n else ""
            ws.column_dimensions[get_column_letter(j)].width = KOLONNEBREDDE.get(felt_her, 12)

        rad_nr = 4

        # Liten dimensjonsoversikt øverst i fanen — egen, kort tabell (ikke filtrerbar,
        # så den forstyrrer ikke autofilteret på hovedtabellen under).
        if vis_dimensjonsoversikt and rader:
            dim_sum = {}
            for r in rader:
                d = r.get("dimensjon") or "ukjent"
                g = dim_sum.setdefault(d, {"pakker": 0, "plank": 0, "kubikk": 0.0})
                g["pakker"] += 1
                g["plank"] += som_tall(r.get("antall_plank")) or 0
                try: g["kubikk"] += float(str(r.get("kubikk_m3", "")).replace(",", "."))
                except ValueError: pass
            c = ws.cell(rad_nr, 1, "Per dimensjon i denne fanen:")
            c.font = SUBTOTAL_FONT
            rad_nr += 1
            overskrift = ["Dimensjon", "Pakker", "Plank", "Kubikk (m³)"]
            for j, h in enumerate(overskrift, start=1):
                c = ws.cell(rad_nr, j, h); c.font = SUBTOTAL_FONT; c.fill = SUBTOTAL_FILL
                c.alignment = Alignment(horizontal="center")
            rad_nr += 1
            for d in sorted(dim_sum):
                g = dim_sum[d]
                verdier = [d, g["pakker"], g["plank"], round(g["kubikk"], 3)]
                for j, v in enumerate(verdier, start=1):
                    c = ws.cell(rad_nr, j, v); c.fill = SUBTOTAL_FILL
                    c.font = Font(name=FONT_NAVN, size=9)
                    c.alignment = Alignment(horizontal="center")
                    if j == 4: c.number_format = "0.000"
                rad_nr += 1
            rad_nr += 1  # luft før hovedtabellen

        header_rad = rad_nr
        skriv_header(ws, 1, header_rad, felter)
        forrige_dim = None
        skygge = False
        for i, rad in enumerate(rader, start=header_rad + 1):
            if rad.get("dimensjon") != forrige_dim:
                skygge = not skygge
                forrige_dim = rad.get("dimensjon")
            skriv_dataceller(ws, i, 1, felter, rad, skygge)

        ws.freeze_panes = f"A{header_rad + 1}"
        siste_kol = get_column_letter(n)
        ws.auto_filter.ref = f"A{header_rad}:{siste_kol}{header_rad + len(rader)}"

    def skriv_sammendrag(ws):
        """Egen 'Sammendrag'-fane øverst i arbeidsboka: totaler per år, måned,
        uke og dag — så ekspeditøren slipper å regne sammen selv."""
        per_ar, per_mnd, per_uke, per_dag = _tid_aggreger(csv_sti)
        ws.sheet_view.showGridLines = False
        BREDDE = 6
        for j, b in enumerate([16, 13, 13, 15, 15, 20], start=1):
            ws.column_dimensions[get_column_letter(j)].width = b

        # Tittelbånd
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=BREDDE)
        c0 = ws.cell(1, 1, "Pakkelapper — sammendrag"); c0.font = TITTEL_FONT; c0.fill = TITTEL_FILL
        c0.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws.row_dimensions[1].height = 26
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=BREDDE)
        c0 = ws.cell(2, 1, f"Generert {datetime.datetime.now():%d.%m.%Y %H:%M}  ·  alt regnet ut automatisk")
        c0.font = UNDERTITTEL_FONT; c0.fill = TITTEL_FILL
        c0.alignment = Alignment(horizontal="left", vertical="center", indent=1)

        rad = [4]  # muterbar teller så indre funksjon kan øke den

        def blokk(tittel, data_dict, nyeste_forst=True, maks=None):
            r = rad[0]
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=BREDDE)
            ct = ws.cell(r, 1, tittel); ct.font = Font(name=FONT_NAVN, size=11, bold=True, color="FFFFFF")
            ct.fill = HEADER_FILL; ct.alignment = Alignment(horizontal="left", indent=1)
            r += 1
            overskrifter = ["Periode", "Pakker", "Plank", "Kubikk (m³)", "Løpemeter", "Sesong (rå/tørr)"]
            for j, h in enumerate(overskrifter, start=1):
                c = ws.cell(r, j, h); c.font = SUBTOTAL_FONT; c.fill = SUBTOTAL_FILL
                c.alignment = Alignment(horizontal="center")
            r += 1
            nøkler = sorted(data_dict.keys(), reverse=nyeste_forst)
            if maks:
                nøkler = nøkler[:maks]
            for nøkkel in nøkler:
                g = data_dict[nøkkel]
                verdier = [nøkkel, g["pakker"], g["plank"], round(g["kubikk"], 3),
                           round(g["lm"], 1), f'{g["rå"]} / {g["tørr"]}']
                for j, v in enumerate(verdier, start=1):
                    c = ws.cell(r, j, v)
                    c.font = DATA_FONT
                    c.border = RAMME
                    if j == 1:   c.alignment = Alignment(horizontal="center")
                    if j == 4:   c.number_format = "0.000"
                    if j == 5:   c.number_format = "#,##0.0"
                    if j == 6:   c.alignment = Alignment(horizontal="center")
                r += 1
            rad[0] = r + 1  # luft før neste blokk

        if not per_ar:
            ws.cell(4, 1, "Ingen pakker registrert ennå.").font = DATA_FONT
            return
        blokk("PER ÅR", per_ar)
        blokk("PER MÅNED", per_mnd)
        blokk("PER UKE (siste 12)", per_uke, maks=12)
        blokk("PER DAG (siste 21)", per_dag, maks=21)

        # Nøkkeltall nederst
        r = rad[0]
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=BREDDE)
        ct = ws.cell(r, 1, "NØKKELTALL"); ct.font = Font(name=FONT_NAVN, size=11, bold=True, color="FFFFFF")
        ct.fill = HEADER_FILL; ct.alignment = Alignment(horizontal="left", indent=1)
        r += 1
        i_ar = str(datetime.date.today().year)
        dager_i_ar = [v for k, v in per_dag.items() if k.startswith(i_ar)]
        snitt = round(sum(d["pakker"] for d in dager_i_ar) / len(dager_i_ar), 1) if dager_i_ar else 0
        beste = max(dager_i_ar, key=lambda d: d["pakker"], default=None)
        beste_dag = max((k for k in per_dag if k.startswith(i_ar)),
                        key=lambda k: per_dag[k]["pakker"], default="—")
        nøkkeltall = [
            (f"Snitt pakker per produksjonsdag ({i_ar})", snitt),
            ("Beste enkeltdag i år", f'{beste_dag}: {beste["pakker"]} pakker' if beste else "—"),
            ("Antall produksjonsdager i år", len(dager_i_ar)),
        ]
        for tittel, verdi in nøkkeltall:
            ws.cell(r, 1, tittel).font = DATA_FONT
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
            c = ws.cell(r, 4, verdi); c.font = SUBTOTAL_FONT
            r += 1
        ws.freeze_panes = "A3"

    wb = Workbook()
    with csv_sti.open(encoding="utf-8") as f:
        alle_rader = list(csv.DictReader(f))

    fane_data = {navn: [] for navn in FANE_REKKEFØLGE}
    for rad in alle_rader:
        fane = SORT_FANE.get(rad.get("sort"), "Uavklart")
        fane_data[fane].append(rad)
    for rader in fane_data.values():
        rader.sort(key=lambda r: (r.get("dimensjon") or "", r.get("dato") or "", som_tall(r.get("pakkenr")) or 0))

    FELTER_KATEGORI = [f for f in KOLONNER if f not in ("sort", "sort_navn")]   # sort er gitt av fanen
    FELTER_UAVKLART = KOLONNER                                                  # her trengs sort/sortnavn

    # Sammendrag alltid først — det ekspeditøren ser når fila åpnes
    sammendrag_ws = wb.active
    sammendrag_ws.title = "Sammendrag"
    skriv_sammendrag(sammendrag_ws)

    forste = True
    for fane in FANE_REKKEFØLGE:
        rader = fane_data[fane]
        if not rader: continue
        ws = wb.create_sheet()
        ws.title = fane
        forste = False
        felter = FELTER_UAVKLART if fane == "Uavklart" else FELTER_KATEGORI
        skriv_fane(ws, f"Pakkelapper — {fane}", felter, rader)
    if forste:
        tom_ws = wb.create_sheet()
        tom_ws.title = "5Sort"
        skriv_fane(tom_ws, "Pakkelapper — 5Sort", FELTER_KATEGORI, [])

    # Samlet oversikt: antall/plank/kubikk per dimensjon, på tvers av alle fanene
    dim_grupper = _grupper_rader(csv_sti, ["sesong", "dimensjon"])
    if dim_grupper:
        dim_felter = ["sesong", "dimensjon", "antall_pakker", "sum_plank", "sum_kubikk_m3"]
        dim_rader = [
            {"sesong": s, "dimensjon": d, "antall_pakker": g["pakker"],
             "sum_plank": g["plank"], "sum_kubikk_m3": round(g["kubikk"], 3)}
            for (s, d), g in sorted(dim_grupper.items())
        ]
        dim_ws = wb.create_sheet("Per dimensjon (alle)")
        skriv_fane(dim_ws, "Oversikt per dimensjon — alle sorter", dim_felter, dim_rader,
                   vis_dimensjonsoversikt=False)

    tmp = xlsx_sti.with_suffix(".tmp.xlsx")
    wb.save(tmp); os.replace(tmp, xlsx_sti)
    antall = {fane: len(rader) for fane, rader in fane_data.items() if rader}
    logg(f"Eksportert til {xlsx_sti}  (" + ", ".join(f"{f}: {n}" for f, n in antall.items()) + ")")



def main():
    p = argparse.ArgumentParser(description="Pakkemaskin Skriver — RS-232 → CSV/Excel.")
    p.add_argument("--port", default="/dev/ttyUSB0")
    p.add_argument("--baud", type=int, default=9600)
    p.add_argument("--databits", type=int, default=8)
    p.add_argument("--paritet", choices=["N", "E", "O"], default="N")
    p.add_argument("--stoppbits", type=int, default=1)
    p.add_argument("--timeout", type=float, default=1.0)
    p.add_argument("--flush", type=float, default=3.0)
    p.add_argument("--reset-terskel", type=int, default=100,
                   help="nytt pakkenr må være ≤ denne (og maks > 9000) for 9999→0-nullstilling")
    filer = aarsfiler()
    p.add_argument("--csv", default=None,
                   help=f"CSV-fil (standard: {filer['csv']} — nytt navn hvert år)")
    p.add_argument("--xlsx", default=None,
                   help=f"Excel-fil (standard: {filer['xlsx']} — oppdateres på stedet)")
    p.add_argument("--utskrift", default="utskrift.txt")
    p.add_argument("--mangler", default=None,
                   help=f"hull-logg (standard: {filer['mangler']})")
    p.add_argument("--oppsummering-fil", default="oppsummering.csv")
    p.add_argument("--dimensjon-fil", default="oppsummering_dimensjon.csv")
    p.add_argument("--sesong-fil", default="sesong.txt")
    p.add_argument("--usb-sti", default="/media/usb0",
                   help='mappe der en minnepenn forventes montert, for sanntids-speiling av '
                        'årets CSV/Excel. SD-kortet er alltid fasiten uansett — sett til "" '
                        'for å slå speiling helt av.')
    p.add_argument("--bare-fangst", action="store_true")
    p.add_argument("--simuler")
    p.add_argument("--list-porter", action="store_true")
    p.add_argument("--eksporter-xlsx", action="store_true")
    p.add_argument("--sjekk-usb", action="store_true",
                   help="sjekk/helbred at minnepennen speiler SD (atomisk omskriv ved avvik)")
    p.add_argument("--oppsummering", action="store_true")
    p.add_argument("--oppsummering-dimensjon", action="store_true",
                   help="antall/plank/kubikk gruppert per dimensjon (uavhengig av dato)")
    p.add_argument("--registrer", help="registrer et pakkenr manuelt (når lappen aldri kom)")
    p.add_argument("--sett-sesong", help='sett gjeldende sesong: "rå" eller "tørr"')
    args = p.parse_args()

    csv_navn = args.csv or filer["csv"]
    xlsx_navn = args.xlsx or filer["xlsx"]
    mangler_navn = args.mangler or filer["mangler"]
    utskrift = Path(args.utskrift)
    csv_sti, xlsx_sti = Path(csv_navn), Path(xlsx_navn)
    mangler_sti, sesong_fil = Path(mangler_navn), Path(args.sesong_fil)
    usb_mappe = Path(args.usb_sti) if args.usb_sti else None
    usb_sti = (usb_mappe / csv_navn) if usb_mappe else None

    if args.list_porter:    list_porter(); return
    if args.sett_sesong:    sett_sesong(args.sett_sesong, sesong_fil); return

    # Oppgrader gamle generiske filnavn → årsfiler (én gang)
    migrer_legacy_aarsfiler(csv_sti, xlsx_sti, mangler_sti)
    migrer_usb_legacy(usb_mappe, csv_navn, xlsx_navn)

    if args.sjekk_usb:
        r = sjekk_og_helbred(csv_sti, usb_sti)
        print(r["melding"])
        if r["helbredt"] and csv_sti.exists():
            eksporter_xlsx(csv_sti, xlsx_sti)
            speil_xlsx_til_usb(xlsx_sti, usb_sti)
        raise SystemExit(0 if r["ok"] else 1)

    if args.eksporter_xlsx:
        eksporter_xlsx(csv_sti, xlsx_sti)
        speil_xlsx_til_usb(xlsx_sti, usb_sti)
        return
    if args.oppsummering:   oppsummering(csv_sti, Path(args.oppsummering_fil)); return
    if args.oppsummering_dimensjon: oppsummering_dimensjon(csv_sti, Path(args.dimensjon_fil)); return

    sesong = les_sesong(sesong_fil)
    if args.registrer:
        registrer_manuelt(args.registrer, csv_sti, mangler_sti, sesong, args.reset_terskel)
        synkroniser_usb(csv_sti, usb_sti)
        eksporter_xlsx(csv_sti, xlsx_sti)
        speil_xlsx_til_usb(xlsx_sti, usb_sti)
        return

    # Langkjøring (fangst/simulering): Excel bygges i bakgrunnen etter CSV-endring
    state = ny_fangst_state(csv_sti, xlsx_sti, mangler_sti, usb_sti, args.reset_terskel, filer["aar"])
    start_xlsx_auto(csv_sti, xlsx_sti, usb_sti)
    reg = Register(csv_sti, mangler_sti, args.reset_terskel)
    if _usb_tilgjengelig(usb_sti):
        logg(f"Minnepenn funnet ved oppstart ({usb_sti.parent}) — sjekker om noe mangler …")
        synkroniser_usb(csv_sti, usb_sti)
    if csv_sti.exists():
        marker_xlsx_oppdatering()  # fersk Excel på SD/penn ved oppstart / etter synk
    if args.simuler:
        kjor_simulering(args, utskrift, state, reg, sesong)
        eksporter_xlsx(state["csv_sti"], state["xlsx_sti"])
        speil_xlsx_til_usb(state["xlsx_sti"], state["usb_sti"])
    else:
        les_serie(args, utskrift, state, reg, sesong)


if __name__ == "__main__":
    main()
