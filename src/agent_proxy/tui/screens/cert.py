"""Certificate installation guide screen."""
from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.containers import Center
from textual.binding import Binding


class CertScreen(Screen):
    """Guide user through CA certificate installation."""

    BINDINGS = [Binding("escape", "app.pop_screen", "Continue")]

    def compose(self):
        yield Center(
            Static(
                "[bold yellow]CA Certificate Setup Required[/bold yellow]\n\n"
                "Agent Proxy uses a self-signed CA certificate to intercept HTTPS traffic.\n\n"
                "[bold]macOS:[/bold]\n"
                "  1. The certificate is at: ~/.mitmproxy/mitmproxy-ca-cert.pem\n"
                "  2. Open Keychain Access and import the certificate\n"
                "  3. Double-click the certificate → Trust → Always Trust\n\n"
                "[bold]iPhone/iPad:[/bold]\n"
                "  1. Open Safari and go to: http://<your-ip>:8080\n"
                "  2. Download the CA certificate\n"
                "  3. Settings → Profile Downloaded → Install\n"
                "  4. Settings → General → About → Certificate Trust Settings → Enable\n\n"
                "[bold]Android:[/bold]\n"
                "  1. Open browser: http://<your-ip>:8080\n"
                "  2. Download CA certificate\n"
                "  3. Settings → Security → Install from storage\n\n"
                "[dim]Press Escape to continue to the main screen[/dim]",
                id="cert_info",
            )
        )
        yield Footer()
