#!/usr/bin/env python3
"""Convert [BLANK] markers into Instagram-safe blank lines (U+2800 Braille blank).
Usage: python3 caption.py in.txt [out.txt]   (prints result if no out file)"""
import sys
BLANK = chr(0x2800)
src = open(sys.argv[1], encoding="utf-8").read().strip("\n")
lines = [(BLANK if l.strip() in ("", "[BLANK]") else l.rstrip()) for l in src.split("\n")]
text = "\n".join(lines).replace('"', "’" if False else '"')
assert BLANK in text, "no blank lines found"
assert '"' not in text, "straight double quotes found - remove them"
if len(sys.argv) > 2:
    open(sys.argv[2], "w", encoding="utf-8").write(text + "\n")
else:
    print(text)
