"""
thermal_pacer/__main__.py

CLI entry point for the IntelligentThermalPacer package.

Dispatch table
--------------
  sudo python3 -m thermal_pacer --install      §9  — Install systemd units
  sudo python3 -m thermal_pacer --uninstall    §10 — Remove systemd units
       python3 -m thermal_pacer --calibrate    §7  — Run calibration protocol
       python3 -m thermal_pacer --help              — Show usage
"""

from __future__ import annotations

import grp
import os
import pathlib
import shutil
import subprocess
import sys
from typing import NoReturn

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

_TEMPLATES_DIR: pathlib.Path = pathlib.Path(__file__).parent / "templates"
_SYSTEMD_DIR: pathlib.Path = pathlib.Path("/etc/systemd/system")
_CONFIG_DIR: pathlib.Path = pathlib.Path("/etc/thermal_pacer")

_SOCKET_UNIT_NAME: str = "thermal_pacer.socket"
_SERVICE_UNIT_NAME: str = "thermal_pacer.service"

_RUNTIME_SOCK: pathlib.Path = pathlib.Path("/var/run/thermal_pacer.sock")
_RUNTIME_BAK: pathlib.Path = pathlib.Path("/var/run/thermal_pacer.governors.bak")

# Default interpreter token written in the template (§9-3)
_TEMPLATE_PYTHON: str = "/usr/bin/python3"


# ---------------------------------------------------------------------------
# Root-privilege guard
# ---------------------------------------------------------------------------

def _require_root(action: str) -> None:
    """Raise PermissionError if the process is not running as root (§9-1, §10-1)."""
    if os.geteuid() != 0:
        raise PermissionError(
            f"[ThermalPacer] '{action}' requires root privileges. "
            "Re-run with: sudo python3 -m thermal_pacer " + action
        )


# ---------------------------------------------------------------------------
# §9  Installation
# ---------------------------------------------------------------------------

def install() -> None:
    """
    Install the IntelligentThermalPacer systemd socket and service (§9).

    Steps:
      1. Verify root execution.
      2. Ensure group 'thermal' exists; add SUDO_USER to it if available.
      3. Patch the service template to use the current Python interpreter.
      4. Write unit files to /etc/systemd/system/.
      5. Create /etc/thermal_pacer/ configuration directory (mode 0755).
      6. Run: systemctl daemon-reload && systemctl enable --now thermal_pacer.socket.
      7. Print confirmation message.
    """
    _require_root("--install")

    # --- Step 2: Ensure group 'thermal' exists ---
    try:
        grp.getgrnam("thermal")
        print("[Install] Group 'thermal' already exists.")
    except KeyError:
        print("[Install] Creating group 'thermal'…")
        _run(["groupadd", "thermal"])

    sudo_user: str | None = os.environ.get("SUDO_USER")
    if sudo_user:
        print(f"[Install] Adding '{sudo_user}' to group 'thermal'…")
        _run(["usermod", "-aG", "thermal", sudo_user])
    else:
        print(
            "[Install] NOTICE: SUDO_USER not set (native root shell). "
            "Skipping user-to-group assignment. "
            "Add your user manually with:  usermod -aG thermal <username>",
        )

    # --- Step 3: Patch service template with current interpreter path ---
    current_python: str = sys.executable
    service_src = (_TEMPLATES_DIR / _SERVICE_UNIT_NAME).read_text(encoding="utf-8")
    # Global substitution of the default token (§9-3)
    service_patched = service_src.replace(_TEMPLATE_PYTHON, current_python)

    socket_src = (_TEMPLATES_DIR / _SOCKET_UNIT_NAME).read_text(encoding="utf-8")

    # --- Step 4: Write unit files ---
    _systemd_service_dest = _SYSTEMD_DIR / _SERVICE_UNIT_NAME
    _systemd_socket_dest  = _SYSTEMD_DIR / _SOCKET_UNIT_NAME

    _SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)

    _systemd_service_dest.write_text(service_patched, encoding="utf-8")
    print(f"[Install] Written: {_systemd_service_dest}")

    _systemd_socket_dest.write_text(socket_src, encoding="utf-8")
    print(f"[Install] Written: {_systemd_socket_dest}")

    # --- Step 5: Create configuration directory ---
    _CONFIG_DIR.mkdir(mode=0o755, parents=True, exist_ok=True)
    print(f"[Install] Configuration directory ready: {_CONFIG_DIR}")

    # --- Step 6: Reload systemd and enable socket ---
    print("[Install] Reloading systemd and enabling socket…")
    _run(["systemctl", "daemon-reload"])
    _run(["systemctl", "enable", "--now", _SOCKET_UNIT_NAME])

    # --- Step 7: Confirmation ---
    print("IntelligentThermalPacer socket successfully installed and initialized via systemd.")


