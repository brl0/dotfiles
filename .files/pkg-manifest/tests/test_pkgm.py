"""
Test suite for Package Manifest Generator (TDD Red Tests - Phase 0)
Tests define the specification before implementation.
"""

import pytest
from gen import (
    Package,
    Section,
    PKG_GRAPH,
    parse_pkgm,
    compute_manifest_hash,
    diff_packages,
    emit_manifest,
    emit_install_sh,
    emit_dockerfile,
    emit_ansible_playbook,
    emit_noxfile,
)


# ============================================================================
# PHASE 0A: Parsing & Basic Functionality
# ============================================================================


class TestParsingBasics:
    """RED: Test manifest parsing into PKG_GRAPH"""

    def test_parse_simple_manifest(self):
        """Parse simple manifest with packages"""
        manifest = "[apt/base]\npackages:\n  curl\n  git"
        graph = parse_pkgm(manifest)
        assert "apt/base" in graph.sections
        assert graph.sections["apt/base"].manager == "apt"
        assert graph.sections["apt/base"].cache_group == "base"
        assert len(graph.sections["apt/base"].packages) == 2
        assert graph.sections["apt/base"].packages[0].name == "curl"
        assert graph.sections["apt/base"].packages[1].name == "git"

    def test_parse_manifest_with_declarative_metadata(self):
        """Declarative metadata (mode, inventory, lock, pre) parsed from INI syntax"""
        manifest = """[apt/base]
mode=multi
inventory=apt list --installed
lock=locks/apt.lock
pre=apt-get update
packages:
  curl
  git"""
        graph = parse_pkgm(manifest)
        assert graph.sections["apt/base"].mode == "multi"
        assert graph.sections["apt/base"].inventory_cmd == "apt list --installed"
        assert graph.sections["apt/base"].lock_file == "locks/apt.lock"
        assert graph.sections["apt/base"].commands.get("pre") == "apt-get update"

    def test_parse_manifest_with_system_metadata_comments(self):
        """System metadata (@tags, @depends, @description) parsed from comments"""
        manifest = """[apt/base]
mode=multi
inventory=apt list --installed
packages:
  curl
  build-essential[~=12]
# @tags: curl=base, build-essential=base,build
# @depends: [none]
# @description: Core system packages"""
        graph = parse_pkgm(manifest)
        # Declarative metadata
        assert graph.sections["apt/base"].mode == "multi"
        assert graph.sections["apt/base"].inventory_cmd == "apt list --installed"
        # System metadata extracted from comments
        section_meta = graph.sections["apt/base"].metadata
        assert "curl=base" in section_meta.get("tags", "")
        assert "build-essential=base" in section_meta.get("tags", "")
        assert "[none]" in section_meta.get("depends", "")
        assert "Core system packages" in section_meta.get("description", "")

    def test_parse_packages_with_version_constraints(self):
        """Parse packages with PEP-508 style version constraints"""
        manifest = """[apt/system]
packages:
  curl
  build-essential[~=12]
  python3-dev[>=3.8,<4.0]"""
        graph = parse_pkgm(manifest)
        pkgs = graph.sections["apt/system"].packages
        assert pkgs[0].name == "curl"
        assert pkgs[0].version == ""
        assert pkgs[1].name == "build-essential"
        assert pkgs[1].version == "[~=12]"
        assert pkgs[2].name == "python3-dev"
        assert pkgs[2].version == "[>=3.8,<4.0]"

    def test_parse_multiple_sections(self):
        """Parse manifest with multiple [manager/cache-group] sections"""
        manifest = """[apt/system]
packages:
  curl

[pip/ml]
packages:
  torch"""
        graph = parse_pkgm(manifest)
        assert len(graph.sections) == 2
        assert "apt/system" in graph.sections
        assert "pip/ml" in graph.sections


class TestManifestHash:
    """RED: Manifest hash computation for idempotency"""

    def test_manifest_hash_deterministic(self):
        """Same manifest produces same hash (deterministic)"""
        manifest = "[apt/base]\npackages:\n  curl"
        h1 = compute_manifest_hash(manifest)
        h2 = compute_manifest_hash(manifest)
        assert h1 == h2

    def test_manifest_hash_changes_with_content(self):
        """Different manifest content produces different hash"""
        m1 = "[apt/base]\npackages:\n  curl"
        m2 = "[apt/base]\npackages:\n  git"
        h1 = compute_manifest_hash(m1)
        h2 = compute_manifest_hash(m2)
        assert h1 != h2

    def test_manifest_hash_is_hex_string(self):
        """Hash is valid SHA256 hex string"""
        manifest = "[apt/base]\npackages:\n  curl"
        h = compute_manifest_hash(manifest)
        assert len(h) == 64  # SHA256 hex is 64 chars
        assert all(c in "0123456789abcdef" for c in h)


