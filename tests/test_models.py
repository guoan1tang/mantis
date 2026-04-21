"""Tests for core data models."""
from agent_proxy.core.models import FlowRecord, ProxyRule, RuleAction, RuleCondition


def test_flow_record_defaults():
    flow = FlowRecord()
    assert flow.id
    assert flow.method == ""
    assert flow.status_code is None
    assert flow.intercepted is False


def test_flow_record_url_parsing():
    flow = FlowRecord(url="https://api.example.com/v1/users?limit=10")
    assert flow.host == "api.example.com"
    assert flow.path == "/v1/users"


def test_rule_condition_matches_url():
    cond = RuleCondition(url_pattern="/api/users")
    flow = FlowRecord(url="https://api.example.com/api/users/123", method="GET")
    assert cond.matches(flow) is True


def test_rule_condition_no_match_method():
    cond = RuleCondition(url_pattern="/api", methods=["POST"])
    flow = FlowRecord(url="https://api.example.com/api/data", method="GET")
    assert cond.matches(flow) is False


def test_proxy_rule_defaults():
    rule = ProxyRule()
    assert rule.enabled is True
    assert rule.source == "manual"
