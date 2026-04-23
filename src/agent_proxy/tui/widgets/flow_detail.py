"""Request/Response detail widget."""
import json

from rich.markup import escape
from rich.text import Text
from textual.widgets import RichLog

from agent_proxy.core.models import FlowRecord

_MAX_BODY = 4000


def _format_body(body: bytes | None, content_type: str = "") -> Text:
    """Format request/response body for display as plain Text (no markup)."""
    if not body:
        return Text("(empty)", style="dim")
    try:
        text = body.decode("utf-8", errors="replace")
    except Exception:
        return Text("(binary data)", style="dim")

    # Try to format as JSON for pretty-printing
    if "json" in content_type.lower() or text.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(text)
            text = json.dumps(parsed, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError):
            pass

    # Truncate without collapsing whitespace
    if len(text) > _MAX_BODY:
        text = text[:_MAX_BODY] + "\n... (truncated)"

    return Text(text)


def _format_headers_text(headers: dict) -> Text:
    """Format headers as plain Text (no markup)."""
    if not headers:
        return Text("  (none)", style="dim")
    lines = []
    for k, v in headers.items():
        lines.append(f"  {k}: {v}")
    return Text("\n".join(lines))


class FlowDetail(RichLog):
    """Shows full request and response for selected flow."""

    DEFAULT_CSS = """
    FlowDetail {
        width: 100%;
        height: 1fr;
        background: $surface;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.markup = True  # Enable markup for labels/headers
        self.wrap = True  # Enable line wrapping

    def show_flow(self, flow: FlowRecord | None) -> None:
        """Display full request/response details."""
        self.clear()
        if not flow:
            self.write("[grey]No flow selected[/grey]")
            return

        status_color = "green" if flow.status_code and flow.status_code < 400 else "red"
        modified_tag = " (modified)" if flow.modified else ""
        intercepted_tag = " (intercepted)" if flow.intercepted else ""

        self.write("[bold underline]REQUEST[/bold underline]")
        self.write(f"[bold]{escape(flow.method)}[/bold] {escape(flow.url)}")
        self.write(f"Host: {escape(flow.host)}  Path: {escape(flow.path)}")
        self.write("")
        self.write("[bold underline]Request Headers[/bold underline]")
        self.write(_format_headers_text(flow.request_headers))
        self.write("")
        self.write("[bold underline]Request Body[/bold underline]")
        self.write(_format_body(flow.request_body, flow.content_type))
        self.write("")
        self.write(f"[bold underline]RESPONSE[/bold underline]{modified_tag}{intercepted_tag}")
        self.write(f"Status: [bold {status_color}]{flow.status_code or '(pending)'}[/bold {status_color}]")
        self.write(f"Duration: {flow.duration_ms:.0f}ms  |  Size: {flow.size}B")
        self.write("")
        self.write("[bold underline]Response Headers[/bold underline]")
        self.write(_format_headers_text(flow.response_headers))
        self.write("")
        self.write("[bold underline]Response Body[/bold underline]")
        self.write(_format_body(flow.response_body, flow.content_type))

        if flow.security_issues:
            self.write("")
            self.write("[bold underline]Security Issues[/bold underline]")
            for issue in flow.security_issues:
                self.write(Text(f"  ! {issue}", style="yellow"))
