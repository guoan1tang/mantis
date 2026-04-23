"""Flow tree widget with domain grouping and filter."""
from collections import defaultdict

from rich.markup import escape
from textual.widgets import Tree, Input
from textual.containers import Vertical
from textual.binding import Binding

from agent_proxy.core.models import FlowRecord


class FlowTree(Vertical):
    """Domain-grouped flow tree with filter."""

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("enter", "expand_or_select", "Select", show=False),
        Binding("escape", "clear_filter", "Clear Filter", show=True),
    ]

    DEFAULT_CSS = """
    FlowTree {
        layout: vertical;
    }
    #flow_filter {
        height: 3;
        dock: top;
        margin: 0 1;
    }
    #flow_tree {
        width: 100%;
        height: 1fr;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._flows: dict[str, FlowRecord] = {}
        self._domains: dict[str, list[str]] = defaultdict(list)  # domain -> [flow_id]
        self._filter_text = ""
        self._tree: Tree[str] | None = None
        self._expanded_domains: set[str] = set()

    def compose(self):
        yield Input(placeholder="筛选域名/路径（例：baidu, /api）...", id="flow_filter")
        yield Tree(label="Flows", id="flow_tree")

    def on_mount(self) -> None:
        self._tree = self.query_one("#flow_tree", Tree)

    def _show_flow_detail(self, flow: FlowRecord | None) -> None:
        """Show flow details in the detail panel."""
        if not flow:
            return
        try:
            detail = self.screen.query_one("#flow_detail")
            detail.show_flow(flow)
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle filter input change."""
        if event.input.id == "flow_filter":
            self._filter_text = event.value.lower()
            self.refresh_tree()

    def add_flow(self, flow: FlowRecord) -> None:
        """Add a flow to the tree."""
        self._flows[flow.id] = flow
        self._domains[flow.host].append(flow.id)
        self.refresh_tree()
        # Auto-select latest flow
        latest_flow = flow
        self._show_flow_detail(latest_flow)

    def refresh_tree(self) -> None:
        """Rebuild the tree from flows, preserving expand state."""
        if not self._tree:
            return

        # Save currently expanded domains before clear
        if self._tree.root.children:
            for node in self._tree.root.children:
                if node.data and node.data.get("type") == "domain" and node.is_expanded:
                    self._expanded_domains.add(node.data.get("domain", ""))

        self._tree.clear()
        root = self._tree.root

        # Group by domain
        for domain, flow_ids in self._domains.items():
            # Apply filter
            visible_ids = [fid for fid in flow_ids if fid in self._flows]
            if self._filter_text:
                domain_match = self._filter_text in domain.lower()
                matching = []
                for fid in visible_ids:
                    f = self._flows[fid]
                    if domain_match or self._filter_text in f.path.lower():
                        matching.append(fid)
                visible_ids = matching

            if not visible_ids:
                continue

            count = len(visible_ids)
            domain_node = root.add(
                f"{'[bold #1f87ff]' if count > 0 else '[dim]'}{escape(domain)}[/] [{count}]",
                data={"type": "domain", "domain": domain},
            )

            # Restore expand state for this domain
            if domain in self._expanded_domains:
                domain_node.expand()

            for fid in visible_ids:
                f = self._flows[fid]
                status = str(f.status_code) if f.status_code else "..."
                status_color = "green" if f.status_code and f.status_code < 400 else "red"
                label = f"[{status_color}]{status}[/] {escape(f.method)} {escape(f.path)}"
                domain_node.add(label, data={"type": "flow", "flow_id": fid})

    def get_selected_flow(self) -> FlowRecord | None:
        """Return the currently selected flow record."""
        if not self._tree:
            return None
        node = self._tree.cursor_node
        if node is None:
            # cursor_line is an int; get the node at that line
            if self._tree.cursor_line is not None:
                node = self._tree.get_node_at_line(self._tree.cursor_line)
            if node is None:
                return None
        if node.data and node.data.get("type") == "flow":
            return self._flows.get(node.data.get("flow_id"))
        # If on domain node, return first flow in that domain
        if node.data and node.data.get("type") == "domain":
            domain = node.data.get("domain", "")
            flow_ids = self._domains.get(domain, [])
            for fid in flow_ids:
                if fid in self._flows:
                    return self._flows[fid]
        return None

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection - show flow detail."""
        flow = self.get_selected_flow()
        if flow:
            self._show_flow_detail(flow)

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Handle cursor move - update detail view."""
        if not self._tree:
            return
        flow = self.get_selected_flow()
        if flow:
            self._show_flow_detail(flow)

    def action_cursor_up(self) -> None:
        """Move cursor up."""
        if self._tree:
            self._tree.action_cursor_up()

    def action_cursor_down(self) -> None:
        """Move cursor down."""
        if self._tree:
            self._tree.action_cursor_down()

    def action_expand_or_select(self) -> None:
        """Toggle expand/collapse for domain, show detail for flow."""
        if not self._tree:
            return
        node = self._tree.cursor_node
        if node is None:
            return
        if node.data and node.data.get("type") == "domain":
            domain = node.data.get("domain", "")
            if node.is_expanded:
                node.collapse()
                self._expanded_domains.discard(domain)
            else:
                node.expand()
                self._expanded_domains.add(domain)
        elif node.data and node.data.get("type") == "flow":
            self._show_flow_detail(self.get_selected_flow())

    def action_clear_filter(self) -> None:
        """Clear the filter input."""
        self.query_one("#flow_filter", Input).value = ""
        self._filter_text = ""
        self.refresh_tree()
