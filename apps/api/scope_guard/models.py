from copy import deepcopy
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResourceType(StrEnum):
    FILESYSTEM_PATH = "filesystem_path"
    REPOSITORY = "repository"
    SERVICE = "service"
    DATABASE = "database"
    PORT = "port"
    DOMAIN = "domain"
    CONTAINER = "container"
    ENVIRONMENT_VARIABLE = "environment_variable"
    SECRET_REFERENCE = "secret_reference"
    NETWORK_DESTINATION = "network_destination"
    CONFIGURATION_FILE = "configuration_file"


class DecisionType(StrEnum):
    ALLOW = "ALLOW"
    ALLOW_WITH_APPROVAL = "ALLOW_WITH_APPROVAL"
    BLOCK_OUT_OF_SCOPE = "BLOCK_OUT_OF_SCOPE"
    BLOCK_DESTRUCTIVE = "BLOCK_DESTRUCTIVE"
    BLOCK_PROTECTED_RESOURCE = "BLOCK_PROTECTED_RESOURCE"
    BLOCK_UNKNOWN_RESOURCE = "BLOCK_UNKNOWN_RESOURCE"
    BLOCK_SECRET_ACCESS = "BLOCK_SECRET_ACCESS"
    BLOCK_NETWORK_DESTINATION = "BLOCK_NETWORK_DESTINATION"
    BLOCK_POLICY_AMBIGUITY = "BLOCK_POLICY_AMBIGUITY"


class Resource(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: ResourceType
    identifier: str
    project_id: str | None = None
    protected: bool = False


class HealthCheck(BaseModel):
    path: str = "/health"
    expected_status: int = 200


class Project(BaseModel):
    id: str
    name: str
    description: str
    repository_paths: list[str]
    services: list[str]
    databases: list[str]
    ports: list[int]
    domains: list[str]
    health_checks: list[HealthCheck]
    environment: str = "synthetic-demo"
    status: str = "healthy"
    protected: bool = False


class TaskIntent(BaseModel):
    raw_instruction: str = Field(min_length=8)
    target_project: str
    requested_operations: list[str]
    constraints: list[str]
    expected_outcome: str
    risk_tolerance: str


class BoundaryManifest(BaseModel):
    task_id: str
    target_project: str
    allowed_resources: list[Resource]
    protected_resources: list[Resource]
    approval_required_resources: list[Resource]
    always_block_rules: list[str]
    unknown_resource_policy: str = "deny"
    created_by: str
    approved_by: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    version: str = "1.0"

    @model_validator(mode="after")
    def resources_are_disjoint(self) -> "BoundaryManifest":
        allowed = {(r.type, r.identifier) for r in self.allowed_resources}
        protected = {(r.type, r.identifier) for r in self.protected_resources}
        if allowed & protected:
            raise ValueError("allowed and protected resources must be disjoint")
        return self


class ProposedAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    sequence: int
    command: str
    operation_type: str
    resource_references: list[Resource] = Field(default_factory=list)
    working_directory: str = "/workspace/projects/rdsocial"
    environment_requirements: list[str] = Field(default_factory=list)
    risk_level: str
    reason: str
    expected_effect: str
    validation_steps: list[str]
    rollback_steps: list[str]


class Violation(BaseModel):
    rule: str
    resource: str | None = None
    detail: str


class PolicyDecision(BaseModel):
    action_id: str
    decision: DecisionType
    matched_rules: list[str]
    violations: list[Violation]
    human_explanation: str
    machine_explanation: dict[str, Any]
    suggested_correction: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Snapshot(BaseModel):
    task_id: str
    resource_hashes: dict[str, str]
    repository_state: dict[str, Any]
    service_state: dict[str, Any]
    container_state: dict[str, Any]
    database_migration_state: dict[str, int]
    health_state: dict[str, bool]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditEvent(BaseModel):
    id: str
    task_id: str
    event_type: str
    actor: str
    severity: str
    payload: dict[str, Any]
    previous_hash: str
    event_hash: str
    created_at: datetime


class PlannerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interpreted_intent: str
    target_project: str
    allowed_resources: list[Resource]
    protected_resources: list[Resource]
    approval_required_resources: list[Resource]
    proposed_steps: list[str]
    risk_summary: str
    validation_plan: list[str]
    rollback_plan: list[str]
    open_questions: list[str]
    confidence: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def plan_is_unambiguous(self) -> "PlannerOutput":
        if self.open_questions:
            raise ValueError("planner output contains unresolved questions")
        allowed = {(resource.type, resource.identifier) for resource in self.allowed_resources}
        protected = {(resource.type, resource.identifier) for resource in self.protected_resources}
        approvals = {(resource.type, resource.identifier) for resource in self.approval_required_resources}
        if allowed & protected or approvals & protected:
            raise ValueError("planner resource sets overlap")
        if not self.target_project or not self.allowed_resources or not self.protected_resources:
            raise ValueError("planner output has an ambiguous resource boundary")
        return self


class ProposedActionSet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actions: list[ProposedAction] = Field(min_length=1, max_length=20)


class CreateTaskRequest(BaseModel):
    instruction: str = Field(min_length=8, max_length=4000)
    failure_injection: bool = False


def strict_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """Convert a Pydantic schema to the all-fields-required strict-output subset."""
    schema = deepcopy(model.model_json_schema())

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            properties = value.get("properties")
            if isinstance(properties, dict):
                value["additionalProperties"] = False
                value["required"] = list(properties)
            elif value.get("type") == "object":
                value["additionalProperties"] = False
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(schema)
    return schema
