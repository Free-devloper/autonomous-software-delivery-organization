"""Security scanner service: SAST, dependency, and secret scanning."""

from __future__ import annotations

import re
from uuid import UUID, uuid4

from autonomous_sdo_api.security.models import (
    FindingSeverity,
    ScanToolCategory,
    SecurityFinding,
    SecurityScanReport,
)


class SecurityScanner:
    """Orchestrates security scans across multiple tool categories."""

    # Patterns for basic static checks (real tools would shell out)
    _SECRET_PATTERNS: list[tuple[str, str]] = [
        (r"(?i)password\s*=\s*['\"][^'\"]+['\"]", "B105"),
        (r"(?i)api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "B106"),
        (r"(?i)secret\s*=\s*['\"][^'\"]+['\"]", "B107"),
    ]

    _UNSAFE_PATTERNS: list[tuple[str, str, str]] = [
        (r"\beval\s*\(", "B307", "Use of eval() detected"),
        (r"\bexec\s*\(", "B102", "Use of exec() detected"),
        (
            r"\bassert\b",
            "B101",
            "Use of assert in production code",
        ),
    ]

    @staticmethod
    def scan_source_files(
        organization_id: UUID,
        scan_target: str,
        source_files: dict[str, str],
        category: ScanToolCategory = ScanToolCategory.SAST,
    ) -> SecurityScanReport:
        """Scan source code for security issues."""
        org_id = (
            organization_id if isinstance(organization_id, UUID) else UUID(str(organization_id))
        )
        findings: list[SecurityFinding] = []
        finding_counter = 0

        for file_path, content in sorted(source_files.items()):
            lines = content.splitlines()
            for line_no, line in enumerate(lines, start=1):
                # Check unsafe patterns
                for pattern, rule_id, msg in SecurityScanner._UNSAFE_PATTERNS:
                    if re.search(pattern, line):
                        finding_counter += 1
                        findings.append(
                            SecurityFinding(
                                id=f"finding-{finding_counter:04d}",
                                rule_id=rule_id,
                                tool="asdo-sast",
                                category=category,
                                severity=FindingSeverity.MEDIUM,
                                message=msg,
                                file_path=file_path,
                                start_line=line_no,
                                snippet=line.strip()[:120],
                            )
                        )

                # Check secret patterns
                for pattern, rule_id in SecurityScanner._SECRET_PATTERNS:
                    if re.search(pattern, line):
                        finding_counter += 1
                        findings.append(
                            SecurityFinding(
                                id=f"finding-{finding_counter:04d}",
                                rule_id=rule_id,
                                tool="asdo-secret-scanner",
                                category=ScanToolCategory.SECRET,
                                severity=FindingSeverity.HIGH,
                                message="Potential hardcoded secret",
                                file_path=file_path,
                                start_line=line_no,
                                snippet=line.strip()[:120],
                            )
                        )

        critical = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL)
        high = sum(1 for f in findings if f.severity == FindingSeverity.HIGH)
        passed = critical == 0 and high == 0

        return SecurityScanReport(
            id=f"scan_{uuid4().hex[:12]}",
            organization_id=org_id,
            scan_target=scan_target,
            tool_name="asdo-sast",
            tool_version="1.0.0",
            category=category,
            findings=findings,
            total_findings=len(findings),
            critical_count=critical,
            high_count=high,
            passed=passed,
        )
