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


import pytest
from unittest.mock import AsyncMock, patch

from agent_proxy.core.store import Store
from agent_proxy.core.config import AppConfig
from agent_proxy.agents.llm import LLMClient
from agent_proxy.agents.rule_agent import RuleAgent
from agent_proxy.agents.mock_agent import MockAgent
from agent_proxy.agents.security_agent import SecurityAgent
from agent_proxy.agents.analysis_agent import AnalysisAgent


@pytest.fixture
def store():
    return Store(AppConfig())


@pytest.fixture
def llm_client():
    config = AppConfig().llm
    return LLMClient(config)


@pytest.fixture
def rule_agent(store, llm_client):
    return RuleAgent(llm_client, store)


@pytest.fixture
def security_agent(store, llm_client):
    return SecurityAgent(llm_client, store)


@pytest.fixture
def analysis_agent(store, llm_client):
    return AnalysisAgent(llm_client, store)


@pytest.mark.asyncio
async def test_rule_agent_creates_rule(rule_agent, store):
    with patch.object(rule_agent.llm, "call_json", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {
            "description": "Block admin endpoint",
            "condition": {"url_pattern": "/api/admin", "methods": None, "header_match": None},
            "action": {"type": "block", "status_code": 403, "headers": None, "body": None},
        }
        result = await rule_agent.execute("Block all /api/admin requests")
        assert result.success is True
        assert len(store.rules) == 1


@pytest.mark.asyncio
async def test_security_agent_no_flows(security_agent):
    result = await security_agent.execute("check security")
    assert result.success is False
    assert "No traffic" in result.message


@pytest.mark.asyncio
async def test_analysis_agent_no_flows(analysis_agent):
    result = await analysis_agent.execute("analyze traffic")
    assert result.success is False
    assert "No traffic" in result.message
