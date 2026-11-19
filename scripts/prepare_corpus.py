#!/usr/bin/env python3
"""Prepare the raw dataset for MFA.
Usage: python scripts/prepare_corpus.py --raw raw_data --out corpus
"""
import argparse, re, subprocess
from pathlib import Path


def clean(text: str) -> str:
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"(\w)-\s+(\w)", r"\1 \2", text)   # "seventy- six" -> "seventy six"
    text = text.lower()
    text = text.replace("de-politicize", "depoliticize")
    text = text.replace("s.j.c.", "s j c")             # initialism -> letters
    text = re.sub(r"[^a-z' ]", " ", text)              # drop punctuation/digits
    return re.sub(r"\s+", " ", text).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw_data")
    ap.add_argument("--out", default="corpus")
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    txts = {p.stem.lower(): p for p in (raw / "transcripts").iterdir()
            if p.suffix.lower() == ".txt"}

    for wav in sorted((raw / "wav").glob("*.wav")):
        stem = wav.stem
        if stem.lower() not in txts:
            print(f"[skip] no transcript for {stem}")
            continue
        dst = out / f"{stem}.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(dst)],
                       check=True)
        text = clean(txts[stem.lower()].read_text(errors="ignore"))
        (out / f"{stem}.txt").write_text(text + "\n")
        print(f"[ok] {stem}: {text[:60]}...")


if __name__ == "__main__":
    main()
