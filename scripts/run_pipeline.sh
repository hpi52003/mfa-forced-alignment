#!/usr/bin/env bash
# Full pipeline for Linux/macOS. Run from the project folder inside the conda env:
#   conda activate aligner && bash scripts/run_pipeline.sh
# These are the same commands that were run manually (on Windows) for the report.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== 1. Download models"
mfa model download acoustic english_us_arpa
mfa model download dictionary english_us_arpa
mfa model download g2p english_us_arpa
mfa model download acoustic english_mfa
mfa model download dictionary english_mfa

echo "== 2. Prepare corpus"
python scripts/prepare_corpus.py --raw raw_data --out corpus

echo "== 3. Validate (reports out-of-vocabulary words)"
mfa validate corpus english_us_arpa english_us_arpa --clean

echo "== 4. G2P for unknown words"
mfa g2p corpus english_us_arpa custom_oov.dict --dictionary_path english_us_arpa

echo "== 5. Build custom dictionary (stock + G2P + manual override for wbur)"
python scripts/build_dictionary.py --g2p custom_oov.dict --overrides manual_overrides.dict --out custom_dictionary.dict

echo "== 6. Align with the custom dictionary"
mfa align corpus custom_dictionary.dict english_us_arpa output/custom_dict --clean --single_speaker

echo "== 7. Align with the second model (english_mfa)"
mfa align corpus english_mfa english_mfa output/english_mfa --clean --single_speaker

echo "Done. TextGrids are in output/custom_dict and output/english_mfa"
