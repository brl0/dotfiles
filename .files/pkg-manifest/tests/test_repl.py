import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from repl import PkgmREPL
from gen import Package

def test_repl_add():
    repl = PkgmREPL()
    repl.do_add("apt/base curl")
    assert "apt/base" in repl.graph.sections
    assert len(repl.graph.sections["apt/base"].packages) == 1
    assert repl.graph.sections["apt/base"].packages[0].name == "curl"

def test_repl_remove():
    repl = PkgmREPL()
    repl.do_add("apt/base curl")
    repl.do_add("apt/base git")
    repl.do_remove("apt/base curl")
    assert len(repl.graph.sections["apt/base"].packages) == 1
    assert repl.graph.sections["apt/base"].packages[0].name == "git"

def test_repl_load_save(tmp_path):
    manifest_file = tmp_path / "test.pkgm"
    manifest_file.write_text("[apt/base]\npackages:\n  curl\n")
    
    repl = PkgmREPL()
    repl.do_load(str(manifest_file))
    
    assert "apt/base" in repl.graph.sections
    assert len(repl.graph.sections["apt/base"].packages) == 1
    
    repl.do_add("apt/base git")
    
    out_file = tmp_path / "out.pkgm"
    repl.do_save(str(out_file))
    
    content = out_file.read_text()
    assert "curl" in content
    assert "git" in content

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
