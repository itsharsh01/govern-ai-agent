from __future__ import annotations

from unittest.mock import patch

from agent.discovery_v2 import llm


def test_discovery_llm_models_dedupes_primary():
    with patch.dict(
        "os.environ",
        {
            "GROQ_API_KEY": "test-key",
            "DISCOVERY_LLM_MODEL": "meta-llama/llama-4-scout-17b-16e-instruct",
            "DISCOVERY_LLM_FALLBACK_MODELS": "meta-llama/llama-4-scout-17b-16e-instruct,llama-3.3-70b-versatile",
        },
        clear=False,
    ):
        from agent.discovery_v2.config import discovery_llm_models

        assert discovery_llm_models() == [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "llama-3.3-70b-versatile",
        ]


@patch("agent.discovery_v2.llm.discovery_llm_available", return_value=True)
@patch("agent.discovery_v2.llm.discovery_llm_models", return_value=["fast", "slow"])
@patch("agent.discovery_v2.llm._generate_one")
def test_generate_text_falls_back_on_transient(mock_gen, _models, _available):
    mock_gen.side_effect = [Exception("503 service unavailable"), "Polished question?"]

    assert llm.generate_text("prompt") == "Polished question?"
    assert mock_gen.call_count == 2


@patch("agent.discovery_v2.llm.discovery_llm_available", return_value=True)
@patch("agent.discovery_v2.llm.discovery_llm_models", return_value=["only-model"])
@patch("agent.discovery_v2.llm._generate_one")
def test_generate_text_returns_empty_when_all_fail(mock_gen, _models, _available):
    mock_gen.side_effect = Exception("503 service unavailable")

    assert llm.generate_text("prompt") == ""


@patch("agent.discovery_v2.llm.discovery_llm_available", return_value=False)
@patch("agent.discovery_v2.llm._generate_one")
def test_skips_api_when_unavailable(mock_gen, _available):
    assert llm.generate_text("prompt") == ""
    mock_gen.assert_not_called()


@patch("agent.discovery_v2.llm.discovery_llm_available", return_value=True)
@patch("agent.discovery_v2.llm.discovery_llm_models", return_value=["a", "b"])
@patch("agent.discovery_v2.llm._stream_one")
def test_stream_generate_text_falls_back(mock_stream, _models, _available):
    mock_stream.side_effect = [
        Exception("503 overloaded"),
        iter(["Hello ", "world"]),
    ]

    chunks = list(llm.stream_generate_text("prompt"))
    assert chunks == ["Hello ", "world"]
    assert mock_stream.call_count == 2


@patch("agent.discovery_v2.llm.discovery_llm_available", return_value=True)
@patch("agent.discovery_v2.llm.discovery_llm_models", return_value=["fast", "slow", "other"])
@patch("agent.discovery_v2.llm._stream_one")
def test_rate_limit_tries_only_first_model(mock_stream, _models, _available):
    llm.reset_llm_status()
    mock_stream.side_effect = Exception("429 rate limit exceeded")

    chunks = list(llm.stream_generate_text("prompt"))
    assert chunks == []
    assert mock_stream.call_count == 1
    assert llm.llm_in_cooldown()


def test_llm_enabled_requires_groq_key():
    with patch.dict(
        "os.environ",
        {"GROQ_API_KEY": "gsk_test", "DISCOVERY_DISABLE_LLM": ""},
        clear=False,
    ):
        from agent.discovery_v2.config import llm_enabled

        assert llm_enabled() is True
