"""QR code generation."""
from __future__ import annotations

import io
import qrcode


def generate_qr(text: str) -> str:
    """Generate ASCII QR code string for terminal display."""
    qr = qrcode.QRCode()
    qr.add_data(text)
    qr.make(fit=True)
    buf = io.StringIO()
    qr.print_ascii(tty=True, invert=False, out=buf)
    return buf.getvalue()


def generate_qr_image(text: str, path: str) -> None:
    """Generate QR code as PNG image."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)
