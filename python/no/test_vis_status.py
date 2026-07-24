#!/usr/bin/env python3
"""Tester for OLED-status (uten fysisk skjerm)."""
import unittest

from vis_status import skjerm_siste_pakke, siste_pakke


class TestSistePakke(unittest.TestCase):
    def test_tom(self):
        self.assertIsNone(siste_pakke([]))
        self.assertEqual(skjerm_siste_pakke([])[0], "SISTE PAKKE:")

    def test_nyeste_tid_fanget_vinner(self):
        rader = [
            {"tid_fanget": "2026-07-24T10:00:00", "pakkenr": "100",
             "dimensjon": "50x100", "sort_navn": "5s", "kubikk_m3": "0.5"},
            {"tid_fanget": "2026-07-24T12:00:00", "pakkenr": "113",
             "dimensjon": "75x150", "sort_navn": "krok", "kubikk_m3": "1.073"},
            {"tid_fanget": "2026-07-24T11:00:00", "pakkenr": "110",
             "dimensjon": "75x150", "sort_navn": "5s", "kubikk_m3": "1.0"},
        ]
        p = siste_pakke(rader)
        self.assertEqual(p["pakkenr"], "113")
        linjer = skjerm_siste_pakke(rader)
        self.assertEqual(linjer[0], "SISTE PAKKE:")
        self.assertIn("113", linjer[1])
        self.assertIn("75x150", linjer[2])
        self.assertIn("krok", linjer[2])
        self.assertIn("1.073", linjer[3])


if __name__ == "__main__":
    unittest.main()
