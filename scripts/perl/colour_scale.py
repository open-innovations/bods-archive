"""Named colour scales for charts (port of OpenInnovations::ColourScale)."""

import re

NAMED_SCALES = {
    "Viridis": "#440154 0%, #482878 11.1%, #3e4989 22.2%, #31688e 33.333%, #26828e 44.444%, #1f9e89 55.555%, #35b779 66.666%, #6ece58 77.777%, #b5de2b 88.888%, #fde725 100%",
    "Viridis-light": "rgb(122,76,139) 0%, rgb(124,109,168) 12.5%, rgb(115,138,177) 25%, rgb(107,164,178) 37.5%, rgb(104,188,170) 50%, rgb(133,211,146) 62.5%, rgb(189,229,97) 75%, rgb(254,240,65) 87.5%, rgb(254,240,65) 100%",
    "Cividis": "#00224e 0%, #123570 11.1%, #3b496c 22.222%, #575d6d 33.333%, #707173 44.444%, #8a8678 55.555%, #a59c74 66.666%, #c3b369 77.777%, #e1cc55 88.888%, #fee838 100%",
    "Heat": "rgb(0,0,0) 0%, rgb(128,0,0) 25%, rgb(255,128,0) 50%, rgb(255,255,128) 75%, rgb(255,255,255) 100%",
    "Inferno": "#000004 0%, #1b0c41 11.1%, #4a0c6b 22.222%, #781c6d 33.333%, #a52c60 44.444%, #cf4446 55.555%, #ed6925 66.666%, #fb9b06 77.777%, #f7d13d 88.888%, #fcffa4 100%",
    "Magma": "#000004 0%, #180f3d 11.1%, #440f76 22.222%, #721f81 33.333%, #9e2f7f 44.444%, #cd4071 55.555%, #f1605d 66.666%, #fd9668 77.777%, #feca8d 88.888%, #fcfdbf 100%",
    "Mako": "#0B0405 0%, #357BA2 50%, #DEF5E5 100%",
    "Planck": "rgb(0,0,255) 0%, rgb(0,112,255) 16.666%, rgb(0,221,255) 33.3333%, rgb(255,237,217) 50%, rgb(255,180,0) 66.666%, rgb(255,75,0) 100%",
    "Plasma": "#0d0887 0%, #46039f 11.1%, #7201a8 22.222%, #9c179e 33.333%, #bd3786 44.444%, #d8576b 55.555%, #ed7953 66.666%, #fb9f3a 77.777%, #fdca26 88.888%, #f0f921 100%",
    "Rocket": "#03051A 0%, #CB1B4F 50%, #FAEBDD 100%",
    "Turbo": "#30123b 0%, #4145ab 7.143%, #4675ed 14.286%, #39a2fc 21.429%, #1bcfd4 28.571%, #24eca6 35.714%, #61fc6c 42.857%, #a4fc3b 50%, #d1e834 57.143%, #f3c63a 64.286%, #fe9b2d 71.429%, #f36315 78.571%, #d93806 85.714%, #b11901 92.857%, #7a0402 100%",
    "PiPG": "#8e0152 0%, #c51b7d 10%, #de77ae 20%, #f1b6da 30%, #fde0ef 40%, #f7f7f7 50%, #e6f5d0 60%, #b8e186 70%, #7fbc41 80%, #4d9221 90%, #276419 100%",
    "PRGn": "#40004b 0%, #762a83 10%, #9970ab 20%, #c2a5cf 30%, #e7d4e8 40%, #f7f7f7 50%, #d9f0d3 60%, #a6dba0 70%, #5aae61 80%, #1b7837 90%, #00441b 100%",
    "PuOr": "#7f3b08 0%, #b35806 10%, #e08214 20%, #fdb863 30%, #fee0b6 40%, #f7f7f7 50%, #d8daeb 60%, #b2abd2 70%, #8073ac 80%, #542788 90%, #2d004b 100%",
    "RdBu": "#67001f 0%, #b2182b 10%, #d6604d 20%, #f4a582 30%, #fddbc7 40%, #f7f7f7 50%, #d1e5f0 60%, #92c5de 70%, #4393c3 80%, #2166ac 90%, #053061 100%",
}
STOP = re.compile(r"(#[A-Fa-f0-9]{6}|[a-z]{3,4}\([^)]+\)) ([0-9.]+)%?")


def num(x):
    """Format a number the way Perl prints it (so output matches the old charts)."""
    return "%.15g" % x


def parse_colour(c):
    if c.startswith("#"):
        return [int(c[i : i + 2], 16) for i in (1, 3, 5)] + [1]
    parts = [float(p) for p in c[c.index("(") + 1 : -1].split(",")]
    return parts + [1] if len(parts) == 3 else parts


def parse_stops(gradient):
    """List of (percent, [r, g, b, alpha]), ending at the first 100% stop."""
    stops = []
    for colour, pc in STOP.findall(gradient):
        stops.append((float(pc), parse_colour(colour)))
        if float(pc) == 100:
            break
    if not stops:
        raise ValueError(f'Can\'t parse gradient string "{gradient}"')
    return stops


class ColourScale:
    def __init__(self, scale="Viridis", empty="#dfdfdf"):
        if scale not in NAMED_SCALES:
            raise ValueError(f'No colour scale named: "{scale}"')
        self.scale = scale
        self.empty = empty
        self.stops = parse_stops(NAMED_SCALES[scale])

    def get_colour(self, v):
        """Colour for v between 0 and 1, as an rgba() string."""
        stops = self.stops
        v2 = 100 * v
        if len(stops) == 1:
            r, g, b, _ = stops[0][1]
            rgba = [r, g, b, "%.3f" % (v2 / 100)]
        elif v2 <= stops[0][0]:
            rgba = stops[0][1]
        elif v2 >= stops[-1][0]:
            rgba = stops[-1][1]
        else:
            for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
                if p0 <= v2 <= p1:
                    f = 100 * (v2 - p0) / (p1 - p0) / 100  # same arithmetic as the Perl
                    rgba = [a + (b - a) * f for a, b in zip(c0, c1)]
                    break
        return (
            "rgba(" + ",".join(x if isinstance(x, str) else num(x) for x in rgba) + ")"
        )
