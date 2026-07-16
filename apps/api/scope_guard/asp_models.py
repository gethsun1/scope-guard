import posixpath
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator


class RiskTolerance(StrEnum):
    STRICT = "strict"
    BALANCED = "balanced"
    PERMISSIVE = "permissive"


class AspVerdict(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


def _safe_text(value: str) -> str:
    value = value.strip()
    if "\x00" in value:
        raise ValueError("null bytes are not allowed")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as error:
        raise ValueError("text must contain valid Unicode") from error
    return value


class AspAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: str = Field(min_length=3, max_length=2000)
    proposed_actions: list[str] = Field(min_length=1, max_length=25)
    allowed_resources: list[str] = Field(default_factory=list, max_length=100)
    protected_resources: list[str] = Field(default_factory=list, max_length=100)
    allowed_paths: list[str] = Field(default_factory=list, max_length=100)
    protected_paths: list[str] = Field(default_factory=list, max_length=100)
    risk_tolerance: RiskTolerance = RiskTolerance.STRICT
    metadata: dict[str, JsonValue] | None = None

    @field_validator("task")
    @classmethod
    def validate_task(cls, value: str) -> str:
        return _safe_text(value)

    @field_validator("proposed_actions")
    @classmethod
    def validate_actions(cls, values: list[str]) -> list[str]:
        result = [_safe_text(value) for value in values]
        if any(not value or len(value) > 2000 for value in result):
            raise ValueError("each action must contain between 1 and 2000 characters")
        return result

    @field_validator("allowed_resources", "protected_resources")
    @classmethod
    def validate_resources(cls, values: list[str]) -> list[str]:
        result = [_safe_text(value) for value in values]
        if any(not value or len(value) > 500 for value in result):
            raise ValueError("resource names must contain between 1 and 500 characters")
        if len(set(result)) != len(result):
            raise ValueError("resource lists must not contain duplicates")
        return result

    @field_validator("allowed_paths", "protected_paths")
    @classmethod
    def validate_paths(cls, values: list[str]) -> list[str]:
        result = [_safe_text(value) for value in values]
        if any(not value or len(value) > 1000 for value in result):
            raise ValueError("paths must contain between 1 and 1000 characters")
        if len(set(result)) != len(result):
            raise ValueError("path lists must not contain duplicates")
        normalized: list[str] = []
        for value in result:
            if not value.startswith("/") or ".." in value.split("/"):
                raise ValueError("boundary paths must be absolute and must not contain traversal")
            suffix = "/**" if value.endswith("/**") else ""
            base = value[:-3] if suffix else value
            normalized.append(posixpath.normpath(base) + suffix)
        return normalized

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: dict[str, JsonValue] | None) -> dict[str, JsonValue] | None:
        if value is None:
            return None
        if len(value) > 25:
            raise ValueError("metadata may contain at most 25 top-level keys")

        def visit(item: JsonValue, depth: int = 0) -> None:
            if depth > 4:
                raise ValueError("metadata may be nested at most four levels")
            if isinstance(item, str):
                if len(item) > 2000:
                    raise ValueError("metadata strings may contain at most 2000 characters")
                _safe_text(item)
            elif isinstance(item, list):
                if len(item) > 100:
                    raise ValueError("metadata arrays may contain at most 100 items")
                for child in item:
                    visit(child, depth + 1)
            elif isinstance(item, dict):
                if len(item) > 100:
                    raise ValueError("metadata objects may contain at most 100 keys")
                for key, child in item.items():
                    if len(key) > 100:
                        raise ValueError("metadata keys may contain at most 100 characters")
                    _safe_text(key)
                    visit(child, depth + 1)

        visit(value)
        return value

    @model_validator(mode="after")
    def boundaries_are_disjoint(self) -> "AspAnalyzeRequest":
        if set(self.allowed_resources) & set(self.protected_resources):
            raise ValueError("allowed and protected resources must be disjoint")
        if set(self.allowed_paths) & set(self.protected_paths):
            raise ValueError("allowed and protected paths must be disjoint")
        return self


class AspActionDecision(BaseModel):
    action: str
    verdict: AspVerdict
    risk_level: str
    reason: str
    matched_resources: list[str]
    matched_paths: list[str]
    policy_codes: list[str]


class AspViolation(BaseModel):
    code: str
    action_index: int
    reason: str


class AspRequiredApproval(BaseModel):
    action_index: int
    reason: str


class AspAnalyzeResponse(BaseModel):
    service: str = "scope-guard"
    service_version: str
    evaluation_id: str
    verdict: AspVerdict
    risk_score: int = Field(ge=0, le=100)
    summary: str
    decisions: list[AspActionDecision]
    violations: list[AspViolation]
    required_approvals: list[AspRequiredApproval]
    recommended_corrections: list[str]
    policy_version: str
    evidence_hash: str
    evaluated_at: datetime


class AspHealthResponse(BaseModel):
    status: str = "ok"
    service: str = "scope-guard-asp"
    version: str
    mode: str = "read-only"
