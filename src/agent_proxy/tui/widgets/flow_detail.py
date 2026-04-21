"""Request detail widget (right panel)."""
from textual.widgets import Static

from agent_proxy.core.models import FlowRecord


class FlowDetail(Static):
    """Shows headers, body, and timing for selected flow."""

    DEFAULT_CSS = """
    FlowDetail {
        width: 60%;
        height: 1fr;
        background: $surface;
        padding: 0 1;
        overflow-y: scroll;
    }
    """

    def show_flow(self, flow: FlowRecord | None) -> None:
        """Display flow details."""
        if not flow:
            self.update("[grey]No flow selected[/grey]")
            return

        headers_text = "\n".join(
            f"  {k}: {v}" for k, v in flow.request_headers.items()
        )
        body_text = ""
        if flow.request_body:
            try:
                body_text = flow.request_body.decode()[:2000]
            except UnicodeDecodeError:
                body_text = "[binary data]"

        resp_body_text = ""
        if flow.response_body:
            try:
                resp_body_text = flow.response_body.decode()[:2000]
            except UnicodeDecodeError:
                resp_body_text = "[binary data]"

        security_text = ""
        if flow.security_issues:
            security_text = "\n[yellow]Security Issues:[/yellow]\n" + "\n".join(
                f"  - {issue}" for issue in flow.security_issues
            )

        color = "green" if flow.status_code and flow.status_code < 400 else "red"
        content = (
            f"[bold]{flow.method}[/bold] [dim]{flow.url}[/dim]\n"
            f"Status: [bold {color}]{flow.status_code}[/bold {color}]\n"
            f"Duration: {flow.duration_ms:.0f}ms | Size: {flow.size}B\n"
            f"\n[bold]Request Headers:[/bold]\n{headers_text}\n"
            f"\n[bold]Request Body:[/bold]\n{body_text}\n"
            f"\n[bold]Response Body:[/bold]\n{resp_body_text}\n"
            f"{security_text}"
        )
        self.update(content)
