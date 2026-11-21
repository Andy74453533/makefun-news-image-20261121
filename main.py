#!/usr/bin/env python3
"""news-image-20261121 — Sum up 21 November 2026 world news in one image.

Entry for make.fun bounty news-image-20261121.

Writes a 1024x1024 PNG front page to <output>/entry.png (default /output,
overridable with MAKEFUN_OUTPUT_DIR / OUTPUT_DIR).

The image is rendered programmatically with Pillow from the fixed story data
below — no network, no downloaded assets, no randomness: two runs write
byte-identical files. Fonts are embedded in assets/fonts/ so rendering does
not depend on system fonts. If Pillow is unavailable, main() falls back to
copying the pre-rendered assets/entry.png (same bytes).

Stories (all first reported on Saturday 21 November 2026):
  1. New York mayor Zohran Mamdani unveils a plan to close Rikers Island
     by 2032, replacing it with four smaller jails across the boroughs
     and cutting the inmate population from about 6,500 to 4,100.
  2. The EU and Indonesia sign their landmark trade deal (IEU-CEPA) in
     Brussels, liberalising about 98% of bilateral trade worth roughly
     $30bn a year.
  3. NATO chief Mark Rutte visits Warsaw as Poland seeks more air
     defences, a day after Russian missiles landed in Poland.
  4. Florida's floods push north: the St. Johns River reaches a record
     18.8 ft, above its 1953 record, as floodwaters spread.
  5. Iraq opens a security headquarters in Jurf al-Sakhar, a day after
     troops entered the Kataib Hezbollah stronghold.
Markets (Friday 20 November US close): Dow -1.93% to 48,147,
S&P 500 -3.70% to 6,910, Nasdaq -5.28% to 22,618; Anthropic -9%,
Nvidia -14%, VIX 40.

Sources: BBC, Reuters, AP, Consilium, National Weather Service — see
SOURCES.md.
"""

import os
import shutil
import sys

W, H = 1024, 1024
MX = 36                       # side margin
CW = W - 2 * MX               # content width = 952

PAPER = (250, 246, 238)       # warm newsprint
INK = (26, 26, 26)
NAVY = (20, 33, 61)
RED = (185, 28, 28)
GREY = (90, 90, 90)
MUTED = (60, 60, 60)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
SKY = (150, 200, 255)

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
FONTS = os.path.join(ASSETS, "fonts")
PRE_RENDERED = os.path.join(ASSETS, "entry.png")


# ------------------------------------------------------------------ fonts
def load_font(name, size):
    from PIL import ImageFont
    for path in (os.path.join(FONTS, name),
                 os.path.join("/usr/share/fonts/truetype/dejavu", name)):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ------------------------------------------------------------------ helpers
