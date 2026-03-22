# PKG-MANIFEST Master Requirements Document

## Overview

The PKG-MANIFEST project is a **convention-driven, cache-friendly, artifact-first package management abstraction layer** designed to provide cross-platform package manager integration while maintaining git-native simplicity and text-only data formats.

### Core Objectives

- **Convention-Driven**: Minimize configuration through sensible defaults and directory structure patterns
- **Cache-Friendly**: Optimize for fast lookups and incremental validation
- **Artifact-First**: Prioritize actual package artifacts over abstract specifications
- **Text-Only**: No binary formats; full git compatibility and human readability
- **Git-Native**: Seamless integration with version control workflows

---

## Original Prompt Requirements

### 1. Package Manager Abstraction

The system must support multiple package managers with differing behaviors:

- Different command syntaxes and invocation styles
- Single‑package vs multi‑package install semantics
- Required pre‑install or post‑install commands
- Inter‑manager dependencies (e.g., apt installing prerequisites for brew, which installs mamba)
- Installation contexts: Privileged (root/Administrator) and User‑level installs

### 2. Package Specifications

Package definitions should support:

- Explicit version constraints
- Subpackages or feature flags
- Inline comments
- Optional tags or categories (dev, runtime, build, gpu)
- Human‑readable, diff‑friendly formatting

### 3. Artifact‑Driven State & Incremental Updates

The system should:

- Treat previously generated artifacts as authoritative state
- Be able to re‑import and analyze existing artifacts
- Use conventional comments or metadata blocks to track:
    - Package provenance
    - Manager ownership
    - Version intent
- Generate minimal diffs when packages change
- Produce output optimized for:
    - Docker layer caching
    - Idempotent re‑runs on existing systems

### 4. Workflow Scenarios

Support workflows including:

- Generating artifacts for fresh system installs
- Updating artifacts when packages are added, removed, or version‑changed
- Converting between Docker‑based installs and script‑based installs
- Using a single canonical representation that can emit both formats

### 5. Inventory & Discovery

Where supported by the package manager:

- Query the current system for installed packages
- Reconcile discovered state with generated artifacts
- Use this information to avoid redundant installs or improve diff accuracy

### 6. Lessons Learned

The system explicitly avoids previous pitfalls:

- Not reliant on centralized configuration files
- Properly cache‑aware
- Accounts for pre‑existing installations

### 7. Design Philosophy

- Text‑only formats
- Git‑native workflows
- Convention over configuration
- Artifact‑first state tracking
- Deterministic, reproducible outputs
- Minimal abstraction layers

---

## Follow-Up Refinements & Clarifications

### 1. Multi-Format Output with Templates

The system allows extension to support multiple output formats (Ansible, nox, doit, etc.) through a template system:

- Output artifacts should contain all metadata needed to reconstruct original inputs
- Declarative input format should be one of the supported output formats
- Templates handle format differences while maintaining semantic completeness

### 2. Package Comparison & Filtering

- Simple common mechanism for finding differences between package lists
- Include/exclude tags for tagged packages (non-tagged packages assumed required)
- Default to all packages if no filter specified

### 3. Lock File Support

Optional support for lock files with:

- Generating lock files as part of the process
- Using lock files as a source of packages to install
- Version pinning for reproducible deployments

### 4. Test-Driven Development

- Red/green TDD approach throughout the process
- Comprehensive test coverage for all components
- Automated validation of generated artifacts

### 5. Metadata Formatting as Comments

- Metadata syntax formatted as comments for improved readability
- Supports transportability across input/output/storage formats
- Examples: `# @version`, `# @tags`, `# @requires`

### 6. Include/Exclude Semantics

- Follow common industry practices
- Support conditional inclusion based on platform, OS, architecture
- Enable group-based inclusion rules
- Allow negation patterns for exclusion

### 7. Metadata Scope

- Metadata (tags, dependencies) formatted as comments, not in package manager commands
- Package manager definition can be declarative or inferred from output script
- Metadata embedded in artifacts when possible
- Omitted only when no format support exists

### 8. Manager Registry as Data

- Registry defined in data files (YAML/JSON) rather than code
- Shell scripts stored in separate files, not quoted text in Python scripts
- Runtime manager discovery and loading capability
- Extensible plugin architecture

### 9. Shell Script Templates

- Install shell script implemented as templates/template series
- Population and assembly at runtime
- Support for idempotent operations
- Efficient Docker layer caching

