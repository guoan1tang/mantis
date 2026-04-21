"""Textual App bootstrap."""
from textual.app import App

from agent_proxy.core.store import Store
from agent_proxy.memory.system import MemorySystem
from agent_proxy.tui.screens.main import MainScreen


class AgentProxyApp(App):
    """Main TUI application."""

    CSS_PATH = None  # Using inline CSS in widgets

    def __init__(self, store: Store, agents: dict, memory: MemorySystem):
        super().__init__()
        self.store = store
        self.agents = agents
        self.memory = memory

    def on_mount(self) -> None:
        main = MainScreen(self.store, self.agents, self.memory)
        self.push_screen(main)
