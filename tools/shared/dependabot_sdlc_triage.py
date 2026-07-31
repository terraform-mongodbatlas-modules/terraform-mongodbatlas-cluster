from __future__ import annotations

import base64
import json
import logging
import os
import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

COMMENT_MARKER = "<!-- dependabot-sdlc-triage -->"
DEPENDABOT_LOGIN = "dependabot[bot]"
SDLC_MARKER = "path-sync copy -n sdlc"
GITHUB_ACTIONS_ECOSYSTEM = "github_actions"
API_REQUEST_TIMEOUT_SECONDS = 15
SECTION_MARKER_PATTERN = re.compile(
    r"^\s*#\s*===\s*(DO_NOT_EDIT|OK_EDIT):\s*path-sync\s+\S+\s*===\s*$"
)
USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*(.+?)\s*$")
# Composite actions do not carry the path-sync marker that identifies copied workflows.
COMPOSITE_ACTION_MANAGED_PREFIXES = (".github/actions/",)


@dataclass(frozen=True)
class Label:
    name: str
    color: str
    description: str


MANAGED_LABEL = Label(
    name="dependabot-cluster",
    color="D93F0B",
    description="Dependency update touches files managed by the cluster SDLC sync.",
)
DESTINATION_LABEL = Label(
    name="dependabot-required",
    color="0E8A16",
    description="Dependency update only touches destination-owned files.",
)
UNSUPPORTED_LABEL = Label(
    name="dependabot-unsupported",
    color="FBCA04",
    description="Dependabot update needs manual review: unsupported or unclassified.",
)
TRIAGE_LABELS = (MANAGED_LABEL, DESTINATION_LABEL, UNSUPPORTED_LABEL)


@dataclass(frozen=True)
class ActionReferenceChange:
    path: str
    action: str
    before: str | None
    after: str | None


@dataclass(frozen=True)
class ActionClassification:
    managed: tuple[ActionReferenceChange, ...]
    destination: tuple[ActionReferenceChange, ...]
    unclassified: tuple[ActionReferenceChange, ...] = ()
    unclassified_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class _UsesReference:
    line_number: int
    action: str
    ref: str


class GitHubApiError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        self.status = status
        super().__init__(f"GitHub API returned {status}: {message}")


