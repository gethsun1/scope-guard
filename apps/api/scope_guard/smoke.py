import argparse
import asyncio
import json

from .codex import CodexAppServerAdapter
from .config import settings
from .inventory import PROJECTS, resources_for
from .models import BoundaryManifest
from .planner import PROMPT_VERSION, OpenAIPlanner

INSTRUCTION = ("Update and deploy RD Social, restart its API, and verify health without "
               "modifying EngageFlow.")


async def smoke_gpt() -> None:
    plan = await OpenAIPlanner().plan(INSTRUCTION)
    print(json.dumps({"provider": "gpt_live", "model": settings().openai_model,
                      "prompt_version": PROMPT_VERSION, "target_project": plan.target_project,
                      "allowed_resources": len(plan.allowed_resources),
                      "protected_resources": len(plan.protected_resources)}, sort_keys=True))


async def smoke_codex() -> None:
    target, protected = PROJECTS
    manifest = BoundaryManifest(task_id="manual-smoke", target_project=target.id,
        allowed_resources=resources_for(target), protected_resources=resources_for(protected),
        approval_required_resources=[], always_block_rules=["protected_resource", "unknown_resource"],
        created_by="manual-smoke", approved_by="manual-smoke")
    adapter = CodexAppServerAdapter()
    actions = await adapter.actions(INSTRUCTION,
        [project.model_dump(mode="json") for project in PROJECTS], manifest)
    print(json.dumps({"provider": adapter.provider, "thread_id": adapter.thread_id,
                      "proposed_action_count": len(actions),
                      "commands": [action.command for action in actions]}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Manually invoke a Scope Guard live provider")
    parser.add_argument("provider", choices=("gpt", "codex"))
    provider = parser.parse_args().provider
    asyncio.run(smoke_gpt() if provider == "gpt" else smoke_codex())


if __name__ == "__main__":
    main()
