#!/bin/zsh
# Rebuild the fertility guide PDF from the LIVE page, so it always matches what
# Julian last published in the Control Center. Run it after every publish.
set -e
cd "$(dirname "$0")"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --no-pdf-header-footer --virtual-time-budget=20000 \
  --print-to-pdf=raw.pdf "https://trt-guy.com/fertility-guide/guide/" 2>/dev/null
python3 stamp.py
rm -f raw.pdf
