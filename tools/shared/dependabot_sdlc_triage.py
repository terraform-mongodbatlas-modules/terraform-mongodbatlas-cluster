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
CLUSTER_REPOSITORY = "terraform-mongodbatlas-modules/terraform-mongodbatlas-cluster"
DEPENDABOT_LOGIN = "dependabot[bot]"
SDLC_MARKER = "path-sync copy -n sdlc"
GITHUB_ACTIONS_ECOSYSTEM = "github_actions"
SECTION_MARKER_PATTERN = re.compile(
    r"^\s*#\s*===\s*(DO_NOT_EDIT|OK_EDIT):\s*path-sync\s+\S+\s*===\s*$"
)
USES_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*(.+?)\s*$")
# Mirrors whole-file workflow mappings in .github/sdlc.src.yaml. Section-managed workflows are
# classified from their trusted base markers instead.
WHOLE_FILE_MANAGED_PATHS = {
    ".github/workflows/check-changelog-entry-file.yml",
    ".github/workflows/dependabot-sdlc-triage.yml",
    ".github/workflows/generate-changelog.yml",
    ".github/workflows/issues.yml",
    ".github/workflows/notify-docs-team.yml",
    ".github/workflows/pull-request-lint.yml",
    ".github/workflows/release.yml",
    ".github/workflows/sdlc-validate.yml",
    ".github/workflows/update-terraform-versions.yml",
}
WHOLE_FILE_MANAGED_PREFIXES = (".github/actions/",)


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
    description=(
        "Dependabot update needs manual review because its ecosystem is unsupported or "
        "automatic SDLC classification was incomplete."
    ),
)


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
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(url, data=data, method=method, headers=headers)
        try:
            with urlopen(request) as response:
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
        try:
            self._request(
                "DELETE",
                f"/issues/{pull_number}/labels/{quote(label.name)}",
            )
        except GitHubApiError as error:
            if error.status != 404:
                raise

    def add_label(self, pull_number: int, label: Label) -> None:
        self._request(
            "POST",
            f"/issues/{pull_number}/labels",
            payload={"labels": [label.name]},
        )

    def list_comments(self, pull_number: int) -> list[dict[str, Any]]:
        return self._paginate(f"/issues/{pull_number}/comments")

    def create_comment(self, pull_number: int, body: str) -> None:
        self._request(
            "POST",
            f"/issues/{pull_number}/comments",
            payload={"body": body},
        )

    def update_comment(self, comment_id: int, body: str) -> None:
        self._request(
            "PATCH",
            f"/issues/comments/{comment_id}",
            payload={"body": body},
        )


def is_dependabot_event(event: dict[str, Any]) -> bool:
    return event.get("pull_request", {}).get("user", {}).get("login") == DEPENDABOT_LOGIN


def dependabot_pull_key(pull_request: dict[str, Any]) -> tuple[str, str] | None:
    if pull_request.get("user", {}).get("login") != DEPENDABOT_LOGIN:
        return None
    head_ref = pull_request.get("head", {}).get("ref")
    title = pull_request.get("title")
    if not head_ref or not title:
        return None
    return head_ref, title


