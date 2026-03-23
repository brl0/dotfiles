"""Parallel execution engine for pkg-manifest."""

import concurrent.futures
import json
import subprocess
import sys
import time
from pathlib import Path

from gen import PKG_GRAPH, emit_install_sh, compute_manifest_hash


def get_state_file(project_name: str = "pkgm") -> Path:
    """Get path to the state file."""
    return Path.home() / f".{project_name}.pkgm.state"


def load_state(project_name: str = "pkgm") -> dict:
    """Load state from JSON file."""
    sf = get_state_file(project_name)
    if sf.exists():
        try:
            with open(sf) as f:
                return json.load(f)
        except Exception:
            pass
    return {"finished_managers": []}


def save_state(state: dict, project_name: str = "pkgm") -> None:
    """Save state to JSON file safely."""
    sf = get_state_file(project_name)
    sf.parent.mkdir(parents=True, exist_ok=True)
    tmp_sf = sf.with_suffix(".state.tmp")
    with open(tmp_sf, "w") as f:
        json.dump(state, f)
    tmp_sf.rename(sf)


class ParallelRunner:
    """Executes PKG_GRAPH sections concurrently based on manager dependencies."""

    def __init__(
        self,
        graph: PKG_GRAPH,
        project_name: str = "pkgm",
        manifest_str: str = "",
        force: bool = False,
        max_workers: int = 4,
    ):
        self.graph = graph
        self.project_name = project_name
        self.manifest_str = manifest_str
        self.force = force
        self.max_workers = max_workers
        self.manifest_hash = compute_manifest_hash(manifest_str) if manifest_str else ""
        self.state = load_state(project_name)
        self.overall_status = 0

    def _build_section_deps(self) -> dict[str, list[str]]:
        """Map each section to its dependent sections."""
        manager_deps = self.graph.manager_deps
        mgr_to_sections = {}
        for sec_name, sec in self.graph.sections.items():
            mgr_to_sections.setdefault(sec.manager, []).append(sec_name)

        sec_deps = {sec_name: [] for sec_name in self.graph.sections}

        for sec_name, sec in self.graph.sections.items():
            mgr = sec.manager
            for dep_mgr in manager_deps.get(mgr, []):
                if dep_mgr in mgr_to_sections:
                    sec_deps[sec_name].extend(mgr_to_sections[dep_mgr])

        return sec_deps

    def _execute_section(self, section_name: str) -> tuple[int, str, str]:
        """Execute a single section and capture its output."""
        script = emit_install_sh(
            self.graph,
            project_name=self.project_name,
            force=True,  # Force internally to bypass bash-level idempotency
            manifest_str=self.manifest_str,
            skip_state=True,
            section_filter=[section_name],
        )

        result = subprocess.run(
            ["/bin/bash", "-c", script],
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout, result.stderr

    def run(self) -> int:
        """Run the graph execution, resolving DAG concurrently."""
        if not self.force and self.manifest_hash:
            last_hash = self.state.get("manifest_hash")
            if last_hash == self.manifest_hash:
                print("✓ Manifest unchanged (hash match), skipping installation", file=sys.stderr)
                return 0

        sec_deps = self._build_section_deps()
        completed = set()
        failed = set()
        in_progress = set()
        pending = set(self.graph.sections.keys())

        start_time = time.time()
        print(f"🚀 Starting parallel execution of {len(pending)} sections...", file=sys.stderr)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_sec = {}

            while pending or in_progress:
                # Submit ready tasks
                for sec in list(pending):
                    deps = sec_deps[sec]
                    if all(d in completed for d in deps):
                        pending.remove(sec)
                        in_progress.add(sec)
                        print(f"  [Queueing] {sec}", file=sys.stderr)
                        future = executor.submit(self._execute_section, sec)
                        future_to_sec[future] = sec

                if not in_progress:
                    if pending:
                        print(f"❌ Deadlock detected! Unresolvable dependencies: {pending}", file=sys.stderr)
                        return 1
                    break

                # Wait for any to complete
                done, _ = concurrent.futures.wait(
                    future_to_sec.keys(), return_when=concurrent.futures.FIRST_COMPLETED
                )

                for future in done:
                    sec = future_to_sec.pop(future)
                    in_progress.remove(sec)
                    try:
                        ret, stdout, stderr = future.result()
                        # Print captured output safely sequentially
                        print(f"\n--- Output for [{sec}] ---", file=sys.stderr)
                        if stdout.strip():
                            print(stdout.strip(), file=sys.stderr)
                        if stderr.strip():
                            print(stderr.strip(), file=sys.stderr)
                        print("-" * (20 + len(sec)), file=sys.stderr)

                        if ret in (0, 2):
                            completed.add(sec)
                            if ret == 2:
                                self.overall_status = 2
                                mgr = self.graph.sections[sec].manager
                                if mgr not in self.state["finished_managers"]:
                                    self.state["finished_managers"].append(mgr)
                            print(f"✅ Finished {sec}", file=sys.stderr)
                        else:
                            failed.add(sec)
                            print(f"❌ Failed {sec} with exit code {ret}", file=sys.stderr)
                            # Abort the rest
                            executor.shutdown(wait=False, cancel_futures=True)
                            return 1
                    except Exception as e:
                        print(f"❌ Exception running {sec}: {e}", file=sys.stderr)
                        executor.shutdown(wait=False, cancel_futures=True)
                        return 1

        elapsed = time.time() - start_time
        print(f"⏱️  Parallel execution complete in {elapsed:.2f}s", file=sys.stderr)

        if not failed:
            self.state["manifest_hash"] = self.manifest_hash
            self.state["timestamp"] = int(time.time())
            save_state(self.state, self.project_name)

        return self.overall_status
