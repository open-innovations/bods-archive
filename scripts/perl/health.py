#!/usr/bin/env python3
"""Make daily zip archives, prune old 10s files and draw calendar charts for the BODS archive."""

import glob
import os
import re
import shutil
import sys
import zipfile
from datetime import UTC, date, datetime, timedelta, timezone
from html import escape

ARCHIVE = os.environ["BODSARCHIVE"].rstrip("/")
WEBDIR = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "/var/www/data.datalibrary.uk/resources/images/"
)
TYPES = {
    "gtfsrt": {"keep_days": 60},
    "sirivm": {"keep_days": 60},
    "timetables": {"filepattern": "*_gtfs_[0-9]*.zip"},
}
NOW = datetime.now(UTC)
TODAY = NOW.strftime("%Y%m%d")


def human_bytes(n):
    for size, fmt in (
        (1e12, "%.2f TB"),
        (1e9, "%.2f GB"),
        (1e6, "%.1f MB"),
        (1e3, "%.1f kB"),
    ):
        if n > size:
            return fmt % (n / size)
    return str(n)


def dir_size(path):
    return sum(
        os.lstat(os.path.join(root, f)).st_size
        for root, _, files in os.walk(path)
        for f in files
    )


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def calendar_svg(rows, value_key, tooltip):
    """Minimal calendar heatmap: one block per year (newest first), weeks across, Mon-Sun down."""
    cell, label, year_h = 12, 40, 7 * 12 + 16
    top = max((r[value_key] for r in rows), default=0) or 1
    years = sorted({r["date"][:4] for r in rows}, reverse=True)
    parts = []
    for i, year in enumerate(years):
        y0 = i * year_h
        offset = date(int(year), 1, 1).weekday()
        parts.append(
            f'<text x="0" y="{y0 + 10}" font-size="10" font-family="sans-serif">{year}</text>'
        )
        for r in (r for r in rows if r["date"].startswith(year)):
            d = date.fromisoformat(r["date"])
            week = (d.timetuple().tm_yday - 1 + offset) // 7
            v = r[value_key]
            fill = (
                f'fill="#1a9850" fill-opacity="{0.15 + 0.85 * v / top:.2f}"'
                if v
                else 'fill="#ddd"'
            )
            text = d.strftime(tooltip)
            for _ in range(2):  # twice, because {{ links }} contains {{ byteshuman }}
                text = re.sub(r"\{\{ (\w+) \}\}", lambda m: str(r.get(m[1], "")), text)
            text = escape(re.sub(r"<[^>]+>", "", text))
            parts.append(
                f'<rect x="{label + week * cell}" y="{y0 + d.weekday() * cell}" '
                f'width="{cell - 2}" height="{cell - 2}" {fill}><title>{text}</title></rect>'
            )
    width, height = label + 54 * cell, len(years) * year_h
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">{"".join(parts)}</svg>'
    )


# Rough number of days of disk left
write(
    f"{ARCHIVE}/free.txt", f"{int(shutil.disk_usage('/').free / (2 * 90e9 / 7))} days"
)

for type_, cfg in sorted(TYPES.items()):
    print(f"Type: {type_}")
    base = f"{ARCHIVE}/{type_}"
    recent = None
    if "keep_days" in cfg:
        recent = (NOW - timedelta(days=cfg["keep_days"])).strftime("%Y%m%d")

    size = human_bytes(dir_size(base))
    print(f"Save {type_} size ({size}) to {base}/total-bytes.txt")
    write(f"{base}/total-bytes.txt", size)

    rows = []
    for daydir in sorted(
        glob.glob(f"{base}/[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]")
    ):
        y, m, d = daydir.split("/")[-3:]
        iso = y + m + d
        dayfile = f"{daydir}/{type_}-{iso}.zip"
        pattern = f"{daydir}/" + cfg.get("filepattern", f"{type_}-{iso}T*.zip")

        # Create the day's archive zip if it doesn't exist yet
        if not os.path.exists(dayfile) and iso < TODAY:
            zips = sorted(glob.glob(f"{daydir}/*.zip"))
            if zips:
                print(f"Create zip archive for {y}-{m}-{d}")
                with zipfile.ZipFile(dayfile, "w", zipfile.ZIP_STORED) as z:
                    for f in zips:
                        z.write(f, os.path.basename(f))

        # Count the 10s files (not the daily one) and remove them if too old
        matches = glob.glob(pattern)
        count = len(matches)
        if count and recent and iso < recent:
            print(f"Removing {pattern} ({count})")
            for f in matches:
                os.remove(f)

        has_day = os.path.exists(dayfile)
        if count == 0 and has_day:
            with zipfile.ZipFile(dayfile) as z:
                count = sum(not info.is_dir() for info in z.infolist())
            links = ""
        else:
            links = f'<a href="{y}/{m}/{d}/">Directory</a>'

        nbytes = os.path.getsize(dayfile) if has_day else 0
        if has_day and iso < TODAY:
            links += (
                ("\n" if links else "")
                + f'<a href="{y}/{m}/{d}/{type_}-{iso}.zip">Download day</a> (<span class="size">{{{{ byteshuman }}}}</span>)'
            )

        rows.append(
            {
                "date": f"{y}-{m}-{d}",
                "files": count,
                "value": f"{count:,}",
                "bytes": nbytes,
                "byteshuman": human_bytes(nbytes),
                "links": links,
            }
        )

    if os.path.isdir(WEBDIR):
        charts = {
            "files": "<strong>%d %B %Y</strong>\nFiles: <strong>{{ value }}</strong>\n{{ links }}",
            "bytes": "<strong>%d %B %Y</strong>\nFiles: <strong>{{ files }}</strong>\n{{ links }}",
        }
        for key, tooltip in charts.items():
            path = os.path.join(WEBDIR, f"{type_}-{key}.svg")
            print(f"Save SVG {path}")
            write(path, calendar_svg(rows, key, tooltip))
