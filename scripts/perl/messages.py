"""Coloured terminal messages (port of scripts/perl/lib/lib.pl).

Colours are written inline as tags, e.g. msg("Saved <cyan>file.svg<none>\\n").
"""

import re
import sys

COLOURS = {
    "black": "\033[0;30m",
    "red": "\033[0;31m",
    "green": "\033[0;32m",
    "yellow": "\033[0;33m",
    "blue": "\033[0;34m",
    "magenta": "\033[0;35m",
    "cyan": "\033[0;36m",
    "white": "\033[0;37m",
    "none": "\033[0m",
}
TAG = re.compile(r"< ?(" + "|".join(COLOURS) + r") ?>")


def msg(text, stream=sys.stdout):
    stream.write(TAG.sub(lambda m: COLOURS[m[1]], text))


def error(text):
    msg(re.sub(r"^(\s*)", r"\1<red>ERROR:<none> ", text, count=1), sys.stderr)


def warning(text):
    msg(re.sub(r"^(\s*)", r"\1<yellow>WARNING:<none> ", text, count=1), sys.stderr)
