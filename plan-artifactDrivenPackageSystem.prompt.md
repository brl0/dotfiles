# Plan: Convention-Driven, Cache-Friendly Package Management Artifact System

**TL;DR:** A complete redesign creating a lightweight `.pkgm` manifest format that generates **atomic, idempotent shell scripts and optimized Dockerfiles** from a single source of truth. Key innovations: treat artifacts as authoritative state, embed manifest hash for resumability, group packages by Docker layer to maximize cache reuse, and support optional inventory queries for drift detection.

---

## **Steps**

### **Phase 1: Package Manifest Format (`.pkgm`)**

Define a declarative, INI-like format with:

- Sections named `{manager}/{cache-group}` (e.g., `apt/base`, `brew/user-tools`)
- Version constraints and feature flags (PEP-508 style: `torch[cu118]~=2.0`)
- Optional per-section `inventory=` command for drift detection
- Tags for filtering (e.g., `tags=gpu,optional`)
- Metadata header (format version, generation date, manager list)
- Support inline comments and multi-line package lists
- **Goal:** Human-readable, diff-friendly, machine-parseable in < 150 lines

### **Phase 2: Package Graph & Generator Engine**

Build `gen.py` to:

- Parse `.pkgm` → internal PKG_GRAPH (managers, versions, dependencies, metadata)
- Topologically sort managers (respecting inter-manager deps: apt → brew → mamba)
- Generate three artifact types from same graph:
    - `install.sh` — Atomic, idempotent shell script with manager modules
    - `Dockerfile.gen` — Docker build optimized for layer caching
    - `gha-matrix.yml` — GitHub Actions job template (optional)
- Validate manifest (missing managers, circular deps, version syntax)

### **Phase 3: Idempotent Installation Runtime** _(depends on Phase 1 & 2)_

Implement install.sh with:

- **Manifest hash embedding** — Header contains SHA256 of input manifest
- **Two-tier state caching:**
    - Tier 1: Skip sections if manifest hash matches (already installed)
    - Tier 2: Optional per-manager inventory queries (e.g., `apt list --installed`)
- **Manager modules** (`apt.sh`, `brew.sh`, `pip.sh`, etc.) with standard interface:
    ```bash
    install_manager_{apt|brew|pip}() {
      local -a packages=("$@")
      local inventory_cmd="${INVENTORY[manager]:-}"
      # Only install missing packages if inventory available
    }
    ```
- **Result:** Re-running same script twice is cheap (second run skips already-installed packages)

### **Phase 4: Docker Layer Optimization** _(depends on Phase 2)_

Restructure Docker builds to defeat cascading invalidation:

- Group packages by **cache-invalidation frequency** (not install order):
    - **Layer 1:** System apt packages (rarely change) → `install.sh --phase system`
    - **Layer 2:** User tools (brew/webi, change moderately) → `install.sh --phase user`
    - **Layer 3:** Language runtimes (Python/Node, change frequently) → `install.sh --phase runtime`
    - **Layer 4+:** Dotfiles & config (highest change frequency) → copy & symlink last
- Each `install.sh --phase X` call is **idempotent** (uses manifest hash to skip)
- **Result:** Changing a pip package only invalidates layers 3+, not 1-2

### **Phase 5: Artifact-Driven Reconciliation** _(depends on Phase 3 & 4)_

Enable incremental updates by treating artifacts as state:

- Generated artifacts carry metadata comments:
    ```bash
    # MANIFEST_HASH: sha256:abc123...
    # MANAGERS: apt,brew,pip
    # INSTALLED_TIMESTAMP: 2026-03-07T12:00:00Z
    # DELTA_FROM_PREVIOUS: ADDED python3-dev, REMOVED vim
    ```
- Workflow: User edits `.pkgm` → `gen.py` → new `install.sh` (version 2) with embedded diff markers
- Script auto-detects: "is manifest_hash different?" → run only changed sections
- Supports: re-importing old artifacts, analyzing Git history of changes, rollback (previous artifact stays valid)

### **Phase 6: Extensible Manager Support & Inventory System** _(depends on Phase 2 & 3)_

Allow registering new package managers and optional discovery:

- Manager registration: Create module (`manager-name.sh`) + register in generator
- Optional per-section inventory:
    ```ini
    [apt/base]
    inventory=apt list --installed
    ```
    → Framework calls command, compares `NEEDED - ALREADY_INSTALLED`, installs delta
- **Result:** New managers + custom checks without touching core runtime

---

## **Relevant Files**

- [.files/scripts/install_from_conf.sh](install_from_conf.sh) — Reuse `process_section()` flow, module-based execution patterns
- [.files/config/\*.conf](packages.conf) — Extract package lists and command sequences as migration reference
- [Dockerfile](Dockerfile) — Analyze current layer structure to inform cache-group boundaries
- _To be created:_ `.files/pkg-manifest/manifest.pkgm`, `gen.py`, `install.sh.tpl`, manager modules in `.files/pkg-manifest/modules/`

---

## **Verification**

1. **Parsing round-trip:** Generate manifest → parse to Python → emit shell code → re-parse artifact = consistent
2. **Idempotency test:** Run `install.sh` once, then again with same manifest → second run adds 0 new work (check time diff)
3. **Diff clarity:** Add one package to manifest, commit → `git diff manifest.pkgm` and `git diff install.sh` both highlight exact changes (no spurious whitespace)
4. **Docker layer reuse:** Modify a pip package in `[pip/ml]` → rebuild Docker → layers 1-2 use cached hashes
5. **Cross-platform:** Same `install.sh` runs idempotently on local machine, GitHub Actions runner, and inside Docker
6. **Backward traceability:** Generated artifact contains manifest hash + version → can reconstruct "what was intended at generation time"

