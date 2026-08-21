# ADR-0003: Provider-neutral SCM, model and embedding interfaces

- **Status:** Accepted
- **Date:** 2026-08-18
- **Decision owner:** Product owner

## Decision

Support GitHub and GitLab behind one repository-provider contract. Implement GitHub first as the
initial production provider and complete GitLab before final production release. Use dedicated
provider test organizations/groups and synthetic public/private repositories; destructive
integration tests never target production. Contract servers are allowed when credentials are absent,
but live verification remains mandatory.

Use LiteLLM or an internal gateway with versioned typed interfaces for OpenAI-compatible,
Anthropic-compatible, Gemini-compatible and local vLLM models. Ollama is development-only. Provider
selection is configurable per organization and repository. Private deployments must support fully
local/offline operation, and Restricted content can never reach external model providers.

Approved embeddings include configurable commercial APIs, preferred open-source `BAAI/bge-m3`, a
maintained E5-family alternative, and local vLLM/TEI-equivalent serving. Store model identifier,
revision, dimensions, content hash and source commit. An embedding-model change starts a controlled
re-indexing workflow. Prompts/snippets/outputs use configurable retention and redaction.

## Repository language and client compatibility

Tier-one languages are TypeScript/JavaScript, Python, Go and Java/Kotlin with full parsing, symbols,
testing and security support. Additional supported languages are Rust, C#, C/C++, Ruby, PHP, SQL,
Bash, YAML, JSON, HCL and Dockerfile, with visible limitations when only lexical or partial LSP
support exists.

Support the latest two stable Chrome, Firefox, Edge and Safari releases; Linux `amd64` and `arm64`;
and Linux, macOS and Windows-through-WSL2 developer environments. Firecracker may begin on Linux
`amd64`, but `arm64` remains an architectural requirement and roadmap item.

Maintain current and previous major API versions, additive changes within a major, 180-day
breaking-change notice, one rolling database-version boundary and deterministic Temporal replay
against retained histories.

## Consequences and verification

No provider SDK may bypass its adapter. Provider fallback cannot change residency/classification
behavior silently. Contract, live-provider, data-egress, re-indexing, language, browser,
architecture and workflow-replay evidence are required before support claims. Exact versions remain
TBD until official-source verification and build approval.
