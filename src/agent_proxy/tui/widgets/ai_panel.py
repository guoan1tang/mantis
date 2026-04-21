"""AI panel: input field and result output."""
from textual.widgets import Static, Input, TextArea
from textual.containers import Vertical


class AIPanel(Vertical):
    """AI command input and result display."""

    DEFAULT_CSS = """
    AIPanel {
        dock: bottom;
        height: 10;
        background: $primary;
    }
    AIPanel Input {
        width: 100%;
    }
    AIPanel Static {
        width: 100%;
        min-height: 6;
        color: $success;
        content-align: left top;
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
        # Convert newlines to markdown line breaks for proper rendering
        formatted = message.replace("\n", "\n\n")
        self.output_widget.update(f"[green]✓[/green] {formatted}")

    def show_error(self, message: str) -> None:
        """Display error."""
        self.output_widget.update(f"[red]✗[/red] {message}")

    def clear_output(self) -> None:
        self.output_widget.update("")