---

## **Key Decisions**

- **Manifest format:** INI-style (familiar to current users), not YAML/JSON (reduces tooling)
- **Single manifest, multiple artifacts:** Avoid drift between Docker/script/GHA versions
- **Atomic install.sh as interchange:** Valid standalone _and_ embeddable in Dockerfiles
- **No breaking changes to existing `.conf` files** (stay in place, migration helper optional)
- **Tags + filters over platform-specific sections:** Keep manifest linear; use `--tag gpu` at generation time
- **User-managed lock files:** (`pip.lock`, `conda.lock` checked into Git alongside manifest)

---

## **Further Considerations**

1. **Multi-manifest hierarchies** (Phase 2 feature): Should `.pkgm` support `include: common.pkgm` for shared base configs?
    - **Recommendation:** Start without it, add if teams need separate dev/prod manifests

2. **Platform specificity:** How to handle `ubuntu-22.04` vs `ubuntu-24.04` apt package name differences?
    - **Recommendation:** Filter at generation time (`gen.py --os ubuntu-22.04`) or use tags. Avoid embedding platform logic in manifest.

3. **Version pinning philosophy:** Enforce user choice (PEP-508: `torch~=2.0` vs `torch==2.1.3`) or auto-resolve?
    - **Recommendation:** User specifies in manifest using standard syntax; generator documents rationale in artifact header

---

## **System Context & Prior Analysis**

### Current State

- **Existing system:** Sequential `.conf` files (`pkgs_sys.conf`, `pkgs_brew.conf`, `packages.conf`)
- **Current pain points:**
    - Docker rebuilds invalidate all downstream layers (no cache reuse)
    - No idempotency checks (re-installs everything even if already present)
    - State management via manual `links.local` file
    - Hardcoded absolute paths
    - Two dotfile installers (unclear which is primary)

### Package Managers in Use

- **System:** apt (root)
- **User tools:** webi, Homebrew
- **Python/Conda:** Micromamba, pip, pipx, xonsh
- **Isolated:** YAML conda environments (brl.yaml, ai.yaml)

### Installation Order (DAG)

1. apt (system packages) → localedef setup
2. webi (pathman, dotenv, etc.)
3. Homebrew (asdf, fzf, direnv, starship)
4. Micromamba (Python runtime + conda packages)
5. pip/pipx (isolated Python CLI tools)
6. xonsh/xpip (shell plugins)
7. Dotfile symlinks (final state)

### Docker Layer Structure (Current)

- Layer 1: Base Ubuntu + user creation
- Layer 2: System apt (pkgs_sys.conf)
- Layer 3: System libraries + locale (pkgs_sys2.conf)
- Layer 4: Homebrew installation (pkgs_brew.conf)
- Layer 5: User package managers (pkgs_good.conf)
- Layer 6: Secondary packages (packages.conf)
- Layer 7: Dotfile symlinks (install_dots.py)

**Issue:** Any change to early layers invalidates downstream caches.

---

## **Design Philosophy**

- **Text-only formats** — No binary files, version control friendly
- **Git-native workflows** — Every artifact dumpable, diffable, committable
- **Convention over configuration** — Manifest structure implies execution order
- **Artifact-first state tracking** — Generated code is source of truth (not config files alone)
- **Deterministic, reproducible outputs** — Same manifest hash → identical artifact
- **Minimal abstraction layers** — Flat manager modules, no complex DSLs

---

## **Implementation Roadmap**

### Iteration 1: Proof of Concept

1. Define `.pkgm` manifest format (hand-write example)
2. Build minimal `gen.py` parser (just INI parsing, no PKG_GRAPH yet)
3. Emit simple `install.sh` with manual manager modules
4. Test on local machine: parse manifest → run install.sh → verify packages installed
5. Verify idempotency: run twice, measure work on second run

### Iteration 2: Validation & Codegen

1. Implement PKG_GRAPH data structure (dependency tracking)
2. Add topological sort for manager ordering
3. Implement manifest hash + embedded metadata in install.sh
4. Test round-trip: manifest → artifact → re-parse hash → regenerate ≡ original
5. Add basic Dockerfile generation (wrapper around install.sh)

### Iteration 3: Optimization & State Caching

1. Implement Tier 1 state caching (manifest hash matching)
2. Add optional per-manager `inventory=` commands
3. Implement Tier 2 state caching (delta install logic)
4. Optimize Docker layer grouping by cache-invalidation frequency
5. Test: modify late-stage packages → verify early layers reuse cache

### Iteration 4: Polish & Extensibility

1. Multi-manager registration system
2. Tag filtering (`gen.py --tag gpu`)
3. Lock file generation for pip/conda
4. Documentation + examples
5. Optional: `conf2pkgm.py` migration helper for existing `.conf` files

---

## **Success Criteria**

| Criterion              | How to Verify                                                                  |
| ---------------------- | ------------------------------------------------------------------------------ |
| Manifest parsing       | Round-trip: `.pkgm` → Python → shell → re-parse hash is deterministic          |
| Idempotency            | Run `install.sh` twice with same manifest; measure work on second run ≈ 0      |
| Cache reuse            | Modify pip package; rebuild Docker; layers 1-3 use cached hashes               |
| Diff clarity           | Add one package to manifest; git diff shows single meaningful line change      |
| Cross-platform         | Same `install.sh` runs on local Linux, Docker, GitHub Actions                  |
| Extensibility          | Add new package manager; only need to create manager module + register         |
| State tracking         | Artifact contains manifest hash; can derive "what changed" from commit history |
| Backward compatibility | Old `.conf` files remain valid; no forced migration                            |
