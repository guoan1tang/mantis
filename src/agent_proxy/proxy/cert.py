"""CA certificate management."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def get_mitmproxy_cert_path() -> Path:
    """Get the default mitmproxy CA certificate path."""
    return Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"


def is_cert_installed_macos() -> bool:
    """Check if mitmproxy CA cert is trusted on macOS."""
    try:
        result = subprocess.run(
            ["security", "find-certificate", "-c", "mitmproxy", "-p"],
            capture_output=True, text=True, timeout=5,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def install_cert_macos(cert_path: Path) -> bool:
    """Install mitmproxy CA cert into macOS keychain."""
    try:
        result = subprocess.run(
            ["sudo", "security", "add-trusted-cert", "-d", "-r", "trustRoot",
             "-k", "/Library/Keychains/System.keychain", str(cert_path)],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def generate_cert_qr_code(host: str, port: int) -> str:
    """Generate QR code text for mitm.it certificate download."""
    return f"http://{host}:{port}"


def get_local_ip() -> str:
    """Get the machine's local IP address."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()
