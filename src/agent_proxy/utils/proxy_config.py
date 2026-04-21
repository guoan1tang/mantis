"""macOS system proxy auto-configuration."""
from __future__ import annotations

import subprocess


def set_system_proxy(host: str, port: int) -> bool:
    """Set macOS system HTTP/HTTPS proxy."""
    try:
        result = subprocess.run(
            ["networksetup", "-getdefaultnetworkservice"],
            capture_output=True, text=True, timeout=5,
        )
        service = result.stdout.strip().replace("Network Service: ", "")
        if not service:
            service = "Wi-Fi"

        subprocess.run(
            ["networksetup", "-setwebproxy", service, host, str(port)],
            capture_output=True, timeout=5,
        )
        subprocess.run(
            ["networksetup", "-setsecurewebproxy", service, host, str(port)],
            capture_output=True, timeout=5,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def clear_system_proxy() -> bool:
    """Clear macOS system proxy."""
    try:
        result = subprocess.run(
            ["networksetup", "-getdefaultnetworkservice"],
            capture_output=True, text=True, timeout=5,
        )
        service = result.stdout.strip().replace("Network Service: ", "")
        if not service:
            service = "Wi-Fi"

        subprocess.run(
            ["networksetup", "-setwebproxystate", service, "off"],
            capture_output=True, timeout=5,
        )
        subprocess.run(
            ["networksetup", "-setsecurewebproxystate", service, "off"],
            capture_output=True, timeout=5,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False
