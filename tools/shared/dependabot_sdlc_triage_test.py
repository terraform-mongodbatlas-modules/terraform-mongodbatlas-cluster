from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from shared import dependabot_sdlc_triage
from shared.dependabot_sdlc_triage import (
    COMMENT_MARKER,
    DESTINATION_LABEL,
    MANAGED_LABEL,
    UNSUPPORTED_LABEL,
    ActionClassification,
    ActionReferenceChange,
    GitHubClient,
    classify_action_references,
    dependabot_ecosystem,
    is_dependabot_pull_request,
    is_sdlc_managed,
    render_comment,
    triage_event,
    triage_open_dependabot_pulls,
)


class FakeClient:
    def __init__(
        self,
        *,
        files: list[dict[str, Any]] | None = None,
        files_by_pull: dict[int, list[dict[str, Any]]] | None = None,
        contents: dict[tuple[str, str], str | None] | None = None,
        comments: list[dict[str, Any]] | None = None,
        issue_labels: list[str] | None = None,
        open_pulls: list[dict[str, Any]] | None = None,
    ) -> None:
        self.files = files or []
        self.files_by_pull = files_by_pull or {}
        self.contents = contents or {}
        self.comments_by_pull = {42: comments or []}
        self.issue_labels_by_pull = {42: set(issue_labels or [])}
        self.open_pulls = open_pulls or []
        self.ensured_labels = []
        self.removed_labels = []
        self.added_labels = []
        self.created_comments = []
        self.operations = []
        self.reads = []
        self.list_open_pulls_count = 0

    def list_pull_files(self, pull_number: int) -> list[dict[str, Any]]:
        return self.files_by_pull.get(pull_number, self.files)

    def list_open_pulls(self) -> list[dict[str, Any]]:
        self.list_open_pulls_count += 1
        return self.open_pulls

    def read_file(self, path: str, ref: str) -> str | None:
        self.reads.append((path, ref))
        return self.contents.get((path, ref))

    def ensure_label(self, label) -> None:
        self.operations.append("ensure-label")
        self.ensured_labels.append(label)

    def remove_label(self, pull_number: int, label) -> None:
        self.operations.append("remove-label")
        self.removed_labels.append((pull_number, label))
        self.issue_labels_by_pull[pull_number].remove(label.name)

    def add_label(self, pull_number: int, label) -> None:
        self.operations.append("add-label")
        self.added_labels.append((pull_number, label))
        self.issue_labels_by_pull.setdefault(pull_number, set()).add(label.name)

    def list_issue_labels(self, pull_number: int) -> list[dict[str, str]]:
        return [{"name": name} for name in self.issue_labels_by_pull.setdefault(pull_number, set())]

    def list_comments(self, pull_number: int) -> list[dict[str, Any]]:
        return self.comments_by_pull.setdefault(pull_number, [])

    def create_comment(self, pull_number: int, body: str) -> None:
        self.operations.append("create-comment")
        self.created_comments.append((pull_number, body))


def _pull(
    number: int = 42,
    *,
    login: str = "dependabot[bot]",
    head_ref: str = "dependabot/github_actions/github-actions-example",
    head_sha: str = "head-sha",
    title: str = "chore(deps): bump actions/example from 1.2.2 to 1.2.3",
    base_sha: str = "base-sha",
    html_url: str | None = None,
) -> dict[str, Any]:
    return {
        "number": number,
        "user": {"login": login},
        "base": {"sha": base_sha},
        "head": {"ref": head_ref, "sha": head_sha},
        "title": title,
        "html_url": html_url or f"https://github.com/example/repo/pull/{number}",
    }


def _event(login: str = "dependabot[bot]") -> dict[str, Any]:
    return {"pull_request": _pull(login=login)}


def _sectioned_workflow(
    managed_ref: str = "old-managed",
    destination_ref: str = "old-destination",
) -> str:
    return f"""# path-sync copy -n sdlc
# === DO_NOT_EDIT: path-sync shared ===
jobs:
  shared:
    steps:
      - uses: actions/checkout@{managed_ref}
# === OK_EDIT: path-sync shared ===
  destination:
    steps:
      - uses: google-github-actions/auth@{destination_ref} # destination setup
"""


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("# path-sync copy -n sdlc\ncontent", True),
        ("<!-- path-sync copy -n sdlc -->\ncontent", True),
        ("content\n# path-sync copy -n sdlc", False),
        (None, False),
        ("", False),
    ],
)
def test_is_sdlc_managed_uses_first_line(content, expected):
    assert is_sdlc_managed(content) is expected


