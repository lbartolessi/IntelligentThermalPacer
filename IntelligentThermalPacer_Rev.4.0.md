# PRODUCTION-READY TECHNICAL SPECIFICATION: `IntelligentThermalPacer` (Revision 4.0 - Final)

## 1. System Overview and Core Life Cycle Model

`IntelligentThermalPacer` is a distributed, proactive application-level thermal throttling solution for Linux systems. The architecture consists of a high-privilege daemon and a lightweight, zero-dependency client library communicating via a Unix Domain Socket located at `/var/run/thermal_pacer.sock`.

* **`thermal_pacerd` (The Daemon):** Runs as a background service with `root` privileges. Its lifecycle is managed exclusively via **systemd socket activation** to ensure zero idle resource consumption. It remains off and consumes no resources until a client application writes to the socket. It aggregates system-wide hardware telemetry, manages Linux scaling governors, enforces thermal limits, and maintains statistical rolling windows.
* **`thermal_pacer` (The Client Library):** Runs in unprivileged user space. It exposes a high-level Python Context Manager (`ThermalGuard`) allowing host applications to gracefully slow down processing loops in-thread based on real-time hardware status.

### Connection Topology and Absolute State Restoration

* The daemon tracks concurrent clients via an internal atomic integer (`client_count`).
* Connection establishment increments `client_count` by 1.
* Socket disconnection (normal exit, unhandled exception, or unexpected termination like `SIGKILL` of the client) is detected by the daemon via an EOF on the read stream, decrementing `client_count` by 1.
* When `client_count` reaches 0, the daemon performs a graceful reset of all hardware parameters to their baseline system values and exits cleanly via `sys.exit(0)`.

---

## 2. Hardened System Configuration (systemd)

To prevent privilege escalation vectors and handle uncatchable signals (`SIGKILL`), the systemd configuration enforces strict access permissions and secondary recovery hooks.

### File: `/etc/systemd/system/thermal_pacer.socket`

```ini
[Unit]
Description=Activation Socket for the IntelligentThermalPacer Daemon
# Hardware thermal preservation

[Socket]
ListenStream=/var/run/thermal_pacer.sock
SocketUser=root
SocketGroup=thermal
SocketMode=0660

[Install]
WantedBy=sockets.target
```

### File: `/etc/systemd/system/thermal_pacer.service`

```ini
[Unit]
Description=IntelligentThermalPacer Intelligent Thermal Regulation Daemon
Requires=thermal_pacer.socket
After=thermal_pacer.socket

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m thermal_pacer.daemon
ExecStopPost=/usr/bin/python3 -m thermal_pacer.daemon --restore-governors
User=root
Group=root
Restart=no

[Install]
WantedBy=multi-user.target
```

---

## 3. Configuration File Schema (`thermal_config.json`)

Located by default at `/etc/thermal_pacer/thermal_config.json`. All CPU boost properties are normalized under platform-agnostic key names to avoid syntax ambiguities.

```json
{
  "thermal_settings": {
    "max_target_temp": 62.0,
    "strategy": "eco",
    "safety_margin_celsius": 5.0
  },
  "linux_governor": {
    "force_powersave_on_start": true,
    "disable_cpu_boost": true,
    "restore_on_exit": true
  },
  "telemetry": {
    "polling_interval_seconds": 1.0,
    "enable_nvidia_gpu": true
  },
  "calibration_diagnostics": {
    "last_calibration_utc": "2026-06-17T11:15:00Z",
    "calibration_expiration_days": 30,
    "thermal_efficiency_rating": "MEDIUM_COMPACT_CHASSIS",
    "hardware_safety_recommendation": "For multi-process apps, do not exceed 50% of available CPU cores as initial workers."
  },
  "statistical_memory": {
    "trend_analysis_window_seconds": 180,
    "emit_warnings": true
  }
}
```

### Rule of Precedence for Initialization Flags

To resolve potential semantic ambiguities between configuration flags:

* If `strategy` is explicitly configured to `"eco"`, it takes absolute functional precedence. The daemon will **always** force the CPU scaling governors to `"powersave"` and disable core boost during startup execution, completely overriding and ignoring a `force_powersave_on_start: false` or `disable_cpu_boost: false` setting.
* The `force_powersave_on_start` and `disable_cpu_boost` binary flags are only independently evaluated if the global `strategy` is set to a non-restrictive baseline mode (e.g., `"custom"` or `"performance"`).

---

## 4. Robust IPC Protocol (Socket Specification)

All communication over the socket consists of single-line valid JSON payloads terminated with a mandatory newline character (`\n`).

### Command 1: Pace Check

* **Client Payload:** `{"command": "pace_check"}`
* **Daemon Response (Allow):** `{"action": "continue"}`
* **Daemon Response (Throttle):** `{"action": "wait", "duration_ms": 45}`

