#!/usr/bin/env python3
"""Build a standalone Physics AI Manager executable with PyInstaller."""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEP = ";" if os.name == "nt" else ":"


def check_tkinter() -> None:
    """Fail before PyInstaller if this interpreter cannot use Tcl/Tk."""
    try:
        import tkinter  # noqa: PLC0415
        import _tkinter  # noqa: F401, PLC0415

        # Tcl() does not require a graphical display, but it verifies that the
        # Python extension can actually load the system Tcl runtime.
        interp = tkinter.Tcl()
        patchlevel = interp.eval("info patchlevel")
        print(
            f"Tkinter preflight: OK "
            f"(Tk {tkinter.TkVersion}, Tcl {patchlevel})"
        )
    except Exception as exc:
        print("ERROR: This Python interpreter cannot use Tkinter/Tcl-Tk.", file=sys.stderr)
        print(f"Interpreter: {sys.executable}", file=sys.stderr)
        print(f"Reason: {exc}", file=sys.stderr)
        if sys.platform.startswith("linux"):
            print(file=sys.stderr)
            print("On Debian/Ubuntu, install Tkinter with:", file=sys.stderr)
            print("  sudo apt update", file=sys.stderr)
            print("  sudo apt install python3-tk", file=sys.stderr)
            print(file=sys.stderr)
            print("Then verify it with:", file=sys.stderr)
            print(
                '  python3 -c "import tkinter, _tkinter; '
                "print(tkinter.TkVersion)\"",
                file=sys.stderr,
            )
        elif sys.platform == "darwin":
            print(
                "Install/use a Python distribution that includes a working Tcl/Tk runtime, "
                "then rebuild.",
                file=sys.stderr,
            )
        elif os.name == "nt":
            print(
                "Reinstall Python with the optional Tcl/Tk and IDLE component enabled, then rebuild.",
                file=sys.stderr,
            )
        raise SystemExit(2) from exc


def main() -> int:
    check_tkinter()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onedir",
        "--name",
        "PhysicsAIManager",
        "--add-data",
        f"{ROOT / 'library'}{SEP}library",
        "--add-data",
        f"{ROOT / 'assets'}{SEP}assets",
        str(ROOT / "app.py"),
    ]
    print("Platform:", platform.platform())
    print("Running:", " ".join(map(str, cmd)))
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
