import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError
from scope_guard.inventory import PROJECTS, resources_for
from scope_guard.models import BoundaryManifest, PlannerOutput
from scope_guard.planner import PROMPT_VERSION, DemoPlanner, OpenAIPlanner


def test_manifest_disallows_overlap() -> None:
    resource = resources_for(PROJECTS[0])[0]
    with pytest.raises(ValidationError):
        BoundaryManifest(task_id="t", target_project="rdsocial", allowed_resources=[resource],
            protected_resources=[resource], approval_required_resources=[], always_block_rules=[], created_by="test")


@pytest.mark.asyncio
async def test_demo_planner_output_is_strictly_validated() -> None:
    plan = await DemoPlanner().plan("Deploy RD Social without modifying EngageFlow")
    assert PlannerOutput.model_validate(plan.model_dump()).target_project == "rdsocial"
    assert plan.confidence == 0.99
    assert all(resource.protected for resource in plan.protected_resources)


class FakeResponses:
    def __init__(self, output: str | None = None, error: Exception | None = None) -> None:
        self.output = output
        self.error = error
        self.kwargs: dict[str, Any] = {}

    async def create(self, **kwargs: Any) -> SimpleNamespace:
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(output_text=self.output)


@pytest.mark.asyncio
async def test_live_planner_uses_strict_schema_and_metadata() -> None:
    expected = await DemoPlanner().plan("Deploy RD Social without modifying EngageFlow")
    responses = FakeResponses(expected.model_dump_json())
    actual = await OpenAIPlanner(responses).plan("Deploy RD Social without modifying EngageFlow")
    assert actual == expected
    assert responses.kwargs["text"]["format"]["strict"] is True
    assert responses.kwargs["metadata"] == {
        "scope_guard_prompt_version": PROMPT_VERSION, "provider": "gpt_live"}


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [None, "not-json", json.dumps({"target_project": "rdsocial"})])
async def test_live_planner_rejects_missing_or_malformed_output(payload: str | None) -> None:
    with pytest.raises(ValueError):
        await OpenAIPlanner(FakeResponses(payload)).plan("Deploy RD Social without modifying EngageFlow")


@pytest.mark.asyncio
async def test_live_planner_rejects_ambiguous_open_questions() -> None:
    plan = (await DemoPlanner().plan("Deploy RD Social without modifying EngageFlow")).model_dump()
    plan["open_questions"] = ["Which project is the target?"]
    with pytest.raises(ValueError):
        await OpenAIPlanner(FakeResponses(json.dumps(plan))).plan(
            "Deploy RD Social without modifying EngageFlow")


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [TimeoutError("timed out"), RuntimeError("provider unavailable")])
async def test_live_planner_fails_closed_on_provider_errors(error: Exception) -> None:
    with pytest.raises(type(error)):
        await OpenAIPlanner(FakeResponses(error=error)).plan(
            "Deploy RD Social without modifying EngageFlow")


def test_timeout_fixture_is_asyncio_compatible() -> None:
    assert issubclass(asyncio.TimeoutError, TimeoutError)
