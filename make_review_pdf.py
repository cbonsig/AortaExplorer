#!/usr/bin/env python
"""Assemble the AortaExplorer visualizations of an output folder into a review PDF.

Collects the PNG files from <output_folder>/all_visualizations, sorts them in
natural order (D1, D2, ... D10 rather than D1, D10, D2), and writes a PDF with
a title page followed by one full-resolution visualization per page.

Fork-specific utility (github.com/cbonsig/AortaExplorer), not part of upstream.
Requires Pillow, which is already a dependency of AortaExplorer.

Usage:
    python make_review_pdf.py /path/to/AortaExplorerOutput/
    python make_review_pdf.py /path/to/AortaExplorerOutput/ --title "KiTS Test Set"
    python make_review_pdf.py /path/to/AortaExplorerOutput/ -o /path/to/review.pdf
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
    "C:/Windows/Fonts/arial.ttf",  # Windows
]


def natural_key(path):
    return [
        int(token) if token.isdigit() else token.lower()
        for token in re.split(r"(\d+)", path.name)
    ]


def load_font(size):
    for candidate in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def make_title_page(size, title, n_scans, source_folder):
    page = Image.new("RGB", size, "black")
    draw = ImageDraw.Draw(page)
    font_big = load_font(size[1] // 17)
    font_small = load_font(size[1] // 30)
    cx = size[0] // 2

    lines_big = ["AortaExplorer Visualizations", title]
    lines_small = [
        f"{n_scans} scans  |  Generated {date.today().isoformat()}",
        f"Source: {source_folder}",
        "AortaExplorer fork: github.com/cbonsig/AortaExplorer",
        "",
        "Research use only - not a medical device, not for clinical use",
    ]

    y = int(size[1] * 0.35)
    for text in lines_big:
        draw.text((cx, y), text, fill="white", font=font_big, anchor="mm")
        y += int(size[1] * 0.083)
    y += int(size[1] * 0.037)
    for text in lines_small:
        draw.text((cx, y), text, fill=(180, 180, 180), font=font_small, anchor="mm")
        y += int(size[1] * 0.052)
    return page


def main():
    parser = argparse.ArgumentParser(
        description="Assemble AortaExplorer visualizations into a review PDF"
    )
    parser.add_argument(
        "output_folder",
        help="AortaExplorer output folder (containing all_visualizations/)",
    )
    parser.add_argument(
        "--title",
        help="Dataset title for the cover page (default: output folder name)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output PDF path (default: <output_folder>/<folder_name>_review.pdf)",
    )
    args = parser.parse_args()

    out_folder = Path(args.output_folder).expanduser().resolve()
    vis_folder = out_folder / "all_visualizations"
    if not vis_folder.is_dir():
        sys.exit(f"No all_visualizations folder found in {out_folder}")

    pngs = sorted(vis_folder.glob("*.png"), key=natural_key)
    if not pngs:
        sys.exit(f"No PNG files found in {vis_folder}")

    title = args.title if args.title else out_folder.name
    out_pdf = (
        Path(args.output).expanduser().resolve()
        if args.output
        else out_folder / f"{out_folder.name}_review.pdf"
    )

    scans = [Image.open(p).convert("RGB") for p in pngs]
    title_page = make_title_page(scans[0].size, title, len(pngs), vis_folder)

    pages = [title_page] + scans
    pages[0].save(out_pdf, save_all=True, append_images=pages[1:], resolution=180.0)
    print(f"Wrote {out_pdf} ({out_pdf.stat().st_size / 1e6:.1f} MB, {len(pages)} pages)")


if __name__ == "__main__":
    main()
