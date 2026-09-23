import pytest

from prlab_eval.judge import JudgeConfigError, LlmJudge, resolve_judge_config


def test_groq_is_selected_from_free_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("PRLAB_JUDGE_API_KEY", raising=False)
    monkeypatch.delenv("PRLAB_JUDGE_PROVIDER", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    config = resolve_judge_config()
    assert config.provider == "groq"
    assert config.model == "openai/gpt-oss-120b"
    assert "groq.com" in config.base_url


def test_explicit_provider_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test")
    config = resolve_judge_config(provider="gemini")
    assert config.provider == "gemini"
    assert config.model == "gemini-3.6-flash"


def test_ollama_needs_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    config = resolve_judge_config(provider="ollama")
    assert config.provider == "ollama"
    assert config.api_key == "ollama"
    assert config.json_mode is False


def test_groq_request_sends_a_browser_user_agent() -> None:
    judge = LlmJudge(
        api_key="gsk-test",
        model="llama-3.3-70b-versatile",
        base_url="https://api.groq.com/openai/v1",
        provider="groq",
    )
    headers = judge._headers()
    assert "Mozilla" in headers["User-Agent"]
    assert headers["Authorization"] == "Bearer gsk-test"


def test_groq_model_aliases(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    assert resolve_judge_config(provider="groq", model="qwen").model == "qwen/qwen3.8-27b"
    assert (
        resolve_judge_config(provider="groq", model="openai/gpt-oss-120b").model
        == "openai/gpt-oss-120b"
    )


def test_openai_rejects_a_groq_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("PRLAB_JUDGE_API_KEY", "gsk_not_openai")
    with pytest.raises(JudgeConfigError, match="Groq key"):
        resolve_judge_config(provider="openai")


def test_openai_uses_openai_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("PRLAB_JUDGE_API_KEY", "gsk_not_openai")
    config = resolve_judge_config(provider="openai")
    assert config.api_key == "sk-test"


def test_ping_sends_a_tiny_probe() -> None:
    judge = LlmJudge(
        api_key="sk-test",
        model="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        provider="openai",
    )
    calls: list[dict] = []

    def fake_complete(payload: dict) -> str:
        calls.append(payload)
        return "ok"

    judge._complete = fake_complete  # type: ignore[method-assign]
    from prlab_eval.judge import precheck_judge

    message = precheck_judge(judge)
    assert "openai" in message
    assert "gpt-4o-mini" in message
    assert calls[0]["messages"][0]["content"] == "Reply with the single word ok."


def test_llm_judge_scores_a_claim() -> None:
    from prlab_eval.cases import Claim

    judge = LlmJudge(
        api_key="gsk-test",
        model="openai/gpt-oss-120b",
        base_url="https://api.groq.com/openai/v1",
        provider="groq",
    )
    judge._complete = lambda payload: (  # type: ignore[method-assign]
        '{"asserts": true, "quote": "omitted confirmation counts a wicket", "reason": "stated"}'
    )
    claim = Claim(
        id="omitted-confirm-counts-wicket",
        must_assert="Omitted confirmation counts a wicket.",
        tokens=("wicket",),
    )
    verdict = judge.judge(claim, "omitted confirmation counts a wicket")
    assert verdict.passed
    assert "wicket" in verdict.quote


def test_unknown_provider_lists_free_options() -> None:
    with pytest.raises(JudgeConfigError, match="groq"):
        resolve_judge_config(provider="not-a-vendor")
