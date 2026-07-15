from abc import ABC, abstractmethod

from .models import ProposedAction


class CodexAdapter(ABC):
    provider: str

    @abstractmethod
    async def actions(self) -> list[ProposedAction]: ...


class DemoCodexAdapter(CodexAdapter):
    provider = "codex_demo"

    async def actions(self) -> list[ProposedAction]:
        validation = ["Verify target health", "Verify EngageFlow integrity"]
        rollback = ["Restore RD Social snapshot", "Restart only rdsocial-api"]
        return [
            ProposedAction(id="edit-rdsocial", sequence=1,
                command="touch /workspace/projects/rdsocial/app/release.txt", operation_type="edit",
                risk_level="low", reason="Prepare the RD Social release",
                expected_effect="Update only the target repository", validation_steps=validation,
                rollback_steps=rollback),
            ProposedAction(id="unsafe-engageflow", sequence=2,
                command="systemctl restart engageflow-api", operation_type="restart",
                risk_level="high", reason="Agent selected the wrong shared-host service",
                expected_effect="Restart an API service", validation_steps=validation,
                rollback_steps=rollback),
            ProposedAction(id="restart-rdsocial", sequence=3,
                command="systemctl restart rdsocial-api", operation_type="restart",
                risk_level="medium", reason="Corrected target service operation",
                expected_effect="Deploy and restart RD Social", validation_steps=validation,
                rollback_steps=rollback),
        ]


class CodexAppServerAdapter(CodexAdapter):
    provider = "codex_live"

    async def actions(self) -> list[ProposedAction]:
        raise RuntimeError("CODEX_APP_SERVER_URL integration requires a reachable Codex app-server")