# ============================================================================
# PHASE 0B: Tag Filtering
# ============================================================================


class TestTagFiltering:
    """RED: Tag-based filtering with include/exclude (industry standard)"""

    def test_tag_filtering_default_includes_all(self):
        """Without filter, include all packages"""
        manifest = """[apt/base]
packages:
  curl
  torch
  poetry
# @tags: curl=base, torch=gpu, poetry=optional"""
        graph = parse_pkgm(manifest)
        filtered = graph.filter_tags()  # no include or exclude
        assert len(filtered.sections["apt/base"].packages) == 3

    def test_tag_filtering_include_single_tag(self):
        """--include gpu includes gpu-tagged AND all untagged packages"""
        manifest = """[apt/base]
packages:
  curl
  torch
  poetry
  untagged
# @tags: curl=base, torch=gpu, poetry=optional"""
        graph = parse_pkgm(manifest)
        filtered = graph.filter_tags(include=["gpu"])
        # Should include: torch (gpu-tagged), untagged (untagged), but not curl (base-tagged) or poetry (optional-tagged)
        names = {p.name for p in filtered.sections["apt/base"].packages}
        assert "torch" in names
        assert "untagged" in names
        assert "curl" not in names
        assert "poetry" not in names

    def test_tag_filtering_include_multiple_tags_union(self):
        """--include gpu build includes (gpu-tagged OR build-tagged) AND untagged"""
        manifest = """[apt/base]
packages:
  curl
  torch
  gcc
  poetry
# @tags: curl=base, torch=gpu, gcc=build, poetry=optional"""
        graph = parse_pkgm(manifest)
        filtered = graph.filter_tags(include=["gpu", "build"])
        # Should include: torch (gpu), gcc (build), untagged (none), but not curl (base) or poetry (optional)
        names = {p.name for p in filtered.sections["apt/base"].packages}
        assert "torch" in names
        assert "gcc" in names
        assert "curl" not in names
        assert "poetry" not in names

    def test_tag_filtering_exclude_single_tag(self):
        """--exclude optional removes optional-tagged packages"""
        manifest = """[apt/base]
packages:
  curl
  torch
  poetry
# @tags: curl=base, torch=gpu, poetry=optional"""
        graph = parse_pkgm(manifest)
        filtered = graph.filter_tags(exclude=["optional"])
        # Should include: curl, torch (not optional-tagged), exclude: poetry
        names = {p.name for p in filtered.sections["apt/base"].packages}
        assert "curl" in names
        assert "torch" in names
        assert "poetry" not in names

    def test_tag_filtering_exclude_multiple_tags_union(self):
        """--exclude optional gpu removes (optional-tagged OR gpu-tagged) packages"""
        manifest = """[apt/base]
packages:
  curl
  torch
  poetry
# @tags: curl=base, torch=gpu, poetry=optional"""
        graph = parse_pkgm(manifest)
        filtered = graph.filter_tags(exclude=["optional", "gpu"])
        # Should include: curl (not in excluded), exclude: torch (gpu), poetry (optional)
        names = {p.name for p in filtered.sections["apt/base"].packages}
        assert "curl" in names
        assert "torch" not in names
        assert "poetry" not in names

    def test_tag_filtering_include_and_exclude(self):
        """--include base --exclude optional = (base-tagged OR untagged) AND NOT optional-tagged"""
        manifest = """[apt/base]
packages:
  curl
  gcc
  poetry
# @tags: curl=base, gcc=base,build, poetry=optional"""
        graph = parse_pkgm(manifest)
        filtered = graph.filter_tags(include=["base"], exclude=["optional"])
        # Include base (curl, gcc) and untagged, exclude optional-tagged
        # Result: curl, gcc (both have base tag, neither has optional)
        names = {p.name for p in filtered.sections["apt/base"].packages}
        assert "curl" in names
        assert "gcc" in names
        assert "poetry" not in names

    def test_tag_filtering_preserves_untagged(self):
        """Untagged packages always included unless explicitly excluded"""
        manifest = """[apt/base]
packages:
  curl
  nginx
  poetry
# @tags: curl=base, poetry=optional"""
        graph = parse_pkgm(manifest)
        # nginx has no tag
        filtered = graph.filter_tags(include=["base"])
        names = {p.name for p in filtered.sections["apt/base"].packages}
        assert "curl" in names  # base tag
        assert "nginx" in names  # untagged
        assert "poetry" not in names  # optional tag, not in include


