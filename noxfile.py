import nox


@nox.session(venv_backend=None)
def convert_pkgs(session):
    cmds = (
        "bash",
        "-c",
        "mamba list --no-banner | grep -e pypi | awk '{print $1}'",
    )
    out = session.run(*cmds, silent=True, external=True)
    print(out)
    _pkgs = out.split("\n")
    _pkgs = [p for p in _pkgs if p]
    pkgs = []
    pypi = []
    for pkg in _pkgs:
        cmds = f"mamba repoquery search --no-banner -C {pkg}".split()
        out = session.run(*cmds, silent=True, external=True, success_codes=[0, 1])
        if "No match found" not in out and "No entries matching" not in out:
            print("found:", pkg)
            pkgs.append("  - " + pkg)
        else:
            print("not found:", pkg)
            pypi.append("  - " + pkg)
    print("pkgs:\n", "\n".join(pkgs))
    print("pypi:\n", "\n".join(pypi))
