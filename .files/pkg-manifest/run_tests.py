"""Simple test runner for gen.py tests (no pytest dependency)"""

import sys

sys.path.insert(0, ".")

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

passed = 0
failed = 0
errors = []


def test(name, func):
    global passed, failed
    try:
        func()
        passed += 1
        print(f"✓ {name}")
    except AssertionError as e:
        failed += 1
        print(f"✗ {name}: {e}")
        errors.append((name, str(e)))
    except Exception as e:
        failed += 1
        print(f"✗ {name}: {type(e).__name__}: {e}")
        errors.append((name, f"{type(e).__name__}: {e}"))


# Phase 0A: Parsing & Basic Functionality
def test_parse_simple_manifest():
    manifest = "[apt/base]\npackages:\n  curl\n  git"
    graph = parse_pkgm(manifest)
    assert "apt/base" in graph.sections
    assert graph.sections["apt/base"].manager == "apt"
    assert graph.sections["apt/base"].cache_group == "base"
    assert len(graph.sections["apt/base"].packages) == 2
    assert graph.sections["apt/base"].packages[0].name == "curl"
    assert graph.sections["apt/base"].packages[1].name == "git"


def test_parse_manifest_with_declarative_metadata():
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


def test_parse_manifest_with_system_metadata():
    manifest = """[apt/base]
mode=multi
packages:
  curl
  build-essential[~=12]
# @tags: curl=base, build-essential=base,build
# @depends: [none]"""
    graph = parse_pkgm(manifest)
    section_meta = graph.sections["apt/base"].metadata
    assert "curl=base" in section_meta.get("tags", "")
    assert "build-essential=base" in section_meta.get("tags", "")


def test_parse_packages_with_version_constraints():
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
    assert "[~=12]" in pkgs[1].version
    assert pkgs[2].name == "python3-dev"


def test_parse_multiple_sections():
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


# Phase 0B: Hash
def test_manifest_hash_deterministic():
    manifest = "[apt/base]\npackages:\n  curl"
    h1 = compute_manifest_hash(manifest)
    h2 = compute_manifest_hash(manifest)
    assert h1 == h2


def test_manifest_hash_changes():
    m1 = "[apt/base]\npackages:\n  curl"
    m2 = "[apt/base]\npackages:\n  git"
    assert compute_manifest_hash(m1) != compute_manifest_hash(m2)


def test_manifest_hash_format():
    manifest = "[apt/base]\npackages:\n  curl"
    h = compute_manifest_hash(manifest)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


# Phase 0C: Tag Filtering
def test_tag_filtering_default():
    manifest = """[apt/base]
packages:
  curl
  torch
  poetry
# @tags: curl=base, torch=gpu, poetry=optional"""
    graph = parse_pkgm(manifest)
    filtered = graph.filter_tags()
    assert len(filtered.sections["apt/base"].packages) == 3


def test_tag_filtering_include():
    manifest = """[apt/base]
packages:
  curl
  torch
  poetry
  untagged
# @tags: curl=base, torch=gpu, poetry=optional"""
    graph = parse_pkgm(manifest)
    filtered = graph.filter_tags(include=["gpu"])
    names = {p.name for p in filtered.sections["apt/base"].packages}
    assert "torch" in names
    assert "untagged" in names
    assert "curl" not in names or len(names) == 2


# Phase 0D: Package Diff
def test_package_diff_basic():
    old = [Package("curl", "7.0"), Package("git", "2.0")]
    new = [Package("curl", "7.1"), Package("git", "2.0"), Package("jq", "1.6")]
    added, removed, modified = diff_packages(old, new)
    assert "jq" in {p.name for p in added}
    assert "curl" in {p.name for p in modified}
    assert len(removed) == 0


# Phase 0E: Lock File
def test_lock_file_consumption():
    lock = "torch==2.0.1\ntransformers==4.30.2\n"
    manifest = """[pip/ml]
lock=locks/pip.lock
packages:
  torch
  transformers"""
    graph = parse_pkgm(manifest)
    graph.apply_lock_file("pip", lock)
    torch_pkg = next(p for p in graph.sections["pip/ml"].packages if p.name == "torch")
    transformers_pkg = next(
        p for p in graph.sections["pip/ml"].packages if p.name == "transformers"
    )
    assert torch_pkg.version == "==2.0.1"
    assert transformers_pkg.version == "==4.30.2"


