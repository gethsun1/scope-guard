import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .models import AuditEvent


class AuditChain:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    def append(self, task_id: str, event_type: str, actor: str, payload: dict[str, Any],
               severity: str = "info") -> AuditEvent:
        previous = self.events[-1].event_hash if self.events else "GENESIS"
        created = datetime.now(UTC)
        body = {"task_id": task_id, "event_type": event_type, "actor": actor,
                "severity": severity, "payload": payload, "previous_hash": previous,
                "created_at": created.isoformat()}
        digest = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        event = AuditEvent(id=str(uuid4()), task_id=task_id, event_type=event_type, actor=actor,
            severity=severity, payload=payload, previous_hash=previous, event_hash=digest,
            created_at=created)
        self.events.append(event)
        return event

    def verify(self) -> bool:
        return all(event.previous_hash == ("GENESIS" if index == 0 else
                   self.events[index - 1].event_hash) for index, event in enumerate(self.events))
