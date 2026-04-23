"""Top status bar widget."""
from textual.widgets import Static


class StatusBar(Static):
    """Displays proxy status: domain, port, flow count, engine health."""

    DEFAULT_CSS = """
    StatusBar {
        dock: top;
        background: $primary;
        color: $text;
        padding: 0 1;
        height: 1;
    }
    """

    def update_status(self, domain: str = "", port: int = 8080, flow_count: int = 0, healthy: bool = True, monitored_domains: list[str] | None = None) -> None:
        status_icon = "●" if healthy else "✗"
        color = "green" if healthy else "red"

        if monitored_domains:
            if len(monitored_domains) > 3:
                domains_display = ", ".join(monitored_domains[:3]) + f" +{len(monitored_domains) - 3}"
            else:
                domains_display = ", ".join(monitored_domains)
        else:
            domains_display = "all"

        self.update(
            f"[{color}]{status_icon}[/{color}] "
            f"Proxy: {domain or domains_display} | Port: {port} | "
            f"Flows: {flow_count}"
        )
