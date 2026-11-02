#!/usr/bin/env python3
"""Make daily zip archives, prune old 10s files and draw calendar charts for the BODS archive."""

import glob
import os
import shutil
import sys
import zipfile
from datetime import UTC, datetime, timedelta

from calendar_chart import calendar_chart
from messages import msg

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


# Rough number of days of disk left
write(
    f"{ARCHIVE}/free.txt", f"{int(shutil.disk_usage('/').free / (2 * 90e9 / 7))} days"
)

for type_, cfg in sorted(TYPES.items()):
    msg(f"Type: <green>{type_}<none>\n")
    base = f"{ARCHIVE}/{type_}"
    recent = None
    if "keep_days" in cfg:
        recent = (NOW - timedelta(days=cfg["keep_days"])).strftime("%Y%m%d")

    size = human_bytes(dir_size(base))
    msg(
        f"Save <yellow>{type_}<none> size (<green>{size}<none>) to <cyan>{base}/total-bytes.txt<none>\n"
    )
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
                msg(f"Create zip archive for <green>{y}-{m}-{d}<none>\n")
                with zipfile.ZipFile(dayfile, "w", zipfile.ZIP_STORED) as z:
                    for f in zips:
                        z.write(f, os.path.basename(f))

        # Count the 10s files (not the daily one) and remove them if too old
        matches = glob.glob(pattern)
        count = len(matches)
        if count and recent and iso < recent:
            msg(f"Removing {pattern} ({count})\n")
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
            msg(f"Save SVG <cyan>{path}<none>\n")
            write(
                path,
                calendar_chart(rows, "date", key, tooltip=tooltip, order="reverse"),
            )
