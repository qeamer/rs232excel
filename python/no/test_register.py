#!/usr/bin/env python3
"""Enhetstester for Register / Bug D, F, H (og flush-kompletthet)."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from read_package import (
    NULLSTILL_MIN_MAKS,
    Register,
    append_csv,
    erstatt_manuell_rad,
    ser_komplett_lapp,
    sjekk_og_helbred,
    skriv_trygt,
    KOLONNER,
)


class TestBugDNullstilling(unittest.TestCase):
    def _reg(self, maks, sett=None, terskel=100):
        with tempfile.TemporaryDirectory() as d:
            csv_sti = Path(d) / "p.csv"
            mangler = Path(d) / "m.csv"
            reg = Register(csv_sti, mangler, terskel)
            reg.maks = maks
            reg.sett = set(sett or range(maks - 5, maks + 1)) if maks else set()
            if maks is not None:
                reg.sett.add(maks)
            return reg, csv_sti, mangler

    def test_reprint_mid_sequence_is_not_reset(self):
        """Bug D: maks=805, reprint 650 må IKKE starte ny runde."""
        reg, _, _ = self._reg(805, sett=set(range(600, 806)))
        status, n, reset = reg.vurder("650")
        self.assertEqual(n, 650)
        self.assertFalse(reset)
        self.assertEqual(status, "duplikat")  # 650 allerede i sett

    def test_late_low_number_without_high_maks_is_not_reset(self):
        """Hoppende bakover midt i serien uten maks>9000 = ikke nullstilling."""
        reg, _, _ = self._reg(805, sett=set(range(700, 806)))
        status, n, reset = reg.vurder("10")
        self.assertEqual(status, "ok")
        self.assertFalse(reset)

    def test_real_rollover_9999_to_0(self):
        reg, _, _ = self._reg(9999, sett={9998, 9999})
        status, n, reset = reg.vurder("0")
        self.assertEqual(status, "ok")
        self.assertEqual(n, 0)
        self.assertTrue(reset)

    def test_rollover_requires_maks_near_end(self):
        self.assertGreater(NULLSTILL_MIN_MAKS, 8000)
        reg, _, _ = self._reg(8500, sett={8499, 8500})
        # 8500 < 9000 → ikke nullstilling selv om n er lavt
        status, n, reset = reg.vurder("0")
        self.assertFalse(reset)

    def test_reprint_near_end_not_reset_if_n_not_low(self):
        """maks=9500, reprint 650: ikke nullstilling (n > terskel)."""
        reg, _, _ = self._reg(9500, sett=set(range(9400, 9501)))
        status, n, reset = reg.vurder("650")
        self.assertFalse(reset)
        self.assertEqual(status, "ok")  # ikke i sett → sen/out-of-order, men ikke ny runde


class TestBugFManuellOppgradering(unittest.TestCase):
    def test_manuell_then_real_is_oppgrader(self):
        with tempfile.TemporaryDirectory() as d:
            csv_sti = Path(d) / "p.csv"
            mangler = Path(d) / "m.csv"
            reg = Register(csv_sti, mangler)
            reg.registrer(42, manuell=True)
            status, n, reset = reg.vurder("42")
            self.assertEqual(status, "oppgrader")
            self.assertFalse(reset)

            rad = {k: "" for k in KOLONNER}
            rad.update(pakkenr="42", runde=1, status="manuell", raa="(manuelt)")
            append_csv(rad, csv_sti)
            ny = dict(rad)
            ny.update(status="ok", dimensjon="75x150", treslag="FURU", raa="ekte")
            self.assertTrue(erstatt_manuell_rad(csv_sti, 1, 42, ny))
            with csv_sti.open(encoding="utf-8") as f:
                rader = list(csv.DictReader(f))
            self.assertEqual(len(rader), 1)
            self.assertEqual(rader[0]["status"], "ok")
            self.assertEqual(rader[0]["dimensjon"], "75x150")


class TestBugHFriskmeld(unittest.TestCase):
    def test_hull_friskmeldes_nar_pakke_kommer(self):
        with tempfile.TemporaryDirectory() as d:
            csv_sti = Path(d) / "p.csv"
            mangler = Path(d) / "m.csv"
            reg = Register(csv_sti, mangler)
            reg.registrer(10)
            reg.registrer(12)  # hull 11
            with mangler.open(encoding="utf-8") as f:
                aapne = [r for r in csv.DictReader(f) if r["manglende_pakkenr"] == "11"]
            self.assertEqual(len(aapne), 1)
            self.assertEqual(aapne[0]["status"], "åpen")

            reg.registrer(11)  # kommer sent
            with mangler.open(encoding="utf-8") as f:
                r11 = [r for r in csv.DictReader(f) if r["manglende_pakkenr"] == "11"][0]
            self.assertEqual(r11["status"], "funnet")


class TestBugEFlush(unittest.TestCase):
    def test_fragment_not_complete(self):
        self.assertFalse(ser_komplett_lapp("645  75X 150\n2024/ 7/21  5"))

    def test_full_label_complete(self):
        # minimal: heltall + kubikk med 3 desimaler
        self.assertTrue(ser_komplett_lapp("645 75X 150\n84  123,4  4,025  30"))


class TestUsbIntegritet(unittest.TestCase):
    def _rad(self, pakkenr, runde=1):
        rad = {k: "" for k in KOLONNER}
        rad.update(pakkenr=str(pakkenr), runde=str(runde), status="ok")
        return rad

    def test_skriv_trygt_atomic(self):
        with tempfile.TemporaryDirectory() as d:
            sti = Path(d) / "p.csv"
            skriv_trygt(sti, [self._rad(1), self._rad(2)])
            with sti.open(encoding="utf-8") as f:
                rader = list(csv.DictReader(f))
            self.assertEqual([r["pakkenr"] for r in rader], ["1", "2"])
            self.assertFalse(sti.with_name("p.csv.tmp").exists())

    def test_helbred_mangler_append(self):
        with tempfile.TemporaryDirectory() as d:
            sd = Path(d) / "sd.csv"
            usb = Path(d) / "usb" / "p.csv"
            usb.parent.mkdir()
            skriv_trygt(sd, [self._rad(1), self._rad(2), self._rad(3)])
            skriv_trygt(usb, [self._rad(1)])
            r = sjekk_og_helbred(sd, usb)
            self.assertTrue(r["ok"])
            self.assertTrue(r["helbredt"])
            self.assertEqual(r["manglet"], 2)
            with usb.open(encoding="utf-8") as f:
                n = {row["pakkenr"] for row in csv.DictReader(f)}
            self.assertEqual(n, {"1", "2", "3"})

    def test_helbred_korrupt_full_rewrite(self):
        with tempfile.TemporaryDirectory() as d:
            sd = Path(d) / "sd.csv"
            usb = Path(d) / "usb" / "p.csv"
            usb.parent.mkdir()
            skriv_trygt(sd, [self._rad(10), self._rad(11)])
            usb.write_text("dette er ikke csv\x00\x00", encoding="utf-8")
            r = sjekk_og_helbred(sd, usb)
            self.assertTrue(r["ok"])
            self.assertTrue(r["helbredt"])
            with usb.open(encoding="utf-8") as f:
                rader = list(csv.DictReader(f))
            self.assertEqual([x["pakkenr"] for x in rader], ["10", "11"])

    def test_ok_nar_lik(self):
        with tempfile.TemporaryDirectory() as d:
            sd = Path(d) / "sd.csv"
            usb = Path(d) / "usb" / "p.csv"
            usb.parent.mkdir()
            skriv_trygt(sd, [self._rad(1)])
            skriv_trygt(usb, [self._rad(1)])
            r = sjekk_og_helbred(sd, usb)
            self.assertTrue(r["ok"])
            self.assertFalse(r["helbredt"])


if __name__ == "__main__":
    unittest.main()
