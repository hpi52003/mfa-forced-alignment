#!/usr/bin/env python3
"""Build custom_dictionary.dict = stock dictionary + G2P output + manual overrides.

Words listed in the overrides file replace any G2P-generated lines for the same word
(used for 'wbur', which G2P pronounces badly because it is read letter by letter).

Usage:
  python scripts/build_dictionary.py --g2p custom_oov.dict \
         --overrides manual_overrides.dict --out custom_dictionary.dict
The stock english_us_arpa.dict is located automatically under ~/Documents/MFA,
or pass --stock <path>.
"""
import argparse, glob, os
from pathlib import Path


def find_stock():
    home = Path.home()
    pats = [home / "Documents" / "MFA" / "pretrained_models" / "dictionary" / "english_us_arpa.dict",
            home / "MFA" / "pretrained_models" / "dictionary" / "english_us_arpa.dict"]
    for p in pats:
        if p.exists():
            return p
    hits = glob.glob(str(home / "**" / "english_us_arpa.dict"), recursive=True)
    if hits:
        return Path(hits[0])
    raise SystemExit("Stock dictionary not found. Run: mfa model download dictionary english_us_arpa")


def word_of(line):
    parts = line.strip().split()
    return parts[0].lower() if parts else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stock")
    ap.add_argument("--g2p", required=True)
    ap.add_argument("--overrides", required=True)
    ap.add_argument("--out", default="custom_dictionary.dict")
    a = ap.parse_args()

    stock = Path(a.stock) if a.stock else find_stock()
    over = [l.rstrip("\n") for l in open(a.overrides, encoding="utf-8") if l.strip()]
    over_words = {word_of(l) for l in over}
    g2p = [l.rstrip("\n") for l in open(a.g2p, encoding="utf-8")
           if l.strip() and word_of(l) not in over_words]

    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        text = open(stock, encoding="utf-8").read()
        f.write(text if text.endswith("\n") else text + "\n")
        for l in g2p + over:
            f.write(l + "\n")
    print(f"stock: {stock}")
    print(f"added {len(g2p)} G2P lines and {len(over)} manual lines -> {a.out}")


if __name__ == "__main__":
    main()
