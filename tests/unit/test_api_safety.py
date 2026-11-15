import os

from program_os.api import live_agent_enabled


def test_live_agent_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("PROGRAM_OS_ENABLE_LIVE_AGENT", raising=False)
    assert live_agent_enabled() is False


def test_live_agent_requires_explicit_enable_flag(monkeypatch):
    monkeypatch.setenv("PROGRAM_OS_ENABLE_LIVE_AGENT", "true")
    assert live_agent_enabled() is True

    monkeypatch.setenv("PROGRAM_OS_ENABLE_LIVE_AGENT", "false")
    assert live_agent_enabled() is False


def test_api_key_alone_does_not_enable_live_agent(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-key")
    monkeypatch.delenv("PROGRAM_OS_ENABLE_LIVE_AGENT", raising=False)
    assert live_agent_enabled() is False
