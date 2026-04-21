"""Flow list widget (left panel)."""
from textual.widgets import DataTable
from textual.binding import Binding

from agent_proxy.core.models import FlowRecord


class FlowList(DataTable):
    """Scrollable table showing captured HTTP flows."""

    DEFAULT_CSS = """
    FlowList {
        width: 40%;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "select_row", "Select", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.add_columns("Status", "Method", "Path", "Size", "Duration")
        self._flows: dict[str, FlowRecord] = {}

    def add_flow(self, flow: FlowRecord) -> None:
        """Add a flow to the table."""
        self._flows[flow.id] = flow
        status = str(flow.status_code) if flow.status_code else "..."
        size = f"{flow.size / 1024:.1f}KB" if flow.size > 1024 else f"{flow.size}B"
        duration = f"{flow.duration_ms:.0f}ms"
        self.add_row(status, flow.method, flow.path, size, duration, key=flow.id)

    def get_selected_flow(self) -> FlowRecord | None:
        """Return the currently selected flow record."""
        if self.cursor_row is not None:
            row_key = self.get_row_at(self.cursor_row).key
            return self._flows.get(row_key)
        return None
