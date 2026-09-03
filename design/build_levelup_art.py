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

BOARDS = [
    ('portrait', 'levelup-flyer-1080x1350.png', 1080, 1350),
    ('landscape', 'levelup-banner-1200x627.png', 1200, 627),
]


def qr_png(scale=12):
    """The registration URL as a QR, highest error correction so the leaf mark
    in the middle does not stop a phone reading it."""
    buf = BytesIO()
    segno.make(REGISTER_URL, error='h').save(
        buf, kind='png', scale=scale, border=2, dark='#101014', light='#ffffff')
    return buf.getvalue()


def data_uri(payload, mime):
    return f'data:{mime};base64,' + base64.b64encode(payload).decode('ascii')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    qr = qr_png()
    (OUT / 'levelup-qr.png').write_bytes(qr)

    html = (ROOT / 'design' / 'levelup-flyer.html').read_text()
    html = html.replace('QR_SRC', data_uri(qr, 'image/png'))
    html = html.replace('LOGO_SRC', data_uri((ROOT / 'static' / 'img' / 'logo.svg').read_bytes(), 'image/svg+xml'))
    html = re.sub(r"url\('\.\./static/fonts/([^']+)'\)",
                  lambda m: f"url('{(ROOT / 'static' / 'fonts' / m.group(1)).as_uri()}')", html)

    staged = ROOT / 'design' / '.levelup-flyer.rendered.html'
    staged.write_text(html)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(device_scale_factor=2)
            page.goto(staged.as_uri())
            page.wait_for_timeout(400)
            for board, name, width, height in BOARDS:
                box = page.locator('#' + board).bounding_box()
                if round(box['width']) != width or round(box['height']) != height:
                    sys.exit(f'{board} is {box["width"]}x{box["height"]}, expected {width}x{height}')
                page.locator('#' + board).screenshot(path=str(OUT / name))
                print('wrote', OUT / name)
            browser.close()
    finally:
        staged.unlink(missing_ok=True)
    print('wrote', OUT / 'levelup-qr.png')


if __name__ == '__main__':
    main()
