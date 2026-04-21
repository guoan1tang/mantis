"""Textual App bootstrap."""
from textual.app import App

from agent_proxy.core.store import Store
from agent_proxy.tui.screens.main import MainScreen


class AgentProxyApp(App):
    """Main TUI application."""

    CSS_PATH = None  # Using inline CSS in widgets

    def __init__(self, store: Store):
        super().__init__()
        self.store = store

    def on_mount(self) -> None:
        self.push_screen(MainScreen(self.store))
