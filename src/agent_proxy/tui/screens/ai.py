"""AI task screen - modal dialog with thinking animation."""
from textual.screen import Screen
from textual.widgets import Static, Input, LoadingIndicator
from textual.containers import Vertical, Horizontal
from textual import work

from agent_proxy.core.store import Store
from agent_proxy.agents.base import IntentRouter
from agent_proxy.memory.system import MemorySystem


class AIScreen(Screen):
    """Modal dialog for AI agent interaction with thinking animation."""

    CSS = """
    AIScreen {
        align: center middle;
        background: $background;
    }
    #dialog {
        width: 80%;
        height: 70%;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }
    #header {
        width: 100%;
        height: 3;
        border-bottom: solid $primary;
        background: $primary-darken-1;
    }
    #header Static {
        color: $text;
        text-style: bold;
    }
    #user_query {
        width: 100%;
        height: auto;
        padding: 1;
        margin: 1 0;
        background: $primary-lighten-1;
        color: $text;
    }
    #thinking {
        width: 100%;
        height: 5;
        margin: 1 0;
    }
    #thinking Static {
        color: $warning;
    }
    #result {
        width: 100%;
        height: 1fr;
        padding: 1;
        overflow-y: auto;
    }
    #result.success {
        color: $success;
    }
    #result.error {
        color: $error;
    }
    #input_area {
        width: 100%;
        height: 3;
        border-top: solid $surface-darken-1;
        background: $surface;
        dock: bottom;
    }
    #input_area Input {
        width: 100%;
    }
    LoadingIndicator {
        width: 3;
        height: 3;
    }
    """

    def __init__(self, store: Store, agents: dict, memory: MemorySystem):
        super().__init__()
        self.store = store
        self.agents = agents
        self.memory = memory
        self._initial_query = ""

    def set_query(self, query: str) -> None:
        """Set the initial query text."""
        self._initial_query = query

    def compose(self):
        with Vertical(id="dialog"):
            with Vertical(id="header"):
                yield Static("[bold]AI Agent[/bold]")
            yield Static("", id="user_query")
            with Horizontal(id="thinking"):
                yield LoadingIndicator()
                yield Static("Analyzing...", id="thinking_text")
            yield Static("", id="result", classes="")
            with Vertical(id="input_area"):
                yield Input(placeholder="Type follow-up question (Esc to close)...", id="followup_input")

    def on_mount(self) -> None:
        """Set query and start the agent."""
        self.query_one("#user_query", Static).update(f"[bold]Query:[/bold] {self._initial_query}")
        # Focus the thinking area, not input
        self._run_agent(self._initial_query)

    @work(exclusive=True)
    async def _run_agent(self, query: str) -> None:
        """Run the agent in background."""
        agent_name = IntentRouter.route(query)
        agent = self.agents.get(agent_name)

        if not agent:
            self.call_from_thread(self._show_result, False, "LLM not configured. Use --api-key.")
            return

        try:
            result = await agent.execute(query)
            self.memory.record_interaction(query, result.message)

            if result.success:
                # Run consolidation in background, don't block
                self.call_from_thread(self._run_consolidation)

            self.call_from_thread(self._show_result, result.success, result.message)
        except Exception as e:
            self.call_from_thread(self._show_result, False, f"Error: {e}")

    async def _run_consolidation(self) -> None:
        """Run memory consolidation in background."""
        try:
            await self.memory.consolidate()
        except Exception:
            pass

    def _show_result(self, success: bool, message: str) -> None:
        """Show result and hide thinking."""
        self.query_one("#thinking").display = False
        result = self.query_one("#result", Static)
        if success:
            result.classes.remove("error")
            result.classes.add("success")
            result.update(f"[bold]Analysis Result:[/bold]\n{message}")
        else:
            result.classes.remove("success")
            result.classes.add("error")
            result.update(f"[bold]Error:[/bold] {message}")
        result.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle follow-up question."""
        if event.input.id == "followup_input":
            query = event.value
            event.input.value = ""
            # Reset for follow-up
            result = self.query_one("#result", Static)
            result.update("")
            result.classes.remove("success", "error")
            self.query_one("#thinking").display = True
            self.query_one("#followup_input", Input).focus()
            self._run_agent(query)

    def action_escape(self) -> None:
        """Close the dialog."""
        self.dismiss()
