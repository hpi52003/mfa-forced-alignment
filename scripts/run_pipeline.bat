@echo off
REM Full pipeline for Windows. Run from the project folder inside the conda env:
REM   conda activate aligner
REM   scripts\run_pipeline.bat
REM These are the same commands that were run manually for the report.
pushd "%~dp0.."
set ERR=0

echo == 1. Download models
mfa model download acoustic english_us_arpa
mfa model download dictionary english_us_arpa
mfa model download g2p english_us_arpa
mfa model download acoustic english_mfa
mfa model download dictionary english_mfa

echo == 2. Prepare corpus (convert audio, clean transcripts)
python scripts\prepare_corpus.py --raw raw_data --out corpus || goto :fail

echo == 3. Validate (reports out-of-vocabulary words; takes about 13 minutes)
mfa validate corpus english_us_arpa english_us_arpa --clean

echo == 4. G2P for unknown words
mfa g2p corpus english_us_arpa custom_oov.dict --dictionary_path english_us_arpa || goto :fail

echo == 5. Build custom dictionary (stock + G2P + manual override for wbur)
python scripts\build_dictionary.py --g2p custom_oov.dict --overrides manual_overrides.dict --out custom_dictionary.dict || goto :fail

echo == 6. Align with the custom dictionary
mfa align corpus custom_dictionary.dict english_us_arpa output\custom_dict --clean --single_speaker || goto :fail

echo == 7. Align with the second model (english_mfa) for comparison
mfa align corpus english_mfa english_mfa output\english_mfa --clean --single_speaker || goto :fail

echo Done. TextGrids are in output\custom_dict and output\english_mfa
popd
exit /b 0

:fail
echo A step failed. See the message above.
popd
exit /b 1