def test_triage_label_names():
    assert MANAGED_LABEL.name == "dependabot-cluster"
    assert DESTINATION_LABEL.name == "dependabot-required"
    assert UNSUPPORTED_LABEL.name == "dependabot-unsupported"
    assert "unclassified" in UNSUPPORTED_LABEL.description
    assert all(
        len(label.description) <= 100
        for label in (MANAGED_LABEL, DESTINATION_LABEL, UNSUPPORTED_LABEL)
    )


def test_dependabot_ecosystem_uses_branch_prefix():
    assert dependabot_ecosystem(_pull()) == "github_actions"
    assert (
        dependabot_ecosystem(_pull(head_ref="dependabot/go_modules/tools/example-1.2.3"))
        == "go_modules"
    )
    assert dependabot_ecosystem(_pull(head_ref="feature/example")) is None


def test_is_dependabot_pull_request_checks_the_pr_author():
    assert is_dependabot_pull_request(_pull())
    assert not is_dependabot_pull_request(_pull(login="octocat"))


def test_classify_action_references_uses_trusted_base_section_markers():
    path = ".github/workflows/pre-release-tests.yml"
    contents = {
        (path, "base"): _sectioned_workflow(),
        (path, "head"): _sectioned_workflow(
            managed_ref="new-managed",
            destination_ref="new-destination",
        ),
    }

    classification = classify_action_references(
        [{"filename": path, "status": "modified"}],
        lambda file_path, ref: contents.get((file_path, ref)),
        "base",
        "head",
    )

    assert classification == ActionClassification(
        managed=(
            ActionReferenceChange(
                path=path,
                action="actions/checkout",
                before="old-managed",
                after="new-managed",
            ),
        ),
        destination=(
            ActionReferenceChange(
                path=path,
                action="google-github-actions/auth",
                before="old-destination",
                after="new-destination",
            ),
        ),
    )


def test_classify_action_references_ignores_untrusted_head_marker_changes():
    path = ".github/workflows/pre-release-tests.yml"
    base = _sectioned_workflow()
    head = _sectioned_workflow(destination_ref="new-destination").replace(
        "OK_EDIT: path-sync shared",
        "DO_NOT_EDIT: path-sync shared",
    )

    classification = classify_action_references(
        [{"filename": path, "status": "modified"}],
        lambda file_path, ref: {(path, "base"): base, (path, "head"): head}.get((file_path, ref)),
        "base",
        "head",
    )

    assert classification.managed == ()
    assert classification.destination == (
        ActionReferenceChange(
            path=path,
            action="google-github-actions/auth",
            before="old-destination",
            after="new-destination",
        ),
    )


def test_classify_action_references_uses_marker_for_new_copied_workflows():
    path = ".github/workflows/notify-docs-team.yml"
    contents = {
        (path, "base"): "# path-sync copy -n sdlc\nsteps:\n  - uses: actions/checkout@old\n",
        (path, "head"): "# path-sync copy -n sdlc\nsteps:\n  - uses: actions/checkout@new\n",
    }

    classification = classify_action_references(
        [{"filename": path, "status": "modified"}],
        lambda file_path, ref: contents.get((file_path, ref)),
        "base",
        "head",
    )

    assert classification.managed == (
        ActionReferenceChange(path, "actions/checkout", "old", "new"),
    )
    assert classification.destination == ()


def test_classify_action_references_treats_composite_actions_as_managed_without_marker():
    path = ".github/actions/setup/action.yml"
    contents = {
        (path, "base"): "runs:\n  using: composite\n  steps:\n    - uses: actions/checkout@old\n",
        (path, "head"): "runs:\n  using: composite\n  steps:\n    - uses: actions/checkout@new\n",
    }

    classification = classify_action_references(
        [{"filename": path, "status": "modified"}],
        lambda file_path, ref: contents.get((file_path, ref)),
        "base",
        "head",
    )

    assert classification.managed == (
        ActionReferenceChange(path, "actions/checkout", "old", "new"),
    )
    assert classification.destination == ()


def test_classify_action_references_treats_unknown_workflow_as_destination_owned():
    path = ".github/workflows/destination-only.yml"
    contents = {
        (path, "base"): 'steps:\n  - uses: "example/action@old" # pinned\n',
        (path, "head"): 'steps:\n  - uses: "example/action@new" # pinned\n',
    }

    classification = classify_action_references(
        [{"filename": path, "status": "modified"}],
        lambda file_path, ref: contents.get((file_path, ref)),
        "base",
        "head",
    )

    assert classification.managed == ()
    assert classification.destination == (
        ActionReferenceChange(path, "example/action", "old", "new"),
    )


