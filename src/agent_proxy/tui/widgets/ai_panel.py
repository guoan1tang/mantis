"""AI panel: input field and result output."""
from textual.widgets import Static, Input
from textual.containers import Vertical


class AIPanel(Vertical):
    """AI command input and result display."""

    DEFAULT_CSS = """
    AIPanel {
        dock: bottom;
        height: 4;
        background: $primary;
    }
    AIPanel Input {
        width: 100%;
    }
    AIPanel Static {
        width: 100%;
        height: 2;
        color: $success;
    }
    """

    def compose(self):
        yield Input(placeholder="> Enter natural language command (e.g. 'analyze traffic', 'mock /api/users')", id="ai_input")
        yield Static("", id="ai_output")

    @property
    def input_widget(self) -> Input:
        return self.query_one("#ai_input", Input)

    @property
    def output_widget(self) -> Static:
        return self.query_one("#ai_output", Static)

    def show_result(self, message: str) -> None:
        """Display agent result."""
        if len(message) > 200:
            message = message[:200] + "..."
        self.output_widget.update(f"[green]✓[/green] {message}")

    def show_error(self, message: str) -> None:
        """Display error."""
        self.output_widget.update(f"[red]✗[/red] {message}")

    def clear_output(self) -> None:
        self.output_widget.update("")
