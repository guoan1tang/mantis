"""Tests for mitmproxy addon."""
import pytest
from unittest.mock import MagicMock

from agent_proxy.core.models import FlowRecord, ProxyRule, RuleAction, RuleCondition
from agent_proxy.core.store import Store
from agent_proxy.proxy.addon import AgentProxyAddon


@pytest.fixture
def store():
    return Store()


@pytest.fixture
def addon(store):
    return AgentProxyAddon(store)


def test_domain_filter_no_filter(addon, store):
    """When no domains set, capture everything."""
    flow = MagicMock()
    flow.request = MagicMock(host="anything.com")
    assert addon._should_capture(flow) is True


def test_domain_filter_exact_match(addon, store):
    addon.domains = ["api.example.com"]
    flow = MagicMock()
    flow.request = MagicMock(host="api.example.com")
    assert addon._should_capture(flow) is True


def test_domain_filter_no_match(addon, store):
    addon.domains = ["api.example.com"]
    flow = MagicMock()
    flow.request = MagicMock(host="other.com")
    assert addon._should_capture(flow) is False


def test_domain_filter_wildcard(addon, store):
    addon.domains = ["*.example.com"]
    flow = MagicMock()
    flow.request = MagicMock(host="api.example.com")
    assert addon._should_capture(flow) is True


def test_mock_rule_blocks_request(addon, store):
    rule = ProxyRule(
        condition=RuleCondition(url_pattern="/blocked"),
        action=RuleAction(type="block", status_code=403),
    )
    store.add_rule(rule)

    flow = MagicMock()
    flow.id = "test1"
    flow.request = MagicMock()
    flow.request.method = "GET"
    flow.request.pretty_url = "https://api.example.com/blocked"
    flow.request.headers = {}
    flow.request.content = None
    flow.response = None

    addon.request(flow)
    # Verify response was set by the block rule
    assert flow.response is not None
    assert flow.response.status_code == 403