def wrap_text(draw, text, fnt, max_w):
    """Greedy word wrap; returns the lines that fit inside max_w."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def shrink_to_fit(draw, text, name, sizes, max_w):
    """Largest font (sizes descending) in which text fits max_w."""
    for size in sizes:
        fnt = load_font(name, size)
        if draw.textlength(text, font=fnt) <= max_w:
            return fnt
    return load_font(name, sizes[-1])


def tile(draw, x, y, s, color):
    draw.rounded_rectangle([x, y, x + s, y + s], radius=14, fill=color)


# ------------------------------------------------------------------ icons
def icon_bars(draw, x, y, s):
    """Jail bars: a cell window with vertical bars."""
    cx = x + s // 2
    draw.rounded_rectangle([x + 8, y + 8, x + s - 8, y + s - 8],
                           radius=8, outline=WHITE, width=4)
    for i in range(5):
        bx = x + 18 + i * 14
        draw.line([(bx, y + 12), (bx, y + s - 12)], fill=WHITE, width=5)


def icon_deal(draw, x, y, s):
    """A signed document: page, text lines, seal and pen."""
    draw.rectangle([x + 20, y + 12, x + 62, y + 76], fill=WHITE)
    draw.line([(x + 26, y + 22), (x + 56, y + 22)], fill=INK, width=3)
    draw.line([(x + 26, y + 32), (x + 56, y + 32)], fill=INK, width=3)
    draw.line([(x + 26, y + 42), (x + 48, y + 42)], fill=INK, width=3)
    draw.ellipse([x + 44, y + 52, x + 64, y + 72], fill=GOLD,
                 outline=INK, width=2)
    draw.line([(x + 62, y + 18), (x + 76, y + 44)], fill=RED, width=4)
    draw.polygon([(x + 76, y + 44), (x + 70, y + 46), (x + 74, y + 52)],
                 fill=RED)


def icon_shield(draw, x, y, s):
    """A shield with a four-point star (alliance / defence)."""
    cx = x + s // 2
    draw.polygon([(cx - 26, y + 12), (cx + 26, y + 12), (cx + 26, y + 44),
                  (cx, y + 74), (cx - 26, y + 44)], fill=WHITE)
    draw.polygon([(cx, y + 20), (cx + 6, y + 36), (cx + 22, y + 42),
                  (cx + 6, y + 48), (cx, y + 64), (cx - 6, y + 48),
                  (cx - 22, y + 42), (cx - 6, y + 36)], fill=NAVY)


def icon_waves(draw, x, y, s):
    """Flood water: three rising waves and rain drops."""
    for k, wy in enumerate((34, 48, 62)):
        draw.arc([x + 10, y + wy - 8, x + s - 10, y + wy + 14],
                 start=180, end=360, fill=SKY, width=5)
    for rx in (22, 44, 66):
        draw.line([(x + rx, y + 12), (x + rx - 3, y + 24)],
                  fill=SKY, width=4)


def icon_hq(draw, x, y, s):
    """A headquarters building with a flag on top."""
    draw.rectangle([x + 18, y + 34, x + s - 18, y + s - 10], fill=WHITE)
    draw.line([(x + s // 2, y + 10), (x + s // 2, y + 34)],
              fill=WHITE, width=4)
    draw.polygon([(x + s // 2, y + 10), (x + s // 2 + 24, y + 16),
                  (x + s // 2, y + 22)], fill=GOLD)
    for wx in (26, 44, 62):
        draw.rectangle([x + wx, y + 44, x + wx + 8, y + 56], fill=NAVY)
    draw.rectangle([x + 38, y + 62, x + 50, y + s - 10], fill=NAVY)


# ------------------------------------------------------------------ lead art
def draw_plan_box(draw, x, y, w, h):
    """The Rikers closure plan, as announced: four lines of fact."""
    draw.rounded_rectangle([x, y, x + w, y + h], radius=10,
                           outline=NAVY, width=2)
    f_t = load_font("DejaVuSans-Bold.ttf", 17)
    f_l = load_font("DejaVuSans.ttf", 18)
    draw.text((x + 22, y + 10), "THE PLAN", font=f_t, fill=RED)
    rows = [
        "Brooklyn jail by 2029",
        "Bronx & Queens by 2031",
        "Manhattan by 2032",
        "Inmates: 6,500 \u2192 4,100",
    ]
    ly = y + 38
    for row in rows:
        draw.text((x + 22, ly), "\u2022  " + row, font=f_l, fill=INK)
        ly += 22


def draw_jail_art(draw, x, y, w, h):
    """Jail bars on a dark panel, beside the plan box."""
    draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=NAVY)
    icon_bars(draw, x + (w - 88) // 2, y + (h - 88) // 2, 88)


# ------------------------------------------------------------------ render
def render():
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    f_mast = load_font("DejaVuSerif-Bold.ttf", 58)
    f_date = load_font("DejaVuSans-Bold.ttf", 21)
    f_kick = load_font("DejaVuSans-Bold.ttf", 20)
    f_lead = load_font("DejaVuSans-Bold.ttf", 46)
    f_sub = load_font("DejaVuSans.ttf", 23)
    f_head = load_font("DejaVuSans-Bold.ttf", 28)
    f_sum = load_font("DejaVuSans.ttf", 21)
    f_mkt = load_font("DejaVuSans-Bold.ttf", 18)
    f_foot = load_font("DejaVuSans.ttf", 14)

    # ---- masthead
    d.text((W // 2, 26), "THE WORLD TODAY", font=f_mast, fill=NAVY,
           anchor="ma")
    d.text((W // 2, 94), "SATURDAY, 21 NOVEMBER 2026", font=f_date,
           fill=RED, anchor="ma")
    d.line([MX, 126, MX + CW, 126], fill=NAVY, width=3)
    d.line([MX, 132, MX + CW, 132], fill=NAVY, width=1)

    # ---- lead story
    y = 148
    d.text((MX, y), "NEW YORK  \u2022  LEAD STORY", font=f_kick, fill=RED)
    y = 176
    for line in ["RIKERS ISLAND TO CLOSE", "BY 2032"]:
        d.text((MX, y), line, font=f_lead, fill=INK)
        y += 56
    y = 292
    sub = ("Mayor Mamdani unveils a plan to shut New York\u2019s notorious "
           "jail \u2014 four smaller jails across the boroughs, and inmate "
           "numbers cut from 6,500 to 4,100.")
    for line in wrap_text(d, sub, f_sub, CW)[:2]:
        d.text((MX, y), line, font=f_sub, fill=INK)
        y += 30

    # ---- lead art: jail bars + plan box
    ay = 366
    draw_jail_art(d, MX, ay, 220, 126)
    draw_plan_box(d, MX + 244, ay, CW - 244, 126)

    # ---- divider
    d.line([MX, 514, MX + CW, 514], fill=NAVY, width=3)

    # ---- four story rows
    stories = [
        ("EU AND INDONESIA SIGN LANDMARK TRADE DEAL",
         "The pact liberalises 98% of trade between the two sides, "
         "worth about $30bn a year.",
         (13, 110, 71), icon_deal),
        ("RUTTE IN WARSAW AS POLAND SEEKS MORE AIR DEFENCES",
         "The NATO chief visits Poland a day after Russian missiles "
         "landed there; Warsaw wants more Eastern Sentry forces.",
         (20, 33, 61), icon_shield),
        ("FLORIDA FLOODS PUSH NORTH AS RIVER HITS RECORD",
         "The St. Johns River reaches 18.8 ft, above its 1953 record, "
         "as floodwaters spread north.",
         (37, 99, 235), icon_waves),
        ("IRAQ OPENS SECURITY HQ IN MILITIA STRONGHOLD",
         "A day after troops entered Jurf al-Sakhar, a security "
         "headquarters opens to oversee the handover.",
         (185, 28, 28), icon_hq),
    ]
    ry = 532
    tile_s = 88
    for headline, summary, color, icon in stories:
        tile(d, MX, ry, tile_s, color)
        icon(d, MX, ry, tile_s)
        tx = MX + tile_s + 16
        tw = CW - tile_s - 16
        hf = shrink_to_fit(d, headline, "DejaVuSans-Bold.ttf",
                           [28, 27, 26, 25, 24], tw)
        d.text((tx, ry + 2), headline, font=hf, fill=INK)
        sy = ry + 38
        for line in wrap_text(d, summary, f_sum, tw)[:2]:
            d.text((tx, sy), line, font=f_sum, fill=MUTED)
            sy += 26
        ry += 94

    # ---- markets band (two lines, Friday 20 Nov US close)
    d.rectangle([0, 946, W, 1000], fill=NAVY)
    mkt_label = "MARKETS"
    mkt_line1 = ("Dow \u22121.93% 48,147    S&P 500 \u22123.70% 6,910    "
                 "Nasdaq \u22125.28% 22,618")
    mkt_gap = 34
    lw = d.textlength(mkt_label, font=f_mkt)
    rw = d.textlength(mkt_line1, font=f_mkt)
    mx = (W - lw - mkt_gap - rw) // 2
    d.text((mx, 950), mkt_label, font=f_mkt, fill=GOLD)
    d.text((mx + lw + mkt_gap, 950), mkt_line1, font=f_mkt, fill=WHITE)
    sep_x = mx + lw + mkt_gap // 2
    d.line([(sep_x, 953), (sep_x, 969)], fill=GOLD, width=2)
    line2 = ("Anthropic \u22129%    Nvidia \u221214%    VIX 40  "
             "\u2014  Friday\u2019s close")
    d.text(((W - d.textlength(line2, font=f_mkt)) // 2, 974), line2,
           font=f_mkt, fill=WHITE)

    # ---- footer
    d.text((W // 2, 1005),
           "A summary of world news \u2014 Saturday 21 November 2026",
           font=f_foot, fill=GREY, anchor="ma")

    return img


def main():
    out_dir = (os.environ.get("MAKEFUN_OUTPUT_DIR")
               or os.environ.get("OUTPUT_DIR") or "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")

    try:
        img = render()
        img.save(out_path, format="PNG")
    except ImportError:
        shutil.copyfile(PRE_RENDERED, out_path)
    print("wrote", out_path)


if __name__ == "__main__":
    sys.exit(main())
