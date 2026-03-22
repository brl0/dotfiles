# pkg-manifest prompts

## Original Prompt

### 📦 Prompt: Design a Convention‑Driven, Cache‑Friendly Package Management Artifact System

Design a system for **describing, generating, and maintaining installation artifacts** across multiple package managers and operating environments.

---

#### 🎯 Core Objective

Create a **text‑only, git‑friendly system** that produces **installation artifacts**—such as Dockerfiles or shell scripts—that reliably install packages across heterogeneous package managers while maximizing **cache reuse**, **incremental updates**, and **reproducibility**.

The system should favor **simple conventions over complex configuration frameworks**, and treat the **generated artifacts themselves as the system of record**.

---

#### 🧩 Package Manager Abstraction

The system must support multiple package managers with differing behaviors, including:

- Different command syntaxes and invocation styles
- Single‑package vs multi‑package install semantics
- Required pre‑install or post‑install commands
- Inter‑manager dependencies
    - Example: using `apt` to install prerequisites required by `brew`, which then installs `mamba`
- Installation contexts:
    - Privileged (root / Administrator)
    - User‑level installs

---

#### 📦 Package Specification Requirements

Package definitions should support:

- Explicit version constraints
- Subpackages or feature flags
- Inline comments
- Optional tags or categories (e.g., `dev`, `runtime`, `build`, `gpu`)
- Human‑readable, diff‑friendly formatting

---

#### 🧠 Artifact‑Driven State & Incremental Updates

The system should:

- Treat **previously generated artifacts** as authoritative state
- Be able to **re‑import and analyze existing artifacts**
- Use conventional comments or metadata blocks to track:
    - Package provenance
    - Manager ownership
    - Version intent
- Generate **minimal diffs** when packages change
- Produce output optimized for:
    - Docker layer caching
    - Idempotent re‑runs on existing systems

---

#### 🔄 Workflow Scenarios

The system should support workflows such as:

- Generating artifacts for fresh system installs
- Updating artifacts when packages are added, removed, or version‑changed
- Converting between:
    - Docker‑based installs
    - Script‑based installs
- Preferably using a **single canonical representation** that can emit both formats

---

#### 📊 Inventory & Discovery (Optional but Valuable)

Where supported by the package manager, the system may:

- Query the current system for installed packages
- Reconcile discovered state with generated artifacts
- Use this information to avoid redundant installs or improve diff accuracy

---

#### ⚠️ Constraints & Lessons Learned

A previous implementation relied on centralized configuration files to track packages, but this approach proved:

- Brittle
- Poorly cache‑aware
- Unable to account for pre‑existing installations

This new design should explicitly avoid those pitfalls.

---

#### 🧱 Design Philosophy

- Text‑only formats
- Git‑native workflows
- Convention over configuration
- Artifact‑first state tracking
- Deterministic, reproducible outputs
- Minimal abstraction layers

## Follow-up Prompts

- The system should allow for extension to support other output formats, such as Ansible, or nox, or doit, etc, perhaps through templates? The output artifacts should, if the format supports comments or other metadata, contain all relevant information to reconstruct the original declarative inputs, and the declarative input format should be one of the supported output formats. Consider adding a simple common mechanism for finding differences between lists of packages. Support using include or exclude tags for tagged packages, assume non-tagged packages are required, and assume all packages if no filter is specified. Add optional support for lock files, such as generating them as part of the process, or using them as a source of packages to be installed.
- Use a red/green test driven approach throughout the process.
- I would prefer metadata syntax to be formatted as comments when possible to improve readability and help transportability across input/output/storage formats.
- Include and exclude semantics should follow common industry practices.
- To clarify, metadata such as tags or dependencies should be formatted as comments, since those are not included in the package manager commands or target output file formats. The package manager definition does not necessarily need to be formatted as comments, since it can be defined declaratively or inferred from the output script.
- The metadata should be embedded in artifacts when possible, such as using comments and should only be omitted when there is no way to support for the target format.
- I would like the manager registry to be defined in a data file rather than in code. I would also like shell scripts to be stored in separate files rather than as quoted text within the python script. Ensure tests are passing after changes.
- Perhaps the install shell script should be put into a template or a series of templates that can be populated and assembled as needed at run time.
- Create appropriate pkg manifest files based on the existing conf files. Create a new dockerfile for testing based on the existing file but updated to use the new project to install the package manifest(s) rather than using install_from_conf.sh to install from the previous conf files.
- Simplify how the new dockerfile calls the project, consider creating one or more stand-alone scripts to be called rather than embedding the code directly into the dockerfile. Test by building the image directly or by running the build_image.sh. Troubleshoot and fix any issues encountered.
- Fix the errors trying to build this dockerfile
- Most of those last changes don't really help, the goal is to use the Dockerfile.pkgm to test and troubleshoot issues with the pkg manifest package installer, not just installing those particular packages in the Docker image. Reconsider the approach and find a way to troubleshoot the pkg manifest installer. Use subagents when running tests or building with Docker to help manage context.
- Create a new dockerfile that shows how to use pkg-manifest to create an installation shell script to install packages defined in pkgs_sys.conf. Using subagents, ensure that the process runs without issues, troubleshoot and fix any problems encountered.
- Create a new simple shell script to demonstrate how to use pkg-manifest to generate an installer script for the packages specified in .files/config/pkgs_sys.conf. If needed, create a new simple python script wrapper to simplify the interface for the shell script.
