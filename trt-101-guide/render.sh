#!/bin/zsh
# Print the LIVE page, not the local file — the live page applies whatever has been
# published in the editor, so the PDF always matches what Julian actually sees.
set -e
cd ~/trt-guy-101-guide
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --no-pdf-header-footer --virtual-time-budget=20000 \
  --print-to-pdf=raw.pdf "https://trt-guy-101-guide.vercel.app/" 2>/dev/null
python3 stamp.py
rm -rf fin && mkdir fin
python3 -c "
from pypdf import PdfReader,PdfWriter
r=PdfReader('TRT-Guy-TRT-101-Guide.pdf')
for i,p in enumerate(r.pages):
    w=PdfWriter(); w.add_page(p); w.write(f'fin/p{i+1:02d}.pdf')"
for f in fin/*.pdf; do sips -s format png -Z 1100 "$f" --out "${f%.pdf}.png" >/dev/null 2>&1; done
