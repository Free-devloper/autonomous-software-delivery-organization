import re

_KNOWN_SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{30,}", re.IGNORECASE),
    re.compile(r"glpat-[A-Za-z0-9_\-]{20,}", re.IGNORECASE),
    re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),
    re.compile(r"bearer\s+[A-Za-z0-9_\-\.]{25,}", re.IGNORECASE),
    re.compile(r"password=([^\s&;]+)", re.IGNORECASE),
]

REDACTED_PLACEHOLDER = "[REDACTED_SECRET]"


class SecretScrubber:
    """Automatic output scrubber to redact canary tokens, API keys, and injected secrets."""

    @staticmethod
    def scrub(text: str, explicit_secret_values: list[str] | None = None) -> tuple[str, int]:
        """Scrub known secret patterns and explicit canary secret strings from text."""
        if not text:
            return "", 0

        redacted_count = 0
        scrubbed = text

        # 1. Scrub explicit injected secrets
        if explicit_secret_values:
            for secret_val in explicit_secret_values:
                if secret_val and len(secret_val) >= 4 and secret_val in scrubbed:
                    occurrences = scrubbed.count(secret_val)
                    redacted_count += occurrences
                    scrubbed = scrubbed.replace(secret_val, REDACTED_PLACEHOLDER)

        # 2. Scrub regex patterns
        for pattern in _KNOWN_SECRET_PATTERNS:
            matches = list(pattern.finditer(scrubbed))
            if matches:
                redacted_count += len(matches)
                scrubbed = pattern.sub(REDACTED_PLACEHOLDER, scrubbed)

        return scrubbed, redacted_count


class SecretInjector:
    """Ephemeral in-memory secret injector for sandboxed command execution."""

    @staticmethod
    def prepare_environment(
        base_env: dict[str, str], ephemeral_secrets: dict[str, str]
    ) -> dict[str, str]:
        """Inject ephemeral secrets directly into memory environment without disk writes."""
        env = base_env.copy()
        env.update(ephemeral_secrets)
        return env
