"""AI chat panel - full-height right panel with thinking animation."""
from textual.widgets import Static, Input, LoadingIndicator
from textual.containers import Vertical, Horizontal
from textual import work

from agent_proxy.agents.base import IntentRouter


class AIPanel(Vertical):
    """AI chat panel with message history and loading animation."""

    DEFAULT_CSS = """
    AIPanel {
        layout: vertical;
        background: $surface;
        border-left: tall $primary;
    }
    #chat_header {
        height: 3;
        padding: 0 1;
        background: $primary-darken-2;
        border-bottom: solid $primary;
    }
    #chat_header Static {
        color: $text;
        text-style: bold;
    }
    #chat_messages {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
    }
    #thinking_area {
        height: auto;
        padding: 0 1;
        display: none;
    }
    #thinking_area LoadingIndicator {
        width: 3;
        height: 3;
    }
    #thinking_area Static {
        color: $warning;
        padding-left: 1;
    }
    #chat_input {
        height: 3;
        dock: bottom;
        border-top: solid $primary;
    }
    #chat_input Input {
        width: 100%;
    }
    """

    def __init__(self, agents=None, store=None, memory=None, **kwargs):
        super().__init__(**kwargs)
        self.agents = agents or {}
        self.store = store
        self.memory = memory
        self._history: list[tuple[str, str]] = []  # (role, message)

    def compose(self):
        yield Static("[bold]  AI Agent[/bold]", id="chat_header")
        yield Static("", id="chat_messages")
        with Horizontal(id="thinking_area"):
            yield LoadingIndicator()
            yield Static("Thinking...", id="thinking_text")
        yield Input(placeholder="Ask AI about the traffic...", id="chat_input")

    @property
    def input_widget(self) -> Input:
        return self.query_one("#chat_input", Input)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input."""
        if event.input.id == "chat_input":
            query = event.value
            event.input.value = ""
            self.run_agent(query)

    def run_agent(self, query: str) -> None:
        """Add user message, show thinking, start background work."""
        self._add_message("user", query)
        self.query_one("#thinking_area").display = True
        self._execute_agent(query)

    @work(exclusive=True)
    async def _execute_agent(self, query: str) -> None:
        """Run agent asynchronously in background."""
        agent_name = IntentRouter.route(query)
        agent = self.agents.get(agent_name)

        if not agent:
            self._show_result(False, "LLM not configured. Use --api-key.")
            return

        try:
            result = await agent.execute(query)

            if self.memory:
                self._do_consolidate(result.message, query)

            self._show_result(result.success, result.message)
        except Exception as e:
            self._show_result(False, f"Error: {e}")

    async def _do_consolidate(self, message: str, query: str) -> None:
        """Run memory consolidation in background."""
        if self.memory:
            await self.memory.record_interaction(query, message)
            try:
                await self.memory.consolidate()
            except Exception:
                pass

    def _show_result(self, success: bool, message: str) -> None:
        """Show result and hide thinking."""
        self.query_one("#thinking_area").display = False
        if success:
            self._add_message("assistant", message)
        else:
            self._add_message("error", message)
        self.query_one("#chat_messages", Static).scroll_end()

    def _add_message(self, role: str, message: str) -> None:
        """Add a message to the chat."""
        self._history.append((role, message))
        self._render_messages()

    def _render_messages(self) -> None:
        """Render all messages."""
        output = self.query_one("#chat_messages", Static)
        lines = []
        for role, msg in self._history[-10:]:  # Show last 10 messages
            if role == "user":
                lines.append(f"[bold #87CEEB]You:[/bold #87CEEB] {msg}")
                lines.append("")
            elif role == "assistant":
                lines.append(f"[bold #90EE90]AI:[/bold #90EE90] {msg}")
                lines.append("")
            elif role == "error":
                lines.append(f"[bold #FF6B6B]Error:[/bold #FF6B6B] {msg}")
                lines.append("")
        lines.append("")
        output.update("\n".join(lines))