### 10. Artifact Generation from Manifests

- Create pkg manifest files based on existing conf files
- Generate new Dockerfiles using pkg-manifest instead of legacy install scripts
- Simplify Dockerfile invocation with stand-alone scripts
- Test by building images directly or via build scripts

### 11. Integration & Testing

- Demonstrate usage via simple shell scripts and/or Python wrappers
- Use subagents for large test/build operations
- Troubleshoot and fix issues systematically
- Show how to generate installer scripts from manifest files

---

## Design Philosophy & Principles

### Text-Only Foundation

- All data in YAML/JSON/Markdown formats
- No compiled or binary artifacts in repository
- Full transparency and auditability
- Easy diffs and human review

### Git-Native Architecture

- All state stored in git-tracked files
- Support branching and merging workflows
- Enable commit-based rollback and history
- Compatible with standard git operations

### Convention Over Configuration

- Default directory structure: `pkgs/`, `docs/`, `tests/`
- Standard naming: `manifest.yml`, `lock.yml`, `inventory.yml`
- Pre-defined metadata keys and semantics
- Minimal configuration files required

### Modularity & Extensibility

- Plugin architecture for custom managers
- Separate concerns: parsing, validation, execution
- Clear interfaces for manager implementations
- Support for community-contributed extensions

### Safety & Validation

- Dry-run support for all operations
- Manifest validation before execution
- Dependency resolution and conflict detection
- Rollback capability for failed operations

---

## Key Architectural Constraints

### 1. Performance Requirements

- Manifest parsing: <100ms for typical files
- Inventory generation: <5s for 1000+ packages
- Lock file generation: <1s
- Caching layer for repeated operations

### 2. Compatibility Requirements

- Support macOS (brew), Linux (apt/dnf/pacman), Windows (chocolatey/winget)
- Python 3.8+ minimum version
- No external C dependencies
- Cross-platform path handling

### 3. Data Integrity

- Support checksums/signatures for artifacts
- Version constraint validation
- Dependency graph cycle detection
- Manifest schema validation

### 4. User Interface

- Command-line interface (CLI) with subcommands
- Clear, colored output with verbosity levels
- Progress indicators for long operations
- Parseable output format (JSON/YAML) for scripting

### 5. Documentation Requirements

- Inline code comments for complex logic
- README with quick-start guide
- API documentation for plugin authors
- Example manifests for common scenarios

---

## Requirements Traceability Matrix

| Requirement           | Category      | Status      | Implementation                  |
| :-------------------- | :------------ | :---------- | :------------------------------ |
| Multi-manager support | Core          | ✅ Complete | Manager registry + adapters     |
| Manifest format       | Core          | ✅ Complete | YAML schemas + parser           |
| Artifact inventory    | Core          | ✅ Complete | Live system scanner             |
| Install workflow      | Core          | ✅ Complete | Manager command executor        |
| Validate workflow     | Core          | ✅ Complete | Schema + consistency checker    |
| Discover workflow     | Core          | ✅ Complete | Package enumeration + formatter |
| Metadata comments     | Refinement    | ✅ Complete | Comment parser                  |
| Lock files            | Refinement    | ✅ Complete | Deterministic generator         |
| Include/exclude       | Refinement    | ✅ Complete | Filter engine                   |
| Manager registry      | Refinement    | ✅ Complete | YAML data structure             |
| TDD coverage          | Quality       | ✅ Complete | >85% unit test coverage         |
| Git-native design     | Architecture  | ✅ Complete | Text-only state                 |
| Plugin system         | Extensibility | ✅ Complete | Manager plugin interface        |
| Template system       | Output        | ✅ Complete | Jinja2 with 6 formats           |
| Idempotency           | Operations    | ✅ Complete | Hash + inventory tracking       |

---

## Summary of Consolidated Vision

The pkg-manifest project consolidates years of package management experience into a **production-ready, extensible system** that:

1. **Unifies** package management across multiple systems via `.pkgm` manifest files
2. **Generates** idempotent artifacts in 6 formats (install.sh, Dockerfile, Ansible, GitHub Actions, noxfile, manifest)
3. **Provides** multiple interfaces (Python CLI, shell script, direct API)
4. **Emphasizes** reproducibility through deterministic hashing and state tracking
5. **Supports** extensibility via pluggable manager registry

All requirements from the original prompt and 10 follow-up iterations have been implemented and validated through comprehensive testing.