# ---------------------------------------------------------------------------
# §10  Uninstallation
# ---------------------------------------------------------------------------

def uninstall() -> None:
    """
    Remove the IntelligentThermalPacer systemd units and all system artifacts (§10).

    Steps:
      1. Verify root execution.
      2. Stop and disable systemd units.
      3. Delete unit files and dangling runtime sockets/backups.
      4. Delete /etc/thermal_pacer/ entirely.
      5. Print confirmation message.
    """
    _require_root("--uninstall")

    # --- Step 2: Stop and disable systemd units ---
    print("[Uninstall] Stopping and disabling systemd units…")

    # Stop the service if it is currently running (ignore error if already stopped)
    _run(
        ["systemctl", "stop", _SERVICE_UNIT_NAME],
        ignore_errors=True,
    )
    _run(
        ["systemctl", "disable", "--now", _SOCKET_UNIT_NAME],
        ignore_errors=True,
    )
    _run(["systemctl", "daemon-reload"])

    # --- Step 3: Delete unit files and dangling runtime artifacts ---
    _remove_file(_SYSTEMD_DIR / _SOCKET_UNIT_NAME)
    _remove_file(_SYSTEMD_DIR / _SERVICE_UNIT_NAME)
    _remove_file(_RUNTIME_SOCK)
    _remove_file(_RUNTIME_BAK)

    # --- Step 4: Delete configuration directory entirely ---
    if _CONFIG_DIR.exists():
        shutil.rmtree(_CONFIG_DIR)
        print(f"[Uninstall] Deleted configuration directory: {_CONFIG_DIR}")
    else:
        print(f"[Uninstall] Configuration directory not found (already clean): {_CONFIG_DIR}")

    # --- Step 5: Confirmation ---
    print("IntelligentThermalPacer completely uninstalled from system.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd: list[str], ignore_errors: bool = False) -> None:
    """Run a subprocess command, printing it first."""
    print(f"[CLI] $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if ignore_errors:
            print(f"[CLI] (ignored) {result.stderr.strip()}")
        else:
            print(result.stderr.strip(), file=sys.stderr)
            sys.exit(result.returncode)


def _remove_file(path: pathlib.Path) -> None:
    """Delete a file if it exists; log the result."""
    if path.exists() or path.is_symlink():
        path.unlink()
        print(f"[Uninstall] Deleted: {path}")
    else:
        print(f"[Uninstall] Not found (skipped): {path}")


def _usage() -> None:
    print(
        "Usage:\n"
        "  sudo python3 -m thermal_pacer --install      Install systemd socket & service\n"
        "  sudo python3 -m thermal_pacer --uninstall    Remove systemd socket & service\n"
        "       python3 -m thermal_pacer --calibrate    Run thermal calibration protocol\n"
        "       python3 -m thermal_pacer.daemon         Start the daemon directly\n"
        "       python3 -m thermal_pacer.daemon --restore-governors  OOB governor restore\n"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        _usage()
        return

    if "--install" in args:
        try:
            install()
        except PermissionError as exc:
            print(exc, file=sys.stderr)
            sys.exit(1)

    elif "--uninstall" in args:
        try:
            uninstall()
        except PermissionError as exc:
            print(exc, file=sys.stderr)
            sys.exit(1)

    elif "--calibrate" in args:
        from thermal_pacer.calibration import run_calibration
        run_calibration()

    else:
        print(f"[ThermalPacer] Unknown argument(s): {args}", file=sys.stderr)
        _usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
