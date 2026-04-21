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

    def update_status(self, domain: str, port: int, flow_count: int, healthy: bool = True) -> None:
        status_icon = "●" if healthy else "✗"
        color = "green" if healthy else "red"
        self.update(
            f"[{color}]{status_icon}[/{color}] "
            f"Proxy: {domain or 'all'} | Port: {port} | "
            f"Flows: {flow_count}"
        )
