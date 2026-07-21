#!/usr/bin/env python3
"""Generate English screenshot assets for docs/en/img/. Run once, then delete."""
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "-q"])
    from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "docs" / "en" / "img"
GREEN = "#1B4D3E"
GREEN_LIGHT = "#D9E5E1"
WHITE = "#FFFFFF"
GRID = "#D9D9D9"
TEXT = "#1A1A1A"
MUTED = "#595959"

def font(size, bold=False):
    names = ["Segoe UI Bold", "Segoe UI", "Calibri Bold", "Calibri", "Arial Bold", "Arial"]
    if not bold:
        names = ["Segoe UI", "Calibri", "Arial", "DejaVu Sans"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_terminal():
    w, h = 1200, 420
    img = Image.new("RGB", (w, h), "#0d1117")
    d = ImageDraw.Draw(img)
    # title bar
    d.rectangle([0, 0, w, 34], fill="#161b22")
    d.text((14, 9), "pi@pakkemaskin: ~/rs232excel/python/en", fill="#c9d1d9", font=font(13))
    y = 52
    lines = [
        ("$ python3 read_package.py --port /dev/ttyUSB0 --usb-path /media/usb0", "#58a6ff", False),
        ("[07:41:02] Starting. Listening on /dev/ttyUSB0 @ 9600 8N1  season=kiln-dried", "#8b949e", False),
        ("[07:41:02] Loaded round 1: 1648 package numbers (highest 1751).", "#8b949e", False),
        ("[07:41:02] Connected.", "#3fb950", False),
        ("[07:44:18] ✓ package 1752 [r1/kiln-dried] 75x150 PINE sort 5(5s), 84 boards, 4.025 m³", "#3fb950", False),
        ("[07:49:03] ✓ package 1753 [r1/kiln-dried] 50x100 SPRUCE sort 1(crook), 31 boards, 0.615 m³", "#3fb950", False),
        ("[07:49:07] ↺ duplicate package 1753 — dropped (raw copy in capture.txt)", "#d29922", False),
        ("[07:55:40] ⚠ Possible gap (round 1): package 1754-1754 → missing.csv", "#f85149", False),
        ("[07:56:12] ✓ package 1755 [r1/kiln-dried] 75x150 PINE sort 6(crook), 70 boards, 3.145 m³", "#3fb950", False),
        ("[07:56:12] 📀 Mirrored to /media/usb0/packages.csv", "#58a6ff", False),
    ]
    f = font(15)
    for text, color, bold in lines:
        d.text((24, y), text, fill=color, font=f)
        y += 30
    img.save(OUT / "terminal-capture.png", optimize=True)
    print("terminal-capture.png")


def draw_table_section(d, x, y, title, headers, rows, col_widths):
    d.text((x, y), title, fill=TEXT, font=font(14, True))
    y += 26
    hx, hy = x, y
    hh = 28
    total_w = sum(col_widths)
    d.rectangle([hx, hy, hx + total_w, hy + hh], fill=GREEN)
    cx = hx
    for i, h in enumerate(headers):
        d.text((cx + 8, hy + 6), h, fill=WHITE, font=font(11, True))
        cx += col_widths[i]
    y += hh
    for ri, row in enumerate(rows):
        fill = GREEN_LIGHT if row[0] == "Total" else (WHITE if ri % 2 == 0 else "#F7F7F7")
        d.rectangle([hx, y, hx + total_w, y + 24], fill=fill, outline=GRID)
        cx = hx
        for i, cell in enumerate(row):
            d.text((cx + 8, y + 5), str(cell), fill=TEXT, font=font(10))
            cx += col_widths[i]
        y += 24
    return y + 18


def draw_excel_summary():
    w, h = 1200, 780
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 56], fill=GREEN)
    d.text((18, 16), "SKJÅK TRELAST AS", fill=WHITE, font=font(18, True))
    d.text((900, 18), "Summary", fill=WHITE, font=font(16, True))
    y = 72
    cols = [130, 80, 80, 120, 100]
    headers = ["Category", "Packages", "Boards", "Metres (lm)", "Volume (m³)"]
    rows1 = [
        ["5Sort", "1,350", "47,960", "266,380.1", "2,708.8"],
        ["Crook", "206", "8,800", "55,158.0", "480.0"],
        ["Flooring", "73", "2,500", "13,282.0", "147.5"],
        ["Hogged", "19", "520", "3,249.0", "26.2"],
        ["Unsorted", "0", "0", "0.0", "0.0"],
        ["Total", "1,648", "59,780", "338,069.1", "3,362.5"],
    ]
    y = draw_table_section(d, 24, y, "Total per sort category", headers, rows1, cols)
    rows2 = [["2026", "1,648", "59,780", "338,069.1", "3,362.5"]]
    y = draw_table_section(d, 24, y, "Per year", headers[:1] + headers[1:], rows2, cols)
    month_headers = ["Month"] + headers[1:] + ["5Sort (m³)"]
    month_cols = [100, 80, 80, 120, 100, 90]
    month_rows = [
        ["Jan 2026", "142", "5,200", "28,400.0", "285.0", "220.0"],
        ["Feb 2026", "168", "6,100", "33,800.0", "340.5", "265.0"],
        ["Mar 2026", "201", "7,300", "41,200.0", "410.2", "318.0"],
        ["Apr 2026", "225", "8,100", "46,500.0", "462.0", "358.0"],
        ["May 2026", "240", "8,800", "50,100.0", "498.5", "385.0"],
        ["Jun 2026", "380", "14,200", "79,800.0", "792.0", "612.0"],
        ["Jul 2026", "292", "10,080", "58,271.1", "574.3", "450.8"],
    ]
    y = draw_table_section(d, 24, y, "Per month", month_headers, month_rows, month_cols)
    day_rows = [
        ["19.06.2026", "42", "1,520", "8,640.0", "86.2"],
        ["22.06.2026", "38", "1,380", "7,920.0", "78.5"],
        ["23.06.2026", "45", "1,620", "9,210.0", "91.4"],
    ]
    draw_table_section(d, 24, y, "Per day (last 21 production days)", headers[:1] + headers[1:], day_rows, cols)
    img.save(OUT / "excel-summary.png", optimize=True)
    print("excel-summary.png")


