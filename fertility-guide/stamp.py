# Stamps a footer rule + page number onto raw.pdf → TRT-Guy-Fertility-Guide.pdf.
# Same treatment as the TRT 101 guide, so the two lead magnets look like a set.
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import io, os

MM = 72 / 25.4
W, H = 595.276, 841.89                 # A4 points
L, R = 16 * MM, W - 16 * MM
HERE = os.path.dirname(os.path.abspath(__file__))

src = PdfReader(os.path.join(HERE, 'raw.pdf'))
out = PdfWriter()

for i, page in enumerate(src.pages):
    if i > 0:                          # the cover carries no footer
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(W, H))
        c.setStrokeColor(HexColor('#e2e6ec')); c.setLineWidth(.7)
        c.line(L, 44, R, 44)
        c.setFillColor(HexColor('#a7aeb9')); c.setFont('Helvetica-Bold', 6.5)
        t = c.beginText(L, 32); t.setCharSpace(1.1); t.textOut('TRT GUY'); c.drawText(t)
        c.setFillColor(HexColor('#1a5cff')); c.setFont('Helvetica-Bold', 8)
        c.drawRightString(R, 31.4, '%02d' % (i + 1))
        c.save(); buf.seek(0)
        page.merge_page(PdfReader(buf).pages[0])
    out.add_page(page)

dest = os.path.join(HERE, 'TRT-Guy-Fertility-Guide.pdf')
with open(dest, 'wb') as f:
    out.write(f)
print('stamped %d pages → %s' % (len(src.pages), dest))
