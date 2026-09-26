import sqlite3
import types

import pytest

from apps.api.app.data import db
from apps.api.app.services.fixture_service import FixtureService
from apps.api.app.services.gemini_analyzer import GeminiAnalyzer, build_prompt


class _FakeModels:
    def __init__(self, fail_after=None):
        self.calls, self.fail_after = [], fail_after

    def generate_content(self, model, contents):
        if self.fail_after is not None and len(self.calls) >= self.fail_after:
            raise RuntimeError("429 RESOURCE_EXHAUSTED")
        self.calls.append(contents)
        return types.SimpleNamespace(text=f"Explanation number {len(self.calls)}.")


def _analyzer(fail_after=None):
    analyzer = GeminiAnalyzer()
    analyzer.client = types.SimpleNamespace(models=_FakeModels(fail_after))
    return analyzer


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    """Explanations written by these tests go to a throwaway copy, not the shared test database."""
    with db.connect() as src:
        dest_path = tmp_path / "copy.db"
        dest = sqlite3.connect(dest_path)
        src.backup(dest)
        dest.close()
    monkeypatch.setenv("LIVELYBORG_DB_PATH", str(dest_path))


@pytest.mark.asyncio
async def test_page_requests_never_call_gemini_and_show_saved_text(isolated_db):
    service = FixtureService()
    service.gemini = _analyzer()
    fixtures = await service.get_all_fixtures_with_predictions()
    assert service.gemini.client.models.calls == []  # building pages made no API calls

    result = await service.gemini.explain_missing(fixtures, max_calls=3, pause_seconds=0)
    assert result == {"written": 3, "remaining": len(fixtures) - 3}
    assert "do not invent injuries" in service.gemini.client.models.calls[0]

    service.refresh_explanations()
    refreshed = await service.get_all_fixtures_with_predictions()
    soonest = sorted(refreshed, key=lambda f: f.kickoff_timestamp)[0]
    assert soonest.prediction.gemini_tactical_summary == "Explanation number 1."

    again = await service.gemini.explain_missing(refreshed, max_calls=3, pause_seconds=0)
    assert again["written"] == 3 and len(service.gemini.client.models.calls) == 6  # only missing ones


@pytest.mark.asyncio
async def test_rate_limit_stops_the_round_without_disabling_gemini(isolated_db):
    service = FixtureService()
    fixtures = await service.get_all_fixtures_with_predictions()
    analyzer = _analyzer(fail_after=2)
    result = await analyzer.explain_missing(fixtures, max_calls=10, pause_seconds=0)
    assert result["written"] == 2 and "429" in result["stopped"]
    assert analyzer.client is not None  # tries again next cycle


@pytest.mark.asyncio
async def test_without_a_key_nothing_is_attempted():
    analyzer = GeminiAnalyzer()
    analyzer.client = None
    assert (await analyzer.explain_missing([]))["written"] == 0


@pytest.mark.asyncio
async def test_prompt_contains_only_model_facts():
    fixtures = await FixtureService().get_all_fixtures_with_predictions()
    prompt = build_prompt(fixtures[0])
    assert fixtures[0].home_team.name in prompt and "%" in prompt
    assert "do not recommend a bet" in prompt
