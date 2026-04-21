"""Tests for agent base classes and intent routing."""
from agent_proxy.agents.base import IntentRouter


def test_route_rule_agent():
    assert IntentRouter.route("change /api/users response") == "rule"


def test_route_mock_agent():
    assert IntentRouter.route("generate mock data for /api/login") == "mock"


def test_route_security_agent():
    assert IntentRouter.route("check for security vulnerabilities") == "security"


def test_route_analysis_agent():
    assert IntentRouter.route("analyze current traffic") == "analysis"


def test_route_default_fallback():
    assert IntentRouter.route("tell me about requests") == "analysis"
