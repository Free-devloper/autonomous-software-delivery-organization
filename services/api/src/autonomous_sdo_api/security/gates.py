"""Quality gate engine evaluating test, coverage, mutation, and security thresholds."""

from __future__ import annotations

from uuid import UUID, uuid4

from autonomous_sdo_api.security.models import (
    MutationReport,
    QualityGateCheck,
    QualityGateEvaluation,
    QualityGateStatus,
    SecurityScanReport,
    TestSuiteReport,
)


class QualityGateEngine:
    """Evaluate combined quality gates for a work package."""

    def __init__(
        self,
        *,
        coverage_threshold: float = 90.0,
        mutation_threshold: float = 80.0,
        max_critical_findings: int = 0,
        max_high_findings: int = 0,
        max_flaky_tests: int = 3,
    ) -> None:
        self.coverage_threshold = coverage_threshold
        self.mutation_threshold = mutation_threshold
        self.max_critical_findings = max_critical_findings
        self.max_high_findings = max_high_findings
        self.max_flaky_tests = max_flaky_tests

    def evaluate(
        self,
        organization_id: UUID,
        work_package_id: str,
        test_report: TestSuiteReport | None = None,
        mutation_report: MutationReport | None = None,
        scan_reports: list[SecurityScanReport] | None = None,
    ) -> QualityGateEvaluation:
        """Run all quality gate checks, return evaluation."""
        checks: list[QualityGateCheck] = []

        # 1. Test pass gate
        if test_report is not None:
            test_passed = test_report.failed == 0
            checks.append(
                QualityGateCheck(
                    name="test_pass_rate",
                    status=(QualityGateStatus.PASSED if test_passed else QualityGateStatus.FAILED),
                    threshold="0 failures",
                    actual=f"{test_report.failed} failures",
                )
            )

            # 2. Flaky test gate
            flaky_ok = test_report.flaky <= self.max_flaky_tests
            checks.append(
                QualityGateCheck(
                    name="flaky_test_limit",
                    status=(QualityGateStatus.PASSED if flaky_ok else QualityGateStatus.WARNING),
                    threshold=f"<= {self.max_flaky_tests}",
                    actual=str(test_report.flaky),
                )
            )

            # 3. Coverage gate
            if test_report.coverage:
                avg_line = sum(c.line_coverage for c in test_report.coverage) / len(
                    test_report.coverage
                )
                cov_ok = avg_line >= self.coverage_threshold
                checks.append(
                    QualityGateCheck(
                        name="line_coverage",
                        status=(QualityGateStatus.PASSED if cov_ok else QualityGateStatus.FAILED),
                        threshold=f">= {self.coverage_threshold}%",
                        actual=f"{avg_line:.1f}%",
                    )
                )

        # 4. Mutation gate
        if mutation_report is not None:
            mut_ok = mutation_report.mutation_score >= self.mutation_threshold
            checks.append(
                QualityGateCheck(
                    name="mutation_score",
                    status=(QualityGateStatus.PASSED if mut_ok else QualityGateStatus.FAILED),
                    threshold=f">= {self.mutation_threshold}%",
                    actual=f"{mutation_report.mutation_score:.1f}%",
                )
            )

        # 5. Security scan gates
        total_critical = 0
        total_high = 0
        for report in scan_reports or []:
            total_critical += report.critical_count
            total_high += report.high_count

        if scan_reports:
            crit_ok = total_critical <= self.max_critical_findings
            checks.append(
                QualityGateCheck(
                    name="critical_findings",
                    status=(QualityGateStatus.PASSED if crit_ok else QualityGateStatus.FAILED),
                    threshold=f"<= {self.max_critical_findings}",
                    actual=str(total_critical),
                )
            )
            high_ok = total_high <= self.max_high_findings
            checks.append(
                QualityGateCheck(
                    name="high_findings",
                    status=(QualityGateStatus.PASSED if high_ok else QualityGateStatus.FAILED),
                    threshold=f"<= {self.max_high_findings}",
                    actual=str(total_high),
                )
            )

        # Overall status: FAILED if any check failed
        has_failed = any(c.status == QualityGateStatus.FAILED for c in checks)
        has_warning = any(c.status == QualityGateStatus.WARNING for c in checks)
        if has_failed:
            overall = QualityGateStatus.FAILED
        elif has_warning:
            overall = QualityGateStatus.WARNING
        else:
            overall = QualityGateStatus.PASSED

        return QualityGateEvaluation(
            id=f"qg_{uuid4().hex[:12]}",
            organization_id=organization_id,
            work_package_id=work_package_id,
            overall_status=overall,
            checks=checks,
        )
