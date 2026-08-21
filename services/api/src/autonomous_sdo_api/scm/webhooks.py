import hashlib
import hmac
from datetime import UTC, datetime
from typing import Any

from autonomous_sdo_api.scm.models import (
    NormalizedWebhookEvent,
    ScmProvider,
    WebhookEventType,
)


def verify_github_signature(raw_body: bytes, signature_header: str | None, secret: str) -> bool:
    """Verify GitHub webhook signature against configured secret using constant-time comparison."""
    if not signature_header or not secret:
        return False

    if not signature_header.startswith("sha256="):
        return False

    received_signature = signature_header.removeprefix("sha256=")
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, received_signature)


def verify_gitlab_token(token_header: str | None, secret: str) -> bool:
    """Verify GitLab webhook token against configured secret using constant-time comparison."""
    if not token_header or not secret:
        return False

    return hmac.compare_digest(token_header, secret)


def normalize_github_webhook(
    event_name: str,
    event_id: str,
    payload: dict[str, Any],
) -> NormalizedWebhookEvent:
    """Normalize a GitHub webhook payload into NormalizedWebhookEvent schema."""
    repo_info = payload.get("repository", {})
    full_name = repo_info.get("full_name", "unknown/unknown")
    sender = payload.get("sender", {}).get("login", "unknown")
    now_utc = datetime.now(UTC)

    if event_name == "push":
        return NormalizedWebhookEvent(
            provider=ScmProvider.GITHUB,
            event_id=event_id,
            event_type=WebhookEventType.PUSH,
            repository_full_name=full_name,
            ref=payload.get("ref"),
            before_sha=payload.get("before") if payload.get("before") != "0" * 40 else None,
            after_sha=payload.get("after") if payload.get("after") != "0" * 40 else None,
            sender=sender,
            timestamp=now_utc,
        )

    if event_name == "pull_request":
        pr = payload.get("pull_request", {})
        head = pr.get("head", {})
        return NormalizedWebhookEvent(
            provider=ScmProvider.GITHUB,
            event_id=event_id,
            event_type=WebhookEventType.PULL_REQUEST,
            repository_full_name=full_name,
            ref=head.get("ref"),
            after_sha=head.get("sha"),
            pr_number=payload.get("number") or pr.get("number"),
            action=payload.get("action"),
            sender=sender,
            timestamp=now_utc,
        )

    if event_name == "ping":
        return NormalizedWebhookEvent(
            provider=ScmProvider.GITHUB,
            event_id=event_id,
            event_type=WebhookEventType.PING,
            repository_full_name=full_name,
            sender=sender,
            timestamp=now_utc,
        )

    return NormalizedWebhookEvent(
        provider=ScmProvider.GITHUB,
        event_id=event_id,
        event_type=WebhookEventType.PUSH,
        repository_full_name=full_name,
        action=event_name,
        sender=sender,
        timestamp=now_utc,
    )


def normalize_gitlab_webhook(
    event_header: str,
    event_id: str,
    payload: dict[str, Any],
) -> NormalizedWebhookEvent:
    """Normalize a GitLab webhook payload into NormalizedWebhookEvent schema."""
    project = payload.get("project", {})
    full_name = project.get("path_with_namespace", "unknown/unknown")
    user_name = payload.get("user_username") or payload.get("user_name", "unknown")
    now_utc = datetime.now(UTC)
    object_kind = payload.get("object_kind") or event_header.lower()

    if "push" in object_kind:
        before = payload.get("before")
        after = payload.get("after")
        return NormalizedWebhookEvent(
            provider=ScmProvider.GITLAB,
            event_id=event_id,
            event_type=WebhookEventType.PUSH,
            repository_full_name=full_name,
            ref=payload.get("ref"),
            before_sha=before if before and before != "0" * 40 else None,
            after_sha=after if after and after != "0" * 40 else None,
            sender=user_name,
            timestamp=now_utc,
        )

    if "merge_request" in object_kind:
        attrs = payload.get("object_attributes", {})
        last_commit = attrs.get("last_commit", {})
        return NormalizedWebhookEvent(
            provider=ScmProvider.GITLAB,
            event_id=event_id,
            event_type=WebhookEventType.PULL_REQUEST,
            repository_full_name=full_name,
            ref=attrs.get("source_branch"),
            after_sha=last_commit.get("id"),
            pr_number=attrs.get("iid"),
            action=attrs.get("action") or attrs.get("state"),
            sender=user_name,
            timestamp=now_utc,
        )

    return NormalizedWebhookEvent(
        provider=ScmProvider.GITLAB,
        event_id=event_id,
        event_type=WebhookEventType.PING,
        repository_full_name=full_name,
        sender=user_name,
        timestamp=now_utc,
    )
