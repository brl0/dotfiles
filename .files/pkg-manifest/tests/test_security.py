import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from install_from_manifest import install_from_manifest
from repl import PkgmREPL

@patch("subprocess.run")
def test_repl_sign_verify(mock_run):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        repl = PkgmREPL()
        manifest = tmp_path / "test.pkgm"
        manifest.write_text("dummy")
        
        mock_run.return_value.returncode = 0
        repl.do_sign(str(manifest))
        mock_run.assert_called_with(["gpg", "--detach-sign", "--armor", str(manifest)], check=True)
        
        repl.do_verify(str(manifest))
        mock_run.assert_called_with(["gpg", "--verify", f"{manifest}.asc", str(manifest)], check=False)

@patch("subprocess.run")
def test_install_enforce_signature_missing_file(mock_run):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manifest = tmp_path / "test.pkgm"
        manifest.write_text("dummy")
        
        code = install_from_manifest(str(manifest), str(tmp_path), enforce_signature=True)
        assert code == 1

@patch("subprocess.run")
def test_install_enforce_signature_verify_success(mock_run):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manifest = tmp_path / "test.pkgm"
        manifest.write_text("dummy")
        sig_file = tmp_path / "test.pkgm.asc"
        sig_file.write_text("dummy sig")
        
        def side_effect(args, **kwargs):
            class Result:
                returncode = 0
            return Result()
        mock_run.side_effect = side_effect
        
        with patch("install_from_manifest.parse_pkgm"):
            with patch("install_from_manifest.emit_install_sh"):
                code = install_from_manifest(str(manifest), str(tmp_path), enforce_signature=True)
                assert code == 0

@patch("subprocess.run")
def test_install_enforce_signature_verify_fail(mock_run):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manifest = tmp_path / "test.pkgm"
        manifest.write_text("dummy")
        sig_file = tmp_path / "test.pkgm.asc"
        sig_file.write_text("dummy sig")
        
        def side_effect(args, **kwargs):
            class Result:
                returncode = 1 if "gpg" in args else 0
            return Result()
        mock_run.side_effect = side_effect
        
        code = install_from_manifest(str(manifest), str(tmp_path), enforce_signature=True)
        assert code == 1

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
