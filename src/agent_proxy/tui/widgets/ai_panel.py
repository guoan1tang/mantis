"""AI panel: compact input bar at the bottom."""
from textual.widgets import Static, Input
from textual.containers import Vertical
from textual.binding import Binding


class AIPanel(Vertical):
    """Compact AI command input bar."""

    BINDINGS = [
        Binding("/", "focus_input", "AI", show=True),
    ]

    DEFAULT_CSS = """
    AIPanel {
        dock: bottom;
        height: 3;
        background: $boost;
    }
    AIPanel Input {
        width: 100%;
        margin: 0 1;
    }
    """

    def compose(self):
        yield Input(placeholder="Press / to ask AI, or type command here...", id="ai_input")

    @property
    def input_widget(self) -> Input:
        return self.query_one("#ai_input", Input)

    def action_focus_input(self) -> None:
        """Focus the input field."""
        self.input_widget.focus()
