"""Calendar heatmap SVGs (port of OpenInnovations::CalendarChart).

Each year is a block of 7 rows (days of the week) by ~53 columns (weeks).
Tooltips are templates: strftime codes for the cell's date, plus {{ field }}
placeholders filled from that day's row.
"""

import re
from datetime import date, timedelta

from colour_scale import ColourScale
from messages import warning

DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}")
PLACEHOLDER = re.compile(r"\{\{ *([^}]+?) *\}\}")
DAY_LETTERS = "SMTWTFSS"  # indexed by ISO weekday (Mon=1 .. Sun=7)


def is_number(v):
    try:
        float(v)
        return not isinstance(v, bool)
    except (TypeError, ValueError):
        return False


def floor_week(d, start):
    """Go back to the start of d's week (start: 0=Sunday, 1=Monday ...)."""
    day = d.isoweekday() % 7
    return d - timedelta(days=(day - start) % 7)


def ceil_week(d, start):
    """Go forward to the end of d's week.

    Kept identical to the Perl, which overshoots when d's weekday number is
    before `start` (e.g. a Sunday with Monday weeks). That only adds a few
    transparent cells after 31 December.
    """
    day = d.isoweekday() % 7
    return d + timedelta(days=6 - abs(day - start))


def fill_tooltip(template, d, dat):
    text = d.strftime(template)
    while m := PLACEHOLDER.search(text):
        value = dat.get(m[1])
        text = re.sub(
            r"\{\{ *" + re.escape(m[1]) + r" *\}\}",
            lambda _: "" if value is None else str(value),
            text,
        )
    return text


def calendar_chart(
    data,
    key,
    value,
    tooltip=None,
    order="chronological",
    width=1080,
    scale="Viridis",
    defaultbg="#efefef",
    min_value=None,
    max_value=None,
    min_date=None,
    max_date=None,
    start_of_week=1,
):
    """Return an SVG string for rows of `data`, dated by `key` and coloured by `value`."""
    lo, hi = 1e100, -1e100
    first, last = "3000-01-01", "0000-01-01"
    days = {}
    d = ""
    for i, row in enumerate(data):
        if DATE.match(str(row.get(key, ""))):
            d = row[key]
            first, last = min(first, d), max(last, d)
        else:
            warning(f"Value for '{key}' in row {i} doesn't look like 0000-00-00\n")
        if is_number(row.get(value)):
            lo, hi = min(lo, row[value]), max(hi, row[value])
            if DATE.match(d):
                days[d] = row
    if is_number(min_value):
        lo = min_value
    if is_number(max_value):
        hi = max_value
    first = min_date if min_date and DATE.match(min_date) else first
    last = max_date if max_date and DATE.match(max_date) else last

    size = width / 56
    space = size * 2
    years = int(last[:4]) - int(first[:4]) + 1
    height = size * 7 * years + (space * (years - 1) if years > 0 else 0)
    opts = {
        "days": days,
        "min": lo,
        "max": hi,
        "size": float(f"{size:.2f}"),
        "startofweek": start_of_week,
        "colours": ColourScale(scale, empty=defaultbg),
        "value": value,
        "tooltip": tooltip,
        "defaultbg": defaultbg,
    }

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 {width:.2f} {height:.2f}" '
        'vector-effect="non-scaling-stroke" preserveAspectRatio="xMidYMin meet" overflow="visible" '
        'data-type="calendar-chart">'
        '<g class="data-layer" role="table">\n'
    )
    year_list = range(int(first[:4]), int(last[:4]) + 1)
    if order == "reverse":
        year_list = reversed(year_list)
    for i, year in enumerate(year_list):
        svg += f'\t<g class="year" role="row" aria-label="Year: {year}">\n'
        svg += build_year(year, (size * 7 + space) * i, opts)
        svg += "\t</g>\n"
    return svg + "</g>\n</svg>\n"


def build_year(year, oy, opts):
    size, start = opts["size"], opts["startofweek"]
    syear, eyear = date(year, 1, 1), date(year, 12, 31)
    sday, eday = floor_week(syear, start), ceil_week(eyear, start)

    # Year label (rotated) and day-of-week letters
    x, y = f"{size:.2f}", f"{oy + 3.5 * size:.2f}"
    svg = (
        f'\t\t<text class="year" x="{x}" y="{y}" transform="rotate(-90)" transform-origin="{x} {y}" '
        f'text-anchor="middle" font-size="{size * 1.5:.2f}" font-family="" dominant-baseline="middle">{year}</text>'
    )
    for i in range(7):
        letter = DAY_LETTERS[(sday + timedelta(days=i)).isoweekday()]
        svg += (
            f'\t\t<text class="day" x="{2.5 * size:.2f}" y="{oy + (i + 0.5) * size:.2f}" '
            f'dominant-baseline="middle" text-anchor="middle" font-size="{size * 0.75:.2f}" '
            f'font-family="">{letter}</text>\n'
        )

    # One cell per day
    template = opts["tooltip"] or "%d %b %Y\n{{ value }}"
    d = sday
    while d <= eday:
        dat = opts["days"].get(d.isoformat(), {})
        in_year = syear <= d <= eyear
        colour = opts["defaultbg"] or ""
        if not in_year:
            colour = "transparent"
        elif is_number(dat.get(opts["value"])):
            lo, hi = opts["min"], opts["max"]
            pc = 1 if hi == lo else (dat[opts["value"]] - lo) / (hi - lo)
            colour = opts["colours"].get_colour(pc)

        col = (d - sday).days // 7
        row = (d.isoweekday() - start) % 7
        text = fill_tooltip(template, d, dat)

        svg += f'\t\t<rect class="{"in-year" if in_year else "not-in-year"}{" has-value" if text else ""}"'
        if colour:
            svg += f' fill="{colour}"'
        svg += (
            f' role="cell" x="{3 * size + col * size:.2f}" y="{oy + row * size:.2f}" '
            f'width="{size:.2f}" height="{size:.2f}">'
        )
        if text:
            svg += f"<title>{text}</title>"
        svg += "</rect>\n"
        d += timedelta(days=1)
    return svg
