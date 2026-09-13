#!/usr/bin/env python3
"""Clean-wheel smoke test for the archharness distribution.

Builds a wheel from the current checkout, installs it into an isolated
virtual environment, and verifies the installed package is self-contained:

- ``archharness --version`` works;
- ``archharness root`` resolves inside site-packages;
- ``archharness doctor`` passes from a directory without a workspace;
- ``archharness/data/config.yaml`` exists and validates;
- tools, standards, and skills directories are present.

Usage:
    python scripts/smoke_wheel.py
    python scripts/smoke_wheel.py --keep  # keep temp dirs for debugging

Exit codes: 0 = smoke passed, 1 = smoke failed, 2 = environment error.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, timeout=300)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keep", action="store_true", help="keep temp build/install dirs for debugging")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="archharness-smoke-"))
    wheel_dir = tmp / "wheel"
    venv_dir = tmp / "venv"
    work_dir = tmp / "work"
    wheel_dir.mkdir()
    work_dir.mkdir()
    failures: list[str] = []

    def fail(message: str) -> None:
        failures.append(message)
        print(f"  [!!]  {message}")

    try:
        print(f"smoke root: {tmp}")
        r = _run([sys.executable, "scripts/assemble_data.py"], cwd=ROOT)
        if r.returncode != 0:
            print(r.stdout + r.stderr)
            return 2

        r = _run([sys.executable, "-m", "build", "--wheel", "--outdir", str(wheel_dir)], cwd=ROOT)
        if r.returncode != 0:
            print(r.stdout[-2000:] + r.stderr[-2000:])
            return 2
        wheels = list(wheel_dir.glob("*.whl"))
        if not wheels:
            print("  [!!]  no wheel built")
            return 2
        wheel = wheels[0]
        print(f"  [ok]  built {wheel.name}")

        r = _run([sys.executable, "-m", "venv", str(venv_dir)])
        if r.returncode != 0:
            print(r.stdout + r.stderr)
            return 2
        vpython = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        vcli = venv_dir / ("Scripts/archharness.exe" if os.name == "nt" else "bin/archharness")
        r = _run([str(vpython), "-m", "pip", "install", "--quiet", str(wheel), "pyyaml"])
        if r.returncode != 0:
            print(r.stdout[-2000:] + r.stderr[-2000:])
            return 2
        print("  [ok]  installed wheel into isolated venv")

        # --version
        r = _run([str(vcli), "--version"], cwd=work_dir)
        if r.returncode != 0 or "ArchHarness" not in r.stdout:
            fail("--version failed")
        else:
            print(f"  [ok]  {r.stdout.strip()}")

        # root resolves inside site-packages
        r = _run([str(vcli), "root"], cwd=work_dir)
        root_out = r.stdout.strip()
        if r.returncode != 0 or "site-packages" not in root_out:
            fail(f"root did not resolve to site-packages: {root_out!r}")
        else:
            print(f"  [ok]  root: {root_out}")

        # doctor passes without a workspace
        r = _run([str(vcli), "doctor"], cwd=work_dir)
        if r.returncode != 0 or "doctor: OK" not in r.stdout:
            fail(f"doctor failed:\n{r.stdout}\n{r.stderr}")
        else:
            print("  [ok]  doctor: OK")

        # config.yaml exists and validates
        data_root = Path(root_out)
        for rel in ("config.yaml", "tools/arch-diagram-gen/generator.py",
                    "standards/arch-gate-policy.yaml", "skills/arch-validate/SKILL.md",
                    "schemas/req-v1.schema.json", "schemas/artifact-v1.schema.json"):
            if not (data_root / rel).is_file():
                fail(f"missing packaged file: {rel}")
        if not failures:
            print("  [ok]  packaged data layout complete")

        cfg = data_root / "config.yaml"
        if cfg.is_file():
            r = _run([str(vcli), "validate-yaml", str(cfg)], cwd=work_dir)
            if r.returncode != 0:
                fail(f"packaged config.yaml failed validation:\n{r.stdout}\n{r.stderr}")
            else:
                print("  [ok]  packaged config.yaml validates")

        if failures:
            print(f"\nsmoke FAILED ({len(failures)} problem(s))")
            return 1
        print("\nsmoke passed")
        return 0
    finally:
        # Always remove the generated runtime data dir; it is git-ignored.
        shutil.rmtree(ROOT / "archharness" / "data", ignore_errors=True)
        if args.keep:
            print(f"kept: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
