"""Tests for core data models."""
import base64

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


def test_flow_to_dict():
    flow = FlowRecord(
        method="POST",
        url="http://api.example.com/v1/users",
        status_code=200,
        request_headers={"Content-Type": "application/json"},
        request_body=b'{"name": "test"}',
        response_body=b'{"id": 1}',
        size=100,
        duration_ms=45.0,
    )
    d = flow.to_dict()
    assert d["id"] == flow.id
    assert d["method"] == "POST"
    assert d["host"] == "api.example.com"
    assert d["path"] == "/v1/users"
    assert d["status_code"] == 200
    assert d["request_body_base64"] == base64.b64encode(b'{"name": "test"}').decode()
    assert d["response_body_base64"] == base64.b64encode(b'{"id": 1}').decode()


def test_flow_to_dict_no_body():
    flow = FlowRecord(method="GET", url="http://example.com/")
    d = flow.to_dict(include_body=False)
    assert "request_body_base64" not in d
    assert "response_body_base64" not in d
