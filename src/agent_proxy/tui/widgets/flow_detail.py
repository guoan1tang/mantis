"""Request/Response detail widget."""
import json
import textwrap

from textual.widgets import Static

from agent_proxy.core.models import FlowRecord


def _format_body(body: bytes | None, content_type: str = "") -> str:
    """Format request/response body for display."""
    if not body:
        return "[dim](empty)[/dim]"
    try:
        text = body.decode("utf-8", errors="replace")
    except Exception:
        return "[dim](binary data)[/dim]"

    # Try to format as JSON
    if "json" in content_type.lower() or text.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, indent=2, ensure_ascii=False)[:4000]
        except (json.JSONDecodeError, ValueError):
            pass

    return textwrap.shorten(text, width=4000, placeholder="...")


def _format_headers(headers: dict) -> str:
    """Format headers with color coding."""
    lines = []
    for k, v in headers.items():
        lines.append(f"  [bold]{k}[/bold]: {v}")
    return "\n".join(lines) if lines else "  [dim](none)[/dim]"


class FlowDetail(Static):
    """Shows full request and response for selected flow."""

    DEFAULT_CSS = """
    FlowDetail {
        width: 100%;
        height: 1fr;
        background: $surface;
        padding: 0 1;
        overflow-y: scroll;
    }
    """

    def show_flow(self, flow: FlowRecord | None) -> None:
        """Display full request/response details."""
        if not flow:
            self.update("[grey]No flow selected[/grey]")
            return

        status_color = "green" if flow.status_code and flow.status_code < 400 else "red"
        modified_tag = " [yellow](modified)[/yellow]" if flow.modified else ""
        intercepted_tag = " [cyan](intercepted)[/cyan]" if flow.intercepted else ""

        sections = [
            f"[bold underline]REQUEST[/bold underline]",
            f"[bold]{flow.method}[/bold] {flow.url}",
            f"Host: {flow.host}  Path: {flow.path}",
            "",
            f"[bold underline]Request Headers[/bold underline]",
            _format_headers(flow.request_headers),
            "",
            f"[bold underline]Request Body[/bold underline]",
            _format_body(flow.request_body, flow.content_type),
            "",
            f"[bold underline]RESPONSE[/bold underline]{modified_tag}{intercepted_tag}",
            f"Status: [bold {status_color}]{flow.status_code or '(pending)'}[/bold {status_color}]",
            f"Duration: {flow.duration_ms:.0f}ms  |  Size: {flow.size}B",
            "",
            f"[bold underline]Response Headers[/bold underline]",
            _format_headers(flow.response_headers),
            "",
            f"[bold underline]Response Body[/bold underline]",
            _format_body(flow.response_body, flow.content_type),
        ]

        if flow.security_issues:
            sections.append("")
            sections.append(f"[bold underline]Security Issues[/bold underline]")
            for issue in flow.security_issues:
                sections.append(f"  [yellow]![/yellow] {issue}")

        self.update("\n".join(sections))