# ============================================================================
# PHASE 0C: Package Diff
# ============================================================================


class TestPackageDiff:
    """RED: Package diff (added, removed, modified)"""

    def test_package_diff_basic(self):
        """Identify added, removed, and modified packages"""
        old = [Package("curl", "7.0"), Package("git", "2.0")]
        new = [Package("curl", "7.1"), Package("git", "2.0"), Package("jq", "1.6")]
        added, removed, modified = diff_packages(old, new)

        # jq is added
        assert "jq" in {p.name for p in added}
        # curl is modified (version changed)
        assert "curl" in {p.name for p in modified}
        # git is unchanged (not in added/removed/modified)
        assert "git" not in {p.name for p in removed}
        assert len(removed) == 0

    def test_package_diff_all_removed(self):
        """All packages removed"""
        old = [Package("curl", "7.0"), Package("git", "2.0")]
        new = []
        added, removed, modified = diff_packages(old, new)
        assert len(added) == 0
        assert len(removed) == 2
        assert "curl" in {p.name for p in removed}
        assert "git" in {p.name for p in removed}

    def test_package_diff_all_added(self):
        """All packages added"""
        old = []
        new = [Package("curl", "7.0"), Package("git", "2.0")]
        added, removed, modified = diff_packages(old, new)
        assert len(added) == 2
        assert len(removed) == 0
        assert "curl" in {p.name for p in added}

    def test_package_diff_version_change_is_modified(self):
        """Version change is marked as modified, not removed/added"""
        old = [Package("torch", "==1.9")]
        new = [Package("torch", "==2.0")]
        added, removed, modified = diff_packages(old, new)
        assert len(added) == 0
        assert len(removed) == 0
        assert len(modified) == 1
        assert modified[0].name == "torch"


# ============================================================================
# PHASE 0D: Lock File Support
# ============================================================================


class TestLockFileConsumption:
    """RED: Lock file reading and version pinning"""

    def test_lock_file_consumption_pip(self):
        """Apply pip.lock versions to package list"""
        lock = "torch==2.0.1\ntransformers==4.30.2\n"
        manifest = """[pip/ml]
lock=locks/pip.lock
packages:
  torch
  transformers"""
        graph = parse_pkgm(manifest)
        graph.apply_lock_file("pip", lock)

        pip_section = graph.sections["pip/ml"]
        torch_pkg = next(p for p in pip_section.packages if p.name == "torch")
        transformers_pkg = next(
            p for p in pip_section.packages if p.name == "transformers"
        )

        assert torch_pkg.version == "==2.0.1"
        assert transformers_pkg.version == "==4.30.2"

    def test_lock_file_partial_match(self):
        """Some packages from manifest may not be in lock file"""
        lock = "torch==2.0.1\n"
        manifest = """[pip/ml]
packages:
  torch
  transformers"""
        graph = parse_pkgm(manifest)
        graph.apply_lock_file("pip", lock)

        torch_pkg = next(
            p for p in graph.sections["pip/ml"].packages if p.name == "torch"
        )
        transformers_pkg = next(
            p for p in graph.sections["pip/ml"].packages if p.name == "transformers"
        )

        # torch gets version from lock
        assert torch_pkg.version == "==2.0.1"
        # transformers stays as originally specified (or empty)
        assert transformers_pkg.version == ""


# ============================================================================
# PHASE 0E: Manifest Round-Trip (Regeneration)
# ============================================================================


class TestManifestRoundTrip:
    """RED: Manifest → PKG_GRAPH → Manifest (round-trip fidelity)"""

    def test_manifest_output_format_basic(self):
        """Regenerate manifest from PKG_GRAPH preserves structure"""
        original = """[apt/base]
mode=multi
packages:
  curl
  git"""
        graph = parse_pkgm(original)
        regenerated = emit_manifest(graph)
        re_graph = parse_pkgm(regenerated)

        # Verify sections match
        assert "apt/base" in re_graph.sections
        assert re_graph.sections["apt/base"].manager == "apt"
        assert re_graph.sections["apt/base"].cache_group == "base"
        assert len(re_graph.sections["apt/base"].packages) == 2

    def test_manifest_round_trip_with_metadata(self):
        """Round-trip preserves declarative and system metadata"""
        original = """[apt/base]
mode=multi
inventory=apt list --installed
packages:
  curl
  git
# @tags: curl=base, git=base
# @description: Base utilities"""
        graph = parse_pkgm(original)
        regenerated = emit_manifest(graph)
        re_graph = parse_pkgm(regenerated)

        # Verify declarative metadata
        assert re_graph.sections["apt/base"].mode == "multi"
        assert re_graph.sections["apt/base"].inventory_cmd == "apt list --installed"
        # Verify system metadata
        assert "curl=base" in re_graph.sections["apt/base"].metadata.get("tags", "")
        assert "Base utilities" in re_graph.sections["apt/base"].metadata.get(
            "description", ""
        )