def matching_cluster_pulls(
    pull_request: dict[str, Any],
    cluster_pulls: list[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    key = dependabot_pull_key(pull_request)
    if key is None:
        return ()
    return tuple(pull for pull in cluster_pulls if dependabot_pull_key(pull) == key)


def dependabot_ecosystem(pull_request: dict[str, Any]) -> str | None:
    if dependabot_pull_key(pull_request) is None:
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
    return (
        path in WHOLE_FILE_MANAGED_PATHS
        or path.startswith(WHOLE_FILE_MANAGED_PREFIXES)
        or is_sdlc_managed(content)
    )


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


def _escape_code(value: str) -> str:
    return value.replace("`", r"\`")


def _reference_list(references: tuple[ActionReferenceChange, ...]) -> str:
    if not references:
        return "_None._"
    lines = []
    for reference in references:
        before = reference.before or "_missing_"
        after = reference.after or "_missing_"
        lines.append(
            f"- `{_escape_code(reference.path)}`: "
            f"`{_escape_code(reference.action)}@{_escape_code(before)}` → "
            f"`{_escape_code(reference.action)}@{_escape_code(after)}`"
        )
    return "\n".join(lines)


def _unclassified_list(classification: ActionClassification) -> str:
    lines = []
    if classification.unclassified:
        lines.append(_reference_list(classification.unclassified))
    lines.extend(
        f"- `{_escape_code(path)}`: automatic GitHub Actions classification was incomplete."
        for path in classification.unclassified_paths
    )
    return "\n".join(lines)


def render_comment(
    classification: ActionClassification,
    cluster_pulls: tuple[dict[str, Any], ...] = (),
) -> str:
    if classification.unclassified or classification.unclassified_paths:
        guidance = (
            "Automatic GitHub Actions classification was incomplete. Review the references "
            "manually and add classifier support before relying on this triage result."
        )
    elif classification.managed and classification.destination:
        guidance = (
            "This pull request mixes cluster-managed and destination-owned GitHub Actions "
            "references.\n\n"
            "Land the equivalent shared update in the "
            "[cluster repository](https://github.com/terraform-mongodbatlas-modules/"
            "terraform-mongodbatlas-cluster) and its SDLC sync first. Then update this pull "
            "request and review the remaining destination-owned references normally."
        )
    elif classification.managed:
        guidance = (
            "This pull request changes only cluster-managed GitHub Actions references.\n\n"
            "Land the equivalent update in the "
            "[cluster repository](https://github.com/terraform-mongodbatlas-modules/"
            "terraform-mongodbatlas-cluster) and its SDLC sync before merging this pull "
            "request. After the sync lands, close this pull request if it was superseded."
        )
    else:
        guidance = (
            "This pull request changes only destination-owned GitHub Actions references, "
            "so it can follow the normal review and merge process."
        )
    lines = [
        COMMENT_MARKER,
        "## Dependabot SDLC triage",
        "",
        guidance,
    ]
    if cluster_pulls:
        lines.extend(
            [
                "",
                "### Matching cluster Dependabot PRs",
                "",
                *(
                    f"- [#{pull['number']}: {pull['title']}]({pull['html_url']})"
                    for pull in cluster_pulls
                ),
            ]
        )
    lines.extend(
        [
            "",
            "### Cluster-managed GitHub Actions references",
            "",
            _reference_list(classification.managed),
            "",
            "### Destination-owned GitHub Actions references",
            "",
            _reference_list(classification.destination),
        ]
    )
    if classification.unclassified or classification.unclassified_paths:
        lines.extend(
            [
                "",
                "### Unclassified GitHub Actions changes",
                "",
                _unclassified_list(classification),
            ]
        )
    return "\n".join(lines)


def render_unsupported_comment(ecosystem: str | None) -> str:
    ecosystem_name = ecosystem or "unknown"
    return "\n".join(
        [
            COMMENT_MARKER,
            "## Dependabot SDLC triage",
            "",
            f"The `{_escape_code(ecosystem_name)}` Dependabot ecosystem is not supported by "
            "automatic SDLC classification.",
            "",
            "No automatic ownership classification was performed. If this ecosystem becomes "
            "destination-managed, add explicit classifier support before relying on automatic "
            "triage.",
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


def apply_triage(
    pull_request: dict[str, Any],
    classification: ActionClassification,
    client: GitHubClient,
    cluster_pulls: tuple[dict[str, Any], ...] = (),
) -> None:
    pull_number = int(pull_request["number"])

    for label in (MANAGED_LABEL, DESTINATION_LABEL, UNSUPPORTED_LABEL):
        client.ensure_label(label)

    if classification.unclassified or classification.unclassified_paths:
        selected_label = UNSUPPORTED_LABEL
    elif classification.managed:
        selected_label = MANAGED_LABEL
    else:
        selected_label = DESTINATION_LABEL
    for label in (MANAGED_LABEL, DESTINATION_LABEL, UNSUPPORTED_LABEL):
        if label != selected_label:
            client.remove_label(pull_number, label)
    client.add_label(pull_number, selected_label)

    body = render_comment(classification, cluster_pulls)
    update_sticky_comment(pull_number, body, client)


def apply_unsupported_triage(
    pull_request: dict[str, Any],
    ecosystem: str | None,
    client: GitHubClient,
) -> None:
    pull_number = int(pull_request["number"])
    for label in (MANAGED_LABEL, DESTINATION_LABEL, UNSUPPORTED_LABEL):
        client.ensure_label(label)
    for label in (MANAGED_LABEL, DESTINATION_LABEL):
        client.remove_label(pull_number, label)
    client.add_label(pull_number, UNSUPPORTED_LABEL)
    update_sticky_comment(
        pull_number,
        render_unsupported_comment(ecosystem),
        client,
    )


def update_sticky_comment(
    pull_number: int,
    body: str,
    client: GitHubClient,
) -> None:
    existing_comment = next(
        (
            comment
            for comment in client.list_comments(pull_number)
            if comment.get("user", {}).get("type") == "Bot"
            and COMMENT_MARKER in comment.get("body", "")
        ),
        None,
    )
    if existing_comment:
        client.update_comment(int(existing_comment["id"]), body)
    else:
        client.create_comment(pull_number, body)


def triage_event(
    event: dict[str, Any],
    client: GitHubClient,
    cluster_pulls: list[dict[str, Any]] | None = None,
) -> ActionClassification | None:
    if not is_dependabot_event(event):
        return None

    pull_request = event["pull_request"]
    ecosystem = dependabot_ecosystem(pull_request)
    if ecosystem != GITHUB_ACTIONS_ECOSYSTEM:
        apply_unsupported_triage(pull_request, ecosystem, client)
        return None

    classification = classify_pull_request(pull_request, client)
    matches = matching_cluster_pulls(pull_request, cluster_pulls or [])
    apply_triage(pull_request, classification, client, matches)
    return classification


def triage_schedule(
    client: GitHubClient,
    cluster_pulls: list[dict[str, Any]],
) -> tuple[int, ...]:
    refreshed: list[int] = []
    for pull_request in client.list_open_pulls():
        matches = matching_cluster_pulls(pull_request, cluster_pulls)
        if not matches:
            continue
        ecosystem = dependabot_ecosystem(pull_request)
        if ecosystem != GITHUB_ACTIONS_ECOSYSTEM:
            apply_unsupported_triage(pull_request, ecosystem, client)
            refreshed.append(int(pull_request["number"]))
            continue
        classification = classify_pull_request(pull_request, client)
        if (
            not classification.managed
            and not classification.unclassified
            and not classification.unclassified_paths
        ):
            continue
        apply_triage(pull_request, classification, client, matches)
        refreshed.append(int(pull_request["number"]))
    return tuple(refreshed)


def open_dependabot_pulls(client: GitHubClient) -> list[dict[str, Any]]:
    return [pull for pull in client.list_open_pulls() if dependabot_pull_key(pull) is not None]


def main() -> None:
    event_path = Path(os.environ["GITHUB_EVENT_PATH"])
    event = json.loads(event_path.read_text())
    destination_client = GitHubClient(
        token=os.environ["GITHUB_TOKEN"],
        repository=os.environ["GITHUB_REPOSITORY"],
        api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
    )
    cluster_client = GitHubClient(
        token=None,
        repository=CLUSTER_REPOSITORY,
        api_url=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
    )
    try:
        cluster_pulls = open_dependabot_pulls(cluster_client)
    except GitHubApiError as error:
        logging.warning("could not list public cluster pull requests: %s", error)
        cluster_pulls = []

    event_name = os.environ["GITHUB_EVENT_NAME"]
    if event_name == "pull_request_target":
        triage_event(event, destination_client, cluster_pulls)
    elif event_name == "schedule":
        triage_schedule(destination_client, cluster_pulls)
    else:
        raise ValueError(f"unsupported GitHub event: {event_name}")


if __name__ == "__main__":
    main()