### Command 2: Concurrency Guidance

* **Client Payload:** `{"command": "get_guidance"}`
* **Daemon Response:** `{"action": "guidance_reply", "decision": "HOLD"}` *(Values: `"SCALE_DOWN"`, `"HOLD"`, `"SCALE_UP"`)*.

### Command 3: Error Fallback

* **Daemon Response (Invalid/Unknown Command):** `{"action": "error", "code": "UNKNOWN_COMMAND"}`.

---

## 5. Client Library Signatures and Interfaces (Python API)

The client library must be completely self-contained, lightweight, and utilize strict type hinting. It does not parse or require local configuration files, communicating exclusively via the socket stream. To avoid stream fragmentation bugs common with raw `recv()` packet pooling, it wraps the socket connection using `makefile('r')` to perform safe line-based readings.

```python
import socket
import sys
import time
import json
from types import TracebackType
from typing import Optional, Type, Literal, Any

class ThermalGuard:
    def __init__(self, socket_path: str = "/var/run/thermal_pacer.sock") -> None:
        """
        Initializes the client library pointing to the shared systemd socket.
        Does not establish connection during instantiation.
        """
        self.socket_path: str = socket_path
        self._socket_conn: Optional[socket.socket] = None
        self._socket_file: Optional[Any] = None

    def __enter__(self) -> "ThermalGuard":
        """
        Context manager entry point. Establishes connection to the Unix domain socket.
        Enforces a 5-second socket timeout to prevent application hanging.
        """
        self._connect_to_daemon()
        return self

    def __exit__(
        self, 
        exc_type: Optional[Type[BaseException]], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[TracebackType]
    ) -> Optional[bool]:
        """
        Ensures proper teardown of the connection socket under all execution flows.
        """
        self._disconnect_from_daemon()
        return False  # Propagates host application exceptions naturally

    def pace(self) -> None:
        """
        Injected directly inside host execution loops. Queries the daemon via 'pace_check'.
        If instructed to wait, blocks execution thread cooperatively via time.sleep().
        """
        if not self._socket_conn or not self._socket_file:
            return

        try:
            self._socket_conn.sendall(b'{"command": "pace_check"}\n')
            response_raw = self._socket_file.readline().strip()
            if not response_raw:
                return
            
            response = json.loads(response_raw)
            if response.get("action") == "wait":
                duration_ms = response.get("duration_ms", 0)
                if duration_ms > 0:
                    time.sleep(duration_ms / 1000.0)
        except (socket.error, json.JSONDecodeError):
            # Fail-safe: if daemon is unresponsive, continue processing to avoid breaking host app
            pass

    def get_concurrency_guidance(self) -> Literal["SCALE_DOWN", "HOLD", "SCALE_UP"]:
        """
        Queries the daemon trend metrics to extract operational guidance for worker orchestration.
        """
        if not self._socket_conn or not self._socket_file:
            return "HOLD"

        try:
            self._socket_conn.sendall(b'{"command": "get_guidance"}\n')
            response_raw = self._socket_file.readline().strip()
            if not response_raw:
                return "HOLD"
            
            response = json.loads(response_raw)
            if response.get("action") == "guidance_reply":
                return response.get("decision", "HOLD")
        except (socket.error, json.JSONDecodeError):
            pass
        return "HOLD"

    def _connect_to_daemon(self) -> None:
        try:
            self._socket_conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket_conn.settimeout(5.0)
            self._socket_conn.connect(self.socket_path)
            self._socket_file = self._socket_conn.makefile('r', encoding='utf-8')
        except socket.error as e:
            raise RuntimeError(f"Failed to connect to ThermalPacer daemon: {e}")

    def _disconnect_from_daemon(self) -> None:
        if self._socket_file:
            try:
                self._socket_file.close()
            except Exception:
                pass
            self._socket_file = None
            
        if self._socket_conn:
            try:
                self._socket_conn.close()
            except socket.error:
                pass
            self._socket_conn = None
```

---

## 6. Daemon Internal Logic (`thermal_pacerd`)

### A. Concurrency Model, Thread Safety, and Telemetry Libraries

To handle asynchronous hardware polling alongside incoming client demands cleanly without incurring high processing costs, `thermal_pacerd` implements a multi-threaded server topology via `socketserver.ThreadingUnixStreamServer`.

* A dedicated background thread executes the telemetry acquisition loop precisely every 1.0 seconds.
* A global `threading.Lock` enforces mutual exclusion on all write/read operations targeting the telemetry circular queue.
* **Telemetry Implementation Dependencies:** Real-time temperature fetching must rely on explicit standard ecosystem libraries:
  1. **CPU Temperatures:** Obtained via `psutil.sensors_temperatures()`. The code must iterate over available keys (such as `'coretemp'` or `'cpu_thermal'`) and extract the maximum current value.
  2. **NVIDIA GPU Temperatures:** If `enable_nvidia_gpu` is true, obtained via `pynvml`. The daemon initializes `pynvml.nvmlInit()`, queries handle references via `pynvml.nvmlDeviceGetHandleByIndex(0)`, and samples core metrics via `pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)`.

