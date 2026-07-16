import asyncio
import json
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import ValidationError

from .config import settings
from .models import BoundaryManifest, ProposedAction, ProposedActionSet, strict_json_schema

EventSink = Callable[[str, dict[str, Any]], Awaitable[None]]


class CodexAdapter(ABC):
    provider: str
    thread_id: str | None = None

    @abstractmethod
    async def actions(self, instruction: str = "", inventory: list[dict[str, Any]] | None = None,
                      manifest: BoundaryManifest | None = None,
                      event_sink: EventSink | None = None) -> list[ProposedAction]: ...

    async def rejection_feedback(self, rejection: dict[str, Any],
                                 event_sink: EventSink | None = None) -> list[ProposedAction]:
        return []


class DemoCodexAdapter(CodexAdapter):
    provider = "codex_demo"
    thread_id = "codex-demo-signature-thread"

    async def actions(self, instruction: str = "", inventory: list[dict[str, Any]] | None = None,
                      manifest: BoundaryManifest | None = None,
                      event_sink: EventSink | None = None) -> list[ProposedAction]:
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
    """Read-only app-server client. Codex proposes JSON; Scope Guard remains the executor."""

    provider = "codex_live"

    def __init__(self, runner: Callable[[str, str | None, dict[str, Any]], Awaitable[tuple[str, str,
                 list[dict[str, Any]]]]] | None = None, thread_id: str | None = None) -> None:
        self._runner = runner or self._run_app_server
        self.thread_id = thread_id

    async def actions(self, instruction: str = "", inventory: list[dict[str, Any]] | None = None,
                      manifest: BoundaryManifest | None = None,
                      event_sink: EventSink | None = None) -> list[ProposedAction]:
        if manifest is None:
            raise ValueError("approved boundary manifest is required")
        prompt = ("Propose actions only; do not execute commands or edit files. Return JSON matching the "
                  "provided schema. Task, inventory, approved boundary, and policy are authoritative.\n" +
                  json.dumps({"task": instruction, "inventory": inventory or [],
                              "manifest": manifest.model_dump(mode="json"),
                              "policy": {"unknown_resources": "deny", "model_is_not_authority": True}},
                             sort_keys=True))
        return await self._turn(prompt, event_sink)

    async def rejection_feedback(self, rejection: dict[str, Any],
                                 event_sink: EventSink | None = None) -> list[ProposedAction]:
        if not self.thread_id:
            raise RuntimeError("Codex thread has not been started")
        prompt = ("The deterministic policy engine rejected the proposed action. Do not dispute or bypass "
                  "the decision. Return a corrected action set within the approved boundary.\n" +
                  json.dumps(rejection, sort_keys=True))
        return await self._turn(prompt, event_sink)

    async def _turn(self, prompt: str, event_sink: EventSink | None) -> list[ProposedAction]:
        try:
            thread_id, output, events = await self._runner(prompt, self.thread_id,
                                                           strict_json_schema(ProposedActionSet))
            self.thread_id = thread_id
            for event in events:
                if event_sink:
                    await event_sink(str(event.get("method", "codex_event")), event)
            return ProposedActionSet.model_validate_json(output).actions
        except (json.JSONDecodeError, ValidationError) as error:
            raise ValueError("Codex returned malformed proposed actions") from error

    async def _run_app_server(self, prompt: str, thread_id: str | None,
                              output_schema: dict[str, Any]) -> tuple[str, str, list[dict[str, Any]]]:
        config = settings()
        try:
            process = await asyncio.create_subprocess_exec(config.codex_command, "app-server", "--stdio",
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL)
        except FileNotFoundError as error:
            raise RuntimeError("Codex app-server tooling is unavailable") from error
        if process.stdin is None or process.stdout is None:
            raise RuntimeError("Codex app-server stdio is unavailable")
        stdin = process.stdin
        stdout = process.stdout

        request_id = 0
        events: list[dict[str, Any]] = []

        async def send(method: str, params: dict[str, Any], expects_response: bool = True) -> int:
            nonlocal request_id
            request_id += 1
            message: dict[str, Any] = {"method": method, "params": params}
            if expects_response:
                message["id"] = request_id
            stdin.write((json.dumps(message) + "\n").encode())
            await stdin.drain()
            return request_id

        async def response_for(expected_id: int) -> dict[str, Any]:
            while True:
                line = await stdout.readline()
                if not line:
                    raise RuntimeError("Codex app-server closed unexpectedly")
                message: dict[str, Any] = json.loads(line)
                if message.get("id") == expected_id:
                    if "error" in message:
                        raise RuntimeError(f"Codex app-server error: {message['error']}")
                    return message
                events.append(message)

        try:
            initialize_id = await send("initialize", {"clientInfo": {
                "name": "scope_guard", "title": "Scope Guard", "version": "0.1.0"}})
            await asyncio.wait_for(response_for(initialize_id), config.codex_timeout_seconds)
            await send("initialized", {}, expects_response=False)
            method = "thread/resume" if thread_id else "thread/start"
            params: dict[str, Any] = ({"threadId": thread_id} if thread_id else {
                "model": config.codex_model, "cwd": config.demo_workspace_root,
                "sandbox": "read-only", "approvalPolicy": "never", "ephemeral": False})
            thread_request_id = await send(method, params)
            thread_response = await asyncio.wait_for(response_for(thread_request_id),
                                                     config.codex_timeout_seconds)
            live_thread_id = str(thread_response["result"]["thread"]["id"])
            turn_id = await send("turn/start", {"threadId": live_thread_id,
                "input": [{"type": "text", "text": prompt}], "outputSchema": output_schema,
                "approvalPolicy": "never"})
            await asyncio.wait_for(response_for(turn_id), config.codex_timeout_seconds)
            output = ""
            while True:
                line = await asyncio.wait_for(stdout.readline(), config.codex_timeout_seconds)
                if not line:
                    raise RuntimeError("Codex app-server closed before turn completion")
                event: dict[str, Any] = json.loads(line)
                events.append(event)
                if event.get("method") == "item/completed":
                    item = event.get("params", {}).get("item", {})
                    if item.get("type") == "agentMessage":
                        output = str(item.get("text", ""))
                if event.get("method") == "turn/completed":
                    break
            if not output:
                summary = [(event.get("method"), (event.get("params") or {}).get("item", {}).get("type"),
                            ((event.get("params") or {}).get("error") or {}).get("message"))
                           for event in events]
                raise ValueError(f"Codex turn completed without proposed actions; events={summary}")
            return live_thread_id, output, events
        finally:
            process.terminate()
            await process.wait()


def codex_adapter() -> CodexAdapter:
    config = settings()
    if config.codex_provider == "live":
        return CodexAppServerAdapter()
    return DemoCodexAdapter()


def codex_event_metadata(adapter: CodexAdapter) -> dict[str, Any]:
    return {"provider": adapter.provider, "thread_id": adapter.thread_id,
            "recorded_at": datetime.now(UTC).isoformat()}
