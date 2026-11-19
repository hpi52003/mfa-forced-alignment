#!/usr/bin/env python3
r"""Quick self-check (about one minute). Run in the Miniforge Prompt, inside the aligner env,
from the project folder:   python scripts\check_setup.py
"""
import argparse, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
results = []


def report(name, status, detail=""):
    results.append(status)
    print(f"[{status}] {name}" + (f"  ({detail})" if detail else ""))


def run(cmd):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return 1, str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stock", help="path to english_us_arpa.dict (found automatically if omitted)")
    a = ap.parse_args()

    # 1. tools
    code, out = run(["mfa", "version"])
    report("mfa installed", "PASS" if code == 0 else "FAIL", out.splitlines()[-1] if out else "not found")
    code, out = run(["ffmpeg", "-version"])
    report("ffmpeg installed", "PASS" if code == 0 else "FAIL",
           out.splitlines()[0][:40] if out else "not found")

    # 2. files
    need = ["raw_data/wav", "raw_data/transcripts", "scripts/prepare_corpus.py",
            "scripts/build_dictionary.py", "manual_overrides.dict", "custom_oov.dict",
            "custom_dictionary.dict"]
    missing = [n for n in need if not (ROOT / n).exists()]
    report("required files present", "PASS" if not missing else "FAIL", ", ".join(missing))
    for m in ("custom_dict", "english_mfa"):
        n = len(list((ROOT / "output" / m).glob("*.TextGrid")))
        report(f"output/{m}: 6 TextGrids", "PASS" if n == 6 else "FAIL", f"found {n}")

    # 3. data preparation
    with tempfile.TemporaryDirectory() as tmp:
        code, out = run([sys.executable, str(ROOT / "scripts/prepare_corpus.py"),
                         "--raw", str(ROOT / "raw_data"), "--out", tmp])
        wavs, txts = len(list(Path(tmp).glob("*.wav"))), len(list(Path(tmp).glob("*.txt")))
        ok = code == 0 and wavs == 6 and txts == 6
        report("prepare_corpus.py: 6 wav + 6 txt", "PASS" if ok else "FAIL", f"{wavs} wav, {txts} txt")

        # 4. dictionary builder
        try:
            import build_dictionary as bd
            stock = Path(a.stock) if a.stock else bd.find_stock()
        except SystemExit:
            report("build_dictionary.py", "SKIP", "stock dictionary not found; run: mfa model download dictionary english_us_arpa")
            stock = None
        if stock:
            outp = Path(tmp) / "test_dictionary.dict"
            code, out = run([sys.executable, str(ROOT / "scripts/build_dictionary.py"), "--stock", str(stock),
                             "--g2p", str(ROOT / "custom_oov.dict"),
                             "--overrides", str(ROOT / "manual_overrides.dict"), "--out", str(outp)])
            if code != 0:
                report("build_dictionary.py runs", "FAIL", out[-120:])
            else:
                mine = sorted(outp.read_text(encoding="utf-8").splitlines())
                theirs = sorted((ROOT / "custom_dictionary.dict").read_text(encoding="utf-8").splitlines())
                report("build_dictionary.py matches custom_dictionary.dict",
                       "PASS" if mine == theirs else "FAIL", f"{len(mine)} vs {len(theirs)} lines")
                wb = [l for l in mine if l.split("\t")[0] == "wbur"]
                report("exactly one 'wbur' entry (manual override)", "PASS" if len(wb) == 1 else "FAIL",
                       f"{len(wb)} found")

    print()
    print("ALL CHECKS PASSED" if "FAIL" not in results else "SOME CHECKS FAILED: see FAIL lines above")
    sys.exit(1 if "FAIL" in results else 0)


if __name__ == "__main__":
    main()
