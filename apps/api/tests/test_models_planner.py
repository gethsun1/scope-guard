import pytest
from pydantic import ValidationError
from scope_guard.inventory import PROJECTS, resources_for
from scope_guard.models import BoundaryManifest, PlannerOutput
from scope_guard.planner import DemoPlanner


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

