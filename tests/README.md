# Phase 0 verification scope

This directory is reserved for cross-service verification. Phase 0A keeps executable unit tests with
their owning packages and services so that test discovery follows each runtime's native conventions.
The CI workflow runs formatting, linting, type checks, unit tests, builds, dependency auditing,
secret scanning, and static analysis on every pull request to `main` and each push to `main`.

Cross-service, contract, tenant-isolation, integration, resilience, security, browser, performance,
and evaluation tests are added in their respective delivery phases.