# Phase 0F: Round-trip
def test_manifest_round_trip():
    original = """[apt/base]
mode=multi
packages:
  curl
  git"""
    graph = parse_pkgm(original)
    regenerated = emit_manifest(graph)
    re_graph = parse_pkgm(regenerated)
    assert "apt/base" in re_graph.sections
    assert len(re_graph.sections["apt/base"].packages) == 2


# Phase 0G: Artifact Embedding
def test_artifact_metadata_shell():
    manifest = """[apt/base]
mode=multi
inventory=apt list --installed
packages:
  curl
# @tags: curl=base"""
    graph = parse_pkgm(manifest)
    install_sh = emit_install_sh(graph)
    assert "# mode=multi" in install_sh
    assert "# inventory=" in install_sh
    assert "# @tags:" in install_sh


# Phase 10: Environment Variable Interpolation
def test_env_var_interpolation():
    import os
    original = os.environ.get("TEST_PKG_PREFIX")
    os.environ["TEST_PKG_PREFIX"] = "custom"
    try:
        manifest = "[apt/base]\npackages:\n  ${TEST_PKG_PREFIX}-tools\n  $TEST_PKG_PREFIX-utils\n# @tags: ${TEST_PKG_PREFIX}-tools=base"
        graph = parse_pkgm(manifest)
        pkgs = graph.sections["apt/base"].packages
        assert pkgs[0].name == "custom-tools"
        assert pkgs[1].name == "custom-utils"
        assert "custom-tools=base" in graph.sections["apt/base"].metadata.get("tags", "")
    finally:
        if original is None:
            del os.environ["TEST_PKG_PREFIX"]
        else:
            os.environ["TEST_PKG_PREFIX"] = original

def test_condition_based_selection():
    import sys
    manifest_incl = f"""[apt/base]
packages:
  curl
# @condition(curl): sys.platform == '{sys.platform}'"""
    graph_incl = parse_pkgm(manifest_incl)
    assert len(graph_incl.sections["apt/base"].packages) == 1

    manifest_excl = """[apt/base]
packages:
  curl
# @condition(curl): sys.platform == 'non_existent_os'"""
    graph_excl = parse_pkgm(manifest_excl)
    assert len(graph_excl.sections["apt/base"].packages) == 0


# Run all tests
print("Running Package Manifest Generator Tests\n" + "=" * 50)

test("test_parse_simple_manifest", test_parse_simple_manifest)
test("test_parse_declarative_metadata", test_parse_manifest_with_declarative_metadata)
test("test_parse_system_metadata", test_parse_manifest_with_system_metadata)
test("test_parse_version_constraints", test_parse_packages_with_version_constraints)
test("test_parse_multiple_sections", test_parse_multiple_sections)
test("test_hash_deterministic", test_manifest_hash_deterministic)
test("test_hash_changes_with_content", test_manifest_hash_changes)
test("test_hash_format", test_manifest_hash_format)
test("test_tag_filtering_default", test_tag_filtering_default)
test("test_tag_filtering_include", test_tag_filtering_include)
test("test_package_diff", test_package_diff_basic)
test("test_lock_file", test_lock_file_consumption)
test("test_manifest_round_trip", test_manifest_round_trip)
test("test_artifact_metadata", test_artifact_metadata_shell)
test("test_env_var_interpolation", test_env_var_interpolation)
test("test_condition_based_selection", test_condition_based_selection)

# Add REPL tests
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tests"))
from test_repl import test_repl_add, test_repl_remove
test("test_repl_add", test_repl_add)
test("test_repl_remove", test_repl_remove)

print("\n" + "=" * 50)
print(f"✓ Passed: {passed}")
if failed > 0:
    print(f"✗ Failed: {failed}")
    for name, err in errors:
        print(f"  - {name}: {err}")
else:
    print("✅ All tests passed!")

sys.exit(0 if failed == 0 else 1)