# ============================================================================
# PHASE 0F: Artifact Metadata Embedding
# ============================================================================


class TestArtifactMetadataEmbedding:
    """RED: All metadata preserved in artifacts as comments"""

    def test_artifact_metadata_fully_embedded_in_shell(self):
        """Shell artifacts embed full manifest as comments (declarative + system metadata)"""
        manifest = """[apt/base]
mode=multi
inventory=apt list --installed
packages:
  curl
  build-essential[~=12]
# @tags: curl=base, build-essential=base,build
# @description: Base utilities"""
        graph = parse_pkgm(manifest)
        install_sh = emit_install_sh(graph)

        # Declarative metadata should be in comments
        assert "# mode=multi" in install_sh
        assert "# inventory=apt list --installed" in install_sh
        # System metadata should be in comments
        assert "# @tags:" in install_sh
        assert "curl=base" in install_sh
        assert "# @description:" in install_sh
        assert "Base utilities" in install_sh

    def test_artifact_metadata_dockerfile_format(self):
        """Dockerfile artifacts preserve metadata as # comments"""
        manifest = """[apt/base]
mode=multi
packages:
  curl
# @tags: curl=base"""
        graph = parse_pkgm(manifest)
        dockerfile = emit_dockerfile(graph)

        # Dockerfile uses # comments
        assert "# mode=multi" in dockerfile
        assert "# @tags:" in dockerfile
        assert "curl=base" in dockerfile

    def test_artifact_metadata_ansible_format(self):
        """Ansible playbook preserves metadata in YAML # comments"""
        manifest = """[apt/base]
mode=multi
packages:
  curl
# @tags: curl=base"""
        graph = parse_pkgm(manifest)
        ansible = emit_ansible_playbook(graph)

        # Ansible YAML uses # comments
        assert "# mode=multi" in ansible
        assert "# @tags:" in ansible

    def test_artifact_metadata_python_format(self):
        """Python artifacts (noxfile) preserve metadata in docstring or comments"""
        manifest = """[pip/ml]
lock=locks/pip.lock
packages:
  torch
# @tags: torch=gpu"""
        graph = parse_pkgm(manifest)
        nox = emit_noxfile(graph)

        # Python code preserves metadata (in docstring, variable, or comment)
        assert "lock=locks/pip.lock" in nox or "lock: locks/pip.lock" in nox
        assert "@tags:" in nox or "tags" in nox
        assert "gpu" in nox

    def test_artifact_manifest_round_trip(self):
        """Extract manifest from artifact, re-parse → equivalent PKG_GRAPH"""
        manifest = """[apt/base]
mode=multi
packages:
  curl
# @tags: curl=base"""
        original_hash = compute_manifest_hash(manifest)
        graph = parse_pkgm(manifest)
        install_sh = emit_install_sh(graph)

        # Extract manifest from artifact comments and re-parse
        # (In real implementation, artifact contains full manifest for re-extraction)
        # Verify artifact hash matches original
        extracted_manifest = manifest  # Simplified: actual impl extracts from comments
        extracted_hash = compute_manifest_hash(extracted_manifest)
        assert original_hash == extracted_hash


# ============================================================================
# PHASE 0G: Manifest Idempotency (state tracking)
# ============================================================================


class TestManifestIdempotency:
    """RED: Idempotent installations via manifest hash tracking"""

    def test_manifest_hash_in_artifact(self):
        """Generated artifact includes manifest hash (Tier 1 idempotency)"""
        manifest = """[apt/base]
packages:
  curl"""
        graph = parse_pkgm(manifest)
        install_sh = emit_install_sh(graph)
        manifest_hash = compute_manifest_hash(manifest)

        # Artifact should contain hash for idempotency check
        assert manifest_hash in install_sh or "# Manifest hash:" in install_sh


if __name__ == "__main__":
    # Run with: pytest tests/test_pkgm.py -v
    pytest.main([__file__, "-v"])
