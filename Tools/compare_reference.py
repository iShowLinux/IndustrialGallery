"""Side-by-side comparison deliverable: reference vs rendered shot.

Produces a wipe slider, a difference overlay with a numeric mean, and a
difference heat map. A high score usually means the CAMERA is in the wrong
place, not that the modelling is wrong -- check the camera first.
"""
from pathlib import Path
import base64
import io
import json

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = Path('C:/Users/mrjul/Downloads/5fa4f58c-618c-43ed-90d1-785c8f010b95.jpg')
REFERENCE_CROP = (0, 47, 1280, 676)
SHOTS = ROOT / 'Saved/Screenshots/WindowsEditor'
OUT = ROOT / 'Saved/ReferenceVerification'
SIZE = (1280, 629)


def data_uri(image, fmt='PNG'):
    buffer = io.BytesIO()
    image.save(buffer, fmt)
    return 'data:image/%s;base64,%s' % (fmt.lower(), base64.b64encode(buffer.getvalue()).decode())


def score(difference):
    """0-8 excellent, 20-45 fair, 45+ the camera is in the wrong place."""
    mean = ImageStat.Stat(difference).mean[0]
    if mean <= 8:
        band = 'excellent'
    elif mean <= 20:
        band = 'good'
    elif mean <= 45:
        band = 'fair - check framing and light levels'
    else:
        band = 'poor - verify camera position/yaw/pitch/FOV before touching materials'
    return round(mean, 2), band


def main():
    reference = Image.open(REFERENCE).convert('RGB').crop(REFERENCE_CROP).resize(SIZE, Image.LANCZOS)
    rows = []
    for path in sorted(SHOTS.glob('Reference_*.png')):
        shot = Image.open(path).convert('RGB').resize(SIZE, Image.LANCZOS)
        difference = ImageChops.difference(reference, shot)
        mean, band = score(difference)
        amplified = difference.point(lambda v: min(255, v * 4))
        rows.append({'name': path.stem, 'difference_mean': mean, 'band': band,
                     'shot': data_uri(shot), 'difference': data_uri(amplified),
                     'metrics': json.loads((OUT / 'exposure.json').read_text())['shots']
                     .get(path.name, {}).get('metrics', {})})
    html = ['<!doctype html><meta charset="utf-8"><title>Reference comparison</title>',
            '<style>body{background:#111;color:#eee;font:14px system-ui;margin:24px}',
            'figure{margin:0 0 32px}h2{font-size:16px;margin:20px 0 6px}',
            '.wipe{position:relative;width:1280px;max-width:100%;line-height:0}',
            '.wipe img{width:100%;display:block}',
            '.wipe .top{position:absolute;inset:0;width:50%;overflow:hidden}',
            '.wipe .top img{width:1280px;max-width:none}',
            'input[type=range]{width:1280px;max-width:100%}',
            'table{border-collapse:collapse;margin-top:8px}td,th{border:1px solid #444;padding:4px 10px;text-align:left}',
            '.ref{border:1px solid #666}</style>',
            '<h1>Reference vs render</h1>',
            '<p>Difference mean is out of 255 on 8-bit luminance. Scale: '
            '<b>0-8 excellent</b>, 8-20 good, <b>20-45 fair</b>, <b>45+ camera is in the wrong place</b>.</p>',
            '<figure><h2>Reference (target)</h2><img class="ref" src="%s"></figure>' % data_uri(reference)]
    for index, row in enumerate(rows):
        html.append('<figure><h2>%s &mdash; difference %s (%s)</h2>' % (row['name'], row['difference_mean'], row['band']))
        html.append('<div class="wipe"><img src="%s"><div class="top" id="top%d"><img src="%s"></div></div>'
                    % (row['shot'], index, data_uri(reference)))
        html.append('<input type="range" min="0" max="100" value="50" oninput="document.getElementById(\'top%d\').style.width=this.value+\'%%\'">' % index)
        html.append('<h2>Difference (4x amplified)</h2><img src="%s">' % row['difference'])
        html.append('<table><tr><th>metric</th><th>render</th><th>reference</th></tr>')
        reference_metrics = json.loads((OUT / 'exposure.json').read_text())['reference']
        for key in ('mean', 'std', 'dark_pct', 'crushed_pct', 'clipped_pct'):
            html.append('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (key, row['metrics'].get(key), reference_metrics.get(key)))
        html.append('</table></figure>')
    destination = OUT / 'comparison.html'
    destination.write_text('\n'.join(html), encoding='utf-8')
    print(json.dumps([{k: v for k, v in row.items() if k in ('name', 'difference_mean', 'band')} for row in rows], indent=2))
    print('wrote', destination)


if __name__ == '__main__':
    main()
