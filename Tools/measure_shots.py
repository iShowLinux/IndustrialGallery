"""Measure render exposure from PNG/JPG shots. No third-party deps beyond Pillow."""
from pathlib import Path
import json
import sys

from PIL import Image, ImageStat

REFERENCE = Path('C:/Users/mrjul/Downloads/5fa4f58c-618c-43ed-90d1-785c8f010b95.jpg')
# Reference JPEG has a letterboxed border; crop to the image area before comparing.
REFERENCE_CROP = (0, 47, 1280, 676)
TARGETS = {'mean': (60, 130), 'std': (25, 45), 'dark_pct': (0, 25),
           'crushed_pct': (0, 5), 'clipped_pct': (0, 5)}
# Distribution targets, measured from the reference itself. Matching only the
# mean hides a globally over-bright render: a frame can average 110 and still
# have 19% of pixels above 200 where the reference has 4%.
DISTRIBUTION = {'p50': (55, 90), 'p90': (125, 170), 'bright_pct': (2, 8)}


def measure(path, crop=None):
    image = Image.open(path).convert('L')
    if crop:
        image = image.crop(crop)
    histogram = image.histogram()
    total = sum(histogram)
    stat = ImageStat.Stat(image)
    pixels = list(image.getdata())
    pixels.sort()
    def percentile(p):
        return pixels[min(len(pixels) - 1, int(len(pixels) * p / 100))]
    return {
        'mean': round(stat.mean[0], 2),
        'std': round(stat.stddev[0], 2),
        'dark_pct': round(sum(histogram[:32]) / total * 100, 2),
        'crushed_pct': round(sum(histogram[:9]) / total * 100, 2),
        'clipped_pct': round(sum(histogram[250:]) / total * 100, 2),
        'p50': percentile(50),
        'p90': percentile(90),
        'bright_pct': round(sum(histogram[200:]) / total * 100, 2),
    }


def verdict(values, targets=None):
    """Report which metrics are outside the target band; never claims 'looks fine'."""
    targets = targets or TARGETS
    return {k: ('ok' if lo <= values[k] <= hi else 'OUT')
            for k, (lo, hi) in targets.items()}


def main():
    root = Path('C:/Users/mrjul/Documents/IndustrialGallery')
    shots = sorted((root / 'Saved/Screenshots/WindowsEditor').glob('Reference_*.png'))
    if not shots:
        raise SystemExit('no shots found')
    report = {'shots': {}, 'reference': measure(REFERENCE, REFERENCE_CROP)}
    report['reference_verdict'] = verdict(report['reference'])
    report['reference_distribution'] = verdict(report['reference'], DISTRIBUTION)
    for path in shots:
        values = measure(path)
        report['shots'][path.name] = {
            'metrics': values,
            'verdict': verdict(values),
            'distribution': verdict(values, DISTRIBUTION),
        }
    out = root / 'Saved/ReferenceVerification/exposure.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    print('saved', out)


if __name__ == '__main__':
    sys.exit(main())
