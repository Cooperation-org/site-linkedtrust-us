"""Render the LevelUp share images from design/levelup-flyer.html.

    pip install segno playwright && playwright install chromium
    python design/build_levelup_art.py

Both are build-time only and stay out of requirements.txt so the running site
does not carry a browser.

Writes static/img/levelup/. The QR encodes the registration URL itself, so it
keeps working with no shortener in the path.
"""
import base64
import re
import sys
from io import BytesIO
from pathlib import Path

import segno
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'static' / 'img' / 'levelup'
REGISTER_URL = 'https://linkedtrust.us/levelup/'

# Boards that also ship as PDF: the contact links stay clickable there.
PDFS = [
    ('levelup-poster.html', 'poster', 'levelup-poster.pdf', 1080, 1350),
]

BOARDS = [
    ('levelup-flyer.html', 'portrait', 'levelup-flyer-1080x1350.png', 1080, 1350),
    ('levelup-flyer.html', 'landscape', 'levelup-banner-1200x627.png', 1200, 627),
    ('levelup-flyer.html', 'qrboard', 'levelup-qr.png', 888, 888),
    ('levelup-poster.html', 'poster', 'levelup-poster-1080x1350.png', 1080, 1350),
]


def qr_png(scale=12):
    """The registration URL as a QR, highest error correction so the leaf mark
    in the middle does not stop a phone reading it."""
    buf = BytesIO()
    segno.make(REGISTER_URL, error='h').save(
        buf, kind='png', scale=scale, border=4, dark='#101014', light='#ffffff')
    return buf.getvalue()


def data_uri(payload, mime):
    return f'data:{mime};base64,' + base64.b64encode(payload).decode('ascii')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    qr = qr_png()
    logo = data_uri((ROOT / 'static' / 'img' / 'logo.svg').read_bytes(), 'image/svg+xml')
    photo = data_uri((ROOT / 'design' / 'levelup-poster-photo.jpg').read_bytes(), 'image/jpeg')

    def stage(source):
        html = (ROOT / 'design' / source).read_text()
        html = html.replace('QR_SRC', data_uri(qr, 'image/png'))
        html = html.replace('LOGO_SRC', logo).replace('PHOTO_SRC', photo)
        html = re.sub(r"url\('\.\./static/fonts/([^']+)'\)",
                      lambda m: f"url('{(ROOT / 'static' / 'fonts' / m.group(1)).as_uri()}')", html)
        path = ROOT / 'design' / f'.{source}.rendered.html'
        path.write_text(html)
        return path

    staged = {source: stage(source) for source in {b[0] for b in BOARDS}}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(device_scale_factor=2)
            loaded = None
            for source, board, name, width, height in BOARDS:
                if source != loaded:
                    page.goto(staged[source].as_uri())
                    page.wait_for_timeout(400)
                    loaded = source
                box = page.locator('#' + board).bounding_box()
                if round(box['width']) != width or round(box['height']) != height:
                    sys.exit(f'{board} is {box["width"]}x{box["height"]}, expected {width}x{height}')
                spill = page.evaluate(
                    '''(id) => {
                        const el = document.querySelector('#' + id + ' .content');
                        if (!el) return 0;
                        const last = el.lastElementChild;
                        const band = document.querySelector('#' + id + ' .band');
                        if (!last || !band) return 0;
                        return Math.round(last.getBoundingClientRect().bottom
                                          - band.getBoundingClientRect().top);
                    }''', board)
                if spill > 0:
                    sys.exit(f'{board}: content runs {spill}px under the contact band')
                page.locator('#' + board).screenshot(path=str(OUT / name))
                print('wrote', OUT / name)

            for source, board, name, width, height in PDFS:
                page.goto(staged[source].as_uri())
                page.add_style_tag(content=(
                    f'body {{ margin: 0; background: #fff; }} '
                    f'#{board} {{ margin: 0; }}'))
                page.wait_for_timeout(300)
                page.pdf(path=str(OUT / name), print_background=True,
                         width=f'{width}px', height=f'{height}px',
                         margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'})
                print('wrote', OUT / name)
            browser.close()
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