def draw_excel_charts():
    w, h = 1200, 520
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 48], fill=GREEN)
    d.text((18, 12), "Production control — Half-year report", fill=WHITE, font=font(15, True))
    d.text((18, 58), "Generated 18.07.2026 06:46  ·  1,648 packages  ·  formulas over Raw data sheet",
           fill=MUTED, font=font(11))
    # simple pie
    d.text((60, 95), "Volume by sort category", fill=TEXT, font=font(12, True))
    cx, cy, r = 180, 240, 90
    slices = [(GREEN, 220), ("#2E7D62", 90), ("#5A9E8F", 50), ("#A8C5BC", 20)]
    start = 0
    for color, extent in slices:
        d.pieslice([cx - r, cy - r, cx + r, cy + r], start, start + extent, fill=color, outline=WHITE)
        start += extent
    # stacked bars
    d.text((420, 95), "Volume per month, by sort", fill=TEXT, font=font(12, True))
    bx, by, bw, bh = 420, 130, 720, 160
    d.rectangle([bx, by, bx + bw, by + bh], outline=GRID)
    months = 7
    bar_w = bw // (months * 2)
    heights = [(120, 40, 20, 10), (140, 45, 22, 12), (160, 50, 25, 15),
               (180, 55, 28, 18), (200, 60, 30, 20), (280, 90, 45, 30), (220, 70, 35, 25)]
    colors = [GREEN, "#2E7D62", "#5A9E8F", "#A8C5BC"]
    for i, stack in enumerate(heights):
        x = bx + 20 + i * (bar_w + 18)
        y_base = by + bh - 10
        for j, h in enumerate(stack):
            y1 = y_base - sum(stack[:j + 1]) * 0.55
            y0 = y_base - sum(stack[:j]) * 0.55
            d.rectangle([x, y1, x + bar_w, y0], fill=colors[j])
        d.text((x, by + bh + 6), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"][i],
               fill=MUTED, font=font(9))
    d.text((420, 320), "Running metres per month", fill=TEXT, font=font(12, True))
    lx, ly = 420, 350
    pts = [(lx + i * 100, ly + 80 - v * 0.4) for i, v in enumerate([60, 72, 85, 95, 110, 140, 120])]
    for i in range(len(pts) - 1):
        d.line([pts[i], pts[i + 1]], fill=GREEN, width=3)
    for p in pts:
        d.ellipse([p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4], fill=GREEN)
    img.save(OUT / "excel-charts.png", optimize=True)
    print("excel-charts.png")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    draw_terminal()
    draw_excel_summary()
    draw_excel_charts()
    print("done")