def test_classify_action_references_marks_missing_content_unclassified():
    path = ".github/workflows/missing.yml"

    classification = classify_action_references(
        [{"filename": path, "status": "modified"}],
        lambda _path, _ref: None,
        "base",
        "head",
    )

    assert classification == ActionClassification(
        managed=(),
        destination=(),
        unclassified_paths=(path,),
    )


def test_non_dependabot_event_has_no_effect():
    client = FakeClient()

    assert triage_event(_event("contributor"), client) is None
    assert client.ensured_labels == []
    assert client.created_comments == []


def test_managed_references_select_sync_label_and_create_comment():
    path = ".github/workflows/notify-docs-team.yml"
    client = FakeClient(
        files=[{"filename": path, "status": "modified"}],
        contents={
            (
                path,
                "base-sha",
            ): "# path-sync copy -n sdlc\nsteps:\n  - uses: actions/checkout@old\n",
            (
                path,
                "head-sha",
            ): "# path-sync copy -n sdlc\nsteps:\n  - uses: actions/checkout@new\n",
        },
    )

    classification = triage_event(_event(), client)

    assert classification == ActionClassification(
        managed=(ActionReferenceChange(path, "actions/checkout", "old", "new"),),
        destination=(),
    )
    assert client.ensured_labels == [MANAGED_LABEL]
    assert client.removed_labels == []
    assert client.added_labels == [(42, MANAGED_LABEL)]
    assert len(client.created_comments) == 1
    assert client.operations[0] == "create-comment"
    body = client.created_comments[0][1]
    assert COMMENT_MARKER in body
    assert "Review this pull request's `dependabot-*` labels" in body
    assert "If it did not run or failed" in body


def test_mixed_references_list_both_and_require_cluster_first():
    path = ".github/workflows/pre-release-tests.yml"
    client = FakeClient(
        files=[{"filename": path, "status": "modified"}],
        contents={
            (path, "base-sha"): _sectioned_workflow(),
            (path, "head-sha"): _sectioned_workflow(
                managed_ref="new-managed",
                destination_ref="new-destination",
            ),
        },
    )

    classification = triage_event(_event(), client)

    assert classification is not None
    assert len(classification.managed) == 1
    assert len(classification.destination) == 1
    assert client.added_labels == [(42, MANAGED_LABEL), (42, DESTINATION_LABEL)]
    body = client.created_comments[0][1]
    assert "If a matching cluster Dependabot PR exists" in body
    assert "Create a cluster PR with the suggested action version" in body
    assert "Both labels: follow the `dependabot-cluster` guidance first" in body


def test_destination_references_reconcile_only_changed_labels_and_keep_comment():
    path = ".github/workflows/destination-only.yml"
    client = FakeClient(
        files=[{"filename": path, "status": "modified"}],
        contents={
            (path, "base-sha"): "steps:\n  - uses: example/action@old\n",
            (path, "head-sha"): "steps:\n  - uses: example/action@new\n",
        },
        comments=[
            {
                "id": 123,
                "user": {"type": "Bot"},
                "body": f"{COMMENT_MARKER}\nold result",
            }
        ],
        issue_labels=[MANAGED_LABEL.name, UNSUPPORTED_LABEL.name],
    )

    classification = triage_event(_event(), client)

    assert classification == ActionClassification(
        managed=(),
        destination=(ActionReferenceChange(path, "example/action", "old", "new"),),
    )
    assert client.removed_labels == [(42, MANAGED_LABEL), (42, UNSUPPORTED_LABEL)]
    assert client.added_labels == [(42, DESTINATION_LABEL)]
    assert client.created_comments == []


def test_non_github_actions_dependabot_pr_gets_unsupported_label_and_comment():
    client = FakeClient()
    event = {
        "pull_request": _pull(
            head_ref="dependabot/go_modules/tools/example-1.2.3",
            title="chore(deps): bump example from 1.2.2 to 1.2.3",
        )
    }

    assert triage_event(event, client) == ActionClassification(
        managed=(),
        destination=(),
        unclassified_paths=("unsupported ecosystem",),
    )
    assert client.reads == []
    assert client.removed_labels == []
    assert client.added_labels == [(42, UNSUPPORTED_LABEL)]
    body = client.created_comments[0][1]
    assert "dependabot-unsupported" in body


