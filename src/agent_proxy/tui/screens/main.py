"""Main screen with left (traffic) + right (AI chat) layout."""
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable

from agent_proxy.core.store import Store
from agent_proxy.memory.system import MemorySystem
from agent_proxy.tui.widgets.flow_list import FlowList
from agent_proxy.tui.widgets.flow_detail import FlowDetail
from agent_proxy.tui.widgets.status_bar import StatusBar
from agent_proxy.tui.widgets.ai_panel import AIPanel


class MainScreen(Screen):
    """Main TUI screen with left traffic panel and right AI chat."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #main_area {
        height: 1fr;
    }
    #traffic_panel {
        width: 55%;
        height: 1fr;
        layout: vertical;
    }
    #flow_list {
        width: 100%;
        height: 50%;
    }
    #flow_detail {
        width: 100%;
    }
    #ai_panel {
        width: 1fr;
        height: 1fr;
    }
    """

    def __init__(self, store: Store, agents: dict, memory: MemorySystem):
        super().__init__()
        self.store = store
        self.agents = agents
        self.memory = memory

    def compose(self):
        yield StatusBar(id="status_bar")
        with Horizontal(id="main_area"):
            with Vertical(id="traffic_panel"):
                yield FlowList(id="flow_list")
                yield FlowDetail(id="flow_detail")
            yield AIPanel(
                agents=self.agents,
                store=self.store,
                memory=self.memory,
                id="ai_panel",
            )

    def on_mount(self) -> None:
        """Subscribe to flow events."""
        self.set_interval(1.0, self.refresh_flows)

    async def refresh_flows(self) -> None:
        """Check for new flows and update the list."""
        flow_list = self.query_one("#flow_list", FlowList)
        flow_detail = self.query_one("#flow_detail", FlowDetail)
        latest_flow = None

        while not self.store.flow_events.empty():
            flow = self.store.flow_events.get_nowait()
            flow_list.add_flow(flow)
            latest_flow = flow

        # Auto-select latest flow and show detail
        if latest_flow:
            flow_detail.show_flow(latest_flow)
            # Move cursor to the new row
            try:
                row_count = flow_list.row_count
                if row_count > 0:
                    flow_list.move_cursor(row=row_count - 1)
            except Exception:
                pass

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
