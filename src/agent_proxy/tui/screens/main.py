"""Main screen with three-panel layout."""
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static
from textual.widgets import DataTable

from agent_proxy.core.store import Store
from agent_proxy.tui.widgets.flow_list import FlowList
from agent_proxy.tui.widgets.flow_detail import FlowDetail
from agent_proxy.tui.widgets.ai_panel import AIPanel
from agent_proxy.tui.widgets.status_bar import StatusBar


class MainScreen(Screen):
    """Main TUI screen with flow list, detail, and AI input."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #main_area {
        height: 1fr;
    }
    """

    def __init__(self, store: Store):
        super().__init__()
        self.store = store

    def compose(self):
        yield StatusBar(id="status_bar")
        with Horizontal(id="main_area"):
            yield FlowList(id="flow_list")
            yield FlowDetail(id="flow_detail")
        yield AIPanel(id="ai_panel")

    def on_mount(self) -> None:
        """Subscribe to flow events."""
        self.set_interval(1.0, self.refresh_flows)

    async def refresh_flows(self) -> None:
        """Check for new flows and update the list."""
        while not self.store.flow_events.empty():
            flow = self.store.flow_events.get_nowait()
            flow_list = self.query_one("#flow_list", FlowList)
            flow_list.add_flow(flow)

        # Update status bar
        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.update_status(
            domain="",
            port=8080,
            flow_count=len(self.store.flows),
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Show selected flow detail."""
        flow_list = self.query_one("#flow_list", FlowList)
        flow = flow_list.get_selected_flow()
        flow_detail = self.query_one("#flow_detail", FlowDetail)
        flow_detail.show_flow(flow)
