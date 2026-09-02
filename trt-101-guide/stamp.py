from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import io

MM = 72/25.4
W, H = 595.276, 841.89          # A4 points
L, R = 16*MM, W-16*MM

src = PdfReader('raw.pdf')
out = PdfWriter()
n = len(src.pages)

for i, page in enumerate(src.pages):
    if i > 0:                                   # no footer on the cover
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=(W, H))
        c.setStrokeColor(HexColor('#e2e6ec')); c.setLineWidth(.7)
        c.line(L, 44, R, 44)
        c.setFillColor(HexColor('#a7aeb9'))
        c.setFont('Helvetica-Bold', 6.5)
        t = c.beginText(L, 32); t.setCharSpace(1.1); t.textOut('TRT GUY'); c.drawText(t)
        title = ''
        wt = c.stringWidth(title, 'Helvetica-Bold', 6.5) + 1.1*(len(title)-1)
        t = c.beginText(R-26-wt, 32); t.setCharSpace(1.1); t.textOut(title); c.drawText(t)
        c.setFillColor(HexColor('#1a5cff')); c.setFont('Helvetica-Bold', 8)
        c.drawRightString(R, 31.4, f'{i+1:02d}')
        c.save(); buf.seek(0)
        page.merge_page(PdfReader(buf).pages[0])
    out.add_page(page)

out.add_metadata({
    '/Title': 'The TRT 101 Guide',
    '/Author': 'TRT Guy',
    '/Subject': 'How to Get the Most Out of Testosterone Replacement Therapy',
    '/Keywords': 'TRT, testosterone, TRT Guy',
    '/Creator': 'TRT Guy',
})
out.write('TRT-Guy-TRT-101-Guide.pdf')
print('stamped', n, 'pages')
