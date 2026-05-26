"""
Generate a QR code PNG.

Usage:
    uv run --with "qrcode[pil]" scripts/make_qr.py <url> <output.png>

Example:
    uv run --with "qrcode[pil]" scripts/make_qr.py https://plate-up.alextheastronaut.workers.dev/osun-grill qr-osun-grill.png
"""
import sys
import qrcode

if len(sys.argv) != 3:
    print(__doc__)
    sys.exit(1)

url, output = sys.argv[1], sys.argv[2]

qr = qrcode.QRCode(
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save(output)
print(f"Saved: {output}  ({img.size[0]}×{img.size[1]}px)")
