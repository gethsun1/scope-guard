import posixpath
import re
import shlex
from dataclasses import dataclass, field

from .inventory import all_resources
from .models import Resource, ResourceType

DANGEROUS = (("rm", "-rf"), ("git", "clean"), ("git", "reset", "--hard"),
             ("find", "-delete"), ("chmod", "-R"), ("chown", "-R"))
SECRETS = (".env", "id_rsa", "credentials", "secret")
OPERATORS = {";", "&&", "||", "|", ">", ">>", "<"}


@dataclass
class CommandAnalysis:
    command: str
    tokens: list[str]
    resources: list[Resource] = field(default_factory=list)
    dangerous_patterns: list[str] = field(default_factory=list)
    secret_access: bool = False
    network_destination: str | None = None
    ambiguous: bool = False


def normalize_path(path: str, working_directory: str) -> str:
    normalized = posixpath.normpath(posixpath.join(working_directory, path) if not path.startswith("/") else path)
    if normalized != "/workspace" and not normalized.startswith("/workspace/"):
        raise ValueError("path escapes /workspace")
    return normalized


def analyze(command: str, working_directory: str = "/workspace/projects/rdsocial") -> CommandAnalysis:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|><")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return CommandAnalysis(command, [], dangerous_patterns=["malformed_shell"], ambiguous=True)
    result = CommandAnalysis(command, tokens)
    lowered = tuple(token.lower() for token in tokens)
    for sequence in DANGEROUS:
        if any(lowered[index:index + len(sequence)] == sequence for index in range(len(lowered))):
            result.dangerous_patterns.append(" ".join(sequence))
    joined = " ".join(lowered)
    if "drop database" in joined or "truncate" in lowered:
        result.dangerous_patterns.append("destructive_database_operation")
    if "find" in lowered and "-delete" in lowered:
        result.dangerous_patterns.append("find -delete")
    result.secret_access = any(secret in token.lower() for token in tokens for secret in SECRETS)
    if any(token in {"curl", "wget", "scp", "nc"} for token in lowered):
        result.network_destination = next((token for token in tokens if "://" in token), "unknown")
    for resource in all_resources():
        pattern = rf"(?<![A-Za-z0-9_-]){re.escape(resource.identifier)}(?![A-Za-z0-9_-])"
        if re.search(pattern, command):
            result.resources.append(resource)
    for token in tokens:
        if token.startswith(("/", "./", "../")) and not token.startswith(("http://", "https://")):
            try:
                path = normalize_path(token, working_directory)
            except ValueError:
                result.dangerous_patterns.append("path_escape")
                continue
            if not any(path == resource.identifier for resource in result.resources):
                protected = path.startswith("/workspace/projects/engageflow")
                project = "engageflow" if protected else (
                    "rdsocial" if path.startswith("/workspace/projects/rdsocial") else None)
                result.resources.append(Resource(type=ResourceType.FILESYSTEM_PATH,
                    identifier=path, project_id=project, protected=protected))
    result.ambiguous = (any(token in OPERATORS for token in tokens) and not result.resources)
    return result