def test_unclassified_github_actions_change_gets_unsupported_label():
    path = ".github/workflows/missing.yml"
    client = FakeClient(
        files=[{"filename": path, "status": "modified"}],
    )

    classification = triage_event(_event(), client)

    assert classification == ActionClassification(
        managed=(),
        destination=(),
        unclassified_paths=(path,),
    )
    assert client.added_labels == [(42, UNSUPPORTED_LABEL)]
    body = client.created_comments[0][1]
    assert "automatic ownership classification was not possible" in body


def test_scheduled_triage_processes_every_open_dependabot_pull():
    managed_path = ".github/workflows/notify-docs-team.yml"
    destination_path = ".github/workflows/destination-only.yml"
    matched_managed = _pull(
        42,
        base_sha="base-42",
        head_sha="head-42",
    )
    second_managed = _pull(
        43,
        head_ref="dependabot/github_actions/github-actions-other",
        head_sha="head-43",
        title="chore(deps): bump actions/other from 1.0.0 to 2.0.0",
        base_sha="base-43",
    )
    destination = _pull(
        44,
        head_ref="dependabot/github_actions/actions/example-2",
        head_sha="head-44",
        title="chore(deps): bump actions/example from 1 to 2",
        base_sha="base-44",
    )
    client = FakeClient(
        open_pulls=[
            matched_managed,
            second_managed,
            destination,
            _pull(45, login="user"),
        ],
        files_by_pull={
            42: [{"filename": managed_path, "status": "modified"}],
            43: [{"filename": managed_path, "status": "modified"}],
            44: [{"filename": destination_path, "status": "modified"}],
        },
        contents={
            (managed_path, "base-42"): "steps:\n  - uses: actions/checkout@old\n",
            (managed_path, "head-42"): "steps:\n  - uses: actions/checkout@new\n",
            (managed_path, "base-43"): "steps:\n  - uses: actions/checkout@old\n",
            (managed_path, "head-43"): "steps:\n  - uses: actions/checkout@new\n",
            (destination_path, "base-44"): "steps:\n  - uses: example/action@old\n",
            (destination_path, "head-44"): "steps:\n  - uses: example/action@new\n",
        },
    )
    refreshed = triage_open_dependabot_pulls(client)

    assert refreshed == (42, 43, 44)
    assert client.list_open_pulls_count == 1
    assert [pull_number for pull_number, _ in client.created_comments] == [42, 43, 44]
    assert (managed_path, "base-43") in client.reads
    assert (destination_path, "base-44") in client.reads


def test_render_comment_explains_label_driven_triage():
    body = render_comment()

    assert "`dependabot-cluster`" in body
    assert "`dependabot-required`" in body
    assert "`dependabot-unsupported`" in body
    assert "`@dependabot recreate`" in body
    assert "If Dependabot PR checks fail because they need credentials" in body


def test_github_actions_error_annotation_escapes_workflow_commands():
    annotation = dependabot_sdlc_triage._github_actions_error_annotation(
        RuntimeError("status 422\ninvalid % payload")
    )

    assert annotation == (
        "::error title=Dependabot SDLC triage failed::status 422%0Ainvalid %25 payload"
    )


def test_github_client_rejects_invalid_repository():
    with pytest.raises(ValueError, match="invalid GitHub repository"):
        GitHubClient("token", "missing-repo")


@pytest.mark.parametrize(
    ("token", "expected_authorization"),
    [
        (None, None),
        ("token", "Bearer token"),
    ],
)
def test_github_client_only_sends_authorization_when_token_is_set(
    token,
    expected_authorization,
):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = b"[]"
    client = GitHubClient(token, "example/repository")

    with patch.object(dependabot_sdlc_triage, "urlopen", return_value=response) as mock_urlopen:
        client._request("GET", "/pulls")

    request = mock_urlopen.call_args.args[0]
    assert request.get_header("Authorization") == expected_authorization
    assert mock_urlopen.call_args.kwargs["timeout"] == 15


def test_github_client_sends_json_content_type_for_payloads():
    response = MagicMock()
    response.__enter__.return_value.read.return_value = b"{}"
    client = GitHubClient("token", "example/repository")

    with patch.object(dependabot_sdlc_triage, "urlopen", return_value=response) as mock_urlopen:
        client._request("POST", "/issues/42/comments", payload={"body": "test"})

    request = mock_urlopen.call_args.args[0]
    assert request.get_header("Content-type") == "application/json"
    assert request.get_header("User-agent") == "dependabot-sdlc-triage"
