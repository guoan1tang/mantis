"""Tests for Store."""
import pytest
from agent_proxy.core.models import FlowRecord, ProxyRule, RuleAction, RuleCondition
from agent_proxy.core.store import Store


@pytest.fixture
def store():
    return Store()


def test_add_flow(store):
    flow = FlowRecord(method="GET", url="https://api.example.com/users")
    store.add_flow(flow)
    assert flow.id in store.flows


def test_flow_eviction_on_max(store):
    store.config.capture.max_flows = 3
    for i in range(5):
        store.add_flow(FlowRecord(url=f"https://api.example.com/{i}"))
    assert len(store.flows) == 3
    # Oldest flows evicted
    assert "https://api.example.com/0" not in store.flows.values()


def test_add_and_get_rules(store):
    rule = ProxyRule(description="test rule")
    store.add_rule(rule)
    assert rule in store.rules


def test_get_matching_rules(store):
    rule = ProxyRule(
        condition=RuleCondition(url_pattern="/api/users"),
        action=RuleAction(type="modify"),
    )
    store.add_rule(rule)
    flow = FlowRecord(url="https://api.example.com/api/users/1", method="GET")
    matches = store.get_matching_rules(flow)
    assert len(matches) == 1
    assert matches[0].id == rule.id


def test_remove_rule(store):
    rule = ProxyRule()
    store.add_rule(rule)
    store.remove_rule(rule.id)
    assert rule.id not in [r.id for r in store.rules]


def test_disabled_rules_ignored(store):
    rule = ProxyRule(
        enabled=False,
        condition=RuleCondition(url_pattern="/api"),
    )
    store.add_rule(rule)
    flow = FlowRecord(url="https://api.example.com/api/test")
    matches = store.get_matching_rules(flow)
    assert len(matches) == 0
