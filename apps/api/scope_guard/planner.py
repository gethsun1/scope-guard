from abc import ABC, abstractmethod
from typing import Any, Protocol, cast

from pydantic import ValidationError

from .inventory import PROJECTS, resources_for
from .models import PlannerOutput, strict_json_schema

PROMPT_VERSION = "scope-guard-planner-v1"
SYSTEM_PROMPT = "Propose task resources and plans as strict JSON. Never grant permissions or make policy decisions."


class Planner(ABC):
    @abstractmethod
    async def plan(self, instruction: str) -> PlannerOutput: ...


class DemoPlanner(Planner):
    async def plan(self, instruction: str) -> PlannerOutput:
        target, protected = PROJECTS
        return PlannerOutput(interpreted_intent=("Update and deploy RD Social, apply its approved "
            "migration, restart its API, and verify health without changing EngageFlow."),
            target_project="rdsocial", allowed_resources=resources_for(target),
            protected_resources=resources_for(protected),
            approval_required_resources=[resource for resource in resources_for(target)
                                         if resource.identifier == "rdsocial-api"],
            proposed_steps=["Edit RD Social", "Apply migration", "Restart rdsocial-api", "Verify health"],
            risk_summary="Migration and service restart require approval; EngageFlow is always protected.",
            validation_plan=["RD Social /health returns 200", "EngageFlow hash and health remain unchanged"],
            rollback_plan=["Restore RD Social snapshot", "Restart only rdsocial-api", "Revalidate both apps"],
            open_questions=[], confidence=0.99)


class ResponsesClient(Protocol):
    async def create(self, **kwargs: Any) -> Any: ...


class OpenAIPlanner(Planner):
    def __init__(self, responses: ResponsesClient | None = None) -> None:
        self._responses = responses

    async def plan(self, instruction: str) -> PlannerOutput:
        from openai import AsyncOpenAI

        from .config import settings

        config = settings()
        responses: Any = self._responses
        if responses is None:
            if not config.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is required when DEMO_MODE=false")
            client = AsyncOpenAI(api_key=config.openai_api_key, timeout=config.openai_timeout_seconds,
                                 max_retries=config.openai_max_retries)
            responses = cast(Any, client.responses)
        response = await responses.create(model=config.openai_model,
            instructions=SYSTEM_PROMPT, input=instruction,
            metadata={"scope_guard_prompt_version": PROMPT_VERSION, "provider": "gpt_live"},
            text={"format": {"type": "json_schema", "name": "scope_guard_plan",
                              "strict": True, "schema": strict_json_schema(PlannerOutput)}},
            timeout=config.openai_timeout_seconds)
        if not getattr(response, "output_text", None):
            raise ValueError("planner returned no structured output")
        try:
            return PlannerOutput.model_validate_json(response.output_text)
        except (ValidationError, ValueError) as error:
            raise ValueError("planner returned malformed structured output") from error