### B. Accurate CPU Topology and Boost Polarity Management

The daemon must map out CPU topology at startup by reading `/proc/cpuinfo` to detect processor architecture. CPU Boost states feature inverse binary logic states across Intel and AMD kernels which must be handled explicitly:

1. **AMD Architecture:** Paths `/sys/devices/system/cpu/amd_pstate/cpb_boost` or `/sys/devices/system/cpu/cpufreq/boost`.
   * **Disable Boost:** Write `"0"` to the register.
   * **Enable Boost:** Write `"1"` to the register.
2. **Intel Architecture:** Path `/sys/devices/system/cpu/intel_pstate/no_turbo`.
   * **Disable Boost (No Turbo Active):** Write `"1"` to the register.
   * **Enable Boost (Turbo Allowed):** Write `"0"` to the register.

* **Hardware Recovery Cache and Out-Of-Band Restoration:** On initialization, the daemon reads the active scaling governors and boost flags, caching them to memory and writing them to a static emergency state file: `/var/run/thermal_pacer.governors.bak`.
* **`--restore-governors` Operational Path:** When the daemon is executed explicitly with this flag (e.g., triggered via systemd's `ExecStopPost` following an uncatchable `SIGKILL`), it bypasses socket server initialization. It parses `/var/run/thermal_pacer.governors.bak`, forcefully writes the recorded baseline values back to their respective hardware sysfs targets, unlinks the `.bak` file, and exits immediately via `sys.exit(0)`.

### C. Real-Time Rolling Windows and Trend Analysis

The daemon maintains a sliding circular queue containing historical telemetry points spanning `trend_analysis_window_seconds` (defaulting to 180 seconds). To remain robust against configuration adjustments, the window is dynamically segmented into 3 equal parts ($S_{size} = \text{window\_seconds} // 3$) relative to the current timestamp:

* `Segment_Current`: Slices from $0$ to $S_{size}$ seconds ago.
* `Segment_Previous`: Slices from $S_{size} + 1$ to $2 \times S_{size}$ seconds ago.
* `Segment_Prior`: Slices from $2 \times S_{size} + 1$ to $3 \times S_{size}$ seconds ago.

For each segment, the daemon computes the mean critical temperature ($T_{avg}$) where $T = \text{MAX}(\text{CPU\_Cores}, \text{GPU\_Core})$. It calculates the Throttling Ratio ($R_e$) using safe zero-division handling:
$$R_e = \frac{\text{wait\_responses}}{\text{total\_pace\_check\_calls} \text{ (Fallback to 0.0 if calls == 0)}}$$

#### Mathematical Concurrency Directives

* **System Warm-up Condition:** If the daemon has been active for less than the total configured `trend_analysis_window_seconds`, `get_guidance` queries instantly return `"HOLD"` to safeguard against premature trend reporting.
* **`SCALE_DOWN`:** Triggered if $T_{avg}(\text{Current}) > T_{avg}(\text{Previous}) > T_{avg}(\text{Prior})$ with an upward trend delta $> 0.5^\circ\text{C}/\text{min}$, OR if $R_e(\text{Current}) > 0.40$. If `emit_warnings` is `true`, it writes a system warning log to syslog.
* **`SCALE_UP`:** Triggered only if the system has operated completely below `max_target_temp - safety_margin_celsius` across the entire window, with a flat or decreasing slope and $R_e == 0.0$.
* **`HOLD`:** Default state when metrics reside within nominal steady bounds.

---

## 7. Automated Intelligent Calibration Protocol (`--calibrate`)

The `--calibrate` flag runs an isolated hardware characterization test. To enforce strict data integrity and runtime isolation:

* The calibration module must obtain an exclusive, non-blocking file lock on `/var/run/thermal_pacer.lock` utilizing Unix native `fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)`. If the lock acquisition fails or if the daemon is actively running with a `client_count > 0`, the calibration utility aborts immediately with an error notification.

1. **Chronological Validity Verification:** Parses `/etc/thermal_pacer/thermal_config.json`. If `last_calibration_utc` shows less than 30 days elapsed, it terminates with an informative notice, protecting hardware from redundant stress testing.
2. **Phase 1 (Idle Baseline):** Measures the machine at rest for 30 seconds to capture baseline $T_{idle}$.
3. **Phase 2 (Eco Thermal Profile):** Forces all cores to `"powersave"`, disables core boost via detected architecture paths, and spins a synthetic intensive matrix multiplication workload on all available threads for 60 seconds. Logs stabilization point $T_{eco}$.
4. **Phase 3 (Peak Thermal Profile):** Restores default performance governors, activates core boost, and reruns the synthetic workload for 60 seconds. Tracks the thermal ramp velocity ($\Delta T/\Delta t$) and maximum temperature $T_{peak}$.
5. **Algorithmic Evaluation and Storage Constraints:**
   * Computes optimal ceiling: $T_{\text{calculated}} = T_{eco} + 4^\circ\text{C}$.
   * **The Restrictive Principle:** Overwrites `max_target_temp` in the configuration JSON **ONLY if $T_{\text{calculated}}$ is lower (more restrictive)** than the value currently saved.
   * If the thermal ramp velocity in Phase 3 exceeded $1.5^\circ\text{C}/\text{sec}$, sets `thermal_efficiency_rating` to `"CRITICAL_COMPACT_CHASSIS"` and appends a warning to `hardware_safety_recommendation`.
   * Updates `last_calibration_utc` with current ISO 8601 UTC timestamp.

---

## 8. Deliverables and Development Acceptance Criteria

The environment delivery must strictly follow this file and module topology:

```text
thermal_pacer/
├── __init__.py          # Exposes the ThermalGuard class for the client API
├── client.py            # Implementation of Context Manager and Socket IPC
├── daemon.py            # Daemon engine code, Telemetry, and Governors
├── calibration.py       # Thermal stress experimental protocol utility
└── templates/
    ├── thermal_pacer.socket
    └── thermal_pacer.service
```

### Mandatory Test Suite (Mock Testing & Architecture Contract)

To verify metric parsing and statistical processing without depending on physical hardware heat emissions, the package must contain a test suite satisfying an explicit Dependency Injection structural contract:

1. **`TelemetryProvider` Abstract Protocol:** The daemon's telemetry acquisition worker must query an internal class interface exposing a single uniform parameterless method signature: `get_critical_temperature(self) -> float`.
2. **`MockTelemetryProvider` Implementation:** Built explicitly into the unit test suite. It implements the `get_critical_temperature` contract but replaces live `psutil`/`pynvml` sampling with a controlled state tracking sequence.
3. **Deterministic Testing:** The test suite initializes the daemon engine, injects an instance of `MockTelemetryProvider`, and programmatically pushes an artificial sequential ramp profile (e.g., simulating 180 seconds of incremental $+1.0^\circ\text{C}/\text{min}$ steps, followed by flat and downward phases). It validates that the underlying daemon background thread shifts statistical window arrays correctly, emitting `"SCALE_DOWN"`, `"SCALE_UP"`, and `"HOLD"` guidance decisions deterministically when queried by a dummy socket test connection.

---

## 9. CLI Installation Utility (`--install`)

Executed via `sudo python3 -m thermal_pacer --install`.

1. Checks that `os.geteuid() == 0` (Raises `PermissionError` if missing root privileges).
2. Checks for group `thermal`. If missing, executes `groupadd thermal` via subprocess. Resolves the calling user via `os.environ.get("SUDO_USER")`. If present, adds the user to the group via `usermod -aG thermal $SUDO_USER`; if executed from a native root login shell (where `SUDO_USER` evaluates to `None`), it gracefully logs a stdout warning notice skipping this step.
3. Inspects `sys.executable` to resolve the absolute path of the environment's interpreter, performing a **global substitution** to replace occurrences of the default `/usr/bin/python3` string inside both the `ExecStart` and `ExecStopPost` lines of the systemd service template.
4. Writes systemd configs to `/etc/systemd/system/`.
5. Creates configuration directory `/etc/thermal_pacer/` with `0755` permissions.
6. Runs subprocess commands: `systemctl daemon-reload` and `systemctl enable --now thermal_pacer.socket`.
7. Outputs a clean confirmation message: "IntelligentThermalPacer socket successfully installed and initialized via systemd."

---

## 10. CLI Uninstallation Utility (`--uninstall`)

Executed via `sudo python3 -m thermal_pacer --uninstall`.

1. Verifies root execution state (`os.geteuid() == 0`).
2. Runs subprocess commands to cleanly stop system hooks:
   * `systemctl stop thermal_pacer.service` (if currently running)
   * `systemctl disable --now thermal_pacer.socket`
   * `systemctl daemon-reload`
3. Physically deletes configuration files and system paths:
   * `/etc/systemd/system/thermal_pacer.socket`
   * `/etc/systemd/system/thermal_pacer.service`
   * `/var/run/thermal_pacer.sock` (if dangling)
   * `/var/run/thermal_pacer.governors.bak` (if dangling)
4. Deletes `/etc/thermal_pacer/` configuration files and its parent folder entirely.
5. Prints a clean confirmation message: "IntelligentThermalPacer completely uninstalled from system."