class GitHubClient:
    def __init__(
        self,
        token: str | None,
        repository: str,
        api_url: str = "https://api.github.com",
    ) -> None:
        owner, separator, repo = repository.partition("/")
        if not separator or not owner or not repo:
            raise ValueError(f"invalid GitHub repository: {repository!r}")
        self.token = token
        self.owner = owner
        self.repo = repo
        self.api_url = api_url.rstrip("/")

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> Any:
        repository_path = f"/repos/{quote(self.owner)}/{quote(self.repo)}"
        url = f"{self.api_url}{repository_path}{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "dependabot-sdlc-triage",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, data=data, method=method, headers=headers)
        try:
            with urlopen(request, timeout=API_REQUEST_TIMEOUT_SECONDS) as response:
                body = response.read()
        except HTTPError as error:
            message = error.read().decode(errors="replace")
            raise GitHubApiError(error.code, message) from error
        if not body:
            return None
        return json.loads(body)

    def _paginate(
        self,
        path: str,
        *,
        query: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page = 1
        while True:
            page_query = dict(query or {})
            page_query.update({"per_page": 100, "page": page})
            batch = self._request(
                "GET",
                path,
                query=page_query,
            )
            if not isinstance(batch, list):
                raise TypeError(f"expected a list from {path}")
            items.extend(batch)
            if len(batch) < 100:
                return items
            page += 1

    def list_pull_files(self, pull_number: int) -> list[dict[str, Any]]:
        return self._paginate(f"/pulls/{pull_number}/files")

    def list_open_pulls(self) -> list[dict[str, Any]]:
        return self._paginate("/pulls", query={"state": "open"})

    def read_file(self, path: str, ref: str) -> str | None:
        try:
            data = self._request(
                "GET",
                f"/contents/{quote(path, safe='/')}",
                query={"ref": ref},
            )
        except GitHubApiError as error:
            if error.status == 404:
                return None
            raise
        if not isinstance(data, dict) or data.get("type") != "file" or not data.get("content"):
            return None
        encoding = data.get("encoding")
        if encoding != "base64":
            raise ValueError(f"unsupported content encoding for {path}: {encoding!r}")
        return base64.b64decode(data["content"]).decode()

    def ensure_label(self, label: Label) -> None:
        try:
            self._request("GET", f"/labels/{quote(label.name)}")
        except GitHubApiError as error:
            if error.status != 404:
                raise
            self._request(
                "POST",
                "/labels",
                payload={
                    "name": label.name,
                    "color": label.color,
                    "description": label.description,
                },
            )

    def remove_label(self, pull_number: int, label: Label) -> None:
        self._request(
            "DELETE",
            f"/issues/{pull_number}/labels/{quote(label.name)}",
        )

    def add_label(self, pull_number: int, label: Label) -> None:
        self._request(
            "POST",
            f"/issues/{pull_number}/labels",
            payload={"labels": [label.name]},
        )

    def list_issue_labels(self, pull_number: int) -> list[dict[str, Any]]:
        return self._paginate(f"/issues/{pull_number}/labels")

    def list_comments(self, pull_number: int) -> list[dict[str, Any]]:
        return self._paginate(f"/issues/{pull_number}/comments")

    def create_comment(self, pull_number: int, body: str) -> None:
        self._request(
            "POST",
            f"/issues/{pull_number}/comments",
            payload={"body": body},
        )


def is_dependabot_event(event: dict[str, Any]) -> bool:
    return is_dependabot_pull_request(event.get("pull_request", {}))


def is_dependabot_pull_request(pull_request: dict[str, Any]) -> bool:
    return pull_request.get("user", {}).get("login") == DEPENDABOT_LOGIN


def dependabot_ecosystem(pull_request: dict[str, Any]) -> str | None:
    if not is_dependabot_pull_request(pull_request):
        return None
    head_ref = pull_request["head"]["ref"]
    parts = head_ref.split("/", 2)
    if len(parts) < 3 or parts[0] != "dependabot":
        return None
    return parts[1]


def is_sdlc_managed(content: str | None) -> bool:
    if content is None:
        return False
    first_line = content.splitlines()[0] if content.splitlines() else ""
    return SDLC_MARKER in first_line


def _whole_file_managed(path: str, content: str) -> bool:
    return path.startswith(COMPOSITE_ACTION_MANAGED_PREFIXES) or is_sdlc_managed(content)


def _line_ownership(path: str, content: str) -> dict[int, str]:
    ownership = "managed" if _whole_file_managed(path, content) else "destination"
    result: dict[int, str] = {}
    for line_number, line in enumerate(content.splitlines(), start=1):
        if marker := SECTION_MARKER_PATTERN.match(line):
            ownership = "managed" if marker.group(1) == "DO_NOT_EDIT" else "destination"
        result[line_number] = ownership
    return result


def _uses_value(line: str) -> str | None:
    match = USES_PATTERN.match(line)
    if not match:
        return None
    value = match.group(1).split(" #", 1)[0].strip()
    if value.startswith(("'", '"')) and value.endswith(value[0]):
        value = value[1:-1]
    if value.startswith(("./", "docker://", "${{")) or "@" not in value:
        return None
    return value


def _uses_references(content: str) -> dict[tuple[str, int], _UsesReference]:
    occurrences: defaultdict[str, int] = defaultdict(int)
    references: dict[tuple[str, int], _UsesReference] = {}
    for line_number, line in enumerate(content.splitlines(), start=1):
        value = _uses_value(line)
        if value is None:
            continue
        action, ref = value.rsplit("@", 1)
        occurrence = occurrences[action]
        occurrences[action] += 1
        references[(action, occurrence)] = _UsesReference(
            line_number=line_number,
            action=action,
            ref=ref,
        )
    return references


def classify_action_references(
    files: list[dict[str, Any]],
    read_file: Callable[[str, str], str | None],
    base_ref: str,
    head_ref: str,
) -> ActionClassification:
    managed: list[ActionReferenceChange] = []
    destination: list[ActionReferenceChange] = []
    unclassified: list[ActionReferenceChange] = []
    unclassified_paths: list[str] = []

    for file in files:
        filename = file["filename"]
        base_path = file.get("previous_filename") if file.get("status") == "renamed" else filename
        if not base_path:
            unclassified_paths.append(filename)
            continue

        base_content = read_file(base_path, base_ref)
        head_content = read_file(filename, head_ref)
        if base_content is None or head_content is None:
            unclassified_paths.append(filename)
            continue

        base_references = _uses_references(base_content)
        head_references = _uses_references(head_content)
        ownership = _line_ownership(base_path, base_content)
        changed_count = 0
        for key in sorted(base_references.keys() | head_references.keys()):
            before = base_references.get(key)
            after = head_references.get(key)
            if before and after and before.ref == after.ref:
                continue
            changed_count += 1
            reference = before or after
            assert reference is not None
            change = ActionReferenceChange(
                path=filename,
                action=reference.action,
                before=before.ref if before else None,
                after=after.ref if after else None,
            )
            if before is None or after is None:
                unclassified.append(change)
            elif ownership.get(before.line_number) == "managed":
                managed.append(change)
            else:
                destination.append(change)
        if changed_count == 0:
            unclassified_paths.append(filename)

    return ActionClassification(
        managed=tuple(managed),
        destination=tuple(destination),
        unclassified=tuple(unclassified),
        unclassified_paths=tuple(unclassified_paths),
    )


def render_comment() -> str:
    return "\n".join(
        [
            COMMENT_MARKER,
            "## Dependabot SDLC triage",
            "",
            "Review this pull request's `dependabot-*` labels.",
            "",
            "- `dependabot-cluster`: this update affects SDLC-managed content. Do not merge this "
            "pull request. If a matching cluster Dependabot PR exists, wait for it and its SDLC "
            "sync. If none exists, the source may be a destination-only workflow that Dependabot "
            "does not scan in cluster. Create a cluster PR with the suggested action version, then "
            "merge its SDLC sync.",
            "- `dependabot-required`: this pull request contains destination-owned updates. It can "
            "follow normal review once it has no `dependabot-cluster` label.",
            "- Both labels: follow the `dependabot-cluster` guidance first. Then run triage again; "
            "merge only when `dependabot-cluster` has been removed.",
            "- `dependabot-unsupported`: automatic ownership classification was not possible. "
            "Review manually and extend the triage script if this update type should be supported.",
            "",
            "If this pull request has no `dependabot-*` label, check the Dependabot SDLC triage "
            "workflow run before relying on it. If it did not run or failed, correct the workflow "
            "or script and rerun it manually.",
            "",
            "After a cluster update and its SDLC sync are merged, comment `@dependabot recreate` "
            "on this pull request to rebuild it from the updated default branch. Triage runs "
            "automatically after the refresh; run it manually if labels still need reconciliation.",
            "",
            "If Dependabot PR checks fail because they need credentials, define them as Dependabot "
            "secrets as well as Actions secrets. Dependabot-triggered checks cannot access Actions "
            "secrets.",
        ]
    )


def classify_pull_request(
    pull_request: dict[str, Any],
    client: GitHubClient,
) -> ActionClassification:
    pull_number = int(pull_request["number"])
    base_ref = pull_request["base"]["sha"]
    head_ref = pull_request["head"]["sha"]
    files = client.list_pull_files(pull_number)
    return classify_action_references(files, client.read_file, base_ref, head_ref)


def desired_labels(classification: ActionClassification) -> tuple[Label, ...]:
    if classification.unclassified or classification.unclassified_paths:
        return (UNSUPPORTED_LABEL,)
    labels = []
    if classification.managed:
        labels.append(MANAGED_LABEL)
    if classification.destination:
        labels.append(DESTINATION_LABEL)
    return tuple(labels) or (UNSUPPORTED_LABEL,)


def reconcile_labels(
    pull_request: dict[str, Any], desired: tuple[Label, ...], client: GitHubClient
) -> None:
    pull_number = int(pull_request["number"])
    current_names = {label["name"] for label in client.list_issue_labels(pull_number)}
    desired_names = {label.name for label in desired}
    for label in desired:
        client.ensure_label(label)
    for label in TRIAGE_LABELS:
        if label.name in current_names - desired_names:
            client.remove_label(pull_number, label)
    for label in desired:
        if label.name not in current_names:
            client.add_label(pull_number, label)


def create_comment_once(pull_number: int, client: GitHubClient) -> None:
    existing_comment = next(
        (
            comment
            for comment in client.list_comments(pull_number)
            if comment.get("user", {}).get("type") == "Bot"
            and COMMENT_MARKER in comment.get("body", "")
        ),
        None,
    )
    if not existing_comment:
        client.create_comment(pull_number, render_comment())


def triage_event(
    event: dict[str, Any],
    client: GitHubClient,
) -> ActionClassification | None:
    if not is_dependabot_event(event):
        return None

    pull_request = event["pull_request"]
    ecosystem = dependabot_ecosystem(pull_request)
    classification = (
        classify_pull_request(pull_request, client)
        if ecosystem == GITHUB_ACTIONS_ECOSYSTEM
        else ActionClassification((), (), unclassified_paths=("unsupported ecosystem",))
    )
    create_comment_once(int(pull_request["number"]), client)
    reconcile_labels(pull_request, desired_labels(classification), client)
    return classification


def triage_open_dependabot_pulls(client: GitHubClient) -> tuple[int, ...]:
    refreshed: list[int] = []
    for pull_request in open_dependabot_pulls(client):
        triage_event({"pull_request": pull_request}, client)
        refreshed.append(int(pull_request["number"]))
    return tuple(refreshed)


def open_dependabot_pulls(client: GitHubClient) -> list[dict[str, Any]]:
    return [pull for pull in client.list_open_pulls() if is_dependabot_pull_request(pull)]


def _github_actions_error_annotation(error: Exception) -> str:
    message = str(error).replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return f"::error title=Dependabot SDLC triage failed::{message}"


def main() -> None:
    event_path = Path(os.environ["GITHUB_EVENT_PATH"])
    event = json.loads(event_path.read_text())
    destination_client = GitHubClient(
        token=os.environ["GITHUB_TOKEN"],
        repository=os.environ["GITHUB_REPOSITORY"],
        api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
    )
    event_name = os.environ["GITHUB_EVENT_NAME"]
    if event_name == "pull_request_target":
        triage_event(event, destination_client)
    elif event_name in {"schedule", "workflow_dispatch"}:
        triage_open_dependabot_pulls(destination_client)
    else:
        raise ValueError(f"unsupported GitHub event: {event_name}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(_github_actions_error_annotation(error))
        logging.exception("Dependabot SDLC triage failed")
        raise
